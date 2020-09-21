import pyaudio
import wave
import time
import numpy as np

RATE = 384000
CHUNK = int(4996)


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

if __name__ == '__main__':
    audio = AudioHandler()
    audio.start()
    time.sleep(6)
    audio.stop()
    audio.save('test.wav')
    audio.close()

