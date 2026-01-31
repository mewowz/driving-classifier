import pandas as pd
import numpy as np
from pathlib import Path
import os

KNOWN_COL_NAMES = [
        "rpm_time", "rpm_value",
        "speed_time", "speed_value",
        "maf_time", "maf_value",
        "throttle_time", "throttle_value",
        "engine_load_time", "engine_load_value",
        "coolant_temp_time", "coolant_temp_value",
        "s_fuel_trim_time", "s_fuel_trim_value",
        "l_fuel_trim_time", "l_fuel_trim_value",
        "timing_advance_time", "timing_advance_value",
        "intake_temp_time", "intake_temp_value"
]

def get_data_from_csv(path: os.PathLike) -> pd.DataFrame:
    """
    Convenience function to load a CSV file into a Pandas dataframe
    """
    if not isinstance(path, (str, bytes, os.PathLike)):
        raise ValueError(f"Argument 'path' is not of str, bytes, or os.PathLike instance. Got '{path}'")

    csv_file = Path(path)
    df = pd.read_csv(path, sep=",", names=KNOWN_COL_NAMES)

    ## need to get derivatives of cols like speed to get accleration
    df["time_diff"] = df["rpm_time"].diff() # We'll just use the rpm's time as the baseline for time - FOR NOW
    df["rpm_accel"] = df["rpm_value"].diff() / df["time_diff"]
    df["rpm_jerk"] = df["rpm_accel"].diff() / df["time_diff"]

    df["speed_accel"] = df["speed_value"].diff() / df["time_diff"]
    df["speed_jerk"] = df["speed_accel"].diff() / df["time_diff"]

    df["maf_accel"] = df["maf_value"].diff() / df["time_diff"]

    df["throttle_rate"] = df["throttle_value"].diff() / df["time_diff"]

    return df

def make_features_clustering(df: pd.DataFrame, window_sz: int = 20) -> pd.DataFrame:
    """
    Returns raw, unscaled features from a given dataframe
    """
    features = pd.DataFrame()
    windows = []
    for window in df.rolling(window_sz):
        row = {}
        
        row["rpm_std"] = window["rpm_value"].std()
        row["rpm_mean"] = window["rpm_value"].mean()
       
        row["rpm_accel_std"] = window["rpm_accel"].std()
        row["rpm_accel_mean"] = window["rpm_accel"].mean()
        row["rpm_accel_min"] = window["rpm_accel"].min()
        row["rpm_accel_max"] = window["rpm_accel"].max()

        row["rpm_jerk_max_abs"] = window["rpm_jerk"].abs().max()

        row["speed_std"] = window["speed_value"].std()
        row["speed_mean"] = window["speed_value"].mean()

        row["speed_accel_std"] = window["speed_accel"].std()
        row["speed_accel_mean"] = window["speed_accel"].mean()
        row["speed_accel_min"] = window["speed_accel"].min()
        row["speed_accel_max"] = window["speed_accel"].max()

        row["speed_jerk_max_abs"] = window["speed_jerk"].abs().max()

        row["maf_std"] = window["maf_value"].std()
        row["maf_mean"] = window["maf_value"].mean()

        row["maf_accel_std"] = window["maf_accel"].std()
        row["maf_accel_mean"] = window["maf_accel"].mean()
        row["maf_accel_min"] = window["maf_accel"].min()
        row["maf_accel_max"] = window["maf_accel"].max()

        row["throttle_std"] = window["throttle_value"].std()
        row["throttle_mean"] = window["throttle_value"].mean()

        row["throttle_rate_std"] = window["throttle_rate"].std()
        row["throttle_rate_mean"] = window["throttle_rate"].mean()
        row["throttle_rate_min"] = window["throttle_rate"].min()
        row["throttle_rate_max"] = window["throttle_rate"].max()

        windows.append(row)

    return pd.DataFrame(windows)


