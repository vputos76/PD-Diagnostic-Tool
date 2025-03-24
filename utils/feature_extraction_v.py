import numpy as np
import pandas as pd
import parselmouth
from parselmouth.praat import call
import wave
import numpy as np
import librosa
import nolds

class Feature_Extraction:
   
    def __init__(self):
        self.acoustic_features = []
        self.mfcc = []

    def extract_acoustic_features(self, voice_sample, f0_min, f0_max, unit):
        with wave.open(voice_sample, 'rb') as wav_file:
            print("File is valid WAV format.")
        try:
            sound = parselmouth.Sound(voice_sample)
            pitch = call(sound, "To Pitch", 0.0, f0_min, f0_max)
            f0_mean = call(pitch, "Get mean", 0, 0, unit) 
            f0_std_deviation= call(pitch, "Get standard deviation", 0, 0, unit) 
            harmonicity = call(sound, "To Harmonicity (cc)", 0.01, f0_min, 0.1, 1.0)
            hnr = call(harmonicity, "Get mean", 0, 0)
            pointProcess = call(sound, "To PointProcess (periodic, cc)", f0_min, f0_max)
            jitter_relative = call(pointProcess, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
            jitter_absolute = call(pointProcess, "Get jitter (local, absolute)", 0, 0, 0.0001, 0.02, 1.3)
            jitter_rap = call(pointProcess, "Get jitter (rap)", 0, 0, 0.0001, 0.02, 1.3)
            jitter_ppq5 = call(pointProcess, "Get jitter (ppq5)", 0, 0, 0.0001, 0.02, 1.3)
            shimmer_relative =  call([sound, pointProcess], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
            shimmer_localDb = call([sound, pointProcess], "Get shimmer (local_dB)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
            shimmer_apq3 = call([sound, pointProcess], "Get shimmer (apq3)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
            shimmer_apq5 = call([sound, pointProcess], "Get shimmer (apq5)", 0, 0, 0.0001, 0.02, 1.3, 1.6)

            df_acoustic_features = pd.DataFrame(
                [[f0_mean, f0_std_deviation, hnr, jitter_relative, jitter_absolute, jitter_rap, jitter_ppq5, 
                shimmer_relative, shimmer_localDb, shimmer_apq3, shimmer_apq5]],
                columns=['meanF0Hz', 'stdevF0Hz', 'HNR', 'localJitter', 'localabsoluteJitter', 
                        'rapJitter', 'ppq5Jitter', 'localShimmer', 'localdbShimmer', 
                        'apq3Shimmer', 'apq5Shimmer']
                )

            return df_acoustic_features
        except:
            print("Unable to process this file: ", voice_sample)


    def extract_mfcc(self, voice_sample):
       
        sound = parselmouth.Sound(voice_sample)
        mfcc_object = sound.to_mfcc(number_of_coefficients=12) #the optimal number of coeefficient used is 12
        mfcc = mfcc_object.to_array()
        mfcc_mean = np.mean(mfcc.T,axis=0)
        df_mfcc = pd.DataFrame(mfcc_mean).T
        df_mfcc.columns = ['mfcc_feature0','mfcc_feature1','mfcc_feature2', 'mfcc_feature3','mfcc_feature4','mfcc_feature5', 'mfcc_feature6', 'mfcc_feature7','mfcc_feature8', 'mfcc_feature9', 'mfcc_feature10','mfcc_feature11', 'mfcc_feature12']

        return df_mfcc


    def extract_voice_features(self, voice_sample, f0_min, f0_max, unit, bins=50, tau=1, sr=22050):
        with wave.open(voice_sample, 'rb') as wav_file:
            print("File is valid WAV format.")
        
        try:
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
            # Embed the time series
            # Downsample signal before embedding
            y_downsampled = y[::10]  # Reduce the number of samples (adjust step as needed)
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
        except Exception as e:
            print("Unable to process this file:", voice_sample, "Error:", str(e))
