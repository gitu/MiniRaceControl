
import time
from ConnectCarrera import RaceTrackImpl
from RaceManager import RaceManager
import settings

race_manager = RaceManager(RaceTrackImpl(settings.serial_port), False)
race_manager.start()
