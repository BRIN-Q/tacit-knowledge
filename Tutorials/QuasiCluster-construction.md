# QuasiCluster Setup Guide

This document is our reference manual and teaching note for current and future QuasiCluster administrators. We describe our login node (`quasi06`) and five compute nodes (`quasi07` to `quasi11`). We assume that Debian is already installed on every node and that administrators have `sudo` access. We use Slurm to schedule work, Munge for Slurm authentication, OpenMPI for parallel jobs, and scientific applications such as Quantum ESPRESSO.

The hostnames, addresses, account IDs, paths, partition name, and hardware figures below describe **our installation**. Before applying a command to a rebuilt or replacement node, we should check those values against the running systems. Commands intended for all nodes presume that hostname resolution and administrator SSH access already work and we run them from `quasi06`. We do not run installation commands against a production node without checking its current state and arranging an appropriate maintenance window.

## Table of Contents

- [Core Infrastructure](#core-infrastructure)
  - [1. Shared Folder Preparation](#1-shared-folder-preparation)
  - [2. SSH Configuration and User Management](#2-ssh-configuration-and-user-management)
    - [The User Creation Script](#the-user-creation-script)
  - [3. Standardized Bash Environment (`bashquasi`)](#3-standardized-bash-environment-bashquasi)
  - [4. Network File System (NFS) using `autofs`](#4-network-file-system-nfs-using-autofs)
    - [NFS Server Setup (`quasi06`)](#nfs-server-setup-quasi06)
    - [NFS Client Setup (`quasi07` to `quasi11`)](#nfs-client-setup-quasi07-to-quasi11)
  - [5. Network Information Service (NIS) Setup](#5-network-information-service-nis-setup)
    - [NIS Master Setup (`quasi06`)](#nis-master-setup-quasi06)
    - [NIS Client Setup (`quasi07` to `quasi11`)](#nis-client-setup-quasi07-to-quasi11)
- [Clustering Setup](#clustering-setup)
  - [1. System Preparation and Time Synchronization](#1-system-preparation-and-time-synchronization)
  - [2. Munge Authentication Setup](#2-munge-authentication-setup)
  - [3. Slurm Configuration (Shared Directory)](#3-slurm-configuration-shared-directory)
  - [4. Install and Start Slurm Services](#4-install-and-start-slurm-services)
  - [5. OpenMPI Configuration](#5-openmpi-configuration)
  - [6. Quantum ESPRESSO Deployment](#6-quantum-espresso-deployment)
  - [7. Standard Job Submission Workflow](#7-standard-job-submission-workflow)

## Core Infrastructure

### 1. Shared Folder Preparation

We use `/clusterfs` on `quasi06` for user home directories, shared Python environments, configuration, and administrative scripts. Compute nodes later mount this same directory through NFS. Files under `/clusterfs` therefore depend on the availability and performance of `quasi06` and the network; a directory made with `mkdir` alone does not provide redundancy or backups.

On `quasi06`, we create the directory and its administrative subdirectory if they do not exist:

```bash
sudo mkdir -p /clusterfs/skel
```

We verify the underlying filesystem and free space before adding users or installing software:

```bash
findmnt /clusterfs
df -h /clusterfs
```

If `/clusterfs` is a dedicated filesystem, we confirm it is mounted before writing data. We also back up its user data and site configuration separately; the compute nodes' NFS mounts are copies of the same storage view, not backups.

### 2. SSH Configuration and User Management

SSH provides administrator access to the nodes and, where our workflow requires it, authenticated connections between them. On each node (`quasi06` through `quasi11`), we install the server and client:

```bash
sudo apt update
sudo apt install openssh-server openssh-client
sudo systemctl enable --now ssh
```

We first check that the hostnames in the NFS section resolve correctly and that an administrator can log in to each node. SSH keys created for ordinary users are private credentials. We never publish their private halves, and we control access to the shared home directories that contain them.

#### The User Creation Script

After NFS and NIS are configured, we create user accounts on `quasi06` with `/clusterfs/skel/newuser.sh`. The script puts each account in `/clusterfs/staff`, `/clusterfs/students`, or `/clusterfs/visitors`, assigns the existing `users` group, links our shared Bash configuration, and generates an Ed25519 key pair. We run it **only on `quasi06`** with an interactive terminal. Its checks stop duplicate names or malformed usernames; we still inspect any partially created account if a later command fails.

Before using the script, we create `/clusterfs/skel/bashquasi` and `/clusterfs/skel/emacs`, confirm that `getent group users` succeeds, and finish the NIS master setup below. If we do not use a shared Emacs configuration, we remove the `.emacs` link and its prerequisite check from the script.

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "Add a new user"
read -r -p "1. Staff, 2. Student, or 3. Visitor? Enter 1, 2, or 3: " ans
case "$ans" in
    1) status=staff ;;
    2) status=students ;;
    3) status=visitors ;;
    *) echo "Invalid selection" >&2; exit 1 ;;
esac

read -r -p "Enter a username (for example, taro): " name
if [[ ! "$name" =~ ^[a-z_][a-z0-9_-]*$ ]]; then
    echo "Use a lowercase Linux username without spaces or shell symbols" >&2
    exit 1
fi
if getent passwd "$name" >/dev/null; then
    echo "The account $name already exists" >&2
    exit 1
fi
getent group users >/dev/null
for item in /clusterfs/skel/bashquasi /clusterfs/skel/emacs; do
    if [[ ! -f "$item" ]]; then
        echo "Missing prerequisite: $item" >&2
        exit 1
    fi
done

homedir="/clusterfs/$status/$name"
echo "Creating $name with home directory $homedir"
sudo mkdir -p "/clusterfs/$status"
sudo useradd -m -d "$homedir" -s /bin/bash -g users "$name"

# Set a unique initial password interactively. Never embed a default password.
sudo passwd "$name"

# This shared file is read by our .bashrc; keep the home directory private.
printf '%s\n' 'source /clusterfs/skel/bashquasi' | sudo tee "$homedir/.bashrc" >/dev/null
sudo ln -sfn "$homedir/.bashrc" "$homedir/.profile"
sudo ln -sfn /clusterfs/skel/emacs "$homedir/.emacs"
sudo touch "$homedir/.hushlogin"
sudo install -d -o "$name" -g users -m 700 "$homedir/.ssh"
sudo -u "$name" ssh-keygen -t ed25519 -f "$homedir/.ssh/id_ed25519" -q -N ''
sudo -u "$name" cp "$homedir/.ssh/id_ed25519.pub" "$homedir/.ssh/authorized_keys"
sudo chown "$name":users "$homedir/.bashrc" "$homedir/.hushlogin"
sudo chmod 700 "$homedir"
sudo chmod 600 "$homedir/.ssh/id_ed25519" "$homedir/.ssh/authorized_keys"
sudo chmod 644 "$homedir/.ssh/id_ed25519.pub"

# Rebuild NIS maps after creating the local account and setting its password.
(cd /var/yp && sudo make)
echo "Account $name created; verify it from a compute node."
```

The `authorized_keys` copy permits SSH authentication using this account's private key. We authorize only the access pattern our cluster needs. Because the key lives on shared NFS storage, administrators with access to that storage must protect it and review SSH server policy. If passwordless node access is not required for ordinary users, we omit the key generation and `authorized_keys` steps. We use a separate, documented process for key rotation or account removal.

After creation, we check `getent passwd <username>` on `quasi06` and on a compute node, check `id <username>`, and confirm that the home directory is mounted. We do not distribute plaintext passwords or leave a published common default in this document.

### 3. Standardized Bash Environment (`bashquasi`)

We manage aliases, Slurm shortcuts, Python activation, and interactive login displays in one shared file. The user creation script writes a small `.bashrc` that sources `/clusterfs/skel/bashquasi`; `.profile` then points to that `.bashrc`. This file returns immediately for non-interactive Bash shells, so its aliases and thread settings are not a reliable way to configure a batch script. We set job requirements explicitly in `#SBATCH` directives and relevant environment variables in the job script. Edits to this shared file affect every account that sources it, so we test changes with a fresh interactive shell.

We store the configuration at `/clusterfs/skel/bashquasi`.

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
# CAUTION: clqe removes *.save and other restart/output data; run it only in a reviewed QE working directory.
alias clqe='rm -Rf *~ *.out *.xml *.save *.bands *.gnu *.rap out* CRASH *.dos *__py* *.log'

# Check personal home directory usage and top 10 largest folders
myusage() {
    echo -e "\e[01;34mCalculating usage for $HOME...\e[0m"
    du -sh "$HOME" 2>/dev/null
    echo -e "\n\e[01;34mTop 10 largest subdirectories:\e[0m"
    du -hs "$HOME"/* 2>/dev/null | sort -hr | head -n 10
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
    local CFS_AVAIL=$(df -hP /clusterfs 2>/dev/null | awk 'NR==2 {print $4}')
    local CFS_TOTAL=$(df -hP /clusterfs 2>/dev/null | awk 'NR==2 {print $2}')
    echo -e "/clusterfs: \e[01;36m${CFS_AVAIL}\e[0m Available / \e[01;36m${CFS_TOTAL}\e[0m Total"
    
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
    echo -e "Use a trusted SSH tunnel or VS Code remote connection to reach the compute node."
    
    # IMPORTANT: --ntasks=1 ensures only ONE Jupyter server starts.
    # --cpus-per-task=$cores reserves the multi-core processing power for it.
    srun --partition=qdisk --nodes=1 --ntasks=1 --cpus-per-task=$cores --pty bash -c "
        source /clusterfs/opt/qupy/bin/activate
        # This hostname is reachable on the cluster network; use an SSH tunnel for external clients.
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
        USAGE=$(du -sh "$HOME" 2>/dev/null | awk '{print $1}')
        echo -e "Home Directory ($HOME): \e[01;36m$USAGE\e[0m"
        echo -e "(Type \e[01;32mmyusage\e[0m for a detailed breakdown)\n"
        
        echo -e "\e[01;33m=== Compute Resource Status ===\e[0m"
        # Use POSIX format (-P) for df to prevent line wrapping on long device names
        CFS_AVAIL=$(df -hP /clusterfs 2>/dev/null | awk 'NR==2 {print $4}')
        CFS_TOTAL=$(df -hP /clusterfs 2>/dev/null | awk 'NR==2 {print $2}')
        echo -e "/clusterfs: \e[01;36m${CFS_AVAIL}\e[0m Available / \e[01;36m${CFS_TOTAL}\e[0m Total"
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

The display uses `df` column 2 for total size and column 4 for available space. The SSH probes in `clust` report `down` if a node cannot be reached **or** if user key authentication fails, so we confirm ambiguous results with `sinfo` and an administrator SSH check. The `clqe` alias removes QE restart files (`*.save`); we use it only after inspecting the working directory and preserving data we need. For Jupyter, we keep access within our trusted SSH or VS Code connection and verify that the chosen port is free.

### 4. Network File System (NFS) using `autofs`

We export `/clusterfs` from `quasi06` and use `autofs` on the compute nodes to mount it when accessed. `autofs` mounts on demand; it does not make NFS storage independent of `quasi06`. In particular, losing the server or the internal network can interrupt running jobs and prevent access to user homes. We keep compute-node scratch on local disks for appropriate single-node jobs.

First, we keep `/etc/hosts` consistent across login and compute nodes. These addresses are specific to our installation; we verify them against each machine's actual interface before changing a live configuration:

```text
10.10.216.30    quasi06
10.10.240.17    quasi07
10.10.240.18    quasi08
10.10.240.19    quasi09
10.10.240.15    quasi10
10.10.240.16    quasi11
```

We check name resolution with `getent hosts quasi06` and an appropriate compute-node hostname from every node. We install the NFS server on `quasi06`, and NFS client utilities and `autofs` on the compute nodes:

```bash
# On quasi06
sudo apt update
sudo apt install nfs-kernel-server

# On each compute node
sudo apt update
sudo apt install nfs-common autofs
```

#### NFS Server Setup (`quasi06`)

We configure `/etc/exports` on `quasi06` for the internal networks that we intend to trust:

```text
/clusterfs    10.10.240.0/22(rw,sync,no_root_squash,no_subtree_check)
/clusterfs    10.10.216.0/21(rw,sync,no_root_squash,no_subtree_check)
```

The original note wrote the second network as `10.10.219.0/21`. With a `/21` mask (`255.255.248.0`), the network base is **`10.10.216.0/21`**, spanning `10.10.216.0` through `10.10.223.255`; it includes `quasi06` (`10.10.216.30`). The first rule spans `10.10.240.0` through `10.10.243.255`. We confirm that these *entire* ranges match the addresses we intend to authorize. If the intended clients are only `quasi07` through `quasi11`, we should narrow the export to those specific hosts or a smaller appropriate network.

`no_root_squash` lets root on an authorized client access the export with root privileges. Our administration may depend on that behavior, but it means that a compromised or mismanaged compute node can alter shared files. We restrict access at the network boundary, maintain control of compute-node root accounts, and review whether `root_squash` is workable for our installation. NFS with its default `sec=sys` does not itself encrypt traffic. See the [NFS exports manual](https://man7.org/linux/man-pages/man5/exports.5.html) for the precise behavior of these options.

After editing, we apply and inspect the effective exports:

```bash
sudo exportfs -ra
sudo exportfs -v
sudo systemctl status nfs-kernel-server
```

#### NFS Client Setup (`quasi07` to `quasi11`)

On each compute node, we configure a direct `autofs` map. We add this line to `/etc/auto.master` (or an equivalent file in `/etc/auto.master.d/`):

```text
/-    /etc/auto.mount
```

We create `/etc/auto.mount` with the following entry:

```text
/clusterfs    -fstype=nfs,rw    quasi06:/clusterfs
```

We restart the service and trigger the mount by accessing the directory:

```bash
sudo systemctl enable --now autofs
sudo systemctl restart autofs
ls /clusterfs
findmnt -T /clusterfs
```

`findmnt -T /clusterfs` should resolve to the NFS mount after access. We also test a read and a permitted write as an ordinary cluster user. We do not place separate local data under the compute nodes' `/clusterfs` mountpoint, because it will be hidden while NFS is mounted.

### 5. Network Information Service (NIS) Setup

We use NIS for our existing cluster account directory: we create local user accounts on `quasi06`, build NIS maps there, and look up the same numeric UIDs and GIDs on the compute nodes. NFS permissions depend on numeric IDs matching across nodes. NIS is a legacy protocol and does not provide modern cryptographic protection for account data; we limit it to the trusted internal network, check firewall exposure, and protect both the server and its maps. The NIS domain name below is **not** a DNS domain.

We install `nis` on all nodes, supplying the domain `quasi` if the package installer requests it. For systems where we use `nscd`, we also install it explicitly before restarting it:

```bash
sudo apt install nis nscd
```

#### NIS Master Setup (`quasi06`)

We configure `quasi06` as the NIS master. In `/etc/ypserv.securenets`, we remove or comment out any unrestricted entries and allow only the intended internal address ranges:

```text
# 0.0.0.0                0.0.0.0
# ::/0
255.255.248.0   10.10.216.0
255.255.252.0   10.10.240.0
```

The `10.10.216.0` entry is the network base for the `/21` described in the NFS section. We verify that the effective rules do not include a broad fallback line elsewhere in this file. NIS `securenets` is one restriction; it does not replace a firewall or secure authentication.

We put the NIS domain in `/etc/defaultdomain`:

```text
quasi
```

We initialize the NIS database **once** on a fresh master:

```bash
sudo /usr/lib/yp/ypinit -m
```

For an existing master, we inspect the configuration and maps rather than reinitializing them. After creating a local account or changing data exported in NIS maps, we rebuild the maps:

```bash
sudo systemctl enable --now rpcbind ypserv
cd /var/yp
sudo make
```

The exact maps built depend on `/var/yp/Makefile`; we inspect that file if an expected account or host entry is absent. Hostname resolution in this guide uses `/etc/hosts` on each node, so rebuilding NIS host maps does **not** replace updating those local files.

#### NIS Client Setup (`quasi07` to `quasi11`)

On each compute node, we add the master and domain to `/etc/yp.conf`:

```text
domain quasi server quasi06
```

We use local files first in `/etc/nsswitch.conf`, followed by systemd and NIS where supported by the installed Debian packages:

```text
passwd:         files systemd nis
group:          files systemd nis
shadow:         files nis
```

We also set `/etc/defaultdomain` to `quasi`:

```text
quasi
```

After making the change, we restart the installed services; we do not assume `nscd` is present unless we installed it:

```bash
sudo systemctl enable --now rpcbind ypbind
sudo systemctl restart rpcbind ypbind nscd
```

We verify on a compute node with `domainname`, `ypwhich`, `ypcat passwd.byname`, `getent passwd <username>`, and `id <username>`. We restrict access to map output because account information can be sensitive. If `getent` fails while `ypcat` succeeds, we examine `nsswitch.conf` and the installed NSS NIS module. We do not create duplicate ordinary users locally on compute nodes.

---

## Clustering Setup

### 1. System Preparation and Time Synchronization

All nodes need working name resolution, compatible packages, a synchronized clock, and consistent service-account UIDs and GIDs. We run the following loop from `quasi06` after verifying administrator SSH and `sudo` on each node. `chrony` uses its configured time sources; we inspect `/etc/chrony/chrony.conf` and `chronyc tracking` rather than assuming installation alone synchronizes the nodes.

**Install prerequisites and enable chrony:**

```bash
for node in quasi06 quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t "$node" 'sudo apt update && sudo apt install chrony cgroup-tools curl build-essential -y && sudo systemctl enable --now chrony'
done
```

We check time sources and offset on every node with `chronyc sources -v` and `chronyc tracking`. Munge rejects credentials when clocks differ substantially.

**Check service accounts before installing Munge and Slurm:**

```bash
for node in quasi06 quasi07 quasi08 quasi09 quasi10 quasi11; do
    echo "=== $node ==="
    ssh "$node" 'getent passwd munge; getent group munge; getent passwd slurm; getent group slurm'
done
```

In an **earlier proposal**, we used UID/GID `990` for `munge` and `991` for `slurm`. As recorded on September 4, 2026, our actual systems use `1111` for `munge` and `1121` for `slurm`. We do **not** run both sets of account-creation commands. On a replacement node, we match its service IDs to the running cluster before installing packages. If a package already created the accounts with different IDs, we investigate ownership and package settings before changing UIDs or GIDs. If accounts truly are absent and we have confirmed the cluster uses the recorded IDs, we create them as follows on that node:

```bash
sudo groupadd -g 1111 munge
sudo useradd -r -u 1111 -g munge -d /nonexistent -s /usr/sbin/nologin munge
sudo groupadd -g 1121 slurm
sudo useradd -r -u 1121 -g slurm -d /nonexistent -s /usr/sbin/nologin slurm
```

These are service accounts, not interactive user accounts. Older nodes may still show the historical home paths or shells; we inspect their effective IDs and permissions rather than changing them merely to match the example above.

**Prepare local scratch on each compute node:**

```bash
for node in quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t "$node" 'sudo mkdir -p /scratch && sudo chown root:root /scratch && sudo chmod 0755 /scratch'
done
```

We keep the top level of `/scratch` writable only by root because Slurm's root-run prolog creates predictable per-job names there. Making the top level group-writable would let users pre-create another job's directory. Individual job directories are owned by their respective users and have mode `0700`. If we also want a general user-writable scratch area, we create a separate sticky directory with its own policy. We check `ls -ld /scratch` and free space on **each** node. We avoid placing permanent results only on this local disk.

Our earlier configuration used `root:users` with mode `1775` on `/scratch`. Before applying the revised permissions to a running node, we inspect existing contents and confirm that no unrelated workflow depends on creating entries directly under `/scratch`.

### 2. Munge Authentication Setup

Munge signs credentials so that Slurm components can authenticate messages across nodes. All nodes must have the **same secret key**, compatible `munge` IDs, and clocks that agree. We install the package everywhere:

```bash
for node in quasi06 quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t "$node" 'sudo apt install munge -y'
done
```

On a **new** cluster, we generate a key once on `quasi06` with `sudo /usr/sbin/mungekey` if the package did not create one. On an existing cluster, we retain the working key; generating a different one would break authentication until every node receives the replacement. We inspect ownership and mode before distribution:

```bash
sudo ls -l /etc/munge/munge.key
```

To copy the key using an administrator account whose remote SSH login works, we stage it temporarily in a private local file and install it with the required ownership on each compute node:

```bash
key_copy=$(mktemp)
sudo cat /etc/munge/munge.key > "$key_copy"
chmod 600 "$key_copy"
for node in quasi07 quasi08 quasi09 quasi10 quasi11; do
    remote_key=$(ssh "$node" mktemp)
    [[ "$remote_key" =~ ^/tmp/tmp\.[A-Za-z0-9]+$ ]] || exit 1
    scp "$key_copy" "$node:$remote_key"
    ssh -t "$node" "sudo install -o munge -g munge -m 0400 '$remote_key' /etc/munge/munge.key && rm -f '$remote_key' && sudo systemctl restart munge"
done
rm -f "$key_copy"
sudo systemctl restart munge
```

We protect the staging files, remove them promptly, and do not add the key to Git. We verify a local encoding and a cross-node check, for example `munge -n | unmunge` on `quasi06` and `munge -n | ssh quasi07 unmunge`, then inspect `systemctl status munge` and `journalctl -u munge` if authentication fails. If `sudo` or SSH interrupts distribution, we remove any remaining per-node temporary key files after resolving the failure.

### 3. Slurm Configuration (Shared Directory)

We keep the site configuration under `/clusterfs/config/slurm` so that we can maintain it on `quasi06` and make it available on every compute node. This introduces a dependency: NFS must be available before compute-node Slurm services start, and a failed mount can prevent prolog execution. We allow only administrators to edit these files because the daemons and root-run prolog/epilog consume them. We test changes on a maintenance schedule and keep versioned backups.

**Create the base configuration directory:**

```bash
sudo install -d -o root -g root -m 0755 /clusterfs/config/slurm
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
We keep the example node values only if they match the actual hosts. `CPUs=24` represents 12 physical cores with two hardware threads each; `CR_ONE_TASK_PER_CORE` changes the default task placement, while `DefMemPerCPU=5200` requests memory per allocated CPU. We check how Slurm counts memory and cores on our installed version before accepting these values. We leave some memory for the operating system instead of assigning all physical RAM to jobs. We install `slurmd` (Section 4) before running `slurmd -C` to inspect each node, and compare its output with the configuration:
```bash
for node in quasi07 quasi08 quasi09 quasi10 quasi11; do
    echo "=== $node ==="
    ssh "$node" '/usr/sbin/slurmd -C'
done
```

The first-run `State=UNKNOWN` is resolved when a healthy `slurmd` registers. The `qdisk` partition permits jobs on five nodes; it does not mean that `/scratch` is a shared disk. We check the cgroup mode used by our Debian release and Slurm version before applying resource limits.

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

We verify that the installed Slurm supports the system's cgroup mode and that this configuration loads. Cgroup settings enforce placement and memory limits; a wrong setting can prevent jobs from starting.

**3. `job_submit.lua`:**
Create `/clusterfs/config/slurm/job_submit.lua` to set default log names for batch submissions while leaving user-specified paths intact. This file is used on the controller (`quasi06`).
```bash
sudo nano /clusterfs/config/slurm/job_submit.lua
```
Write these contents and save:
```lua
function slurm_job_submit(job_desc, part_list, submit_uid)
    if job_desc.script ~= nil and job_desc.script ~= "" then
        if job_desc.std_out == nil or job_desc.std_out == "" then
            job_desc.std_out = "slurm-%j.out"
        end
        if job_desc.std_err == nil or job_desc.std_err == "" then
            job_desc.std_err = "slurm-%j.log"
        end
    end
    return slurm.SUCCESS
end

function slurm_job_modify(job_desc, job_rec, part_list, modify_uid)
    return slurm.SUCCESS
end
```

Slurm's Lua job descriptor uses `std_out` and `std_err`, not `standard_output` and `standard_error`. We check the interface against our installed version and submit a short test job to confirm the resulting file names. See [SchedMD's Lua job submission documentation](https://slurm.schedmd.com/job_submit_plugins.html) and [the field names in its source](https://github.com/SchedMD/slurm/blob/master/src/plugins/job_submit/lua/job_submit_lua.c). We retain the user's `--output` or `--error` setting when it is supplied.

**4. Administrative Scripts:**
We create these scripts on `quasi06` and make them executable. `Prolog` and `Epilog` run on **each allocated compute node**, normally as root. `TaskProlog` runs before a task or job step and communicates environment changes by printing `export` statements. It does not by itself guarantee that the batch script's shell has those variables, so we also export them explicitly in our job template below. The prolog and epilog use `SLURM_JOB_WORK_DIR`, which Slurm supplies, rather than parsing `scontrol` output. See [Slurm's prolog and epilog guide](https://slurm.schedmd.com/prolog_epilog.html).

`/clusterfs/config/slurm/prolog.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Slurm runs this on the allocated compute node before its first job step.
# /scratch itself is root-owned and inaccessible for user-created entries.
job_id=${SLURM_JOB_ID:?missing Slurm job ID}
[[ "$job_id" =~ ^[0-9]+$ ]] || exit 1
job_dir="/scratch/slurm-$job_id"
if [[ -e "$job_dir" || -L "$job_dir" ]]; then
    echo "Unexpected pre-existing scratch directory: $job_dir" >&2
    exit 1
fi
install -d -o "${SLURM_JOB_USER:?}" -g "${SLURM_JOB_GID:?}" -m 0700 "$job_dir"
```

`/clusterfs/config/slurm/epilog.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

job_id=${SLURM_JOB_ID:?missing Slurm job ID}
[[ "$job_id" =~ ^[0-9]+$ ]] || exit 1
job_dir="/scratch/slurm-$job_id"
workdir=${SLURM_JOB_WORK_DIR:?missing Slurm working directory}
job_user=${SLURM_JOB_USER:?missing Slurm job user}

# Every node has its own local scratch. Separate destinations avoid collisions.
# An allocated node without any job step may never have run its prolog.
if [[ ! -e "$job_dir" ]]; then
    exit 0
fi
if [[ ! -d "$job_dir" || ! -d "$workdir" ]]; then
    echo "Scratch or submission directory is unusable for job $job_id" >&2
    exit 1
fi
dest="$workdir/out-$job_id/$(hostname -s)"
runuser -u "$job_user" -- mkdir -p -- "$dest"

# If rsync fails, set -e stops here; preserve the scratch directory.
runuser -u "$job_user" -- rsync -a -- "$job_dir/" "$dest/"
rm -rf -- "$job_dir"
```

We install `rsync` on every compute node (`sudo apt install rsync`). A failed epilog is reported to Slurm and can drain the node, so we investigate the log, preserve the local data, and restore service only after the transfer issue is resolved. The copy runs after job termination and can delay the node becoming free; for very large results we arrange explicit checkpoints and copies in the batch script. The epilog is a safety net, not a substitute for backups. A node failure or power loss can still destroy its local scratch before the epilog runs.

`/clusterfs/config/slurm/taskprolog.sh`:

```bash
#!/usr/bin/env bash
# Slurm interprets these lines to set variables for an individual task.
job_id=${SLURM_JOB_ID:?missing Slurm job ID}
[[ "$job_id" =~ ^[0-9]+$ ]] || exit 1
printf 'export OMP_NUM_THREADS=%s\n' "${SLURM_CPUS_PER_TASK:-1}"
printf 'export SLURM_TMPDIR=/scratch/slurm-%s/\n' "$job_id"
printf 'export LOCAL_SCRATCH=/scratch/slurm-%s/\n' "$job_id"
printf 'export ESPRESSO_TMPDIR=/scratch/slurm-%s/\n' "$job_id"
```

On a **multi-node** job, `/scratch/slurm-$job_id` names a different physical directory on each node. We must not assume these directories form a shared filesystem. Quantum ESPRESSO restart and distributed data can require shared access across MPI ranks and across steps; its [parallel I/O guidance](https://www.quantum-espresso.org/Doc/user_guide/node21.html) explicitly warns about local disks for such workflows. Our single-node example below uses one node throughout all QE stages.

Apply executable permissions:

```bash
sudo chown root:root /clusterfs/config/slurm/{slurm.conf,cgroup.conf,job_submit.lua,prolog.sh,epilog.sh,taskprolog.sh}
sudo chmod 0644 /clusterfs/config/slurm/{slurm.conf,cgroup.conf,job_submit.lua}
sudo chmod 0755 /clusterfs/config/slurm/{prolog.sh,epilog.sh,taskprolog.sh}
```

### 4. Install and Start Slurm Services

We install controller and client packages on `quasi06`, and the node daemon on the compute nodes. We confirm that the Debian packages on all six nodes provide compatible Slurm versions. The shared configuration and NFS mount must be readable before starting a daemon.

**Login Node (`quasi06`):**

```bash
sudo apt install slurmctld slurm-client -y
sudo install -d -o slurm -g slurm -m 0750 /var/spool/slurmctld
sudo ln -sf /clusterfs/config/slurm/slurm.conf /etc/slurm/slurm.conf
sudo ln -sf /clusterfs/config/slurm/cgroup.conf /etc/slurm/cgroup.conf
sudo ln -sf /clusterfs/config/slurm/job_submit.lua /etc/slurm/job_submit.lua
sudo systemctl enable --now slurmctld
```

**Compute Nodes (`quasi07` to `quasi11`):**

```bash
for node in quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t "$node" 'sudo apt install slurmd slurm-client rsync -y'
    ssh -t "$node" 'sudo install -d -o root -g root -m 0755 /var/spool/slurmd'
    ssh -t "$node" 'sudo ln -sf /clusterfs/config/slurm/slurm.conf /etc/slurm/slurm.conf'
    ssh -t "$node" 'sudo ln -sf /clusterfs/config/slurm/cgroup.conf /etc/slurm/cgroup.conf'
    ssh -t "$node" 'sudo systemctl enable --now slurmd'
done
```

We check `systemctl status slurmctld` on `quasi06` and `systemctl status slurmd` on each compute node. From `quasi06`, `sinfo -N -l` and `scontrol show nodes` should show the expected hosts and resources. We submit a small test (`srun --partition=qdisk --nodes=1 --ntasks=1 hostname`) and confirm that scratch creation, environment, copy-back, and cleanup work before accepting user workloads. A node in `DOWN` or `DRAIN` needs its daemon and journal inspected (`journalctl -u slurmd`), along with the controller log; we resolve the cause before returning it to service.

### 5. OpenMPI Configuration

We install the same compatible OpenMPI runtime on all nodes and the development files where applications are compiled:

```bash
for node in quasi06 quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t "$node" 'sudo apt install openmpi-bin libopenmpi-dev -y'
done
```

Within a Slurm allocation, OpenMPI's `mpirun` can use Slurm's assigned nodes and tasks without a hand-written hostfile. We check the installed OpenMPI version, `mpirun --version`, and the allocation reported by Slurm before tuning process placement. We run a short MPI application on one node, then across nodes if we plan to permit such jobs. Slurm `srun` direct launch requires compatible PMIx support, which we can inspect with `srun --mpi=list`; `mpirun` is the default shown in our job template. See [OpenMPI's Slurm launch guide](https://docs.open-mpi.org/en/main/launching-apps/slurm.html).

Our earlier setup appended `hwloc_base_use_hwthreads_as_cpus = true` and `rmaps_base_mapping_policy = core:OVERSUBSCRIBE` to the global OpenMPI configuration. We do **not** add blanket oversubscription while rebuilding nodes: allowing more ranks than intended can conflict with the CPU allocation and degrade calculations. If those settings already exist, we record the installed OpenMPI version, inspect `/etc/openmpi/openmpi-mca-params.conf`, test a representative allocated job, and then decide whether version-specific placement settings are needed. We avoid appending duplicate lines on each maintenance run.

### 6. Quantum ESPRESSO Deployment

We install runtime libraries on each compute node and development packages on the build node. Binary compatibility matters: executables built against one MPI or numerical-library ABI must find matching libraries on all nodes. Before changing BLAS alternatives, we inspect the active implementation and check whether other applications on that node depend on it.

```bash
for node in quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t $node 'sudo apt install libblas3 liblapack3 libscalapack-mpi-dev libfftw3-double3 libopenblas0 -y'
    ssh -t $node 'sudo update-alternatives --set libblas.so.3-x86_64-linux-gnu /usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3'
    ssh -t $node 'sudo update-alternatives --set liblapack.so.3-x86_64-linux-gnu /usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3'
done
```

On `quasi06`, we install the compilers and development dependencies used by our build, then inspect the `./configure` summary to verify that MPI and the intended libraries were detected:

```bash
sudo apt install gfortran make openmpi-bin libopenmpi-dev libblas-dev liblapack-dev libfftw3-dev libscalapack-mpi-dev -y
```

We keep the build toolchain and the compute-node runtime compatible. For the first installation of Quantum ESPRESSO on `quasi06`, we can create `/clusterfs/opt/QE` there:
```bash
sudo mkdir -p /clusterfs/opt/QE
```
We keep an example maintenance script under `/clusterfs/skel/`. It downloads source code, compiles on `quasi06`, and replaces shared and local binaries. We schedule this disruptive operation outside active jobs and keep a known working version for rollback. Before using a release archive, we verify its source, version, and checksum against a trusted release reference. If `/clusterfs/skel/` does not exist yet, we create it:
```bash
sudo mkdir -p /clusterfs/skel
cd /clusterfs/skel/
```
Create the `/clusterfs/skel/update_qe.sh` script below. We review `QE_VERSION`, `QE_URL`, `TAR_FILE`, `BUILD_DIR`, `SHARED_BIN_DIR`, `LOCAL_BIN_DIR`, and `NODES` before use. This is a single-version example: it copies into live `bin` directories, so it needs a maintenance window and a separate rollback copy. `make -j8` also consumes eight cores on the login node; we run it only when that load is acceptable.

```bash
#!/bin/bash
# Script to automate downloading, compiling, and distributing Quantum ESPRESSO

# Stop on command failures and undefined variables.
set -euo pipefail

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

# Supply a trusted checksum independently of the archive download.
: "${QE_SHA256:?Set the verified QE source archive SHA-256 digest}"
printf '%s  %s\n' "$QE_SHA256" "$TAR_FILE" | sha256sum -c -
echo "Extracting archive..."
tar -xzf "$TAR_FILE"
cd "q-e-qe-${QE_VERSION}"

echo -e "\e[01;34m[3/5] Configuring and compiling source code...\e[0m"
# Review configure output: verify MPI, compilers and numerical libraries.
./configure

# Limit the build load on the login node; adjust only for a maintenance window.
make all -j8

echo -e "\e[01;34m[4/5] Deploying binaries to shared storage (/clusterfs)...\e[0m"
sudo mkdir -p "$SHARED_BIN_DIR"
# The compiled binaries are in bin/. Keep a backup of the old installation.
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
Before running it from `/clusterfs/skel/` on `quasi06`, we obtain and independently verify the expected SHA-256 digest of the archive, then supply it as `QE_SHA256`. The script stops if the value is absent or the checksum fails. We also back up the existing `/clusterfs/opt/QE/bin` and `/opt/QE/bin` trees; the script does not keep them. We verify that downloads succeeded, that the `configure` summary enabled the expected MPI build, and that no user jobs are using the binaries. After these checks:

```bash
QE_SHA256='<verified-sha256-digest>' bash update_qe.sh
```

The example deletes its build tree only after all commands succeed. If distribution fails partway through, some nodes may already have the new binaries; we inspect each copy and restore the saved version or complete the update before accepting new jobs. After installation, we test `command -v pw.x`, the binary's shared libraries with `ldd`, its version, and a small QE calculation under Slurm. A copied executable alone does not prove that all runtime dependencies are present on every node.
If a tested Quantum ESPRESSO tree is already present at `/clusterfs/opt/QE` on `quasi06`, we can distribute that same tree to local `/opt/QE` on the compute nodes. We again schedule a maintenance window and verify that each node can read the source mount:
```bash
for node in quasi07 quasi08 quasi09 quasi10 quasi11; do
    ssh -t "$node" 'sudo mkdir -p /opt/QE && sudo chown "$USER":"$USER" /opt/QE'
    rsync -av /clusterfs/opt/QE/ "$node:/opt/QE/"
    ssh -t "$node" 'sudo chown -R root:users /opt/QE'
done
```

The shared `/clusterfs/opt/QE/bin` remains a possible fallback in `PATH`, while `/opt/QE/bin` is the preferred local copy in our `bashquasi` file. We check `command -v pw.x` **inside a submitted batch job**, since batch shells do not necessarily load `bashquasi`. We record the version and library dependencies for both copies to prevent a mixed installation.

### 7. Standard Job Submission Workflow

We submit a single-node, eight-rank QE calculation as a batch job. Slurm creates `/scratch/slurm-$SLURM_JOB_ID` with the prolog, and the batch script exports the scratch path explicitly. Quantum ESPRESSO uses `ESPRESSO_TMPDIR` as the default `outdir` when an input file does not set `outdir`; an explicit `outdir` in an input file can direct data elsewhere. We check that `scf.in`, `nscfbands.in`, and `bands.in` use the **same `prefix` and data directory** where they need to share QE data. We keep pseudopotentials in an accessible, stable location. The [QE parallel I/O guide](https://www.quantum-espresso.org/Doc/user_guide/node21.html) explains the role of `outdir/prefix.save` and the limitations of local scratch.

**Standard `run.sh` template:**

```bash
#!/usr/bin/env bash
#SBATCH --job-name=Silicon_Bands
#SBATCH --partition=qdisk
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --cpus-per-task=1
#SBATCH --time=24:00:00

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"
export OPENBLAS_NUM_THREADS=1
export SLURM_TMPDIR="/scratch/slurm-${SLURM_JOB_ID:?}"
export LOCAL_SCRATCH="$SLURM_TMPDIR"
export ESPRESSO_TMPDIR="$SLURM_TMPDIR"
[[ -d "$SLURM_TMPDIR" ]] || { echo "Missing local scratch: $SLURM_TMPDIR" >&2; exit 1; }

# Batch shells need an explicit executable path or environment setup.
QE_BIN=/opt/QE/bin
[[ -x "$QE_BIN/pw.x" && -x "$QE_BIN/bands.x" ]] || {
    echo "Quantum ESPRESSO binaries are unavailable in $QE_BIN" >&2
    exit 1
}

echo "Job $SLURM_JOB_ID started on $(hostname)"
echo "QE scratch directory: $ESPRESSO_TMPDIR"

echo "Starting SCF..."
mpirun -np "$SLURM_NTASKS" "$QE_BIN/pw.x" -in scf.in > scf.out

echo "Starting NSCF for bands..."
mpirun -np "$SLURM_NTASKS" "$QE_BIN/pw.x" -in nscfbands.in > nscfbands.out

echo "Processing bands..."
mpirun -np "$SLURM_NTASKS" "$QE_BIN/bands.x" -in bands.in > bands.out

echo "Quantum ESPRESSO workflow finished."
```

We run `sbatch run.sh` from the directory holding the input files. The redirected `*.out` files and Slurm's stdout/stderr stay in the submission directory. The calculation's files in local scratch are copied after the job to `out-<jobid>/<compute-hostname>/`, then removed from the compute node **only if the copy succeeds**. We inspect the output and the copied directory before deleting any source inputs or expecting to restart the calculation later. A failed QE step stops the batch script because of `set -e`; the epilog still attempts copy-back. If the job needs a restart after node failure or runs across multiple nodes, we plan shared storage or deliberate checkpoint transfers rather than relying on the local scratch directory.

We use `squeue -u "$USER"`, `scontrol show job <jobid>`, and `sinfo -N -l` to inspect job and node states. We review the Slurm log and compute-node journal if a job fails before it starts, and we check both the submission directory and the compute-node scratch area if copy-back fails.
