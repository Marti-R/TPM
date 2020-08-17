from enum import Enum, auto


class Instructions(Enum):
    Ready = auto()
    Start_Trial = auto()
    Set_Disk = auto()
    Trial_Aborted = auto()
    End_Trial = auto()
    Sending_Records = auto()
    Stop_Experiment = auto()


class Phases(Enum):
    Trial = auto()
    Reward = auto()
    Inter_Trial = auto()
