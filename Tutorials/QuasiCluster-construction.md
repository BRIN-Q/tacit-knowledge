# QuasiCluster Setup Guide

This document serves as a reference manual and teaching note for current and future administrators of QuasiCluster. We outline the foundational setup of our cluster architecture, covering the primary login node (`quasi06`) and the compute nodes (`quasi07` to `quasi11`). In this guide, we assume that a basic Debian Linux operating system is already installed on all machines. Our cluster utilize Slurm, OpenMPI, and some scientific packages such as Quantum ESPRESSO and various science software.

## Core Infrastructure

### 1. Shared Folder Preparation

To ensure all nodes have access to the exact same files, scripts, and user data, we designate `/clusterfs` as our primary shared directory. We initialize this directory on the login node (`quasi06`) before sharing it across the network.

Run this command on `quasi06`:

```bash
sudo mkdir /clusterfs
```

This directory will host our user home folders, shared Python environments, and administrative scripts.

### 2. SSH Configuration and User Management

Secure Shell (SSH) is required for secure communication between nodes and for user access. We must install both the SSH server and client packages on all nodes (`quasi06` through `quasi11`).

Run this command on all nodes:

```bash
sudo apt update
sudo apt install openssh-server openssh-client
```

#### The User Creation Script

To maintain consistency and security, administrators must not create users manually. We use a dedicated shell script that automates directory creation, environment variable assignment, and SSH key pair generation (using the secure `ed25519` algorithm).

We store this script at `/clusterfs/skel/newuser.sh`.

```bash
#!/bin/bash

echo "Add a new user"
echo "1. Staff, 2. Student, or 3. Visitors ...?"
read -p "Enter a number (1,2,3): " ans

# Safely evaluate input to prevent crashes
case "$ans" in
    1) status='staff' ;;
    2) status='students' ;;
    3) status='visitors' ;;
    *) echo -e "\e[01;31mInvalid input. Please run the script again.\e[0m"; exit 1 ;;
esac

read -p "Enter a username (e.g. taro): " name
if [[ -z "$name" ]]; then
    echo -e "\e[01;31mUsername cannot be empty.\e[0m"
    exit 1
fi

echo "We are now making the user: $name"
homedir="/clusterfs/$status/$name"
echo "Target directory: $homedir"

# Create directory and user (-g users makes 'users' the primary default group)
sudo mkdir -p "$homedir"
sudo useradd -d "$homedir" -s /bin/bash -g users "$name" 
echo "$name:${name}Q720" | sudo chpasswd

# Setup bash environments
echo "source /clusterfs/skel/bashquasi" | sudo tee "$homedir/.bashrc" >/dev/null
sudo ln -s "$homedir/.bashrc" "$homedir/.profile"
sudo ln -s /clusterfs/skel/emacs "$homedir/.emacs"
sudo touch "$homedir/.hushlogin"

# Generate SSH Keys
sudo mkdir -p "$homedir/.ssh"
sudo ssh-keygen -t ed25519 -f "$homedir/.ssh/quasikey" -q -N ""
sudo cp "$homedir/.ssh/quasikey" "$homedir/.ssh/id_ed25519"
sudo cp "$homedir/.ssh/quasikey.pub" "$homedir/.ssh/authorized_keys"

# Apply strict ownership and SSH-mandated permissions
sudo chown -R "$name":users "$homedir"
sudo chmod 700 "$homedir/.ssh"
sudo chmod 600 "$homedir/.ssh/authorized_keys" "$homedir/.ssh/id_ed25519" "$homedir/.ssh/quasikey"
sudo chmod 644 "$homedir/.ssh/quasikey.pub"

# Update NIS (Network Information Service) maps
echo "Pushing updates to NIS maps..."
cd /var/yp || exit
sudo make
cd /clusterfs/skel/ || exit

echo -e "\e[01;32mSuccess! User $name is ready.\e[0m"

```

### 3. Standardized Bash Environment (`bashquasi`)

To provide a uniform experience for all users, we manage aliases, Slurm shortcuts, Python configurations, and login displays through a single shared file. The `newuser.sh` script automatically links this file to each new user's profile.

We store this configuration at `/clusterfs/skel/bashquasi`.

```bash
# ~/.bashrc: executed by bash(1) for non-login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# don't put duplicate lines or lines starting with space in the history.
HISTCONTROL=ignoreboth

# append to the history file, don't overwrite it
shopt -s histappend

# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
HISTSIZE=1000
HISTFILESIZE=2000

# check the window size after each command and, if necessary, update the values.
shopt -s checkwinsize

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color|*-256color) color_prompt=yes;;
esac

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
        color_prompt=yes
    else
        color_prompt=
    fi
fi

if [ "$color_prompt" = yes ]; then
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
else
    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi
unset color_prompt force_color_prompt

# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
    ;;
*)
    ;;
esac

# enable programmable completion features
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/bin" ] ; then
    PATH="$HOME/bin:$PATH"
fi

#===============================================================================
#  ALIASES AND FUNCTIONS
#===============================================================================

# enable color support 
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && \
        eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias dir='dir --color=auto'
    alias vdir='vdir --color=auto'

    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

# colored GCC warnings and errors
export GCC_COLORS='error=01;31:warning=01;35:note=01;36:caret=01;32:locus=01:quote=01'

# The 'ls' family
alias ls='ls -h --color=auto'
alias lx='ls -lXB'   #  Sort by extension.
alias lk='ls -lSr'   #  Sort by size, biggest last.
alias lt='ls -ltr'   #  Sort by date, most recent last.
alias lc='ls -ltcr'  #  Sort by/show change time,most recent last.
alias lu='ls -ltur'  #  Sort by/show access time,most recent last.
alias ll="ls -lv --group-directories-first"
alias lm='ll |more'  
alias lr='ll -R'     
alias la='ll -A'     
alias tree='tree -Csuh' 

# Tailoring 'less'
alias more='less'
export PAGER=less
export LESSCHARSET='latin1'
export LESSOPEN='|/usr/bin/lesspipe.sh %s 2>&-'
export LESS='-i -N -w  -z-4 -g -e -M -X -F -R -P%t?f%f \
:stdin .?pb%pb\%:?lbLine %lb:?bbByte %bb:-...'

export LESS_TERMCAP_mb=$'\E[01;31m'
export LESS_TERMCAP_md=$'\E[01;31m'
export LESS_TERMCAP_me=$'\E[0m'
export LESS_TERMCAP_se=$'\E[0m'
export LESS_TERMCAP_so=$'\E[01;44;33m'
export LESS_TERMCAP_ue=$'\E[0m'
export LESS_TERMCAP_us=$'\E[01;32m'

# Other Personal Aliases
alias rm='rm -i'
alias cp='cp -i'
alias mv='mv -i'
alias mkdir='mkdir -p'

alias h='history'
alias j='jobs -l'
alias which='type -a'
alias ..='cd ..'

alias path='echo -e ${PATH//:/\\n}'
alias libpath='echo -e ${LD_LIBRARY_PATH//:/\\n}'

alias du='du -kh'
alias df='df -kTh'

alias f644='find . -type f -exec chmod 0644 {} \;'
alias d755='find . -type d -exec chmod 0755 {} \;'

alias xs='cd'
alias vf='cd'
alias moer='more'
alias moew='more'
alias kk='ll'

# checking disk capacity (sudo removed so standard users can run it safely)
alias cekiceki='du -hs ./* 2>/dev/null | sort -hr'

#===============================================================================
#  CLUSTER & SLURM UTILITIES
#===============================================================================

# Slurm shortcuts
alias sq='squeue -u $USER'
alias si='sinfo'
alias scancel='scancel -s KILL'
alias scancelall='scancel -u $USER'

# cleaning QE
alias clqe='rm -Rf *~ *.out *.xml *.save *.bands *.gnu *.rap out* CRASH *.dos *__py* *.log'

# Check personal home directory usage and top 10 largest folders
myusage() {
    echo -e "\e[01;34mCalculating usage for $HOME...\e[0m"
    du -sh $HOME 2>/dev/null
    echo -e "\n\e[01;34mTop 10 largest subdirectories:\e[0m"
    du -hs $HOME/* 2>/dev/null | sort -hr | head -n 10
}

# Smart archive extractor
extract() {
    if [ -f $1 ] ; then
        case $1 in
            *.tar.bz2)   tar xvjf $1    ;;
            *.tar.gz)    tar xvzf $1    ;;
            *.bz2)       bunzip2 $1     ;;
            *.rar)       unrar x $1     ;;
            *.gz)        gunzip $1      ;;
            *.tar)       tar xvf $1     ;;
            *.tbz2)      tar xvjf $1    ;;
            *.tgz)       tar xvzf $1    ;;
            *.zip)       unzip $1       ;;
            *.Z)         uncompress $1  ;;
            *.7z)        7z x $1        ;;
            *)           echo "Don't know how to extract '$1'..." ;;
        esac
    else
        echo "'$1' is not a valid file!"
    fi
}

clust() {
    echo -e "\e[01;33m=== Compute Resource Status ===\e[0m"
    
    # Use POSIX format (-P) for df to prevent line wrapping on long device names
    local CFS_USED=$(df -hP /clusterfs 2>/dev/null | awk 'NR==2 {print $4}')
    local CFS_TOTAL=$(df -hP /clusterfs 2>/dev/null | awk 'NR==2 {print $3}')
    echo -e "/clusterfs: \e[01;36m${CFS_USED}\e[0m Used / \e[01;36m${CFS_TOTAL}\e[0m Total"
    
    echo "Load Averages:"
    
    for node in quasi06 quasi07 quasi08 quasi09 quasi10 quasi11; do
        if [ "$node" == "quasi06" ]; then
            # Gather metrics locally without SSH overhead
            local LOAD=$(awk '{print $1}' /proc/loadavg)
            local CPUS=$(nproc)
            echo -e "  $node: \e[01;32m$LOAD\e[0m / $CPUS CPUs"
        else
            # Fetch compute node status instantly via SSH
            local OUT=$(ssh -o ConnectTimeout=1 -o BatchMode=yes -q $node "awk '{print \$1}' /proc/loadavg && nproc" 2>/dev/null)
            if [ $? -eq 0 ] && [ -n "$OUT" ]; then
                local LOAD=$(echo "$OUT" | sed -n '1p')
                local CPUS=$(echo "$OUT" | sed -n '2p')
                echo -e "  $node: \e[01;32m$LOAD\e[0m / $CPUS CPUs"
            else
                echo -e "  $node: \e[01;31mdown\e[0m"
            fi
        fi
    done
}

#===============================================================================
#  PYTHONIC STUFFS
#===============================================================================

alias python='python3'
alias qupy='source /clusterfs/opt/qupy/bin/activate'

alias da='deactivate'

# Launch Jupyter on a Slurm Compute Node
qupy-jupyter() {
    # Default to 4 cores if the user does not specify a number
    local cores=${1:-4}
    local port=$(shuf -i 8000-9999 -n 1)
    
    echo -e "\e[01;32mAllocating $cores cores on a compute node for Jupyter...\e[0m"
    echo -e "When the server starts, copy the URL provided and paste it into VS Code."
    
    # IMPORTANT: --ntasks=1 ensures only ONE Jupyter server starts.
    # --cpus-per-task=$cores reserves the multi-core processing power for it.
    srun --partition=qdisk --nodes=1 --ntasks=1 --cpus-per-task=$cores --pty bash -c "
        source /clusterfs/opt/qupy/bin/activate
        # Binding to hostname ensures VS Code on quasi06 can route to it
        jupyter notebook --no-browser --port=$port --ip=\$(hostname)
    "
}

#===============================================================================
#  ADDITIONAL PATH VARIABLES
#===============================================================================

export PATH="$HOME/.local/bin:$PATH"
export PATH=/opt/QE/bin:$PATH
export PATH=/clusterfs/opt/QE/bin:$PATH

#===============================================================================
#  PARALLELIZATION SETTINGS
#===============================================================================

if [ -n "$SLURM_JOB_ID" ]; then
    # If inside a Slurm job (interactive), strictly obey the requested CPU cores.
    # If CPUs per task isn't defined, default to 1 to prevent MPI thread collisions.
    export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
    export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
    export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
    export VECLIB_MAXIMUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
    export NUMEXPR_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
else
    # If on the login node (quasi06), safely default to 4 threads.
    export OMP_NUM_THREADS=4
    export OPENBLAS_NUM_THREADS=4
    export MKL_NUM_THREADS=4
    export VECLIB_MAXIMUM_THREADS=4
    export NUMEXPR_NUM_THREADS=4
fi

#===============================================================================
#  LOGIN STATUS DISPLAY
#===============================================================================

# Only display status if the shell is interactive (avoids breaking rsync/scp)
if [[ $- == *i* ]]; then
    echo -e "\n\e[01;32mWelcome to QuasiCluster, $USER!\e[0m\n"
    
    # Only calculate and display storage and cluster status if logged into quasi06
    if [[ "$(hostname -s)" == "quasi06" ]]; then
        echo -e "\e[01;33m=== Storage Status ===\e[0m"
        USAGE=$(du -sh $HOME 2>/dev/null | awk '{print $1}')
        echo -e "Home Directory ($HOME): \e[01;36m$USAGE\e[0m"
        echo -e "(Type \e[01;32mmyusage\e[0m for a detailed breakdown)\n"
        
        echo -e "\e[01;33m=== Compute Resource Status ===\e[0m"
        # Use POSIX format (-P) for df to prevent line wrapping on long device names
        CFS_USED=$(df -hP /clusterfs 2>/dev/null | awk 'NR==2 {print $4}')
        CFS_TOTAL=$(df -hP /clusterfs 2>/dev/null | awk 'NR==2 {print $3}')
        echo -e "/clusterfs: \e[01;36m${CFS_USED}\e[0m Used / \e[01;36m${CFS_TOTAL}\e[0m Total"
        echo "Load Averages:"
        
        for node in quasi06 quasi07 quasi08 quasi09 quasi10 quasi11; do
            if [ "$node" == "quasi06" ]; then
                # Gather metrics locally without SSH overhead
                LOAD=$(awk '{print $1}' /proc/loadavg)
                CPUS=$(nproc)
                echo -e "  $node: \e[01;32m$LOAD\e[0m / $CPUS CPUs"
            else
                # Use BatchMode and ConnectTimeout to instantly fail if a node is offline
                OUT=$(ssh -o ConnectTimeout=1 -o BatchMode=yes -q $node "awk '{print \$1}' /proc/loadavg && nproc" 2>/dev/null)
                if [ $? -eq 0 ] && [ -n "$OUT" ]; then
                    LOAD=$(echo "$OUT" | sed -n '1p')
                    CPUS=$(echo "$OUT" | sed -n '2p')
                    echo -e "  $node: \e[01;32m$LOAD\e[0m / $CPUS CPUs"
                else
                    echo -e "  $node: \e[01;31mdown\e[0m"
                fi
            fi
        done
        echo ""
    fi
    
    # Always display Slurm jobs regardless of the node
    echo -e "\e[01;33m=== Slurm Jobs ===\e[0m"
    JOB_COUNT=$(squeue -u $USER -h 2>/dev/null | wc -l)
    if [ "$JOB_COUNT" -gt 0 ]; then
        squeue -u $USER
    else
        echo "You currently have no active or pending jobs."
    fi
    echo ""
fi

```

### 4. Network File System (NFS) using `autofs`

We use NFS to mount `/clusterfs` across all compute nodes. We deploy `autofs` to mount directories automatically only when a user accesses them, which conserves network resources.

First, we synchronize the `/etc/hosts` file across all nodes (login and compute nodes) to map the internal IPs:

```text
10.10.216.30    quasi06
10.10.240.17    quasi07
10.10.240.18    quasi08
10.10.240.19    quasi09
10.10.240.15    quasi10
10.10.240.16    quasi11

```
Make sure that `/etc/hosts` files for `quasi06-11` contain the same lines as above.

Next, we install `autofs` on all nodes:

```bash
sudo apt update
sudo apt install autofs

```

#### NFS Server Setup (`quasi06`)

On the login node, we define the export rules for the BRIN-Q subnets by editing `/etc/exports`:

```text
/clusterfs    10.10.240.0/22(rw,sync,no_root_squash,no_subtree_check)
/clusterfs    10.10.219.0/21(rw,sync,no_root_squash,no_subtree_check)

```

After editing, apply the exports by running `sudo exportfs -a`.

#### NFS Client Setup (`quasi07` to `quasi11`)

On the compute nodes, we configure `autofs` to link the shared directory.

1. Add the following line to `/etc/auto.master`:
```text
/-    /etc/auto.mount
```

2. Create or edit `/etc/auto.mount` and add the specific mount instruction:
```text
/clusterfs    -fstype=nfs,rw    quasi06:/clusterfs
```

3. Restart the service: `sudo systemctl restart autofs`.

### 5. Network Information Service (NIS) Setup

To manage user credentials efficiently, we use NIS. This allows us to create a user account on `quasi06` once, and have that account recognized by every compute node automatically.

First, install the NIS package on all nodes:

```bash
sudo apt install nis
```

#### NIS Master Setup (`quasi06`)

We configure `quasi06` to serve as the NIS master.

1. Edit `/etc/ypserv.securenets` to grant access strictly to our internal subnets:
```text
# comment out
#0.0.0.0                0.0.0.0
#::/0
255.255.248.0   10.10.219.0
255.255.252.0   10.10.240.0

```

2. Edit `/etc/defaultdomain` and set the domain name:
```text
quasi

```

3. Initialize the NIS database by running:
```bash
sudo /usr/lib/yp/ypinit -m

```

4. Whenever we add new users or modify the `/etc/hosts` file on `quasi06`, we must push the updates to the database:
```bash
cd /var/yp
sudo make

```

#### NIS Client Setup (`quasi07` to `quasi11`)

We configure the compute nodes to query `quasi06` for user authentication.

1. Edit `/etc/yp.conf` and add the master server domain at the end of the file:
```text
domain quasi server quasi06

```

2. Edit `/etc/nsswitch.conf` to prioritize local files, then systemd, and finally NIS. Modify these specific lines around line 7:
```text
passwd:         files systemd nis
group:          files systemd nis
shadow:         files nis

```

3. Edit `/etc/defaultdomain` to match the master server:
```text
quasi

```

4. Restart and enable the required services to apply the configuration:
```bash
sudo systemctl restart rpcbind nscd ypbind
sudo systemctl enable rpcbind ypbind

```

## Clustering Setup

### 1. System Preparation and Time Synchronization

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
    ssh -t $node 'sudo groupadd -g 1111 munge && sudo useradd -m -d /home/munge -u 1111 -g munge -s /bin/bash munge'
    
    # Create the slurm group and user (UID/GID 1121)
    ssh -t $node 'sudo groupadd -g 1121 slurm && sudo useradd -m -d /home/slurm -u 1121 -g slurm -s /bin/bash slurm'
done
```

**Configure local scratch storage on compute nodes:**
Create the job temporary directory with a sticky bit to prevent cross-user data deletion.

```bash
for node in quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t $node 'sudo mkdir -p /scratch && sudo chown root:users /scratch && sudo chmod 1775 /scratch'
done
```
### 2. Munge Authentication Setup

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

### 3. Slurm Configuration (Shared Directory)

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
DefMemPerCPU=5200

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

# Safely retrieve the submission directory and save it locally for the epilog
WORKDIR=$(scontrol show job $SLURM_JOB_ID | grep WorkDir | awk -F '=' '{print $2}' | awk '{print $1}')
if [ -n "$WORKDIR" ]; then
    echo "$WORKDIR" > /scratch/slurm-$SLURM_JOB_ID/.workdir_path
fi
```

`/clusterfs/config/slurm/epilog.sh`:

```bash
#!/bin/bash

# 1. Read the saved submission directory
WORKDIR_FILE="/scratch/slurm-$SLURM_JOB_ID/.workdir_path"

if [ -f "$WORKDIR_FILE" ]; then
    WORKDIR=$(cat "$WORKDIR_FILE")
    
    # 2. If the directory exists, transfer the data back as the user
    if [ -n "$WORKDIR" ] && [ -d "$WORKDIR" ]; then
        # Creates a unique folder in your submission directory to prevent overwriting
        DEST_DIR="$WORKDIR/out-$SLURM_JOB_ID"
        
        # Execute rsync as the job owner, excluding the hidden tracking file
        sudo -u $SLURM_JOB_USER bash -c "mkdir -p \"$DEST_DIR\" && rsync -a --exclude='.workdir_path' /scratch/slurm-$SLURM_JOB_ID/ \"$DEST_DIR/\""
    fi
fi

# 3. Clean up the compute node's local disk
rm -rf /scratch/slurm-$SLURM_JOB_ID
```

`/clusterfs/config/slurm/taskprolog.sh`:

```bash
#!/bin/bash
# Injects the environment variable into the user's batch script.

echo "export OMP_NUM_THREADS=1"

# Generic scratch variables for all cluster applications
echo "export SLURM_TMPDIR=/scratch/slurm-$SLURM_JOB_ID/"
echo "export LOCAL_SCRATCH=/scratch/slurm-$SLURM_JOB_ID/"
# Specific variable for native Quantum ESPRESSO routing
echo "export ESPRESSO_TMPDIR=/scratch/slurm-$SLURM_JOB_ID/"
```

Apply executable permissions:

```bash
chmod +x /clusterfs/config/slurm/prolog.sh /clusterfs/config/slurm/epilog.sh /clusterfs/config/slurm/taskprolog.sh
```

### 4. Install and Start Slurm Services

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

### 5. OpenMPI Configuration

Disable OpenMPI's default processor binding limits system-wide. This prevents crashes when OpenMPI interacts with the strict CPU mapping enforced by Slurm's cgroups on hyperthreaded nodes.

```bash
for node in quasi06 quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t $node 'sudo apt install openmpi-bin libopenmpi-dev -y'
    ssh -t $node 'echo "hwloc_base_use_hwthreads_as_cpus = true" | sudo tee -a /etc/openmpi/openmpi-mca-params.conf'
    ssh -t $node 'echo "rmaps_base_mapping_policy = core:OVERSUBSCRIBE" | sudo tee -a /etc/openmpi/openmpi-mca-params.conf'
done
```

### 6. Quantum ESPRESSO Deployment

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

### 7. Standard Job Submission Workflow

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