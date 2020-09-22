import pyaudio
import wave
import time
import numpy as np
from multiprocessing import Process, Manager
from ctypes import c_wchar_p
import json

class AudioHandler(object):
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.open_mic_stream()
        self.record = []
        self.active = False

    def stop(self):
        self.active = False

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

    def find_input_device(self):
        device_index = None
        for i in range(self.pa.get_device_count()):
            devinfo = self.pa.get_device_info_by_index(i)
            print('Device %{}: %{}'.format(i, devinfo['name']))

            for keyword in ['ultramic']:
                if keyword in devinfo['name'].lower():
                    print('Found an input: device {} - {}'.format(i, devinfo['name']))
                    device_index = i
                    return device_index

        if device_index == None:
            print('No preferred input found; using default input device.')

        return device_index

    # define callback (2)
    def callback(self, in_data, frame_count, time_info, status):
        if self.active:
            self.record.append(in_data)
        data = np.zeros(frame_count*1).tobytes()
        if False:
            callback_flag = pyaudio.paComplete
        else:
            callback_flag = pyaudio.paContinue
        return data, callback_flag

        raw_block = self.stream.read(CHUNK, exception_on_overflow=False)
        self.record.append(raw_block)

    def open_mic_stream(self):
        device_index = self.find_input_device()

        stream = self.pa.open(format=pyaudio.paInt16,
                              channels=1,
                              rate=RATE,
                              input=True,
                              input_device_index=device_index,
                              frames_per_buffer=CHUNK,
                              stream_callback=self.callback)

        return stream

    def save(self, location):
        self.active = False
        waveFile = wave.open(location, 'wb')
        waveFile.setnchannels(1)
        waveFile.setsampwidth(self.pa.get_sample_size(pyaudio.paInt16))
        waveFile.setframerate(RATE)
        waveFile.writeframes(b''.join(self.record))
        self.record = []
        waveFile.close()

    def start(self):
        self.active = True


class AudioHandlerProcess(Process):
    def __init__(self, alive_flag, recording_flag, saving_list, saving_location, device_id, process_id):
        super().__init__()
        self.alive_flag = alive_flag
        self.recording_flag = recording_flag
        self.saving_list = saving_list
        self.saving_location = saving_location
        self.device_id = device_id
        self.process_id = process_id

        self.pa = None
        self.stream = None

        self.buffer = []
        self.current_chunk = None
        self.meta = {}
        self.alive_time = 0

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
        self.alive_time = time.perf_counter()
        self.meta['start'] = time.time()

        while self.alive_flag.is_set():
            self.current_chunk = self.stream.read(4096, exception_on_overflow=False)

            if self.recording_flag.is_set:
                self.buffer.append(self.current_chunk)

            if self.saving_list[self.process_id]:
                self.meta['stop'] = time.time()
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


if __name__ == '__main__':
    pa = pyaudio.PyAudio()
    devices = []
    handler_processes = []

    valid_mics = ['Microphone (UltraMic384K 16bit ']
    print(pa.get_device_count())
    for i in range(pa.get_device_count()):
        devinfo = pa.get_device_info_by_index(i)
        print('Device %{}: %{}'.format(i, devinfo['name']))
        for name in valid_mics:
            if name == devinfo['name']:
                devices.append(i)

    print(devices)

    manager = Manager()
    all_alive = manager.Event()
    all_recording = manager.Event()
    mic_list = manager.list([0] * len(devices))
    saving_location = manager.Value(c_wchar_p, r'trial0\\')

    for process_id, device_id in enumerate(devices):
        p = AudioHandlerProcess(all_alive, all_recording, mic_list, saving_location, device_id, process_id)
        p.daemon = True
        p.start()
        handler_processes.append(p)

    time.sleep(2)
    all_alive.set()
    all_recording.set()
    time.sleep(5)
    all_recording.clear()

    mic_list[:] = [1] * len(mic_list)

    all_alive.clear()

    while sum(mic_list) != 0:
        pass

    for i, handler in enumerate(handler_processes):
        handler.join()

