# Python and VS Code Integration

Welcome to the QuasiCluster Python environment. This cluster provides a fully shared, pre-configured Python environment containing the essential scientific libraries (NumPy, SciPy, QuTiP, mpi4py, Qiskit, etc.) optimized for our hardware.

This guide explains how we can connect Visual Studio Code (VS Code) to the cluster, utilize the shared Python environment, and submit heavy parallelized tasks across our compute nodes.

## 1. Connecting VS Code to the Login Node

To interact with the cluster and edit scripts, we first need to connect VS Code to our login node (`quasi06`). Because our cluster is accessible globally, we use a Cloudflare tunnel to securely route the SSH connection to `ssh.quasicluster.org`.

We must ensure the `cloudflared` executable is installed on our local machine. Then, we configure our local SSH settings by editing the SSH config file. The `User username` and `IdentityFile ...` part should be modified accordingly to our real `username` and `/path/to/user/quasikey` (the real location where we put `quasikey` given by the QuasiCluster administrators).

**For Linux and macOS users,**
add the following configuration to `~/.ssh/config`:

```text
Host *
    PubkeyAcceptedKeyTypes=+ssh-rsa
    HostKeyAlgorithms=+ssh-rsa
    ServerAliveInterval 20
    TCPKeepAlive no

Host quasicluster
    HostName ssh.quasicluster.org
    ProxyCommand /usr/bin/cloudflared access ssh --hostname ssh.quasicluster.org
    User username
    IdentityFile /path/to/user/quasikey
```

**For Windows users,**
add the following configuration to `C:\Users\Username\.ssh\config`. Ensure `cloudflared.exe` is installed and accessible in the system PATH:

```text
Host *
    PubkeyAcceptedKeyTypes=+ssh-rsa
    HostKeyAlgorithms=+ssh-rsa
    ServerAliveInterval 20
    TCPKeepAlive no

Host quasicluster
    HostName ssh.quasicluster.org
    ProxyCommand cloudflared.exe access ssh --hostname ssh.quasicluster.org
    User username
    IdentityFile C:\Users\Username\.ssh\quasikey
```

Again, don't forget to adjust the `User` and `IdentityFile` parts acccording to our real situations.

**Connecting via VS Code:**

1. Open VS Code on the local computer.
2. Ensure the **Remote - SSH** and **Jupyter** extensions are installed.
3. Open the Command Palette (`Ctrl + Shift + P` or `Cmd + Shift + P`) and select **Remote-SSH: Connect to Host...**
4. Select `quasicluster` from the list.
5. Open the working folder (e.g., something like `/clusterfs/username/my_project`) via the File Explorer.

---

## 2. Accessing the Shared Python Environment

We maintain a shared, optimized Python environment at `/clusterfs/opt/qupy`.

### A. Terminal Access

To activate the environment in the terminal, we simply run the shortcut alias:

```bash
qupy
```

Our prompt will update to `(qupy)`, indicating that all scientific modules are loaded.

### B. Standard Python Scripts (`.py`) in VS Code

To assign the shared environment to our `.py` scripts:

1. Open a `.py` file.
2. Open the Command Palette (`Ctrl + Shift + P`) and select **Python: Select Interpreter**.
3. Select **Enter interpreter path...**
4. Paste the path: `/clusterfs/opt/qupy/bin/python`

### C. Installing Personal Packages

Because the shared environment is locked for stability, we cannot run standard `pip install` commands. If we need a custom module, we install it into our personal user directory by appending the `--user` flag:

```bash
qupy
pip install --user <package_name>
```

### D. Light Calculations on Jupyter Notebook

While heavy calculations must run on compute nodes, we are allowed to perform short, light interactive data analysis directly on the login node (`quasi06`). We must keep resource usage minimal to avoid slowing down the system for other users.

To access the shared environment for light Jupyter Notebook calculations in VS Code:

1. Open a `.ipynb` file in VS Code.
2. Click the **Select Kernel** button located in the top right corner.
3. Choose **Jupyter Kernel**.
4. Select **Quasi Python (Shared)** from the available kernels list. If it does not appear, select **Python Environments** and choose the path `/clusterfs/opt/qupy/bin/python`.

VS Code will automatically start a background Jupyter session on `quasi06` using our shared environment. We can then execute our code cells normally.

---

## 3. Running Interactive Jupyter Notebooks on Compute Nodes

**IMPORTANT:** We must never run heavy calculations interactively on `quasi06`. The login node only has 4 cores and is shared by all of us.

To run Jupyter Notebooks (`.ipynb`) in VS Code using the power of a compute node (`quasi07` to `quasi11`):

1. Open the integrated terminal in VS Code (which is connected to `quasi06`).
2. Run the `qupy-jupyter` command, specifying how many cores we need (default is 4, maximum is 12 physical cores):

```bash
qupy-jupyter 8
```

3. Slurm will automatically allocate the cores on a free compute node (e.g., `quasi08`) and output a URL like:
`http://quasi08:8341/?token=abcdef123456...`
4. Copy that URL.
5. In our `.ipynb` file in VS Code, click the **Select Kernel** button in the top right corner.
6. Choose **Select Another Kernel...** -> **Existing Jupyter Server**.
7. Paste the URL.

Our notebook is now directly executing on a compute node.

### Verifying the Compute Allocation

To confirm that our notebook is properly utilizing the allocated resources and bypassing the login node, we can paste the following Python code into the first cell of our notebook and execute it:

```python
import os
import socket
import time
import numpy as np

# 1. Verify the current machine and environmental limits
hostname = socket.gethostname()
slurm_cpus = os.environ.get('SLURM_CPUS_PER_TASK', 'Not set')
omp_threads = os.environ.get('OMP_NUM_THREADS', 'Not set')

print(f"=== Compute Environment Verification ===")
print(f"Running on node         : {hostname}")
print(f"Allocated Slurm CPUs    : {slurm_cpus}")
print(f"Active Math Threads     : {omp_threads}")

# 2. Execute a heavy calculation to utilize the cores
print("\nGenerating massive matrices for multiplication...")
start_time = time.time()

# Creating two 10000x10000 matrices requires significant RAM
matrix_a = np.random.rand(10000, 10000)
matrix_b = np.random.rand(10000, 10000)

print("Calculating dot product...")
# NumPy automatically detects the OMP_NUM_THREADS limit and spreads the work
matrix_c = np.dot(matrix_a, matrix_b)

end_time = time.time()
print(f"Calculation completed in {end_time - start_time:.2f} seconds.")
```

The example output is below.
```
=== Compute Environment Verification ===
Running on node         : quasi08
Allocated Slurm CPUs    : 8
Active Math Threads     : 8

Generating massive matrices for multiplication...
Calculating dot product...
Calculation completed in 9.99 seconds.
```

#### Stopping the Jupyter Compute Allocation

To stop the Jupyter kernel related to the previous compute node allocation, we can press `CTRL + c` on the VS Code's terminal. We can go back to use the default `qupy` environment for light Python calculations on `quasi06`.

### Handling Sudden Disconnections and Persistent Sessions

If we close VS Code, our SSH connection to the login node drops. This destroys the integrated terminal session, which instantly kills the `srun` command. Slurm will then terminate the Jupyter server and release the allocated cores back to the cluster. This is an intentional safety feature designed to prevent "zombie" servers from permanently locking up compute nodes if we forget to close our notebooks.

If our internet connection is unstable, or if we intentionally want the Jupyter server to survive closing VS Code, we must use a terminal multiplexer like `tmux`.

**To keep the Jupyter server alive:**

1. Open the integrated terminal in VS Code.
2. Type `tmux` and press Enter to start a persistent session.
3. Run the `qupy-jupyter` command inside this `tmux` session.
4. If VS Code is suddenly closed, the background session on `quasi06` remains active, keeping the Slurm allocation alive.
5. When we reconnect to VS Code, we can open a new terminal and type `tmux attach` to restore our previous view and cleanly shut down the server with `Ctrl + C` when finished.

---

## 4. Submitting Heavy Python Workflows

For massive calculations or overnight runs, we must submit our Python script to the Slurm queue using an `sbatch` script.

### Single-Node Multithreading (NumPy/SciPy/QuTiP)

Standard scientific libraries rely on C-based OpenBLAS and OpenMP to accelerate matrix math. To utilize multiple cores on a single compute node (up to 12 physical cores), we map hardware threads to the CPU allocation.

#### Example Script: `main_simulation.py` and `submit_python.sh`

To test our single-node Slurm submission, we can use the following example scripts. First, open a new file named `main_simulation.py` and edit it. This script creates a large mock Hamiltonian and solves for its eigenvalues. This operation heavily utilizes the multithreading limits we will set in our batch script and should take roughly 1 to 2 minutes to complete on a 12-core allocation.

```python
import numpy as np
import time
import os

print("=== QuasiCluster: Python Multithreading Test ===")
# Verify that the script respects the threads allocated by Slurm
threads = os.environ.get('OMP_NUM_THREADS', 'Not Set')
print(f"Allocated Threads (OMP_NUM_THREADS): {threads}")

# 1. Generate a large symmetric matrix (Mock Hamiltonian)
matrix_size = 12000
print(f"\nGenerating a {matrix_size} x {matrix_size} symmetric matrix...")
start_time = time.time()

# Create a random matrix and add it to its transpose to make it symmetric
A = np.random.rand(matrix_size, matrix_size)
H = A + A.T 

# 2. Perform Eigenvalue Decomposition
print("Starting eigenvalue decomposition (Diagonalization)...")
print("This will heavily utilize the allocated OpenBLAS/MKL CPU cores.")
eigenvalues, eigenvectors = np.linalg.eigh(H)

# 3. Perform a heavy Matrix Multiplication
print("Performing dense matrix multiplication...")
C = np.dot(H, H)

end_time = time.time()

# 4. Output the results
print("\n=== Simulation Complete ===")
print(f"Ground state (Lowest eigenvalue) : {eigenvalues[0]:.4f}")
print(f"Highest energy eigenvalue        : {eigenvalues[-1]:.4f}")
print(f"Total time elapsed               : {end_time - start_time:.2f} seconds.")
```

Next, create a file named `submit_python.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=Py_Sim
#SBATCH --partition=qdisk
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=12
#SBATCH --time=24:00:00
#SBATCH --output=slurm-%j.out

# 1. Activate the shared environment
source /clusterfs/opt/qupy/bin/activate

# 2. Align numerical libraries with the Slurm CPU allocation
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
export OPENBLAS_NUM_THREADS=$SLURM_CPUS_PER_TASK
export MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK

# 3. Execute the workflow
python main_simulation.py
```

Submit the script using:

```bash
sbatch submit_python.sh
```

When we submit the job using something like that, Slurm will run the code in the background. Once the job finishes, we can open the generated `slurm-XXXXXX.out` file to verify that the environment successfully detected our 12 cores and completed the calculation efficiently. The example output is below.

```
=== QuasiCluster: Python Multithreading Test ===
Allocated Threads (OMP_NUM_THREADS): 12

Generating a 12000 x 12000 symmetric matrix...
Starting eigenvalue decomposition (Diagonalization)...
This will heavily utilize the allocated OpenBLAS/MKL CPU cores.
Performing dense matrix multiplication...

=== Simulation Complete ===
Ground state (Lowest eigenvalue) : -89.2042
Highest energy eigenvalue        : 12001.0997
Total time elapsed               : 132.04 seconds.
```

### Multi-Node Parallelization (mpi4py)

If our workflow exceeds 12 cores, we must modify our Python code to use `mpi4py` and distribute the calculation across the network.

**Example Python Script (`test_mpi.py`):**

```python
from mpi4py import MPI
import socket

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
hostname = socket.gethostname()

print(f"Task {rank}/{size-1} is running on {hostname}")
```

**Submission Script (`submit_mpi.sh`):**
Because Slurm handles the network communication natively, we must use `srun` to launch the Python interpreter, and we must strictly set the underlying threads to 1 to prevent core overloads.

```bash
#!/bin/bash
#SBATCH --job-name=PyMPI_test
#SBATCH --partition=qdisk
#SBATCH --nodes=2
#SBATCH --ntasks=24             # Total tasks requested (2 nodes x 12 physical cores)
#SBATCH --ntasks-per-node=12    # Pack 12 tasks onto each node
#SBATCH --time=01:00:00
#SBATCH --output=slurm-%j.out

# 1. Activate the shared environment
source /clusterfs/opt/qupy/bin/activate

# 2. Restrict underlying multithreading to prevent MPI collisions
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1

# 3. Launch the Python script across the network via Slurm
srun python test_mpi.py
```

Submit the script using: `sbatch submit_mpi.sh`

---

# Quantum ESPRESSO Basic Workflow

In this tutorial, we will learn how to perform a complete electronic structure calculation for a silicon crystal using Quantum ESPRESSO on our cluster. We will calculate the self-consistent field (SCF), the electronic band structure, and the density of states (DOS), and finally plot the results using a Jupyter Notebook.

## 1. Creating the Input Files

To begin, we need to create five specific Quantum ESPRESSO input files in our project folder. Using our VS Code connection to the cluster, we can open the File Explorer, create a new folder (for example, `silicon_bands`), and create the following files inside it. 

### The Role of Each Input File

1. **`scf.in` (Self-Consistent Field):** This is the foundational calculation. It solves the Kohn-Sham equations iteratively to find the ground-state electron charge density of the silicon crystal. 
2. **`nscfbands.in` (Non-SCF for Bands):** This calculation reads the converged charge density from the SCF step and calculates the eigenvalues (energy levels) along a specific path of high-symmetry points in the Brillouin zone.
3. **`bands.in` (Bands Post-processing):** This lightweight script extracts the raw eigenvalue data from the previous step and reformats it into a readable structure (`si.bands.gnu`) for plotting.
4. **`nscf.in` (Non-SCF for DOS):** Unlike the bands calculation which follows a linear path, this step calculates the eigenvalues over a dense, uniform 3D grid of k-points. This volumetric data is necessary to determine the Density of States.
5. **`dos.in` (DOS Post-processing):** This script processes the uniform grid data to calculate how many electronic states exist at each energy level, outputting the `si.dos` file.

### Important Configuration Notes

In the `&CONTROL` section of all our input files, there are two important settings to observe:

* **Shared Pseudopotentials:** We use `pseudo_dir = '/clusterfs/repo/pseudo/'`. Instead of downloading pseudopotentials for every project, we rely on this shared repository maintained on our cluster. It saves space and ensures we all use consistent, high-quality atomic data.
* **Omitting `outdir`:** We deliberately omit the standard `outdir` parameter. By omitting it, Quantum ESPRESSO defaults to generating the temporary `.save` folder and the `.xml` output data directly inside our current submission directory (usually as `./si.save`). This keeps our project folder self-contained and prevents users from accidentally overwriting each other's files in the `/tmp` directory. 

### The Input File Contents

Please copy and paste the following text into their respective files.

**File 1: `scf.in`**
```fortran
&CONTROL
  calculation  = 'scf'
  restart_mode = 'from_scratch'
  prefix       = 'si'
  pseudo_dir   = '/clusterfs/repo/pseudo/'
/
&SYSTEM
  ibrav       = 2
  celldm(1)   = 10.20
  nat         = 2
  ntyp        = 1
  ecutwfc     = 30.0
/
&ELECTRONS
  conv_thr    = 1.0e-8
  mixing_beta = 0.7
/
ATOMIC_SPECIES
  Si  28.0855  Si_ONCV_PBE-1.2.upf

ATOMIC_POSITIONS (alat)
  Si 0.00 0.00 0.00
  Si 0.25 0.25 0.25

K_POINTS (automatic)
  6 6 6 1 1 1
```

**File 2: `nscfbands.in`**

```fortran
&CONTROL
  calculation  = 'bands'
  prefix       = 'si'
  pseudo_dir   = '/clusterfs/repo/pseudo/'
/
&SYSTEM
  ibrav       = 2
  celldm(1)   = 10.20
  nat         = 2
  ntyp        = 1
  ecutwfc     = 30.0
  nbnd        = 12
/
&ELECTRONS
  conv_thr    = 1.0e-8
/
ATOMIC_SPECIES
  Si  28.0855  Si_ONCV_PBE-1.2.upf

ATOMIC_POSITIONS (alat)
  Si 0.00 0.00 0.00
  Si 0.25 0.25 0.25

K_POINTS (crystal_b)
  5
  0.500  0.500  0.500  20 
  0.000  0.000  0.000  20 
  0.500  0.000  0.500  20 
  0.625  0.250  0.625  20 
  1.000  1.000  1.000  0
```

**File 3: `bands.in`**

```fortran
&BANDS
  prefix  = 'si'
  filband = 'si.bands'
/
```

**File 4: `nscf.in`**

```fortran
&CONTROL
  calculation  = 'nscf'
  prefix       = 'si'
  pseudo_dir   = '/clusterfs/repo/pseudo/'
/
&SYSTEM
  ibrav       = 2
  celldm(1)   = 10.20
  nat         = 2
  ntyp        = 1
  ecutwfc     = 30.0
  nbnd        = 12
  occupations = 'tetrahedra'
/
&ELECTRONS
  conv_thr    = 1.0e-8
/
ATOMIC_SPECIES
  Si  28.0855  Si_ONCV_PBE-1.2.upf

ATOMIC_POSITIONS (alat)
  Si 0.00 0.00 0.00
  Si 0.25 0.25 0.25

K_POINTS (automatic)
  18 18 18 1 1 1
```

**File 5: `dos.in`**

```fortran
&DOS
  prefix  = 'si'
  fildos  = 'si.dos'
  Emin    = -15.0
  Emax    = 15.0
  DeltaE  = 0.05
/
```

---

## 2. Submitting the SLURM Batch Job

To execute this sequence of calculations, we use a Slurm batch script. Create a file named `run.sh` and paste the following content:

```bash
#!/bin/bash
#SBATCH --job-name=Silicon_Bands_DOS
#SBATCH --partition=qdisk
#SBATCH --nodes=1
#SBATCH --ntasks=6             # Number of MPI ranks
#SBATCH --cpus-per-task=2      # OpenMP threads per rank (6 x 2 = 12 cores total)
#SBATCH --time=24:00:00

# bashquasi automatically reads SLURM_CPUS_PER_TASK=2 and sets OMP_NUM_THREADS=2

NK=2
NDIAG=1

echo "Job started on node: $(hostname)"

echo "Starting SCF..."
mpirun -np $SLURM_NTASKS pw.x -nk $NK -ndiag $NDIAG -in scf.in > scf.out

echo "Starting NSCF for Bands..."
mpirun -np $SLURM_NTASKS pw.x -nk $NK -ndiag $NDIAG -in nscfbands.in > nscfbands.out

echo "Processing Bands..."
mpirun -np $SLURM_NTASKS bands.x -in bands.in > bands.out

echo "Starting NSCF for DOS..."
mpirun -np $SLURM_NTASKS pw.x -nk $NK -ndiag $NDIAG -in nscf.in > nscf.out

echo "Processing DOS..."
mpirun -np $SLURM_NTASKS dos.x -in dos.in > dos.out

echo "Quantum ESPRESSO workflow finished."
```

### Understanding the Resource Allocation

Because our compute nodes contain 12 physical cores, we must strictly design our jobs to respect that limit.

* `#SBATCH --ntasks=6`: We ask Slurm to spawn 6 independent MPI processes.
* `#SBATCH --cpus-per-task=2`: We assign 2 OpenMP threads to each MPI process to handle the heavy mathematical matrices.
* **The Result:** $6 \times 2 = 12$. This perfectly fills the 12 physical cores of a single compute node (`#SBATCH --nodes=1`) without overloading the system.

### Understanding the Parallelization Flags (`NK` and `NDIAG`)

We optimize Quantum ESPRESSO's performance across our 6 MPI tasks using physics-specific command line flags.

* **`NK=2`:** We divide the Brillouin zone calculations into 2 separate pools. Since we have 6 total tasks, this places **3 tasks in each pool**.
* **`NDIAG=1`:** The linear algebra matrix diagonalization requires a perfect square (1, 4, 9, 16). Because we only have 3 tasks in each pool, the largest perfect square that fits is 1.

If we wanted to change the job structure to use purely MPI (12 tasks, 1 thread per task), we could change to `#SBATCH --ntasks=12` and `#SBATCH --cpus-per-task=1`. In that case, we might choose `NK=3` (giving 4 tasks per pool). The largest perfect square that fits in 4 tasks is 4, so we could then optimize the script with `NDIAG=4`.

To submit the job, we run:

```bash
sbatch run.sh
```

---

## 3. Plotting the Results in Jupyter Notebook

Once the workflow finishes, we can visualize our results. Start an interactive Jupyter Notebook session via VS Code as explained in our general Python user guide, create a new notebook (e.g., `plot.ipynb`), and run the following Python code.

### A Note on the Output Directory (`outdir`)

Because we omitted the `outdir` parameter in our Quantum ESPRESSO input files, all outputs are located right where we submitted the script. In the Python code below, look closely at the variable `outdir = './out/'`. If all our resulting files (like `si.xml` inside `si.save`) are in our current working directory, we must change this line in the script to `outdir = './'`. If we manually organized our files into an `out` folder, we leave it as `./out/`.

### The Plotting Script

```python
import os
import glob
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import FuncFormatter

# use plotting style from shared repository in QuasiCluster
plt.style.use('/clusterfs/repo/plot.mplstyle')

# 1. Automate Fermi Energy Extraction from XML
HA_TO_EV = 27.211386245988
efermi = 0.0
outdir = './out/' # change this outdir corresponding to the resulting output folder
prefix = 'si'

in_files = glob.glob('*.in')
if in_files:
    with open(in_files[0], 'r') as f:
        content = f.read()
        outdir_match = re.search(r"outdir\s*=\s*['\"](.*?)['\"]", content)
        prefix_match = re.search(r"prefix\s*=\s*['\"](.*?)['\"]", content)
        if outdir_match:
            outdir = outdir_match.group(1)
        if prefix_match:
            prefix = prefix_match.group(1)

xml_file = os.path.join(outdir, f"{prefix}.xml")
if not os.path.exists(xml_file):
    xml_files = glob.glob(os.path.join(outdir, '*.xml'))
    if xml_files:
        xml_file = xml_files[0]

try:
    with open(xml_file, 'r') as f:
        xml_content = f.read()
        fermi_match = re.search(r'<fermi_energy>\s*(.*?)\s*</fermi_energy>', xml_content)
        highest_match = re.search(r'<highestOccupiedLevel>\s*(.*?)\s*</highestOccupiedLevel>', xml_content)
        lowest_match = re.search(r'<lowestUnoccupiedLevel>\s*(.*?)\s*</lowestUnoccupiedLevel>', xml_content)

        if fermi_match:
            efermi_ha = float(fermi_match.group(1))
            efermi = efermi_ha * HA_TO_EV
            print(f"Extracted Fermi energy: {efermi:.4f} eV")
        elif highest_match and lowest_match:
            highest = float(highest_match.group(1))
            lowest = float(lowest_match.group(1))
            efermi_ha = (highest + lowest) / 2.0
            efermi = efermi_ha * HA_TO_EV
            print(f"Extracted mid-gap energy: {efermi:.4f} eV")
        else:
            print("Energy levels not found in XML. Defaulting Fermi energy to 0.0 eV.")
except FileNotFoundError:
    print(f"XML file {xml_file} not found. Defaulting Fermi energy to 0.0 eV.")

# 2. Initialize figure
fig = plt.figure(figsize=(8, 5))
axBand = fig.add_axes([0,    0, 0.55, 1])
axDOS  = fig.add_axes([0.70, 0, 0.30, 1])

# 3. PLOT EBANDS
data = np.loadtxt(f'{prefix}.bands.gnu')
k = np.unique(data[:, 0])
bands = np.reshape(data[:, 1], (-1, len(k)))

# Map the 5 high-symmetry points defined in nscfbands.in (each segment has 20 points)
pt_L  = k[0]
pt_G1 = k[20]
pt_X  = k[40]
pt_K  = k[60]
pt_G2 = k[-1]

axBand.axhline(0, c='gray', ls=':')
axBand.axvline(pt_G1, c='gray')
axBand.axvline(pt_X, c='gray')
axBand.axvline(pt_K, c='gray')

for band in range(len(bands)):
    axBand.plot(k, bands[band, :] - efermi, c='b')

axBand.set_xlabel('High-symmetry points')
axBand.set_ylabel('Energy (eV)')
axBand.set_xlim(pt_L, pt_G2)
axBand.set_ylim(-10, 5)

axBand.set_xticks([pt_L, pt_G1, pt_X, pt_K, pt_G2], ['L', r'$\Gamma$', 'X', 'U,K', r'$\Gamma$'])
axBand.tick_params(axis='x', which='minor', bottom=False, top=False)
axBand.yaxis.set_major_locator(mpl.ticker.MultipleLocator(5))
axBand.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(1))

# 4. PLOT DOS
ener, dos, idos = np.loadtxt(f'{prefix}.dos', unpack=True)
axDOS.plot(dos, ener - efermi, color='red')

axDOS.set_xlabel('DOS (states/eV/u.c.)')
axDOS.set_ylabel('Energy (eV)')
axDOS.set_xlim(0, 5)
axDOS.set_ylim(-10, 5)
axDOS.yaxis.set_major_locator(mpl.ticker.MultipleLocator(5))
axDOS.yaxis.set_minor_locator(mpl.ticker.MultipleLocator(1))

def format_dos_ticks(x, pos):
    if x == 0:
        return '0'
    else:
        return f'{x:.1f}'

axDOS.xaxis.set_major_formatter(FuncFormatter(format_dos_ticks))

# 5. ADD PANEL LABELS
axBand.text(-0.22, 0.98, '(a)', transform=axBand.transAxes)
axDOS.text(-0.4, 0.98, '(b)', transform=axDOS.transAxes)

plt.savefig('plot-bands-dos.pdf', bbox_inches='tight')
```

Executing this code blocks aligns the extracted Fermi level automatically and applies our standard aesthetic using `plt.style.use('/clusterfs/repo/plot.mplstyle')`. It creates a high-quality PDF file containing both the band structure and the density of states.