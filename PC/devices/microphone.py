from multiprocessing import Process
import pyaudio
import time
import wave


class AudioSaveHandler(Process):
    def __init__(self, saving_location, settings, record):
        super(AudioSaveHandler, self).__init__()
        self.saving_location = saving_location
        self.settings = settings
        self.record = record

    def run(self):
        with wave.open(self.saving_location, 'wb') as wavefile:
            wavefile.setnchannels(self.settings["channels"])
            wavefile.setsampwidth(self.settings["sample_width"])
            wavefile.setframerate(self.settings["sampling_rate"])


class MicrophoneProcess(Process):
    def __init__(self, initial_settings, assigned_name):
        super(MicrophoneProcess, self).__init__()

        self.settings = initial_settings
        self.name = assigned_name

        self.pa = pyaudio.PyAudio()
        self.settings["sample_width"] = self.pa.get_sample_size(pyaudio.paInt32)
        self.stream = self.pa.open(format=pyaudio.paInt32,
                                   channels=self.settings["channels"],
                                   rate=self.settings["sampling_rate"],
                                   input=True,
                                   input_device_index=initial_settings["microphone_index"],
                                   frames_per_buffer=initial_settings["buffer_frames"])

        self.buffer = []
        self.meta = {}

        self.current_sample = None

        self.saving_process = None

        self.recording = True
        self.alive = True

    def run(self):
        self.stream.start_stream()

        while self.alive:
            sample = self.stream.read(self.settings["buffer_frames"])
            self.current_sample = sample

            if self.recording:
                self.buffer.append(sample)

            time.sleep(self.settings["read_interval"])

        if self.saving_process and self.saving_process.is_alive():
            self.saving_process.join()

        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

    def stop_process(self):
        self.alive = False

    def set_recording(self, value):
        self.recording = value

    def return_buffer(self):
        buffer = self.buffer
        self.buffer = []
        return buffer

    def save_buffer(self, saving_location):
        self.meta['save'] = time.time()

        if self.saving_process and self.saving_process.is_alive():
            self.saving_process.join()

        self.saving_process = AudioSaveHandler(self.settings, self.return_buffer())
        self.saving_process.start()