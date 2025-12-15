"""
Check available audio devices
Run this to find your microphone/system audio device index
"""
import sounddevice as sd

def check_devices():
    print("\n" + "="*60)
    print("AVAILABLE AUDIO DEVICES")
    print("="*60)
    
    devices = sd.query_devices()
    
    print("\n📥 INPUT DEVICES (for listening to audio):\n")
    for i, device in enumerate(devices):
        if device.get('max_input_channels', 0) > 0:
            default = " ← DEFAULT" if device.get('name') == sd.query_devices(sd.default.device[0])['name'] else ""
            print(f"  [{i}] {device['name']}{default}")
    
    print("\n" + "-"*60)
    print("\nTo use a specific device, edit config.py:")
    print("  AUDIO_DEVICE_INDEX = <number>")
    print("\nFor virtual audio cable (to capture meeting audio):")
    print("  Install 'VB-CABLE' or 'Stereo Mix'")
    print("="*60 + "\n")

if __name__ == "__main__":
    check_devices()
