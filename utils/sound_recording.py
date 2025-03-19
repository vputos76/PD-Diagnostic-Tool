# This script access the Blue Yeti microphone and records soundbites, stored in a .wav file
    # File renaming and relocation is completed in main.py

import sounddevice as sd                # Access device
import scipy.io.wavfile as wav          # Write to .wav files
# Record audio on the Blue Yeti microphone--initial 2.2s delay before recording is live
def record_audio(keyword, duration=17, samplerate=44100):
    print("Recording...")
    # Search for device within entire audio device query
    for i, device in enumerate(sd.query_devices()):
        if keyword.lower() in device["name"].lower():
            channel = i # Matching index of keyword
    # Record the data
    audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=2, dtype='int16', device=channel)
    sd.wait()  # Wait until recording is finished
    # Write data to file
    wav.write("speech_test.wav", samplerate, audio_data)


if __name__ == "__main__":
    record_audio(keyword="Microphone (Yeti Stereo Microph") # Test for Blue Yeti Mic
