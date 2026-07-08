import pyvisa
import numpy as np
import csv, time

rm = pyvisa.ResourceManager()
rm.timeout = 20000 # 20 s
nf = rm.open_resource("GPIB0::2::INSTR") #FG
sig = rm.open_resource("USB0::0x0AAD::0x01D6::113416::INSTR") #Osc

# --- FUNCTION GENERATOR ---
nf.write(":SOURce1:FUNCtion:SHAPe PULSe")
nf.write(":SOURce1:VOLTage:LEVel:IMMediate:AMPLitude 3VPK")

width = float(input("pulse width (us): "))
# width = 20
nf.write(f":SOURce1:PULSe:WIDTh {width}US") # !!! --- WIDTH PARAMETER: USER-INPUT --- !!!

tau = float(input("tau (us): "))
period = tau + width # affects the trigger signal's config
# period = 500
nf.write(f":SOURce1:PULSe:PERiod {period}US") #prev: 500 us

# time_scale = float(input("time scale to be displayed (s): "))
# time_scale = period*1e-6 + 1e-6 
range_time = 2*period*1e-6
# sig.write(f"TIM:SCAL {time_scale}")
sig.write(f"TIMebase:RANGe {range_time}") # 

# nf.write(":SOURce1:PULSe:PERiod 500US") # !!! --- CALCULATE FROM SCALE AND RANGE PARAMETERS --- !!! 
nf.write(":OUTPut1:STATe ON")
# (assume it continuously generate the waveform)

time.sleep(0.2)

# --- OSCILLOSCOPE ---
# CHANnel1:STATe ON
sig.write("CHANnel1:STATe ON") 
sig.write("TRIGger:A:SOURce EXTernanalog")
# sig.write("TRIG:A:LEVel5 1") # trig level in V
sig.write("TRIG:A:EDGE:SLOPe POS")
sig.write("ACQuire:MODE NORM")
sig.write("FORM ASC") # ASCII format
sig.write("TIM:REF 50")

# # Safety check
# if values_per_interval != 1:
#     print("Warning: Values per interval =", values_per_interval)


# DATA ACQUISITION (for 1 tau)
num_waveform = int(input("number of measured waveforms: ")) # number of waveforms

for i in range(num_waveform):
    sig.write(":SINGLE") # single acquisition
    sig.query("*OPC?")  # Wait until acquisition complete, Stops command processing until 1 is returned.

    header_str = sig.query("CHAN1:DATA:HEADer?") # ex: "-9.477E-008,9.477E-008,120000,1" (string data)
    header = header_str.strip().split(',')
    Xstart = float(header[0]) # !!! NECESSARY FOR DATA PROCESSING, EXTRACT THIS PARAMETER !!!
    Xstop = float(header[1])
    num_samples = int(header[2])
    step = (Xstop-Xstart)/(num_samples-1)
    time = np.linspace(Xstart, Xstop, num_samples)
    waveform_str = sig.query("CHAN1:DATA?") # string data
    voltage = np.array(waveform_str.strip().split(','), dtype=float)
    print("Samples received:", len(voltage))

    # # Safety check
    # if len(voltage) != num_samples:
    #     print("Warning: Sample mismatch!")

    # ---- Save to CSV ----
    filename = f"D:/trina/TA_internal/waveform_{i}.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Time (s)", "Voltage (V)"])
        writer.writerows(zip(time, voltage))
    
    print("Waveform saved to: ", filename)

