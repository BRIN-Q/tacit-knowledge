import numpy as np
import matplotlib.pyplot as plt

# Load CSV (skip header row)
data = np.loadtxt("D:/trina/TA_internal/waveform_0.csv", delimiter=",", skiprows=1)

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
