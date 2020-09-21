from pypylon import genicam
from pypylon import pylon
import os

try:
    #Get the transport layer factory.
    tlFactory = pylon.TlFactory.GetInstance()

    #Get all attached devices and exit application if no device is found.
    devices = tlFactory.EnumerateDevices()
    if len(devices) == 0:
        raise pylon.RUNTIME_EXCEPTION("No camera present.")

    # Create an array of instant cameras for the found devices and avoid exceeding a maximum number of devices.
    cameras = pylon.InstantCameraArray(min(len(devices), 1))

    l = cameras.GetSize()

    # Create and attach all Pylon Devices.
    for i, cam in enumerate(cameras):
        cam.Attach(tlFactory.CreateDevice(devices[i]))

        cam.Open()

        print('camera ' + str(i) + ' model name')
        print(cam.GetDeviceInfo().GetModelName(), "-", cam.GetDeviceInfo().GetSerialNumber())
        # Print the model name of the camera.
        print("Using device ", cam.GetDeviceInfo().GetModelName())
        cam.Close()
        print()

finally:
    pass