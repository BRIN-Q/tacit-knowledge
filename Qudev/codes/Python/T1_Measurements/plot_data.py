import numpy as np
import matplotlib.pyplot as plt

# Load CSV (skip header row)
number = int(input("enter the waveform number: "))
data = np.loadtxt(f"D:/trina/TA_internal/waveform_{number}.csv", delimiter=",", skiprows=1)

time = data[:, 0]
voltage = data[:, 1]

# Plot
plt.figure()
plt.plot(time, voltage)
plt.xlabel("Time (s)")
plt.ylabel("Voltage (V)")
plt.title("Oscilloscope Waveform")
plt.grid(True)
plt.show()

