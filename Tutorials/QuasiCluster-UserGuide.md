# Python and VS Code Integration

Welcome to the QuasiCluster Python environment. This cluster provides a fully shared, pre-configured Python environment containing the essential scientific libraries (NumPy, SciPy, QuTiP, mpi4py, Qiskit, etc.) optimized for our hardware.

This guide explains how we can connect Visual Studio Code (VS Code) to the cluster, utilize the shared Python environment, and submit heavy parallelized tasks across our compute nodes.

## 1. Connecting VS Code to the Login Node

To interact with the cluster and edit scripts, we first need to connect VS Code to our login node (`quasi06`). Because our cluster is accessible globally, we use a Cloudflare tunnel to securely route the SSH connection to `ssh.quasicluster.org`.

We must ensure the `cloudflared` executable is installed on our local machine. Then, we configure our local SSH settings by editing the SSH config file. The `User username` and `IdentityFile ...` part should be modified accordingly to our real `username` and `/path/to/user/quasikey` (the real location where we put `quasikey` given by the QuasiCluster administrators).

**For Linux and macOS users:**
Add the following configuration to `~/.ssh/config`:

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

**For Windows users:**
Add the following configuration to `C:\Users\Username\.ssh\config`. Ensure `cloudflared.exe` is installed and accessible in the system PATH:

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
2. Run the `qupy-jupyter` command, specifying how many cores we need (default is 4, maximum is 24):
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
Active Math Threads     : 1

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

Standard scientific libraries rely on C-based OpenBLAS and OpenMP to accelerate matrix math. To utilize multiple cores on a single compute node (up to 24 cores), we map hardware threads to the CPU allocation.

Create a file named `submit_python.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=Py_Sim
#SBATCH --partition=qdisk
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
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

Submit the script using: `sbatch submit_python.sh`

### Multi-Node Parallelization (mpi4py)

If our workflow exceeds 24 cores, we must modify our Python code to use `mpi4py` and distribute the calculation across the network.

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
#SBATCH --ntasks=48             # Total cores requested (2 nodes x 24 cores)
#SBATCH --ntasks-per-node=24    # Pack 24 tasks onto each node
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