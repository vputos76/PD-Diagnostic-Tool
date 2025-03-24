import pickle
from feature_extraction_v import Feature_Extraction

from pydub import AudioSegment, silence
from pydub.effects import low_pass_filter, high_pass_filter
import numpy as np

patientfile = "test_data/AH_545616858-3A749CBC-3FEB-4D35-820E-E45C3E5B9B6A.wav"

def remove_noise_and_trim(audio_path, output_path, noise_duration=4000, silence_thresh=-40):
    # Load audio file
    audio = AudioSegment.from_file(audio_path)

    audio = high_pass_filter(audio, cutoff=100)  # Removes low hum
    audio = low_pass_filter(audio, cutoff=8000)  

    # # Trim silence from beginning and end
    nonsilent_ranges = silence.detect_nonsilent(
        audio, min_silence_len=500, silence_thresh=silence_thresh
    )
    print(nonsilent_ranges)
    start_trim = nonsilent_ranges[0][0]
    end_trim = nonsilent_ranges[-1][1]
    trimmed_audio = audio[start_trim:end_trim]

    # Export cleaned audio
    trimmed_audio.export(output_path, format="wav")
    print(f"Processed audio saved to {output_path}")

# Example usage
remove_noise_and_trim(patientfile, "test_data/output_test.wav")

df = Feature_Extraction.extract_voice_features(Feature_Extraction, "test_data/output.wav", 20, 16000, "Hertz")

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
with open("trained_models/scaler_v.pkl", "rb") as f:
    scaler = pickle.load(f)
with open("trained_models/pca_v.pkl", "rb") as f:
    pca = pickle.load(f)
with open("trained_models/best_svm_model_voice.pkl", "rb") as f:
    best_svm_model = pickle.load(f)

scaled_data = scaler.transform(df)
pca_data = pca.transform(scaled_data)

# Get predictions
predictions = best_svm_model.predict(pca_data)
predictions