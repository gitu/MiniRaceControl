import threading
import datetime
import plotly
import plotly.plotly as py
import plotly.tools as tls
from plotly.graph_objs import *
import time

import settings


class StreamHeartBeat(threading.Thread):
    def __init__(self, stream):
        super(StreamHeartBeat, self).__init__()
        self.stream = stream

    def run(self):
        while True:
            time.sleep(59)
            self.stream.heartbeat()


class StreamWriter(object):

    def __init__(self):
        py.sign_in(settings.plotly_login, settings.plotly_api_key)
        self.stream_count = 0
        self.streams = {}
        self.heartbeats = {}

    def get_stream(self, car):
        if self.streams.has_key(car):
            return self.streams.get(car)
        else:
            stream = py.Stream(settings.plotly_stream_id[car-1])
            stream.open()
            heartbeat = StreamHeartBeat(stream)
            heartbeat.setDaemon(True)
            heartbeat.start()
            self.streams[car] = stream
            self.heartbeats[car] = heartbeat
            return stream

    def write(self, round_data):
        scatter = Scatter(x=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), y=round_data['time'])
        print(scatter)
        return self.get_stream(round_data['car']).write(scatter)




if __name__ == "__main__":
    sw = StreamWriter()
    sw.write({'car':1,'time':3002})
    time.sleep(1)
    sw.write({'car':2,'time':323})
    sw.write({'car':3,'time':323})
    sw.write({'car':4,'time':323})
    time.sleep(1)
    sw.write({'car':1,'time':1022})
    time.sleep(1)
    sw.write({'car':2,'time':1223})
    time.sleep(1)
    sw.write({'car':1,'time':1022})
    time.sleep(1)
    sw.write({'car':2,'time':1223})




