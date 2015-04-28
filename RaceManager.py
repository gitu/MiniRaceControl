import ConnectFirebase
from ConnectPlotly import StreamWriter
import settings
from ConnectCarrera import RaceTrack


class RaceManager(object):
    def __init__(self, export_data=False):
        self.race_state_counter = 0
        self._export_data = export_data
        self._rt = RaceTrack(settings.serial_port)

        self._rt.add_round_listener(self.catch_round_result)
        self._rt.add_track_state_listener(self.catch_track_state)
        self.rounds = []
        self.cars = {}

        if export_data:
            self.sw = StreamWriter()

    def catch_round_result(self, nri):
        self.rounds.append(nri)
        car_id = nri['car']

        if not self.cars.get(car_id):
            self.cars[car_id] = {'car': car_id, 'fastest': nri['time'], 'rounds': 1}
        else:
            car = self.cars.get(car_id)
            car['rounds'] += 1
            if car['fastest'] > nri['time']:
                car['fastest'] = nri['time']

        if  self._export_data:
            ConnectFirebase.PiFire.write_async(nri)
            self.sw.write_async(nri)

        self.race_state_counter += 1


    def catch_track_state(self, track_state):
        if track_state.startLamp == 1:
            self.reset()

    def reset(self):
        print("##########################")
        print("## START NEW RACE       ##")
        print("##########################")
        self.rounds = []
        self.cars = {}

        if self._export_data:
            self.sw.reset_sw()
            ConnectFirebase.PiFire.reset()


if __name__ == "__main__":
    rm = RaceManager(True)

