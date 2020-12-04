from pypylon import pylon
from multiprocessing import Process
import numpy as np
import time
from imageio import get_writer


class VideoSaveProcess(Process):
    def __init__(self, saving_location, fps, record):
        super(VideoSaveProcess, self).__init__()
        self.saving_location = saving_location
        self.fps = fps
        self.record = record

    def run(self):
        writer = get_writer(self.saving_location, fps=self.fps)
        for image in self.record:
            writer.append_data(image)
        writer.close()


class BaslerImageHandler(pylon.ImageEventHandler):
    def __init__(self, parent):
        super(BaslerImageHandler, self).__init__()
        self.parent = parent

        self.buffer = []
        self.meta = {}

        self.recording = False

    def OnImagesSkipped(self, camera, countOfSkippedImages):
        print(f'Camera {self.parent.name} has skipped {countOfSkippedImages} images!\n')

    def OnImageGrabbed(self, camera, grabResult):
        if grabResult.GrabSucceeded():
            grabArray = grabResult.GetArray()
            self.parent.set_current_frame(np.array(grabArray)[::10, ::10])
            if self.recording:
                self.buffer.append(grabArray)
                self.meta[len(self.buffer)] = {
                    'NumberOfSkippedImages': grabResult.NumberOfSkippedImages,
                    'TimeStamp': grabResult.TimeStamp,
                }
            else:
                print("Error: ", grabResult.GetErrorCode(), grabResult.GetErrorDescription())

    def return_buffer(self):
        buffer = self.buffer
        self.buffer = []
        return buffer

    def set_recording(self, value):
        self.recording = value


class BaslerCameraProcess(Process):
    def __init__(self, assigned_camera_index, assigned_name):
        super(BaslerCameraProcess, self).__init__()

        self.camera_index = assigned_camera_index

        # cannot be initiated during init, must be created after process starts
        self.camera = None
        self.image_event_handler = None

        self.name = assigned_name

        self.current_frame = None
        self.saving_process = None

        self.alive = True

    def run(self):
        self.camera_setup()

        while self.alive:
            time.sleep(0.05)

        if self.saving_process and self.saving_process.alive():
            self.saving_process.join()

        self.camera.StopGrabbing()
        self.camera.Close()

    def camera_setup(self):
        # sadly necessary since (python) multiprocessing is incapable of working with anything more complex than a dict
        TlFactory = pylon.TlFactory.GetInstance()
        available_devices = TlFactory.EnumerateDevices()
        assigned_camera = TlFactory.CreateDevice(available_devices[self.camera_index])

        self.camera = pylon.InstantCamera(assigned_camera)
        self.image_event_handler = BaslerImageHandler(self)

        self.camera.Open()
        pylon.FeaturePersistence.Load("Camera_Settings.pfs", self.camera.GetNodeMap())
        self.camera.RegisterCameraEventHandler(self.image_event_handler, pylon.RegistrationMode_ReplaceAll,
                                               pylon.Cleanup_Delete)
        self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne, pylon.GrabLoop_ProvidedByInstantCamera)

    def set_camera_mode(self, mode):
        if mode == 'hw_trigger':
            self.camera.TriggerMode.SetValue("On")
        elif mode == 'no_trigger':
            self.camera.TriggerMode.SetValue("Off")
        else:
            print(f'Unknown mode: {mode}')

    def set_current_frame(self, frame):
        self.current_frame = frame

    def set_recording(self, value):
        self.image_event_handler.set_recording(value)

    def stop_process(self):
        self.alive = False

    def save_buffer(self, saving_location, fps):
        if self.saving_process and self.saving_process.is_alive():
            self.saving_process.join()

        self.saving_process = VideoSaveProcess(saving_location, fps, self.image_event_handler.return_buffer())
        self.saving_process.start()
