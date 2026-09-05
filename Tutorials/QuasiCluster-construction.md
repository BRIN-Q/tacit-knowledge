# Quasi Cluster Setup Guide

This guide details the configuration of a Debian-based computing cluster utilizing Slurm, OpenMPI, and Quantum ESPRESSO. We assume a base Debian installation with SSH access and a shared filesystem mounted at `/clusterfs`.

## 1. System Preparation and Time Synchronization

All nodes require precise time synchronization and identical system user configurations to prevent authentication errors and scheduling anomalies.

Execute the following commands on the login node (`quasi06`) to prepare all nodes (`quasi06`, `quasi07`, `quasi08`, `quasi09`, `quasi10`, `quasi11`).

**Install prerequisites and NTP daemon:**

```bash
for node in quasi06 quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t $node 'sudo apt update && sudo apt install chrony cgroup-tools curl build-essential -y && sudo systemctl enable --now chrony'
done
```

**Create uniform system users:**
To prevent package manager conflicts, explicitly create identical `munge` and `slurm` users on all nodes before installing their respective packages.

```bash
for node in quasi06 quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t $node 'sudo groupadd -g 990 munge && sudo useradd -m -c "MUNGE Uid 'N' Gid Emporium" -d /nonexistent -u 990 -g munge -s /usr/sbin/nologin munge'
    ssh -t $node 'sudo groupadd -g 991 slurm && sudo useradd -m -c "Slurm workload manager" -d /nonexistent -u 991 -g slurm -s /usr/sbin/nologin slurm'
done
```

Note that as of September 4, 2026 we use the following `munge` and `slurm` settings accidentally:
```bash
for node in quasi06 quasi07 quasi08 quasi09 quasi10 quasi11; do
    # Create the munge group and user (UID/GID 1111)
    ssh -t $node 'echo "munge:x:1111:" | sudo tee -a /etc/group'
    ssh -t $node 'echo "munge:x:1111:1111:Munge Auth:/nonexistent:/usr/sbin/nologin" | sudo tee -a /etc/passwd '
    
    # Create the slurm group and user (UID/GID 1121)
    ssh -t $node 'echo "slurm:x:1121:" | sudo tee -a /etc/group'
    ssh -t $node 'echo "slurm:x:1121:1121:Slurm Manager:/nonexistent:/bin/bash" | sudo tee -a /etc/passwd'
done
```

**Configure local scratch storage on compute nodes:**
Create the job temporary directory with a sticky bit to prevent cross-user data deletion.

```bash
for node in quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t $node 'sudo mkdir -p /scratch && sudo chown root:users /scratch && sudo chmod 1775 /scratch'
done
```
## 2. Munge Authentication Setup

Munge requires an identical cryptographic key across the entire cluster.

**Install Munge on all nodes:**

```bash
for node in quasi06 quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t $node 'sudo apt install munge -y'
done
```

**Generate and distribute the key:**
Generate the key on `quasi06` and replicate it to the compute nodes with strict permissions.

```bash
sudo /usr/sbin/mungekey
for node in quasi07 quasi08 quasi09 quasi10 quasi11; do
    sudo scp /etc/munge/munge.key $node:/tmp/munge.key
    ssh -t $node 'sudo mv /tmp/munge.key /etc/munge/munge.key && sudo chown munge:munge /etc/munge/munge.key && sudo chmod 400 /etc/munge/munge.key && sudo systemctl restart munge'
done
```

## 3. Slurm Configuration (Shared Directory)

Create all configuration scripts inside the shared `/clusterfs` filesystem so they can be maintained from the login node and read by all compute nodes.

**Create the base configuration directory:**

```bash
mkdir -p /clusterfs/config/slurm
```

**1. `slurm.conf`:**
Create `/clusterfs/config/slurm/slurm.conf` and input the cluster parameters using any text editor, e.g., 
```bash
sudo nano /clusterfs/config/slurm/slurm.conf
```
Write the following contents:

```ini
ClusterName=quasi
SlurmctldHost=quasi06

# Security and Base Configuration
SlurmUser=slurm
ReturnToService=2
InactiveLimit=0
MinJobAge=300
Waittime=0

# Timers
SlurmctldTimeout=120
SlurmdTimeout=1200
KillWait=30

# Logging and State
SlurmctldPidFile=/var/run/slurmctld.pid
SlurmctldPort=6817
SlurmdPidFile=/var/run/slurmd.pid
SlurmdPort=6818
SlurmdSpoolDir=/var/spool/slurmd
StateSaveLocation=/var/spool/slurmctld
SlurmctldDebug=info
SlurmctldLogFile=/var/log/slurmctld.log
SlurmdDebug=info
SlurmdLogFile=/var/log/slurmd.log

# Prolog and Epilog Setup
Prolog=/clusterfs/config/slurm/prolog.sh
Epilog=/clusterfs/config/slurm/epilog.sh
TaskProlog=/clusterfs/config/slurm/taskprolog.sh

JobSubmitPlugins=lua

# Resource Allocation and Process Tracking
ProctrackType=proctrack/cgroup
TaskPlugin=task/affinity,task/cgroup
SelectType=select/cons_tres
SelectTypeParameters=CR_Core_Memory,CR_ONE_TASK_PER_CORE

# Scheduling
SchedulerType=sched/backfill
JobCompType=jobcomp/none
JobAcctGatherFrequency=30

# COMPUTE NODES
NodeName=quasi07 CPUs=24 RealMemory=128701 Sockets=1 CoresPerSocket=12 ThreadsPerCore=2 State=UNKNOWN
NodeName=quasi08 CPUs=24 RealMemory=128701 Sockets=1 CoresPerSocket=12 ThreadsPerCore=2 State=UNKNOWN
NodeName=quasi09 CPUs=24 RealMemory=128701 Sockets=1 CoresPerSocket=12 ThreadsPerCore=2 State=UNKNOWN
NodeName=quasi10 CPUs=24 RealMemory=128669 Sockets=1 CoresPerSocket=12 ThreadsPerCore=2 State=UNKNOWN
NodeName=quasi11 CPUs=24 RealMemory=128669 Sockets=1 CoresPerSocket=12 ThreadsPerCore=2 State=UNKNOWN

# PARTITIONS
PartitionName=qdisk Nodes=quasi[07-11] Default=YES MaxTime=INFINITE State=UP
```
Update the `CPUs`, `RealMemory`, `Sockets`, `CoresPerSocket`, and `ThreadsPerCore` values to match your specific hardware profiling from `slurmd -C`. Note that if we want to see all outputs of `slurmd -C` command across all nodes from `quasi06`, it is possible to do the following:
```bash
for node in quasi06 quasi07 quasi08 quasi09 quasi10 quasi11; do 
    ssh -t $node 'echo "=== $node ===" && /usr/sbin/slurmd -C'; 
done
```

**2. `cgroup.conf`:**
Create `/clusterfs/config/slurm/cgroup.conf`.
```bash
sudo nano /clusterfs/config/slurm/cgroup.conf
```
Write these contents and save:
```ini
ConstrainCores=yes
ConstrainRAMSpace=yes
```

**3. `job_submit.lua`:**
Create `/clusterfs/config/slurm/job_submit.lua` to enforce default batch log names without affecting interactive jobs.
```bash
sudo nano /clusterfs/config/slurm/cgroup.conf
```
Write these contents and save:
```lua
function slurm_job_submit(job_desc, part_list, submit_uid)
    if job_desc.script ~= nil and job_desc.script ~= "" then
        if job_desc.standard_output == nil or job_desc.standard_output == "" then
            job_desc.standard_output = "slurm-%j.out"
        end
        if job_desc.standard_error == nil or job_desc.standard_error == "" then
            job_desc.standard_error = "slurm-%j.log"
        end
    end
    return slurm.SUCCESS
end

function slurm_job_modify(job_desc, job_rec, part_list, modify_uid)
    return slurm.SUCCESS
end
```

**4. Administrative Scripts:**
Create the dynamic scripts to manage the scratch directory and environment variables (e.g., using `sudo nano` command again). Hereafter, we skip showing `sudo nano` in the creation of any file for simplicity, unless we would like to emphasize specific contexts.

`/clusterfs/config/slurm/prolog.sh`:

```bash
#!/bin/bash
# Prepares the local directory on the compute node before the job starts.

mkdir -p /scratch/slurm-$SLURM_JOB_ID
chown $SLURM_JOB_USER: /scratch/slurm-$SLURM_JOB_ID
```

`/clusterfs/config/slurm/epilog.sh`:

```bash
#!/bin/bash
# Cleans the local directory after the job completely finishes.

rm -rf /scratch/slurm-$SLURM_JOB_ID
```

`/clusterfs/config/slurm/taskprolog.sh`:

```bash
#!/bin/bash
# Injects the environment variable into the user's batch script.

echo "export OMP_NUM_THREADS=1"
echo "export ESPRESSO_TMPDIR=/scratch/slurm-$SLURM_JOB_ID"
```

Apply executable permissions:

```bash
chmod +x /clusterfs/config/slurm/prolog.sh /clusterfs/config/slurm/epilog.sh /clusterfs/config/slurm/taskprolog.sh
```

## 4. Install and Start Slurm Services

**Login Node (`quasi06`):**

```bash
sudo apt install slurmctld slurm-client -y
sudo ln -sf /clusterfs/config/slurm/slurm.conf /etc/slurm/slurm.conf
sudo ln -sf /clusterfs/config/slurm/cgroup.conf /etc/slurm/cgroup.conf
sudo ln -sf /clusterfs/config/slurm/job_submit.lua /etc/slurm/job_submit.lua
sudo systemctl enable --now slurmctld
```

**Compute Nodes (`quasi07` to `quasi11`):**

```bash
for node in quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t $node 'sudo apt install slurmd slurm-client -y'
    ssh -t $node 'sudo ln -sf /clusterfs/config/slurm/slurm.conf /etc/slurm/slurm.conf'
    ssh -t $node 'sudo ln -sf /clusterfs/config/slurm/cgroup.conf /etc/slurm/cgroup.conf'
    ssh -t $node 'sudo systemctl enable --now slurmd'
done
```

## 5. OpenMPI Configuration

Disable OpenMPI's default processor binding limits system-wide. This prevents crashes when OpenMPI interacts with the strict CPU mapping enforced by Slurm's cgroups on hyperthreaded nodes.

```bash
for node in quasi06 quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t $node 'sudo apt install openmpi-bin libopenmpi-dev -y'
    ssh -t $node 'echo "hwloc_base_use_hwthreads_as_cpus = true" | sudo tee -a /etc/openmpi/openmpi-mca-params.conf'
    ssh -t $node 'echo "rmaps_base_mapping_policy = core:OVERSUBSCRIBE" | sudo tee -a /etc/openmpi/openmpi-mca-params.conf'
done
```

## 6. Quantum ESPRESSO Deployment

Install the required mathematics libraries and configure OpenBLAS on all compute nodes to support Quantum ESPRESSO executables.

```bash
for node in quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t $node 'sudo apt install libblas3 liblapack3 libscalapack-mpi-dev libfftw3-double3 libopenblas0 -y'
    ssh -t $node 'sudo update-alternatives --set libblas.so.3-x86_64-linux-gnu /usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3'
    ssh -t $node 'sudo update-alternatives --set liblapack.so.3-x86_64-linux-gnu /usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3'
done
```

For the first installation of Quantum ESPRESSO in `quasi06`, we can create `/clusterfs/opt/QE` there:
```bash
sudo mkdir -p /clusterfs/opt/QE
```
We also would like to execute an automated flow for Quantum ESPRESSO maintenance from `/clusterfs/skel/` folder. If the folder does not exist yet, do:
```bash
sudo mkdir -p /clusterfs/skel
cd /clusterfs/skel/
```
Create the `/clusterfs/skel/update_qe.sh` script below. Note that `QE_VERSION`, `QE_URL`, `TAR_FILE`, `BUILD_DIR`, `SHARED_BIN_DIR`, `LOCAL_BIN_DIR`, and `NODES` can be adjusted depending on the real situation.

```bash
#!/bin/bash
# Script to automate downloading, compiling, and distributing Quantum ESPRESSO

# Exit immediately if a command exits with a non-zero status
set -e

QE_VERSION="7.6"
QE_URL="https://gitlab.com/QEF/q-e/-/archive/qe-${QE_VERSION}/q-e-qe-${QE_VERSION}.tar.gz"
TAR_FILE="q-e-qe-${QE_VERSION}.tar.gz"
BUILD_DIR="/clusterfs/skel/build_qe_${QE_VERSION}"

SHARED_BIN_DIR="/clusterfs/opt/QE/bin"
LOCAL_BIN_DIR="/opt/QE/bin"
NODES=("quasi06" "quasi07" "quasi08" "quasi09" "quasi10" "quasi11")

echo -e "\e[01;34m[1/5] Preparing build directory...\e[0m"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

echo -e "\e[01;34m[2/5] Downloading Quantum ESPRESSO $QE_VERSION...\e[0m"
if [ ! -f "$TAR_FILE" ]; then
    wget -q --show-progress "$QE_URL" -O "$TAR_FILE"
else
    echo "Archive already exists. Skipping download."
fi

echo "Extracting archive..."
tar -xzf "$TAR_FILE"
cd "q-e-qe-${QE_VERSION}"

echo -e "\e[01;34m[3/5] Configuring and compiling source code...\e[0m"
# Run configure with  standard Debian library flags
./configure

# Compile using all available CPU cores on the current machine to speed up the process
make all -j8

echo -e "\e[01;34m[4/5] Deploying binaries to shared storage (/clusterfs)...\e[0m"
sudo mkdir -p "$SHARED_BIN_DIR"
# The compiled binaries are located in the bin/ folder of the source directory
sudo cp bin/* "$SHARED_BIN_DIR/"
echo "Binaries successfully updated in $SHARED_BIN_DIR"

echo -e "\e[01;34m[5/5] Distributing binaries to local storage on all nodes...\e[0m"
for node in "${NODES[@]}"; do
    echo "Updating local binaries on $node..."
    # We use ssh -t to allocate a terminal for sudo.
    # The nodes copy the files directly from the mounted /clusterfs, avoiding network bottlenecks.
    ssh -t "$node" "sudo mkdir -p $LOCAL_BIN_DIR && sudo cp $SHARED_BIN_DIR/* $LOCAL_BIN_DIR/ && echo 'Success on $node'"
done

echo -e "\e[01;34m[Cleanup] Removing temporary build files...\e[0m"
cd /clusterfs/skel
rm -rf "$BUILD_DIR"

echo -e "\e[01;32mQuantum ESPRESSO update complete across the entire cluster.\e[0m"
```
Then, run the script from the folder `/clusterfs/skel/` of `quasi06`.
```bash
bash update_qe.sh
```
On the other hand, if we assume Quantum ESPRESSO is already compiled in `/clusterfs/opt/QE` on `quasi06`, we can simply distribute the binaries to all compute nodes with the following commands.
```bash
for node in quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t $node 'sudo mkdir -p /opt/QE && sudo chown $USER:$USER /opt/QE'
    rsync -av /clusterfs/opt/QE/ $node:/opt/QE/
    ssh -t $node 'sudo chown -R root:users /opt/QE'
done
```

## 7. Standard Job Submission Workflow

With data routing and logging handled natively by the cluster scripts, users can run calculations using minimal bash scripts. The native `$ESPRESSO_TMPDIR` parameter injected by Slurm automatically forces heavy I/O operations into the node's local `/scratch`, while retaining small output files in the user's submission directory.

**Standard `run.sh` template:**

```bash
#!/bin/bash
#SBATCH --job-name=Silicon_Bands
#SBATCH --partition=qdisk
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --time=24:00:00

echo "Job started on node: $(hostname)"

echo "Starting SCF..."
mpirun -np $SLURM_NTASKS pw.x -in scf.in > scf.out

echo "Starting NSCF for Bands..."
mpirun -np $SLURM_NTASKS pw.x -in nscfbands.in > nscfbands.out

echo "Processing Bands..."
mpirun -np $SLURM_NTASKS bands.x -in bands.in > bands.out

echo "Quantum ESPRESSO workflow finished."
```