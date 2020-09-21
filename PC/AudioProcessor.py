# from https://stackoverflow.com/questions/43353172/producing-spectrogram-from-microphone
# kazemakase and syb0rg

import pyaudio
import struct
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

THRESHOLD = 40  # dB
RATE = 384000
INPUT_BLOCK_TIME = 1  # 30 ms
INPUT_FRAMES_PER_BLOCK = int(RATE * INPUT_BLOCK_TIME)


def get_rms(block):
    return np.sqrt(np.mean(np.square(block)))


class AudioHandler(object):
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.open_mic_stream()
        self.threshold = THRESHOLD
        self.plot_counter = 0

    def stop(self):
        self.stream.close()

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

    def open_mic_stream(self):
        device_index = self.find_input_device()

        stream = self.pa.open(format=pyaudio.paInt32,
                              channels=1,
                              rate=RATE,
                              input=True,
                              input_device_index=device_index,
                              frames_per_buffer=INPUT_FRAMES_PER_BLOCK)

        return stream

    def processBlock(self, snd_block):
        # f, t, Sxx = signal.spectrogram(snd_block, RATE, nperseg=65, nfft=256, noverlap=60)
        f, t, Sxx = signal.spectrogram(snd_block, RATE, noverlap=250)
        dBS = 10 * np.log10(Sxx)  # convert to dB
        plt.pcolormesh(t, f, dBS)
        plt.ylabel('Frequency [Hz]')
        plt.xlabel('Time [sec]')
        plt.savefig('spec{}.png'.format(self.plot_counter), bbox_inches='tight')
        self.plot_counter += 1

    def listen(self):
        try:
            raw_block = self.stream.read(INPUT_FRAMES_PER_BLOCK, exception_on_overflow=False)
            count = len(raw_block) / 2
            format = '%dh' % (count)
            snd_block = np.array(struct.unpack(format, raw_block))
        except Exception as e:
            print('Error recording: {}'.format(e))
            return

        amplitude = get_rms(snd_block)
        if amplitude > self.threshold:
            self.processBlock(snd_block)
        else:
            pass


if __name__ == '__main__':
    audio = AudioHandler()
    for i in range(0, 1):
        audio.listen()
