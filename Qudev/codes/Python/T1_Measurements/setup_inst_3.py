import pyvisa
import numpy as np
import csv, time

rm = pyvisa.ResourceManager()
rm.timeout = 20000 # 20 s
nf = rm.open_resource("GPIB0::2::INSTR") #FG
# sig = rm.open_resource("USB0::0x0AAD::0x01D6::113416::INSTR") #Osc
sig = rm.open_resource("TCPIP0::192.168.0.10::inst0::INSTR") #Osc (LAN-PC)

range_time = (period+2*width)*1e-6
sig.write(f"TIMebase:RANGe {range_time}") # Oscilloscope config
sig.write(f"ACQuire:POINts 80000000") # Oscilloscope acq sample

# --- FUNCTION GENERATOR ---
nf.write(":SOURce1:FUNCtion:SHAPe PULSe")
nf.write(":SOURce1:VOLTage:LEVel:IMMediate:AMPLitude 1VPK")

width = float(input("pulse width (us): "))
# width = 20 (dummy)
nf.write(f":SOURce1:PULSe:WIDTh {width}US")

tau = float(input("tau (us): "))
period = tau + width # in us, affects the trigger signal's config
width_trig = 1 # in us
timer_trig = width_trig + 2*period - width
# period = 500 (dummy)
nf.write(f":SOURce1:PULSe:PERiod {period}US") #prev: 500 us

# tau = period + width_trig - width
# timer (1 period)= width_trig + period + (period-width)
# width_trig (set constant) = 1 us 

# BURST OSCILLATION
nf.write(":OUTPut1:BURST:STATe ON")
nf.write(":SOURce1:BURSt:MODE TRIG")
nf.write(":SOURce1:BURSt:TRIG:NCYCles 1") #Sets the mark wave number of auto burst of CH1 to 2 waves
# nf.write(":SOURce1:BURSt:AUTO:SPACe 1")
nf.write(":OUTPut1:SYNC:BURSt:TYPE BSYNC")
nf.write(":TRIGger1:BURSt:SOURce TIM")
nf.write(f":TRIGger1:BURSt:TIMer {timer_trig}US") # period of the sync signal

nf.write(":OUTPut1:STATe ON")
# (assume it continuously generate the waveform

time.sleep(0.2)

# --- OSCILLOSCOPE ---

# CHANnel1:STATe ON
sig.write("CHANnel1:STATe ON") 
sig.write("TRIGger:A:SOURce EXTernanalog")
# sig.write("TRIG:A:LEVel5 1") # trig level in V
sig.write("TRIG:A:EDGE:SLOPe NEG") # burst-sync signal is low during oscillation and high during oscillation stop
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

    # ---- Save to CSV ----
    filename = f"waveform_{i}.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Time (s)", "Voltage (V)"])
        writer.writerows(zip(time, voltage))
    
    print("Waveform saved to: ", filename)


