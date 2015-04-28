from pprint import pprint
import datetime
import time

import serial


class TrackState(object):
    def __init__(self, command):
        self.command = command
        self.gas1 = ord(command[2]) & 0x0F
        self.gas2 = ord(command[3]) & 0x0F
        self.gas3 = ord(command[4]) & 0x0F
        self.gas4 = ord(command[5]) & 0x0F
        self.gas5 = ord(command[6]) & 0x0F
        self.gas6 = ord(command[7]) & 0x0F
        self.startLamp = ord(command[10]) & 0x0F
        self.gasMode = ord(command[11]) & 0x0F
        self.pitLaneBitMask = ((ord(command[12]) & 0x0F) << 1) + (ord(command[13]) & 0x0F)
        self.positionMode = ord(command[14]) & 0x0F

    def __eq__(self, other):
        if type(other) != TrackState:
            return False
        return self.command == other.command


class TimeResult(object):
    def __init__(self, command):
        self.command = command
        self.carNr = ord(command[1]) - 48
        self.group = ord(command[10]) - 48

        result = 0
        byte_time = command[2:10]

        result += (ord(byte_time[1]) & 0xF) << 28
        result += (ord(byte_time[0]) & 0xF) << 24
        result += (ord(byte_time[3]) & 0xF) << 20
        result += (ord(byte_time[2]) & 0xF) << 16
        result += (ord(byte_time[5]) & 0xF) << 12
        result += (ord(byte_time[4]) & 0xF) << 8
        result += (ord(byte_time[7]) & 0xF) << 4
        result += (ord(byte_time[6]) & 0xF)
        self.time = result

        self.createTime = datetime.datetime.now()

    def __eq__(self, other):
        if type(other) != TimeResult:
            return False
        return self.command == other.command


class RaceTrack(object):
    def __init__(self, port):
        self.round_listener = []
        self.track_state_listeners = []
        self.time_listeners = []
        self.port = port
        self.ser = serial.Serial(port, 19200, timeout=1)
        print(self.ser.name)
        self.ser.write('"=')
        self._readline()
        self.listeners = []
        self.reset()
        self.last_state = 0

    def process_round_data(self, new_time_result):
        if self.cars.get(new_time_result.carNr) and self.cars.get(new_time_result.carNr).time != new_time_result.time:
            new_round = {'timestamp': new_time_result.createTime, 'time': new_time_result.time - self.cars[new_time_result.carNr].time, 'car': new_time_result.carNr}
            self.rounds.append(new_round)
            for listener in self.round_listener:
                listener(new_round)
        self.cars[new_time_result.carNr] = new_time_result

    def reset(self):
        self.rounds = []
        self.cars = {}

    def _readline(self, eol='$'):
        len_eol = len(eol)
        line = bytearray()
        while True:
            c = self.ser.read(1)
            if c:
                line += c
                if line[-len_eol:] == eol:
                    break
            else:
                break
        return bytes(line)

    def read_state(self):
        self.ser.write('"?')
        result = self._readline()
        if result.startswith('?:'):
            return TrackState(result)
        else:
            return TimeResult(result)

    def add_listener(self, listener):
        self.listeners.append(listener)

    def add_track_state_listener(self, listener):
        self.track_state_listeners.append(listener)

    def add_time_listener(self, listener):
        self.time_listeners.append(listener)

    def add_round_listener(self, listener):
        self.round_listener.append(listener)


    def read_track(self, do_sleep=True):
        try:
            state = self.read_state()
            changed = False
            if self.last_state == state:
                if do_sleep:
                    time.sleep(0.01)
            else:
                changed = True
                for listener in self.listeners:
                    listener(state)
                if type(state) == TimeResult:
                    for listener in self.time_listeners:
                        listener(state)
                    self.process_round_data(state)
                elif type(state) == TrackState:
                    for listener in self.track_state_listeners:
                        listener(state)
            self.last_state = state
            return changed
        except IndexError:
            return False

    def continues_reader(self):
        while True:
            self.read_track()


if __name__ == "__main__":
    assert TimeResult("?2003037?>1=").time == 226287
    assert TimeResult("?20030:9211<").time == 236050
    assert TimeResult("?200301<?618").time == 246127
    assert TimeResult("?200301<?618") == TimeResult("?200301<?618")

    rt = RaceTrack('COM5')

    def time_result(result):
        print("new time_result:")
        pprint(result.__dict__)

    def round_result(result):
        print("new round_result:")
        pprint(result)


    rt.add_time_listener(time_result)
    rt.add_round_listener(round_result)

    rt.continues_reader()