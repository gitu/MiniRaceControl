from Queue import Queue, Empty
import random
import threading
import time

import ConnectFirebase
from ConnectPlotly import StreamWriter
from ConnectCarrera import RaceTrack, TimeResult, TrackState


class RaceManager(object):
    def __init__(self, rt, export_data=False):
        self.race_state_counter = 0
        self._export_data = export_data
        self._rt = rt

        self.rounds = []
        self.cars = {}

        if export_data:
            self.sw = StreamWriter()

        self.worker = threading.Thread(target=self._reader)
        self.worker.daemon = True

        self.async_process_queue_plotly = Queue()
        self.async_worker_plotly = threading.Thread(target=self._process_async_plotly)
        self.async_worker_plotly.daemon = True

        self.async_process_queue_firebase = Queue()
        self.async_worker_firebase = threading.Thread(target=self._process_async_firebase)
        self.async_worker_firebase.daemon = True


        self._rt.add_round_listener(self._catch_round_result)
        self._rt.add_track_state_listener(self._catch_track_state)

        self.async_worker_plotly.start()
        self.async_worker_firebase.start()
        self.worker.start()

    def _reader(self):
        while True:
            self._rt.read_track(True)

    def _catch_round_result(self, nri):
        print('new round: {0}, {1}'.format(nri['car'], nri['time']))
        self.rounds.append(nri)
        car_id = nri['car']

        if not self.cars.get(car_id):
            self.cars[car_id] = {'car': car_id, 'fastest': nri['time'], 'rounds': 1}
        else:
            car = self.cars.get(car_id)
            car['rounds'] += 1
            if car['fastest'] > nri['time']:
                car['fastest'] = nri['time']

        self.race_state_counter += 1

        if self._export_data:
            def send_plotly():
                self.sw.write(nri)

            def send_firebase():
                ConnectFirebase.PiFire.write(nri)

            self.async_process_queue_firebase.put(send_firebase)
            self.async_process_queue_plotly.put(send_plotly)


    def _catch_track_state(self, track_state):
        if track_state.startLamp == 1:
            self.reset()

    def reset(self):
        print("##########################")
        print("## START NEW RACE       ##")
        print("##########################")
        self.rounds = []
        self.cars = {}

        if self._export_data:
            self.async_process_queue_firebase.put(ConnectFirebase.PiFire.reset)
            self.async_process_queue_plotly.put(self.sw.reset_sw)

    def _process_async_plotly(self):
        self._process_async('plotly', self.async_process_queue_plotly)

    def _process_async_firebase(self):
        self._process_async('firebase', self.async_process_queue_firebase)

    @staticmethod
    def _process_async(qname, queue):
        while True:
            try:
                func = queue.get()
                func()
            except Exception as e:
                print 'Error executing async task:', e
            finally:
                queue.task_done()
                print 'Q:', qname, ' size:', queue.qsize()


class CarSim(threading.Thread):
    def __init__(self, results, car):
        super(CarSim, self).__init__()
        self.results = results
        self.car = car

    def run(self):
        n = 0
        t = random.randint(1500, 15000)
        tx = t
        while n < 100:
            f1 = 0.1 if t < 1500 else 0.3
            f2 = 0.1 if t > 15000 else 0.2
            t += random.randint(-int(f1 * t), abs(int(f2 * t)))
            tx += t
            time.sleep(t / 1000.0)
            result = TimeResult(str(self.car) + "-" + str(n), False)
            result.carNr = self.car
            result.time = tx
            result.group = 1
            self.results.put(result)
            n += 1


class TrackSim(threading.Thread):
    def __init__(self, results):
        super(TrackSim, self).__init__()
        self.results = results

    def run(self):
        n = 0
        while n < 2:
            time.sleep(20)
            result = TrackState("1", False)
            result.startLamp = 1
            self.results.put(result)
            n += 1


class RaceTrackSim(RaceTrack):
    def __init__(self, cars=4):
        super(RaceTrackSim, self).__init__()
        self.results = Queue()
        self._cars = []
        self._tracksim = TrackSim(self.results)
        self._tracksim.start()
        for cid in range(cars):
            sim = CarSim(self.results, cid + 1)
            self._cars.append(sim)
            sim.start()

    def _read_state(self):
        try:
            return self.results.get(block=False)
        except Empty:
            return TrackState("0", False)


if __name__ == "__main__":
    rm = RaceManager(RaceTrackSim(4), True)

