from enum import Enum, auto
from multiprocessing import Event


class Instructions(Enum):
    Pause = auto()
    Ready = auto()
    Reset = auto()
    Dump = auto()
    Phase = auto()
    SamplingRate = auto()
    Stop = auto()
    Release = auto()


class Phases(Enum):
    Trial = auto()
    Reward = auto()
    Inter_Trial = auto()
