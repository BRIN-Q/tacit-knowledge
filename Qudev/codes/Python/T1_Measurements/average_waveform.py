import pandas as pd
import glob

files = sorted(glob.glob("D:/trina/TA_internal/Test_5us Pol-Read_1us dark/tau 200 us/waveform_*.csv"))

dataframes = []

for f in files:
    df = pd.read_csv(f)
    dataframes.append(df["Voltage (V)"])

# combine voltages column-wise
combined = pd.concat(dataframes, axis=1)

# compute average voltage
avg_voltage = combined.mean(axis=1)

# use time from first file
time = pd.read_csv(files[0])["Time (s)"]

avg_df = pd.DataFrame({
    "Time (s)": time,
    "Voltage (V)": avg_voltage
})

avg_df.to_csv("D:/trina/TA_internal/Test_5us Pol-Read_1us dark/tau 200 us/averaged_waveform.csv", index=False)