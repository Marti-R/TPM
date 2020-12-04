from pypylon import pylon


class BaslerCameraControl:
    def __init__(self):
        self.cameras = {}
        self.update_cameras()

    def update_cameras(self):
        TlFactory = pylon.TlFactory.GetInstance()
        available_devices = TlFactory.EnumerateDevices()

        for device_index, device in enumerate(available_devices):
            self.cameras[device_index] = TlFactory.CreateDevice(device)