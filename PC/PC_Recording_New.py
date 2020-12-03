from multiprocessing import Process, Manager
from pid import PidFile, PidFileError
from time import sleep


class RecordingDeviceManager(Process):
    def __init__(self):
        super(RecordingDeviceManager, self).__init__()

    def run(self):
        try:
            with PidFile('Recorder'):

                while True:
                    self.counter += 1

        except PidFileError:
            print('Process already running!')


if __name__ == '__main__':
    test_process = RecordingDeviceManager()
    test_process.daemon = True
    test_process.start()

    test_process2 = RecordingDeviceManager()
    test_process2.daemon = True
    test_process2.start()

    sleep(10)
