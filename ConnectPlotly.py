import random
import threading
import datetime
import time

import plotly.plotly as py
from plotly.graph_objs import *

import settings


class StreamHeartBeat(threading.Thread):
    def __init__(self, stream):
        super(StreamHeartBeat, self).__init__()
        self.stream = stream

    def run(self):
        while True:
            time.sleep(50)
            print('send heartbeat')
            self.stream.heartbeat()



class StreamWriter(object):

    def __init__(self, auto_start=False):
        py.sign_in(settings.plotly_login, settings.plotly_api_key, stream_ids=settings.plotly_stream_ids)
        self.stream_count = 0
        self.streams = {}
        self.heartbeats = {}
        self.reset_sw(auto_start)


    def reset_sw(self, auto_start=False):
        traces = []
        for x in range(4):
            traces.append(
                Scatter(
                    x=[],
                    y=[],
                    name='Car ' + str(x + 1),
                    stream=dict(token=settings.plotly_stream_ids[x], maxpoints=100),
                    line=Line(
                        shape='spline'
                    )
                )
            )
        layout = Layout(
            title='Confinale Race View',
            autosize=True,
            xaxis=XAxis(
                title='Time',
                showgrid=True,
                zeroline=True
            ),
            yaxis=YAxis(
                title='seconds',
                showline=False,
                type='log',
                autorange=True
            ),
            showlegend=True,
            legend=Legend(
                x=0,
                y=1,
                traceorder='normal',
                font=Font(
                    family='sans-serif',
                    size=12,
                    color='#000'
                ),
                bgcolor='#E2E2E2',
                bordercolor='#FFFFFF',
                borderwidth=2
            )
        )
        data = Data(traces)
        fig = Figure(data=data, layout=layout)
        self.url = py.plot(fig, filename='Confinale Race View', fileopt='overwrite', auto_open=auto_start)

    def get_stream(self, car):
        if not self.streams.has_key(car):
            stream = py.Stream(settings.plotly_stream_ids[car - 1])
            print('new stream for id: ' + settings.plotly_stream_ids[car - 1])
            stream.open()
            print('opened stream')
            heartbeat = StreamHeartBeat(stream)
            heartbeat.setDaemon(True)
            heartbeat.start()
            self.streams[car] = stream
            self.heartbeats[car] = heartbeat

        return self.streams.get(car)

    def write(self, round_data):
        if round_data['time'] < 40000:
            x = round_data['timestamp']
            y = round_data['time']/1000.0
            stream = self.get_stream(round_data['car'])
            try:
                stream.write({'x': x, 'y': y})
                stream.close()
            except Exception as e1:
                print("######## trying to reopen stream ########", e1)
                try:
                    stream.open()
                    stream.write({'x': x, 'y': y})
                    stream.close()
                except Exception as e2:
                    print('######## exception while writing to stream... ########', e2)



class RandomGen(threading.Thread):
    def __init__(self, streamwriter, car):
        super(RandomGen, self).__init__()
        self.car = car
        self.streamwriter = streamwriter

    def run(self):
        n = 0
        t = random.randint(1500, 15000)
        while n < 100:
            f1 = 0.1 if t<1500 else 0.3
            f2 = 0.1 if t>15000 else 0.2
            t += random.randint(-int(f1*t), abs(int(f2*t)))
            time.sleep(t / 1000.0)
            self.streamwriter.write({'car': self.car, 'time': t, 'timestamp': datetime.datetime.now()})
            print(str(n) + ' - ' + str({'car': self.car, 'time': t, 'timestamp': datetime.datetime.now()}))
            n += 1


if __name__ == "__main__":
    sw = StreamWriter(True)

    time.sleep(10)
    rg1 = RandomGen(sw, 1)
    rg1.start()
    time.sleep(5)
    rg2 = RandomGen(sw, 2)
    rg2.start()
    rg3 = RandomGen(sw, 3)
    rg3.start()
    rg4 = RandomGen(sw, 4)
    rg4.start()
    print("started all threads")

    rg1.join()
    rg2.join()
    rg3.join()
    rg4.join()
    print("joined threads")






