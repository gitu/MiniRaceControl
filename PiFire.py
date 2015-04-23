import random
import threading
import datetime
import firebase
from multiprocessing import freeze_support
import time

import settings


freeze_support()

def cb(input):
    print(input)

class PiFire(object):
    def  __init__(self):
        self.fb = firebase.FirebaseApplication(settings.firebase_url, authentication=firebase.FirebaseAuthentication(settings.firebase_secret, settings.firebase_email))

    def write(self, round_data):
        self.fb.post(url='/rounds/', data=round_data, params={'print': 'pretty'})



class RandomGen(threading.Thread):
    def __init__(self, pifire, car):
        super(RandomGen, self).__init__()
        self.car = car
        self.pifire = pifire

    def run(self):
        n = 0
        t = random.randint(1500, 15000)
        while n < 100:
            f1 = 0.1 if t<1500 else 0.3
            f2 = 0.1 if t>15000 else 0.2
            t += random.randint(-int(f1*t), abs(int(f2*t)))
            time.sleep(t / 1000.0)
            self.pifire.write({'car': self.car, 'time': t, 'timestamp': datetime.datetime.now()})
            print(str(n) + ' - ' + str({'car': self.car, 'time': t, 'timestamp': datetime.datetime.now()}))
            n += 1


if __name__ == "__main__":
    freeze_support()

    sw = PiFire()

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