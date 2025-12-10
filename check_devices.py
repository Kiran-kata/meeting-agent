import sounddevice as sd

devices = sd.query_devices()
for i, dev in enumerate(devices):
    print(f"{i}: {dev['name']} (Input: {dev['max_input_channels']}, Output: {dev['max_output_channels']})")
