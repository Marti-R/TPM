import os
from pypylon import pylon
from imageio import get_writer

camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()

fsamp = 50
time_exposure = 1000000 / fsamp

camera.ExposureTime.Value = time_exposure

camera.StartGrabbingMax(200)
buffer = []

while camera.IsGrabbing():
    # Wait for an image and then retrieve it. A timeout of 5000 ms is used.
    grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

    # Image grabbed successfully?
    if grabResult.GrabSucceeded():
        buffer.append(grabResult.Array)
    else:
        print("Error: ", grabResult.ErrorCode, grabResult.ErrorDescription)
    grabResult.Release()
camera.Close()

print(buffer[0])

with get_writer('output-filename.avi', fps=fsamp) as writer:
    for image in buffer:
        writer.append_data(image)
del buffer
