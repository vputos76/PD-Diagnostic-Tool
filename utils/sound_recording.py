# This script access the Blue Yeti microphone and records soundbites, stored in a .wav file
    # File renaming and relocation is completed in main.py

import sounddevice as sd                # Access device
import scipy.io.wavfile as wav          # Write to .wav files

# Record audio on the Blue Yeti microphone--initial 2.2s delay before recording is live
def record_audio(duration=5, samplerate=44100):
    print("Recording...")
    audio_data = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=2, dtype='int16', device=3)
    sd.wait()  # Wait until recording is finished
    print("Recording complete. Saving file...")
    # Write data to file
    wav.write("output.wav", samplerate, audio_data)



if __name__ == "main":
    record_audio(5, "test_recording.wav")
