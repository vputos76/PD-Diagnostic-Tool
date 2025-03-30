import numpy as np
import pandas as pd

import parselmouth
from parselmouth.praat import call
import wave
import librosa
import nolds
from scipy.signal import argrelextrema
from pydub import AudioSegment, silence
from pydub.effects import low_pass_filter, high_pass_filter


import scipy.signal as signal
from scipy.signal import hilbert
from scipy.integrate import trapezoid
from scipy.signal import butter, filtfilt

################################ Hand Motion ##################################################
class Feature_Extraction_v:
   
    def __init__(self):
        self.acoustic_features = []
        self.mfcc = []

    def remove_noise_and_trim(self, audio_path, output_path, silence_thresh=-40):
        audio = AudioSegment.from_file(audio_path)
        audio = high_pass_filter(audio, cutoff=100)  # Removes low hum
        audio = low_pass_filter(audio, cutoff=8000)  

        # Trim silence from beginning and end
        nonsilent_ranges = silence.detect_nonsilent(
            audio, min_silence_len=500, silence_thresh=silence_thresh
        )
        start_trim = nonsilent_ranges[0][0]
        end_trim = nonsilent_ranges[-1][1]
        trimmed_audio = audio[start_trim:end_trim]
        # Export cleaned audio
        trimmed_audio.export(output_path, format="wav")
      

    def extract_voice_features(self, voice_sample, f0_min, f0_max, unit, bins=50, tau=1, sr=22050):
        with wave.open(voice_sample, 'rb') as wav_file:

            sound = parselmouth.Sound(voice_sample)
            pitch = call(sound, "To Pitch", 0.0, f0_min, f0_max)
            # Fundamental frequency features
            f0_mean = call(pitch, "Get mean", 0, 0, unit) 
            f0_maximum = call(pitch, "Get maximum", 0, 0, unit, 'Parabolic')
            f0_minimum = call(pitch, "Get minimum", 0, 0, unit, 'Parabolic')
            # Jitter features
            pointProcess = call(sound, "To PointProcess (periodic, cc)", f0_min, f0_max)
            jitter_relative = call(pointProcess, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
            jitter_absolute = call(pointProcess, "Get jitter (local, absolute)", 0, 0, 0.0001, 0.02, 1.3)
            jitter_rap = call(pointProcess, "Get jitter (rap)", 0, 0, 0.0001, 0.02, 1.3)
            jitter_ppq5 = call(pointProcess, "Get jitter (ppq5)", 0, 0, 0.0001, 0.02, 1.3)
            jitter_ddp = 3 * jitter_rap
            # Shimmer features
            shimmer_relative = call([sound, pointProcess], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
            shimmer_localDb = call([sound, pointProcess], "Get shimmer (local_dB)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
            shimmer_apq3 = call([sound, pointProcess], "Get shimmer (apq3)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
            shimmer_apq5 = call([sound, pointProcess], "Get shimmer (apq5)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
            shimmer_apq = call([sound, pointProcess], "Get shimmer (apq11)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
            shimmer_dda = 3 * shimmer_apq3
            # Harmonicity (NHR)
            harmonicity = call(sound, "To Harmonicity (cc)", 0.01, f0_min, 0.1, 1.0)
            hnr = call(harmonicity, "Get mean", 0, 0)
            if hnr > 0:
                nhr = 1 / (10 ** (hnr / 10))  # Convert HNR (dB) to NHR
            else:
                nhr = 1     

            ## Additional nonlinear features using librosa
            y, sr = librosa.load(voice_sample, sr=sr)

            ## 1st and 2nd spectral spread
            D = np.abs(librosa.stft(y))**2
            freqs = librosa.fft_frequencies(sr=sr)
            # Find first two formants (approximate using spectral peaks)
            formants = sound.to_formant_burg(time_step=0.01)  # Extract formants
            # Get F1, F2, and F3 at the middle of the file
            time = sound.xmax / 2
            F1 = formants.get_value_at_time(1, time)  # 1st formant
            F2 = formants.get_value_at_time(2, time)  # 2nd formant
            if F1 is not None and F2 is not None:
                spread1 = np.sqrt(np.sum(D * (freqs[:, None] - F1)**2) / np.sum(D))
                spread2 = np.sqrt(np.sum(D * (freqs[:, None] - F2)**2) / np.sum(D))
            else:
                spread1, spread2 = np.nan, np.nan  # Avoid crashing if formants are not found

            ## Correlation dimension of speech signal
            d2 = nolds.corr_dim(y[:5000], emb_dim=10)  # Use only first 5000 samples

            ###### RPDE calculation
            # Embed the time series # Downsample signal before embedding
            y_downsampled = y[::10]  
            embedded = np.array([y_downsampled[i:len(y_downsampled)-tau+i] for i in range(tau)]).T
            # Use a subset of the matrix (1000 x 1000 max)
            max_size = 1000
            if embedded.shape[0] > max_size:
                embedded = embedded[:max_size, :]
            # Compute distances between points in phase space
            dist_matrix = np.linalg.norm(embedded[:, None, :] - embedded[None, :, :], axis=-1)
            # Apply a threshold (e.g., median distance)
            threshold = np.median(dist_matrix)
            recurrence_matrix = (dist_matrix < threshold).astype(int)
            # Compute recurrence periods
            recurrence_periods = np.diff(np.where(recurrence_matrix == 1)[1])
            # Compute probability density function (PDF)
            hist, bin_edges = np.histogram(recurrence_periods, bins=bins, density=True)
            pdf = hist / np.sum(hist)
            # Compute Shannon entropy
            rpde = -np.nansum(pdf * np.log2(pdf + 1e-10))  # Avoid log(0)

            #### DFA, Detrended Fluctuation Analysis
            dfa = nolds.dfa(y[::10])
            ### PPE, Pitch Period Entropy
            f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=50, fmax=300)
            # Remove NaN values (unvoiced parts)
            f0 = f0[~np.isnan(f0)]
            # Compute entropy of pitch period (PPE)
            prob_density, _ = np.histogram(f0, bins=30, density=True)
            prob_density = prob_density[prob_density > 0]  # Remove zero values
            ppe = -np.sum(prob_density * np.log2(prob_density))  # Entropy formula

          
            df_voice_features = pd.DataFrame(
                [[f0_mean, f0_maximum, f0_minimum, jitter_relative, jitter_absolute, jitter_rap, jitter_ppq5, jitter_ddp,
                shimmer_relative, shimmer_localDb, shimmer_apq3, shimmer_apq5, shimmer_apq, shimmer_dda,
                nhr, hnr, rpde, dfa, spread1, spread2, d2, ppe]],
                columns=['MDVP:Fo', 'MDVP:Fhi', 'MDVP:Flo', 'MDVP:Jitter', 'MDVP:Jitter.1', 'MDVP:RAP', 'MDVP:PPQ', 'Jitter:DDP',
                        'MDVP:Shimmer', 'MDVP:Shimmer.1', 'Shimmer:APQ3', 'Shimmer:APQ5', 'MDVP:APQ', 'Shimmer:DDA',
                        'NHR','HNR', 'RPDE', 'DFA', 'spread1', 'spread2', 'D2', 'PPE']
            )
            
            return df_voice_features

class HandMotionFeatureExtractor:
    def __init__(self):
        self.dataframes = []  # Store extracted features from multiple files

    def extract_features(self, file_path):
        df = pd.read_csv(file_path, names=["Timestamp", "X", "Y", "Pressure"])
        df = df[df["Pressure"] != 0]
     

        # Compute delta time
        df["dt"] = df["Timestamp"].diff()
        df["dt"] = df["dt"].replace(0, np.nan).interpolate().ffill().bfill()  # No zeros!
          # Avoid division by zero
        # Compute displacement
        df["dx"] = df["X"].diff().fillna(0)
        df["dy"] = df["Y"].diff().fillna(0)
        # Compute trajectory length
        df["trajectory_length"] = np.sqrt(df["dx"]**2 + df["dy"]**2)
        # Stroke speed
        stroke_speed = df["trajectory_length"].sum() / (df["Timestamp"].iloc[-1] - df["Timestamp"].iloc[0])
        # Compute velocity
        df["velocity"] = df["trajectory_length"] / df["dt"]
        df["velocity"] = df["velocity"].replace([np.inf, -np.inf], np.nan).interpolate().ffill().bfill()
        # Compute acceleration
        df["acceleration"] = df["velocity"].diff().fillna(0) / df["dt"]
        df["acceleration"] = df["acceleration"].replace([np.inf, -np.inf], np.nan).interpolate().ffill().bfill()
        # Compute jerk
        df["jerk"] = df["acceleration"].diff().fillna(0) / df["dt"]
        df["jerk"] = df["jerk"].replace([np.inf, -np.inf], np.nan).interpolate().ffill().bfill()
        # Number of changes in velocity and acceleration direction
        ncv = len(argrelextrema(df["velocity"].values, np.less)[0]) + len(argrelextrema(df["velocity"].values, np.greater)[0])
        nca = len(argrelextrema(df["acceleration"].values, np.less)[0]) + len(argrelextrema(df["acceleration"].values, np.greater)[0])
        # Path efficiency
        euclidean_distance = np.sqrt((df["X"].iloc[-1] - df["X"].iloc[0])**2 + (df["Y"].iloc[-1] - df["Y"].iloc[0])**2)
        path_efficiency = euclidean_distance / df["trajectory_length"].sum()
        # Stroke duration
        stroke_duration = df["Timestamp"].iloc[-1] - df["Timestamp"].iloc[0]
        # Pressure features
        mean_pressure = df["Pressure"].mean()
        std_pressure = df["Pressure"].std()
        num_pressure_drops = sum(df["Pressure"].diff().fillna(0) < -0.1)

        # Store extracted features
        feature_data = pd.DataFrame([[
            stroke_speed, df["velocity"].mean(), df["acceleration"].mean(), df["jerk"].mean(),
            ncv, nca, path_efficiency, stroke_duration, mean_pressure, std_pressure, num_pressure_drops
        ]], columns=[
            "stroke_speed", "mean_velocity", "mean_acceleration", "mean_jerk",
            "NCV", "NCA", "path_efficiency", "stroke_duration",
            "mean_pressure", "std_pressure", "num_pressure_drops"
        ])

        self.dataframes.append(feature_data)

    def get_feature_dataframe(self):
        """Returns the combined DataFrame of all extracted features."""
        if self.dataframes:
            return pd.concat(self.dataframes, ignore_index=True)
        return pd.DataFrame()


class FeatureExtractor_RT:
    def __init__(self, fs=100, lowcut=0.65, highcut=40, order=6):
        self.fs = fs
        self.lowcut = lowcut
        self.highcut = highcut
        self.order = order

    def bandpass_filter(self, df):
        nyquist = 0.5 * self.fs
        low = self.lowcut / nyquist
        high = self.highcut / nyquist
        b, a = butter(self.order, [low, high], btype='band')
        return filtfilt(b, a, df)

    def compute_rms_acceleration(self, df):
        return np.sqrt((df["X"]**2 + df["Y"]**2 + df["Z"]**2) / 3)

    def compute_sample_entropy(self, df_rms, m=2, r=0.2):
        N = len(df_rms)
        r *= np.std(df_rms)

        def _phi(m):
            X = np.array([df_rms[i: i + m] for i in range(N - m + 1)])
            C = np.zeros(len(X))
            for i in range(len(X)):
                dist = np.max(np.abs(X - X[i]), axis=1)
                C[i] = np.sum(dist <= r) - 1
            return np.sum(C) / (N - m + 1)

        phi_m = _phi(m)
        phi_m1 = _phi(m + 1)
        return np.inf if phi_m == 0 or phi_m1 == 0 else -np.log(phi_m1 / phi_m)

    def compute_psd_features(self, df):
        freqs, psd_x = signal.welch(df["X"], fs=self.fs, nperseg=256)
        _, psd_y = signal.welch(df["Y"], fs=self.fs, nperseg=256)
        _, psd_z = signal.welch(df["Z"], fs=self.fs, nperseg=256)
        acc_mag = np.sqrt(df["X"]**2 + df["Y"]**2 + df["Z"]**2)
        freqs, psd = signal.welch(acc_mag, fs=self.fs, nperseg=256)
        peak_power = np.max(psd)
        peak_freq = freqs[np.argmax(psd)]
        auc_power = trapezoid(psd, freqs)
        mean_acc = np.mean(np.abs(acc_mag))
        total_energy = trapezoid(psd_x, freqs) + trapezoid(psd_y, freqs) + trapezoid(psd_z, freqs)
        return peak_power, peak_freq, total_energy, auc_power, mean_acc

    def process_dataframe(self, patientfile):
        df = pd.read_csv(patientfile)
        df = df.drop(columns=["DeviceName", "AsX(°/s)", "AsY(°/s)", "AsZ(°/s)", "AngleX(°)", "AngleY(°)", "AngleZ(°)", "HX(uT)", "HY(uT)", "HZ(uT)", "Q0()", "Q1()", "Q2()", "Q3()", "Temperature(°C)", "Version()", "Battery level(%)"])
        df.columns = ['Time', 'X', 'Y', 'Z']
        df['X']= df['X'].values*(-1)
        for axis in ['X', 'Y', 'Z']:
            df[axis] = self.bandpass_filter(df[axis])
        df_rms = self.compute_rms_acceleration(df)
        sample_entropy = self.compute_sample_entropy(df_rms)
        peak_power, peak_freq, total_energy, auc_power, mean_acc = self.compute_psd_features(df)
        features = {
            "peak_power": peak_power,
            "peak_freq": peak_freq,
            "auc_power": auc_power,
            "total_energy": total_energy,
            "sample_entropy": sample_entropy,
            "mean_acceleration": mean_acc
        }
        return pd.DataFrame([features])