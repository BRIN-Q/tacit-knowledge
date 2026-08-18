# Thermoelectric Properties of Monolayer MoS₂ with Quantum ESPRESSO and BoltzTraP2

## 1. Overview

This tutorial gives a typical workflow for calculating the electronic structure and electronic thermoelectric properties of **monolayer 1H-MoS₂** using Quantum ESPRESSO, BoltzTraP2, NumPy, and Matplotlib.

For a simple file management, we will work with all user-created input files, plotting scripts, and pseudopotentials in a single directory:

```text
mos2/
├── mos2.scf.in
├── mos2.nscfbands.in
├── mos2.bands.in
├── mos2.nscf.in
├── mos2.dos.in
├── plot_band_dos.py
├── plot_thermoelectric.py
├── Mo.pbe-spn-kjpaw_psl.1.0.0.UPF
└── S.pbe-n-kjpaw_psl.1.0.0.UPF
```

Quantum ESPRESSO scratch data are stored in:

```text
./out
```

Therefore all QE inputs use:

```text
pseudo_dir = './'
outdir     = './out'
```

The same dense file `mos2.nscf.in` is used for both DOS post-processing and BoltzTraP2.

The workflow is:

```text
SCF
 |
 +------------------------------+
 |                              |
 v                              v
Gamma-M-K-Gamma bands      dense uniform NSCF
 |                              |
 v                              +----------------+
bands.x                         |                |
 |                              v                v
band structure                 dos.x       QE XML in ./out
 |                              |                |
 +---------------+--------------+                |
                 |                               v
                 v                          BoltzTraP2
          band + DOS plot                        |
                                                 v
                                            interpolate
                                                 |
                                                 v
                                             integrate
                                                 |
                                                 v
                                           mos2.condtens
                                                 |
                                                 v
                                      thermoelectric plots
```

Monolayer 1H-MoS₂ is expected to have a **direct gap at K**, but this should be verified from the actual calculated band structure.

---

# 2. Brief transport theory

BoltzTraP2 interpolates the DFT eigenvalues

$$
E_{n\mathbf{k}}
$$

and obtains the band velocities from

$$
\mathbf{v}_{n\mathbf{k}}
=
\frac{1}{\hbar}
\nabla_{\mathbf{k}}E_{n\mathbf{k}}.
$$

This is why a dense, uniform k mesh is needed for transport.

A transport distribution tensor can be written schematically as

$$
\Xi_{\alpha\beta}(E)
=
\frac{1}{V}
\sum_{n\mathbf{k}}
v_{n\mathbf{k},\alpha}
v_{n\mathbf{k},\beta}
\tau_{n\mathbf{k}}
\delta(E-E_{n\mathbf{k}}).
$$

The transport moments are

$$
L_{\alpha\beta}^{(m)}
=
\int
(E-\mu)^m
\Xi_{\alpha\beta}(E)
\left(
-\frac{\partial f}{\partial E}
\right)dE.
$$

The electrical conductivity is

$$
\boldsymbol{\sigma}=e^2\mathbf{L}^{(0)}.
$$

The Seebeck tensor is

$$
\mathbf{S}
=
-\frac{1}{eT}
\left(\mathbf{L}^{(0)}\right)^{-1}
\mathbf{L}^{(1)}.
$$

The electronic thermal conductivity at zero current is

$$
\boldsymbol{\kappa}_e
=
\frac{1}{T}
\left[
\mathbf{L}^{(2)}
-
\mathbf{L}^{(1)}
\left(\mathbf{L}^{(0)}\right)^{-1}
\mathbf{L}^{(1)}
\right].
$$

Under the constant relaxation-time approximation, BoltzTraP2 directly provides quantities such as

$$
\frac{\sigma}{\tau}
$$

and

$$
\frac{\kappa_e}{\tau}.
$$

The Seebeck coefficient does not explicitly depend on a constant $\tau$.

The power factor is

$$
PF=S^2\sigma,
$$

so

$$
\frac{PF}{\tau}
=
S^2\frac{\sigma}{\tau}.
$$

A complete figure of merit requires

$$
ZT=
\frac{S^2\sigma T}{\kappa_e+\kappa_l},
$$

so a physical $ZT$ also requires a relaxation time and lattice thermal conductivity.

---

# 3. Install Quantum ESPRESSO

For Ubuntu or Debian:

```bash
sudo apt update

sudo apt install -y \
    build-essential \
    gfortran \
    gcc \
    g++ \
    make \
    cmake \
    openmpi-bin \
    libopenmpi-dev \
    libfftw3-dev \
    libblas-dev \
    liblapack-dev \
    wget \
    git \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev
```

Check:

```bash
mpirun --version
mpif90 --version
gfortran --version
```

For an example source build, assuming `~/software/qe-7.5.0`:

```bash
cd ~/software/qe-7.5.0

mkdir -p build
cd build

../configure MPIF90=mpif90

make -j2 all
```

Add the executables to `PATH`:

```bash
echo 'export PATH=$HOME/software/qe-7.5.0/build/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

Check:

```bash
which pw.x
which bands.x
which dos.x
```

Use two MPI processes and one OpenMP thread per process:

```bash
export OMP_NUM_THREADS=1
```

---

# 4. Install BoltzTraP2 and plotting packages

Create a virtual environment:

```bash
python3 -m venv ~/venvs/boltztrap2
```

Activate it:

```bash
source ~/venvs/boltztrap2/bin/activate
```

Install:

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install BoltzTraP2 numpy matplotlib
```

Optional:

```bash
python -m pip install pyfftw
```

Check:

```bash
btp2 -V
btp2 -h
```

Use two workers where applicable:

```bash
btp2 -n 2 ...
```

---

# 5. Create the working directory

```bash
mkdir -p ~/calculations/mos2
cd ~/calculations/mos2

mkdir -p out figures
```

All commands below are assumed to be run from this `mos2/` directory.

---

# 6. Download the pseudopotentials

Download the UPF files directly into the same directory:

```bash
wget https://pseudopotentials.quantum-espresso.org/upf_files/Mo.pbe-spn-kjpaw_psl.1.0.0.UPF

wget https://pseudopotentials.quantum-espresso.org/upf_files/S.pbe-n-kjpaw_psl.1.0.0.UPF
```

Check:

```bash
ls -lh *.UPF
```

For research calculations, the pseudopotential choice and cutoffs should be tested for convergence.

---

# 7. Monolayer structure

Use a primitive 1H-MoS₂ cell with:

$$
a=3.160\ {\rm \AA},
\qquad
L_z=20.0\ {\rm \AA}.
$$

The fractional coordinates are:

```text
Mo  0.0000000000  0.0000000000  0.5000000000
S   0.3333333333  0.6666666667  0.5782500000
S   0.3333333333  0.6666666667  0.4217500000
```

The large $L_z$ supplies vacuum between periodic images.

For quantitative work, relax the structure or use a well-defined reference geometry.

---

# 8. SCF calculation

The file is:

```text
mos2.scf.in
```

Its key settings are:

```text
calculation = 'scf'
pseudo_dir  = './'
outdir      = './out'
```

and:

```text
K_POINTS automatic
12 12 1 0 0 0
```

Run:

```bash
mpirun -np 2 pw.x \
    -in mos2.scf.in \
    > mos2.scf.out
```

Check:

```bash
tail -n 20 mos2.scf.out

grep -i "JOB DONE" mos2.scf.out

grep -i "convergence has been achieved" mos2.scf.out

grep -i "number of electrons" mos2.scf.out
```

For the supplied pseudopotentials, the monolayer normally has 26 valence electrons. In a non-spin-polarized calculation:

$$
N_{\rm occupied}
=
\frac{26}{2}
=
13.
$$

This is the value used by `plot_band_dos.py` for a simple band-edge check.

---

# 9. Electronic band structure

The band-path input is:

```text
mos2.nscfbands.in
```

with:

$$
\Gamma\rightarrow M\rightarrow K\rightarrow\Gamma.
$$

The points are:

```text
Gamma = (0, 0, 0)
M     = (1/2, 0, 0)
K     = (1/3, 1/3, 0)
Gamma = (0, 0, 0)
```

Run:

```bash
mpirun -np 2 pw.x \
    -in mos2.nscfbands.in \
    > mos2.nscfbands.out
```

Then process the result with:

```text
mos2.bands.in
```

using:

```bash
mpirun -np 2 bands.x \
    -in mos2.bands.in \
    > mos2.bands.out
```

The plotting file should be:

```text
mos2.bands.dat.gnu
```

Check:

```bash
ls -lh mos2.bands.dat*
```

This high-symmetry calculation is for visualization and direct-gap inspection. It is not the transport k mesh.

---

# 10. Dense NSCF calculation for both DOS and BoltzTraP2

The dense file is:

```text
mos2.nscf.in
```

with:

```text
K_POINTS automatic
24 24 1 0 0 0
```

Run:

```bash
mpirun -np 2 pw.x \
    -in mos2.nscf.in \
    > mos2.nscf.out
```

This single NSCF result is then used by both `dos.x` and BoltzTraP2.

For transport convergence, compare meshes such as:

```text
18 x 18 x 1
24 x 24 x 1
30 x 30 x 1
36 x 36 x 1
```

The relevant convergence targets are the transport coefficients themselves.

---

# 11. DOS calculation

The DOS post-processing input is:

```text
mos2.dos.in
```

Run:

```bash
mpirun -np 2 dos.x \
    -in mos2.dos.in \
    > mos2.dos.out
```

The DOS is written to:

```text
mos2.dos
```

Check:

```bash
head mos2.dos
tail mos2.dos
```

The supplied DOS settings use Gaussian broadening:

```text
bz_sum  = 'smearing'
ngauss  = 0
degauss = 0.005
```

with `degauss` in Ry.

---

# 12. Find the Fermi or reference energy

The band and DOS plots are shifted so that:

$$
E_F=0.
$$

Search the QE outputs:

```bash
grep -Ei "fermi|highest occupied|lowest unoccupied" \
    mos2.scf.out \
    mos2.nscfbands.out \
    mos2.nscf.out
```

If QE prints:

```text
the Fermi energy is    X.XXXX ev
```

use that value.

For a semiconductor with:

```text
occupations = 'fixed'
```

a unique metallic Fermi energy inside the gap is not required. A convenient intrinsic reference is the middle of the gap:

$$
E_F^{\rm ref}
=
\frac{E_{\rm VBM}+E_{\rm CBM}}{2}.
$$

For example, if:

$$
E_{\rm VBM}=5.20\ {\rm eV},
\qquad
E_{\rm CBM}=6.90\ {\rm eV},
$$

then:

$$
E_F^{\rm ref}=6.05\ {\rm eV}.
$$

The number above is only an example.

Insert your own value into both Python scripts:

```python
FERMI_ENERGY_EV = 6.05
```

Using the same reference allows the electronic-structure and transport plots to share the same energy zero.

---

# 13. Plot band structure and DOS in adjacent panels

Use:

```text
plot_band_dos.py
```

The key settings are:

```python
BAND_FILE = Path("mos2.bands.dat.gnu")
DOS_FILE = Path("mos2.dos")

FERMI_ENERGY_EV = 0.0

N_OCCUPIED_BANDS = 13

HIGH_SYMMETRY_INDICES = [0, 40, 80, -1]
HIGH_SYMMETRY_LABELS = [r"$\Gamma$", "M", "K", r"$\Gamma$"]
```

Replace `FERMI_ENERGY_EV` with the value from your calculation.

Run:

```bash
source ~/venvs/boltztrap2/bin/activate

python plot_band_dos.py
```

The outputs are:

```text
figures/mos2_band_dos.png
figures/mos2_band_dos.pdf
```

The figure has two adjacent panels that share the energy axis:

```text
+--------------------------------+------------------+
| Electronic band structure      | DOS              |
| Gamma -> M -> K -> Gamma       |                  |
| E - E_F                        | E - E_F          |
+--------------------------------+------------------+
```

Both panels place:

$$
E_F=0.
$$

---

# 14. Verify the direct gap at K

The supplied path has 40 intervals per segment, so the plotting script assumes:

```text
Gamma : index 0
M     : index 40
K     : index 80
Gamma : final point
```

For 26 valence electrons, the script assumes 13 occupied bands and checks the top occupied and first unoccupied bands.

A direct gap at $K$ requires:

$$
k_{\rm VBM}=k_{\rm CBM}=K.
$$

Then:

$$
E_g^{\rm direct}(K)
=
E_{\rm CBM}(K)
-
E_{\rm VBM}(K).
$$

The script prints the estimated VBM, CBM, global gap, and direct gap at K.

The direct-gap character should be verified from the numerical result, not assumed.

---

# 15. Spin-orbit coupling and band-gap accuracy

The supplied calculation is scalar-relativistic for simplicity.

For research-level monolayer MoS₂, spin-orbit coupling should be tested because it splits the valence bands near $K$.

With fully relativistic pseudopotentials, typical QE settings include:

```text
noncolin = .true.
lspinorb = .true.
```

PBE also does not generally give a quantitatively exact quasiparticle gap. Depending on the research question, possible improvements include hybrid functionals, GW, or a physically justified scissor correction.

---

# 16. Use the dense QE XML directly in BoltzTraP2

After `mos2.nscf.in` has been run, the dense QE dataset is in:

```text
out/mos2.save/
```

and normally includes:

```text
out/mos2.save/data-file-schema.xml
```

No separate `qe_data/` directory is needed.

BoltzTraP2 can read directly from:

```text
./out/mos2.save
```

---

# 17. BoltzTraP2 interpolation

Run from the `mos2/` directory:

```bash
btp2 -vv -n 2 interpolate \
    -m 5 \
    -e -0.15 \
    -E 0.15 \
    -o mos2.bt2 \
    ./out/mos2.save
```

Here:

```text
-n 2
```

uses two workers.

```text
-m 5
```

increases the interpolation density.

The interpolation energy limits:

```text
-e -0.15
-E  0.15
```

are in Hartree.

Since:

$$
1\ {\rm Ha}\approx27.2114\ {\rm eV},
$$

we have:

$$
0.15\ {\rm Ha}\approx4.08\ {\rm eV}.
$$

Inspect the result:

```bash
btp2 describe mos2.bt2
```

---

# 18. Integrate the transport coefficients

For temperatures from 300 K to 1000 K in steps of 100 K:

```bash
btp2 -vv -n 2 integrate \
    mos2.bt2 \
    300:1001:100
```

Typical outputs are:

```text
mos2.trace
mos2.condtens
mos2.halltens
mos2.btj
```

The plotting script uses:

```text
mos2.condtens
```

---

# 19. In-plane tensor components

For a hexagonal monolayer, use the in-plane average:

$$
\frac{\sigma_{\parallel}}{\tau}
=
\frac{1}{2}
\left(
\frac{\sigma_{xx}}{\tau}
+
\frac{\sigma_{yy}}{\tau}
\right),
$$

$$
S_{\parallel}
=
\frac{S_{xx}+S_{yy}}{2},
$$

and

$$
\frac{\kappa_{e,\parallel}}{\tau}
=
\frac{1}{2}
\left(
\frac{\kappa_{e,xx}}{\tau}
+
\frac{\kappa_{e,yy}}{\tau}
\right).
$$

The power factor per relaxation time is:

$$
\frac{PF_{\parallel}}{\tau}
=
S_{\parallel}^2
\frac{\sigma_{\parallel}}{\tau}.
$$

This avoids averaging the artificial out-of-plane vacuum direction into the main in-plane transport quantity.

---

# 20. Plot the thermoelectric properties versus chemical potential

Use:

```text
plot_thermoelectric.py
```

The main settings are:

```python
CONDTENS_FILE = Path("mos2.condtens")

FERMI_ENERGY_EV = 0.0

TEMPERATURES_K = [300.0, 500.0, 700.0, 900.0]

MU_WINDOW_EV = (-1.5, 1.5)

TAU_SECONDS = None
```

Set `FERMI_ENERGY_EV` to the same reference used in `plot_band_dos.py`.

Run:

```bash
python plot_thermoelectric.py
```

The outputs are:

```text
figures/mos2_thermoelectric_vs_mu.png
figures/mos2_thermoelectric_vs_mu.pdf
```

The four panels show:

1. $S_{\parallel}(\mu)$,
2. $\sigma_{\parallel}(\mu)/\tau$,
3. $\kappa_{e,\parallel}(\mu)/\tau$,
4. $PF_{\parallel}(\mu)/\tau$.

The horizontal axis is:

$$
\mu-E_F.
$$

---

# 21. Seebeck coefficient

The script plots:

$$
S_{\parallel}
=
\frac{S_{xx}+S_{yy}}{2}.
$$

BoltzTraP2 stores $S$ in V/K. The script converts it to:

$$
\mu{\rm V/K}
$$

through:

$$
S_{\mu{\rm V/K}}
=
10^6 S_{\rm V/K}.
$$

Positive $S$ usually indicates hole-like transport and negative $S$ usually indicates electron-like transport.

---

# 22. Electrical conductivity

With the constant relaxation-time approximation:

$$
\frac{\sigma_{\parallel}}{\tau}
$$

is obtained directly.

If a physically justified relaxation time is available:

$$
\sigma_{\parallel}
=
\left(
\frac{\sigma_{\parallel}}{\tau}
\right)\tau.
$$

The default plotting setting is:

```python
TAU_SECONDS = None
```

If you set, for example:

```python
TAU_SECONDS = 1.0e-14
```

the script plots $\sigma$ instead of $\sigma/\tau$.

Do this only when the relaxation time has a defensible physical basis.

---

# 23. Electronic thermal conductivity

Likewise:

$$
\frac{\kappa_{e,\parallel}}{\tau}
$$

is obtained directly.

If $\tau$ is known:

$$
\kappa_{e,\parallel}
=
\left(
\frac{\kappa_{e,\parallel}}{\tau}
\right)\tau.
$$

The lattice thermal conductivity is a separate quantity and is not obtained from this BoltzTraP2 electronic calculation.

---

# 24. Power factor

The power factor is:

$$
PF_{\parallel}
=
S_{\parallel}^2
\sigma_{\parallel}.
$$

Without a specified relaxation time:

$$
\frac{PF_{\parallel}}{\tau}
=
S_{\parallel}^2
\frac{\sigma_{\parallel}}{\tau}.
$$

The script calculates this quantity directly.

The largest $|S|$ does not generally coincide with the largest power factor because increasing carrier density changes $S$ and $\sigma$ in opposite ways.

---

# 25. Important 2D normalization issue

Quantum ESPRESSO and BoltzTraP2 use a three-dimensional periodic supercell.

For the monolayer:

$$
V_{\rm cell}=A L_z.
$$

Because $L_z$ contains vacuum, raw volumetric values of:

$$
\sigma,
\quad
\frac{\sigma}{\tau},
\quad
\kappa_e,
\quad
\frac{\kappa_e}{\tau},
\quad
PF
$$

depend on the chosen vacuum height.

The Seebeck coefficient does not have the same volume-normalization problem.

If an effective physical thickness $d_{\rm eff}$ is adopted, one possible correction is:

$$
X_{\rm corrected}
=
X_{\rm supercell}
\frac{L_z}{d_{\rm eff}},
$$

for:

$$
X=\sigma,\ \kappa_e,\ PF.
$$

The supplied script contains:

```python
APPLY_2D_RESCALE = False
LZ_ANGSTROM = 20.0
D_EFFECTIVE_ANGSTROM = 6.15
```

Setting:

```python
APPLY_2D_RESCALE = True
```

applies the factor:

$$
\frac{L_z}{d_{\rm eff}}.
$$

The example value $d_{\rm eff}=6.15$ Å is only a convention. It is not a unique thickness defined by first principles.

When reporting results, state the normalization convention explicitly.

---

# 26. Optional carrier-concentration calculation

BoltzTraP2 can also calculate properties for specified carrier concentrations:

```bash
btp2 -vv -n 2 dope \
    mos2.bt2 \
    300:901:100 \
    '1e18,1e19,1e20,-1e18,-1e19,-1e20'
```

For a monolayer, volumetric carrier concentrations also depend on the chosen thickness convention. If needed, define a sheet density consistently.

---

# 27. Convergence tests

At minimum, test the following.

## Plane-wave cutoff

For example:

```text
50 Ry
60 Ry
70 Ry
80 Ry
```

Check the band gap and band curvature as well as total energy.

## Vacuum height

For example:

```text
15 Angstrom
20 Angstrom
25 Angstrom
```

The in-plane band structure should converge as periodic-image interactions become negligible.

## SCF k mesh

For example:

```text
8 x 8 x 1
12 x 12 x 1
16 x 16 x 1
```

## Dense NSCF transport mesh

For example:

```text
18 x 18 x 1
24 x 24 x 1
30 x 30 x 1
36 x 36 x 1
```

Check convergence of:

$$
S(\mu,T),
\quad
\sigma(\mu,T)/\tau,
\quad
\kappa_e(\mu,T)/\tau,
\quad
PF(\mu,T)/\tau.
$$

## Number of bands

For example:

```text
nbnd = 32
nbnd = 40
nbnd = 48
```

## BoltzTraP2 interpolation

Compare, for example:

```bash
-m 3
-m 5
-m 7
```

---

# 28. Practical settings for only two CPUs

A useful progression is:

```text
Debugging:
SCF mesh      8 x 8 x 1
NSCF mesh    12 x 12 x 1
nbnd         28-32

Preliminary:
SCF mesh     12 x 12 x 1
NSCF mesh    18 x 18 x 1
nbnd         36-40

Production starting point:
SCF mesh     12-16 x 12-16 x 1
NSCF mesh    24 x 24 x 1 or denser
nbnd         40 or more
```

Use:

```bash
mpirun -np 2
```

for QE and:

```bash
btp2 -n 2
```

where BoltzTraP2 supports worker parallelism.

---

# 29. Complete command sequence

From the working directory:

```bash
cd ~/calculations/mos2
mkdir -p out figures

export OMP_NUM_THREADS=1
```

Download pseudopotentials:

```bash
wget https://pseudopotentials.quantum-espresso.org/upf_files/Mo.pbe-spn-kjpaw_psl.1.0.0.UPF

wget https://pseudopotentials.quantum-espresso.org/upf_files/S.pbe-n-kjpaw_psl.1.0.0.UPF
```

SCF:

```bash
mpirun -np 2 pw.x \
    -in mos2.scf.in \
    > mos2.scf.out
```

Band path:

```bash
mpirun -np 2 pw.x \
    -in mos2.nscfbands.in \
    > mos2.nscfbands.out
```

Band post-processing:

```bash
mpirun -np 2 bands.x \
    -in mos2.bands.in \
    > mos2.bands.out
```

Dense NSCF:

```bash
mpirun -np 2 pw.x \
    -in mos2.nscf.in \
    > mos2.nscf.out
```

DOS:

```bash
mpirun -np 2 dos.x \
    -in mos2.dos.in \
    > mos2.dos.out
```

Find the energy reference:

```bash
grep -Ei "fermi|highest occupied|lowest unoccupied" \
    mos2.scf.out \
    mos2.nscfbands.out \
    mos2.nscf.out
```

Edit `plot_band_dos.py`:

```python
FERMI_ENERGY_EV = <your_QE_reference_energy>
```

Plot bands and DOS:

```bash
source ~/venvs/boltztrap2/bin/activate
python plot_band_dos.py
```

BoltzTraP2 interpolation directly from QE:

```bash
btp2 -vv -n 2 interpolate \
    -m 5 \
    -e -0.15 \
    -E 0.15 \
    -o mos2.bt2 \
    ./out/mos2.save
```

Inspect:

```bash
btp2 describe mos2.bt2
```

Integrate transport:

```bash
btp2 -vv -n 2 integrate \
    mos2.bt2 \
    300:1001:100
```

Edit `plot_thermoelectric.py` using the same reference:

```python
FERMI_ENERGY_EV = <your_QE_reference_energy>
```

Plot:

```bash
python plot_thermoelectric.py
```

---

# 30. Expected final directory

After running the calculations:

```text
mos2/
│
├── Mo.pbe-spn-kjpaw_psl.1.0.0.UPF
├── S.pbe-n-kjpaw_psl.1.0.0.UPF
│
├── mos2.scf.in
├── mos2.nscfbands.in
├── mos2.bands.in
├── mos2.nscf.in
├── mos2.dos.in
├── plot_band_dos.py
├── plot_thermoelectric.py
│
├── mos2.scf.out
├── mos2.nscfbands.out
├── mos2.bands.out
├── mos2.nscf.out
├── mos2.dos.out
│
├── mos2.bands.dat
├── mos2.bands.dat.gnu
├── mos2.dos
│
├── mos2.bt2
├── mos2.btj
├── mos2.trace
├── mos2.condtens
├── mos2.halltens
│
├── out/
│   └── mos2.save/
│       └── data-file-schema.xml
│
└── figures/
    ├── mos2_band_dos.png
    ├── mos2_band_dos.pdf
    ├── mos2_thermoelectric_vs_mu.png
    └── mos2_thermoelectric_vs_mu.pdf
```

The essential distinction remains:

- `mos2.nscfbands.in` uses a high-symmetry path for visualizing the bands.
- `mos2.nscf.in` uses a dense uniform mesh for DOS and transport.

This compact organization keeps the entire user-facing workflow in one `mos2/` folder while leaving QE scratch data in `./out`.
