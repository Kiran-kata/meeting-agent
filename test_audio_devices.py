"""Test audio devices to identify which ones are active"""
import sounddevice as sd

devices = sd.query_devices()
print("=" * 80)
print("AVAILABLE AUDIO DEVICES")
print("=" * 80)

for i in range(len(devices)):
    device = devices[i]
    device_type = "INPUT" if device.get("max_input_channels", 0) > 0 else "OUTPUT"
    print(f"\n[{i}] {device['name']}")
    print(f"    Type: {device_type}")
    print(f"    Input Channels: {device.get('max_input_channels', 0)}")
    print(f"    Output Channels: {device.get('max_output_channels', 0)}")
    print(f"    Sample Rate: {device.get('default_samplerate', 0)} Hz")

print("\n" + "=" * 80)
print("CURRENT CONFIG IN main.py:")
print("=" * 80)
print("MEETING_DEVICE_INDEX = 9")
print("MIC_DEVICE_INDEX = 2")
print("\nTo change, edit app/main.py and update these indices")
print("=" * 80)
