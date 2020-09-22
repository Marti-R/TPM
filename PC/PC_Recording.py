from pypylon import pylon
from imageio import get_writer
import pyaudio
from multiprocessing import Process, Manager
from ctypes import c_wchar_p
import json
import wave
import time
import tkinter as tk
from PIL import ImageTk, Image

class VideoHandlerProcess(Process):
    def __init__(self, process_id, alive_flag, recording_flag, saving_list, saving_location, device_id):
        super().__init__()
        self.process_id = process_id
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
        self.current_frame = None
        self.meta = {}

    def run(self):
        self.TlFactory = pylon.TlFactory.GetInstance()
        self.devices = self.TlFactory.EnumerateDevices()
        self.camera = pylon.InstantCamera(self.TlFactory.CreateDevice(self.devices[self.device_id]))
        self.camera.StartGrabbing()
        self.framerate = 1000000 / self.camera.ExposureTime.Value
        print('camera ' + str(self.device_id) + ' model name')
        print(self.devices[self.device_id].GetModelName(), "-", self.devices[self.device_id].GetSerialNumber())

        self.alive_flag.wait()
        time_reference = time.perf_counter()
        self.meta['start'] = time.time()

        while self.alive_flag.is_set():
            if self.camera.IsGrabbing():
                grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if grabResult.GrabSucceeded():
                    self.current_frame = grabResult.Array
                    if self.recording_flag.is_set:
                        self.buffer.append(self.current_frame)
                        self.meta[grabResult.ImageNumber] = {
                            'NumberOfSkippedImages': grabResult.NumberOfSkippedImages,
                            'TimeStamp': grabResult.TimeStamp,
                            'RelativeTimeStamp': time.perf_counter() - time_reference
                        }
                else:
                    print("Error: ", grabResult.ErrorCode, grabResult.ErrorDescription)
                grabResult.Release()
            if self.saving_list[self.process_id]:
                self.meta['save'] = time.time()
                with get_writer(rf'{self.saving_location.value}\cam{self.device_id}.avi', fps=self.framerate) as writer:
                    for image in self.buffer:
                        writer.append_data(image)
                with open(rf'{self.saving_location.value}\cam{self.device_id}_meta.json', 'w') as outfile:
                    json.dump(self.meta, outfile)
                # print(len(self.buffer))
                self.buffer = []
                self.meta = {}
                self.saving_list[self.process_id] = 0

        self.camera.StopGrabbing()
        self.camera.Close()


class AudioHandlerProcess(Process):
    def __init__(self, process_id, alive_flag, recording_flag, saving_list, saving_location, device_id):
        super().__init__()
        self.process_id = process_id
        self.alive_flag = alive_flag
        self.recording_flag = recording_flag
        self.saving_list = saving_list
        self.saving_location = saving_location
        self.device_id = device_id

        self.pa = None
        self.stream = None

        self.buffer = []
        self.current_chunk = None
        self.meta = {}

    def run(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=pyaudio.paInt32,
                                   channels=1,
                                   rate=384000,
                                   input=True,
                                   input_device_index=self.device_id,
                                   frames_per_buffer=4096)

        print('Device %{}: %{}'.format(self.device_id, self.pa.get_device_info_by_index(self.device_id)['name']))

        self.alive_flag.wait()
        time_reference = time.perf_counter()
        self.meta['start'] = time.time()

        while self.alive_flag.is_set():
            self.current_chunk = self.stream.read(4096, exception_on_overflow=False)

            if self.recording_flag.is_set:
                self.buffer.append(self.current_chunk)

            if self.saving_list[self.process_id]:
                self.meta['save'] = time.time()
                self.meta['delta'] = time.perf_counter() - time_reference
                with wave.open(rf'{self.saving_location.value}\mic{self.device_id}.wav', 'wb') as wavefile:
                    wavefile.setnchannels(1)
                    wavefile.setsampwidth(self.pa.get_sample_size(pyaudio.paInt32))
                    wavefile.setframerate(384000)
                    wavefile.writeframes(b''.join(self.buffer))
                with open(rf'{self.saving_location.value}\mic{self.device_id}_meta.json', 'w') as outfile:
                    json.dump(self.meta, outfile)
                # print(len(self.buffer))
                self.buffer = []
                self.meta = {}
                self.saving_list[self.process_id] = 0

        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()


class TkHandler(Process):
    def __init__(self):
        super().__init__()
        self.window = None

    def run(self):
        self.window = tk.Tk()

        frame1 = tk.Frame(master=self.window, width=200, height=100, bg="red")
        frame1.pack(fill=tk.Y, side=tk.LEFT)

        frame2 = tk.Frame(master=self.window, width=100, bg="yellow")
        frame2.pack(fill=tk.Y, side=tk.LEFT)

        frame3 = tk.Frame(master=self.window, width=50, bg="blue")
        frame3.pack(fill=tk.Y, side=tk.LEFT)

        self.window.mainloop()


class App:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)

        self.canvas = tkinter.Canvas(window, width=600, height=600)
        self.canvas.pack()

        # After it is called once, the update method will be automatically called every delay milliseconds
        self.delay = 20
        self.update()

        self.window.mainloop()

    def update(self):
        # Get a frame from the video source

        self.window.after(self.delay, self.update)


if __name__ == '__main__':
    tlFactory = pylon.TlFactory.GetInstance()
    cameras = tlFactory.EnumerateDevices()

    pa = pyaudio.PyAudio()
    microphones = []
    valid_mics = ['Microphone (UltraMic384K 16bit ']
    for i in range(pa.get_device_count()):
        devinfo = pa.get_device_info_by_index(i)
        for name in valid_mics:
            if name == devinfo['name']:
                microphones.append(i)

    handler_processes = []
    manager = Manager()
    all_alive = manager.Event()
    all_recording = manager.Event()
    saving_list = manager.list([0] * (len(cameras) + len(microphones)))
    saving_location = manager.Value(c_wchar_p, r'trial0\\')

    # Create a window and pass it to the Application object
    App = TkHandler()
    App.daemon = True
    App.start()

    process_id = 0
    for device in cameras:
        p = VideoHandlerProcess(process_id, all_alive, all_recording, saving_list, saving_location, process_id)
        p.daemon = True
        p.start()
        handler_processes.append(p)
        process_id += 1

    for device in microphones:
        p = AudioHandlerProcess(process_id, all_alive, all_recording, saving_list, saving_location, device)
        p.daemon = True
        p.start()
        handler_processes.append(p)
        process_id += 1

    time.sleep(2)
    all_alive.set()
    all_recording.set()
    time.sleep(2)
    all_recording.clear()

    saving_list[:] = [1] * len(saving_list)

    all_alive.clear()

    while sum(saving_list) != 0:
        pass

    for i, handler in enumerate(handler_processes):
        handler.join()

