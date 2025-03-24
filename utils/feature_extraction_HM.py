import pandas as pd
import numpy as np
from scipy.signal import argrelextrema

class HandMotionFeatureExtractor:
    def __init__(self):
        self.dataframes = []  # Store extracted features from multiple files

    def extract_features(self, file_path):
        df = pd.read_csv(file_path, names=["Timestamp", "X", "Y", "Pressure"])
        df = df[df["Pressure"] != 0]
        # df = df.sort_values(by="Timestamp").reset_index(drop=True)

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


