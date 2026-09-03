# UPDATE FROM setup_inst_6.py : REPEAT THE FIRST TAU VALUE (2 uS) TWICE, WHERE THE FIRST REPETITION ACTS AS THE FIRST POLARIZING PULSE 
import pyvisa
import numpy as np
import csv, time
import os
from datetime import datetime

cwd = os.getcwd()

rm = pyvisa.ResourceManager()
rm.timeout = 20000 # 20 s
nf = rm.open_resource("GPIB0::2::INSTR") #FG
sig = rm.open_resource("TCPIP0::192.168.0.10::inst0::INSTR") #Osc (LAN-PC)

# --- FUNCTION GENERATOR ---
nf.write(":SOURce1:FUNCtion:SHAPe PULSe")
# nf.write(":SOURce1:VOLTage:LEVel:IMMediate:AMPLitude 1VPK")
nf.write(":SOURce1:VOLTage:LEVel:IMMediate:HIGH 1V")
nf.write(":SOURce1:VOLTage:LEVel:IMMediate:LOW 0V")


width = float(input("pulse width (us): "))
nf.write(f":SOURce1:PULSe:WIDTh {width}US")

period = width + 0.1 # in us, affects the trigger signal's config
nf.write(f":SOURce1:PULSe:PERiod {period}US") #prev: 500 us

# BURST OSCILLATION
nf.write(":OUTPut1:BURST:STATe ON")
nf.write(":SOURce1:BURSt:MODE TRIG")
nf.write(":SOURce1:BURSt:TRIG:NCYCles 1") #Sets the mark wave number of auto burst of CH1 to 1 waves
nf.write(":OUTPut1:SYNC:BURSt:TYPE BSYNC")
nf.write(":TRIGger1:BURSt:SOURce TIM")

time.sleep(0.2)

# --- OSCILLOSCOPE ---

# CHANnel1:STATe ON
range_time = (1.5*width)*1e-6
sig.write(f"TIMebase:RANGe {range_time}") # Oscilloscope config
sig.write(f"ACQuire:POINts 80000000") # Oscilloscope acq sample
sig.write("CHANnel1:STATe ON") 
sig.write("TRIGger:A:SOURce EXTernanalog")
sig.write("TRIG:A:LEVel5 1") # trig level in V
sig.write("TRIG:A:EDGE:SLOPe NEG") # burst-sync signal is low during oscillation and high during oscillation stop
#sig.write("ACQuire:MODE NORM")
sig.write("CHANnel1:ARIThmetics AVERage")
sig.write("ACQuire:AVERage:COUNt 500") # Average waveform count
sig.write("FORM ASC") # ASCII format
sig.write("TIM:REF 8.33")


# DATA ACQUISITION (for all tau)
n = int(input("input number of tau's variation: ")) # number of tau
num_rep = int(input("number of repetitions: "))
tau_minimum = 2
tau_maximum = float(input("input max tau value: "))
tau = np.geomspace(tau_minimum, tau_maximum, n)

# NEW SCENARIO
for x in range(num_rep):
    output_path = os.path.join(cwd, f"rep_{x}")
    os.makedirs(output_path, exist_ok=True)

    # warmup at the front, then full tau sweep
    tau_sequence = [(0, tau[0])] + list(enumerate(tau))
    # result: [(0, 2), (0, 2), (1, 2.44), (2, 2.98), ..., (39, 5000)]
    #          ^ warmup  ^ real measurement starts here

    acq_count = {}

    for t, i in tau_sequence:
        acq_count[t] = acq_count.get(t, 0) + 1
        acq_idx = acq_count[t]

        timer_trig = i + width
        nf.write(f":TRIGger1:BURSt:TIMer {timer_trig}US")

        nf.write(":OUTPut1:STATe ON")
        sig.write("ACQuire:AVERage:RESet")
        sig.write(":SINGLe")
        timeout = 15
        t0 = time.time()
        finish = False
        while time.time() - t0 < timeout:
            if sig.query("ACQuire:AVERage:COMPlete?").strip() == "1":
                finish = True
                break
            time.sleep(0.1)
        sig.query("*OPC?")

        header_str = sig.query("CHAN1:DATA:HEADer?")
        header = header_str.strip().split(',')
        Xstart = float(header[0])
        Xstop  = float(header[1])
        num_samples = int(header[2])
        times = np.linspace(Xstart, Xstop, num_samples)
        waveform_str = sig.query("CHAN1:DATA?")
        voltage = np.array(waveform_str.strip().split(','), dtype=float)
        
        timestamp_tau = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp_tau}] Samples received: {len(voltage)}")

        # ---- Save logic ----
        if t == 0 and acq_idx == 1:
            # very first acquisition of each rep → warmup, discard
            print(f"[rep_{x}] Warmup (discarded): tau={i:.6f}uS")
        else:
            filename = os.path.join(output_path, f"tau_{int(i)}uS_{t}_.csv")
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Time (s)", "Voltage (V)"])
                writer.writerows(zip(times, voltage))
            print(f"[rep_{x}] Saved: tau={i:.6f}uS → {filename}")

        nf.write(":OUTPut1:STATe OFF")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Rep_{x} complete.")

    nf.write(":OUTPut1:STATe OFF")