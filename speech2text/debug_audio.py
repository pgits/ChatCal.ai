#!/usr/bin/env python3
"""
Debug script to test audio input and microphone detection
"""

import sounddevice as sd
import numpy as np
import time

def list_audio_devices():
    print("🎤 Available Audio Devices:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        device_type = []
        if device['max_input_channels'] > 0:
            device_type.append('INPUT')
        if device['max_output_channels'] > 0:
            device_type.append('OUTPUT')
        
        print(f"  {i}: {device['name']} ({', '.join(device_type)})")
        print(f"      Channels: In={device['max_input_channels']}, Out={device['max_output_channels']}")
        print(f"      Sample Rate: {device['default_samplerate']}")
    
    print(f"\nDefault Input Device: {sd.default.device[0]}")
    print(f"Default Output Device: {sd.default.device[1]}")

def test_microphone():
    print("\n🔊 Testing microphone input...")
    print("Speak for 5 seconds - you should see audio level indicators:")
    
    duration = 5  # seconds
    sample_rate = 44100
    
    def audio_callback(indata, frames, time, status):
        if status:
            print(f"Audio status: {status}")
        
        # Calculate audio level
        volume_norm = np.linalg.norm(indata) * 10
        print("|" + "█" * int(volume_norm) + " " * (50 - int(volume_norm)) + f"| {volume_norm:.1f}", end='\r', flush=True)
    
    try:
        with sd.InputStream(callback=audio_callback, channels=1, samplerate=sample_rate):
            time.sleep(duration)
        print("\n✅ Microphone test completed")
    except Exception as e:
        print(f"\n❌ Microphone test failed: {e}")

def test_permissions():
    print("\n🔒 Testing microphone permissions...")
    try:
        # Try to record a short sample
        recording = sd.rec(int(0.5 * 44100), samplerate=44100, channels=1, dtype='float64')
        sd.wait()  # Wait until recording is finished
        
        if np.max(np.abs(recording)) > 0.001:  # Check if we got actual audio
            print("✅ Microphone permissions OK - audio detected")
        else:
            print("⚠️  Microphone accessible but no audio detected - check if muted or too quiet")
            
    except Exception as e:
        print(f"❌ Microphone permission denied or error: {e}")
        print("   Try: System Preferences > Security & Privacy > Privacy > Microphone")

if __name__ == "__main__":
    print("🧪 Audio Input Debug Tool\n")
    
    list_audio_devices()
    test_permissions()
    test_microphone()
    
    print("\n💡 If you see issues:")
    print("   1. Check System Preferences > Security & Privacy > Privacy > Microphone")
    print("   2. Make sure Terminal or your app has microphone access")
    print("   3. Try a different microphone if available")
    print("   4. Check if microphone is muted or volume is too low")