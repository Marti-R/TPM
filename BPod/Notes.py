from pybpodapi.bpod_modules.bpod_module import BpodModule

AnalogIn = BpodModule(connected=True, module_name='Analog Input Module', firmware_version=0, serial_port='COM3')

# 'D' read SD card and send data to USB
# 'A2' set max number of actively sampled channels to 2
# 'L0/1' stop or start logging to SD card

AnalogIn.load_message('A2')

# PyAudio for microphone
# pypylon for cameras

print(AnalogIn)