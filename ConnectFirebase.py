import json
import random
import threading
import datetime
import time

import requests

import settings


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()
        else:
            return super(DateTimeEncoder, self).default(obj)


def cb(input):
    print(input)


class PiFire(object):
    @staticmethod
    def reset():
        url = 'https://{0}.firebaseio.com/rounds.json?auth={1}'.format(settings.firebase_name, settings.firebase_secret)
        return requests.put(url, DateTimeEncoder().encode([]))

    @staticmethod
    def write(round_data):
        url = 'https://{0}.firebaseio.com/rounds.json?auth={1}'.format(settings.firebase_name, settings.firebase_secret)
        return requests.post(url, DateTimeEncoder().encode(round_data))


class RandomGen(threading.Thread):
    def __init__(self, pifire, car):
        super(RandomGen, self).__init__()
        self.car = car
        self.pifire = pifire

    def run(self):
        n = 0
        t = random.randint(1500, 15000)
        while n < 100:
            f1 = 0.1 if t < 1500 else 0.3
            f2 = 0.1 if t > 15000 else 0.2
            t += random.randint(-int(f1 * t), abs(int(f2 * t)))
            time.sleep(t / 1000.0)
            self.pifire.write({'car': self.car, 'time': t, 'timestamp': datetime.datetime.now()})
            print(str(n) + ' - ' + str({'car': self.car, 'time': t, 'timestamp': datetime.datetime.now()}))
            n += 1


if __name__ == "__main__":
    sw = PiFire()

    sw.reset()

    time.sleep(5)

    rg1 = RandomGen(sw, 1)
    rg1.start()
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

