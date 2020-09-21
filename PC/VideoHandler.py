from pypylon import pylon
from imageio import get_writer
from threading import Thread
from multiprocessing import Process, Manager
from ctypes import c_wchar_p
import json
import time

class VideoHandler(object):
    def __init__(self, camera):
        self.camera = pylon.InstantCamera(camera)
        self.camera.Open()
        self.camera.StartGrabbing()
        self.camera.ExposureTime = 10000
        self.framerate = 1000000 / self.camera.ExposureTime.Value

        self.current_frame = []
        self.buffer = []
        self.recording = False
        self.alive = True

        self.update_thread = Thread(target=self.update, args=())
        self.update_thread.daemon = True
        self.update_thread.start()

    def update(self):
        while self.alive:
            if self.camera.IsGrabbing():
                grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if grabResult.GrabSucceeded():
                    self.current_frame = grabResult.Array
                    if self.recording:
                        self.buffer.append(self.current_frame)
                else:
                    print("Error: ", grabResult.ErrorCode, grabResult.ErrorDescription)
                grabResult.Release()

    def start_recording(self):
        self.recording = True

    def stop_recording(self):
        self.recording = False

    def close(self):
        self.alive = False
        self.update_thread.join()
        self.camera.StopGrabbing()
        self.camera.Close()

    def save(self, location):
        self.active = False
        with get_writer(location, fps=self.framerate) as writer:
            for image in self.buffer:
                writer.append_data(image)
        self.buffer = []


class VideoHandlerProcess(Process):
    current_frame = []

    def __init__(self, alive_flag, recording_flag, saving_list, saving_location, device_id):
        super().__init__()
        self.alive_flag = alive_flag
        self.recording_flag = recording_flag
        self.saving_list = saving_list
        self.saving_location = saving_location
        self.device_id = device_id

        self.TlFactory = None
        self.devices = None
        self.camera = None
        self.framerate = None

        self.buffer = []
        self.meta = {}
        self.alive_time = 0

    def run(self):
        self.TlFactory = pylon.TlFactory.GetInstance()
        self.devices = self.TlFactory.EnumerateDevices()
        self.camera = pylon.InstantCamera(self.TlFactory.CreateDevice(self.devices[self.device_id]))
        self.camera.StartGrabbing()
        self.framerate = 1000000 / self.camera.ExposureTime.Value
        print('camera ' + str(self.device_id) + ' model name')
        print(self.devices[self.device_id].GetModelName(), "-", self.devices[self.device_id].GetSerialNumber())
        self.alive_flag.wait()
        self.alive_time = time.perf_counter()

        while self.alive_flag.is_set():
            if self.camera.IsGrabbing():
                grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if grabResult.GrabSucceeded():
                    current_frame = grabResult.Array
                    if self.recording_flag.is_set:
                        self.buffer.append(current_frame)
                        self.meta[grabResult.ImageNumber] = {
                            'NumberOfSkippedImages': grabResult.NumberOfSkippedImages,
                            'TimeStamp': grabResult.TimeStamp,
                            'RelativeTimeStamp': time.perf_counter() - self.alive_time
                        }
                else:
                    print("Error: ", grabResult.ErrorCode, grabResult.ErrorDescription)
                grabResult.Release()
            if self.saving_list[self.device_id]:
                with get_writer(rf'{self.saving_location.value}\cam{self.device_id}.avi', fps=self.framerate) as writer:
                    for image in self.buffer:
                        writer.append_data(image)
                with open(rf'{self.saving_location.value}\cam{self.device_id}_meta.json', 'w') as outfile:
                    json.dump(self.meta, outfile)
                # print(len(self.buffer))
                self.buffer = []
                self.meta = {}
                self.saving_list[self.device_id] = 0

        self.camera.StopGrabbing()
        self.camera.Close()


if __name__ == '__main__':
    tlFactory = pylon.TlFactory.GetInstance()
    devices = tlFactory.EnumerateDevices()
    cam_processes = []

    manager = Manager()
    all_alive = manager.Event()
    all_recording = manager.Event()
    saving_list = manager.list([0] * len(devices))
    saving_location = manager.Value(c_wchar_p, r'trial0\\')

    for i in range(len(devices)):
        p = VideoHandlerProcess(all_alive, all_recording, saving_list, saving_location, i)
        p.daemon = True
        p.start()
        cam_processes.append(p)

    time.sleep(2)
    all_alive.set()
    all_recording.set()
    time.sleep(2)
    all_recording.clear()

    saving_list[:] = [1] * len(saving_list)

    all_alive.clear()

    while sum(saving_list) != 0:
        pass

    for i, cam_process in enumerate(cam_processes):
        cam_process.join()
