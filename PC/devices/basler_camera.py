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
        print(f'In saving: {len(self.record)}')
        for image in self.record:
            writer.append_data(image)
        writer.close()


class BaslerImageHandler(pylon.ImageEventHandler):
    def __init__(self, parent):
        super(BaslerImageHandler, self).__init__()
        self.parent = parent
        self.buffer = []
        self.meta = {}

    def OnImagesSkipped(self, camera, countOfSkippedImages):
        print(f'Camera {self.parent.name} has skipped {countOfSkippedImages} images!\n')

    def OnImageGrabbed(self, camera, grabResult):
        if grabResult.GrabSucceeded():
            grabArray = grabResult.GetArray()
            self.parent.current_frame = np.array(grabArray)[::10, ::10]
            if self.parent.is_recording:
                self.buffer.append(grabArray)
                self.meta[len(self.buffer)] = {
                    'NumberOfSkippedImages': grabResult.NumberOfSkippedImages,
                    'TimeStamp': grabResult.TimeStamp,
                }
            else:
                print("Error: ", grabResult.GetErrorCode(), grabResult.GetErrorDescription())

    def clear_buffer(self):
        self.buffer = []

class BaslerCameraProcess(Process):
    def __init__(self, assigned_camera, assigned_name):
        super(BaslerCameraProcess, self).__init__()

        self.camera = pylon.InstantCamera(assigned_camera)
        self.camera.Open()
        pylon.FeaturePersistence.Load("Camera_Settings.pfs", self.camera.GetNodeMap())
        self.image_event_handler = BaslerImageHandler(self)
        self.camera.RegisterCameraEventHandler(self.image_event_handler, pylon.RegistrationMode_ReplaceAll,
                                               pylon.Cleanup_Delete)
        self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne, pylon.GrabLoop_ProvidedByInstantCamera)

        self.name = assigned_name

        self.current_frame = None

        self.saving_process = None

        self.is_recording = True
        self.is_alive = True

    def run(self):
        while self.is_alive:
            time.sleep(0.05)

        if self.saving_process and self.saving_process.is_alive():
            self.saving_process.join()

        self.camera.StopGrabbing()
        self.camera.Close()

    def set_camera_mode(self, mode):
        if mode == 'hw_trigger':
            self.camera.TriggerMode.SetValue("On")
        elif mode == 'no_trigger':
            self.camera.TriggerMode.SetValue("Off")
        else:
            print(f'Unknown mode: {mode}')

    def stop_process(self):
        self.is_alive = False

    def save_buffer(self, saving_location, fps):
        if self.saving_process and self.saving_process.is_alive():
            self.saving_process.join()

        self.saving_process = VideoSaveProcess(saving_location, fps, self.image_event_handler.buffer)
        self.saving_process.start()
        self.image_event_handler.clear_buffer()
