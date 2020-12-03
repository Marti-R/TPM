

class BaslerCameraControl:
    def __init__(self):
        pass

    def get_camera_factory(self):
        tlFactory = pylon.TlFactory.GetInstance()
        cameras = tlFactory.EnumerateDevices()
