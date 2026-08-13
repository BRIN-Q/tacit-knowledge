# Tutorial Kalkulasi Sifat Termoelektrik Monolayer MoS₂ dengan Quantum ESPRESSO dan BoltzTraP2

## 1. Tujuan dan alur kerja

Tutorial ini membahas alur kerja lengkap untuk menghitung struktur elektronik dan sifat termoelektrik **monolayer MoS₂** menggunakan:

1. **Quantum ESPRESSO** untuk perhitungan DFT.
2. **BoltzTraP2** untuk interpolasi pita dan perhitungan transport Boltzmann semiklasik.
3. **Python, NumPy, dan Matplotlib** untuk mengolah dan memplot struktur pita, DOS, serta sifat termoelektrik.

Sistem yang digunakan adalah **monolayer 1H-MoS₂**, yaitu satu lapisan S-Mo-S dengan koordinasi trigonal-prismatik. Monolayer ini merupakan bentuk satu-lapis yang berkaitan dengan lapisan penyusun bulk 2H-MoS₂. Berbeda dari bulk 2H-MoS₂ yang memiliki gap tidak langsung, monolayer MoS₂ dikenal memiliki **direct band gap pada titik K**. Hal tersebut telah diamati secara eksperimen dan juga muncul dalam banyak perhitungan struktur elektronik.

Untuk seluruh perhitungan Quantum ESPRESSO, diasumsikan hanya tersedia dua proses CPU:

```bash
mpirun -np 2 ...
```

Untuk BoltzTraP2, dua worker digunakan dengan:

```bash
btp2 -n 2 ...
```

Alur kerja yang digunakan adalah:

```text
struktur monolayer MoS2
        |
        v
       SCF
        |
        +-------------------------------+
        |                               |
        v                               v
bands pada lintasan               NSCF mesh seragam rapat
Gamma-M-K-Gamma                         |
        |                               +----------------+
        v                               |                |
     bands.x                            v                v
        |                             dos.x        data XML QE
        v                               |                |
struktur pita                           v                v
        |                              DOS           BoltzTraP2
        |                               |                |
        +---------------+---------------+                |
                        |                                v
                        v                           interpolate
               plot struktur pita                         |
                  + DOS                                   v
                                                mos2.bt2
                                                        |
                                                        v
                                                   integrate
                                                        |
                                                        v
                                                mos2.condtens
                                                        |
                                                        v
                                               skrip Python
                                                        |
                                    +-------------------+-------------------+
                                    |                   |                   |
                                    v                   v                   v
                                  S(mu)           sigma(mu)/tau       kappa_e(mu)/tau
                                                                            |
                                                                            v
                                                                       PF(mu)/tau
```

Sumber utama yang relevan:

- Quantum ESPRESSO `pw.x`: https://www.quantum-espresso.org/Doc/INPUT_PW.html
- Quantum ESPRESSO `bands.x`: https://www.quantum-espresso.org/Doc/INPUT_BANDS.html
- Quantum ESPRESSO `dos.x`: https://www.quantum-espresso.org/Doc/INPUT_DOS.html
- BoltzTraP2: https://gitlab.com/sousaw/BoltzTraP2
- BoltzTraP2 di PyPI: https://pypi.org/project/BoltzTraP2/
- Mak et al., *Atomically Thin MoS₂: A New Direct-Gap Semiconductor*: https://arxiv.org/abs/1004.0546

---

# 2. Dasar teori singkat transport termoelektrik

BoltzTraP2 membangun interpolasi halus dari eigenvalue elektronik

$$
E_{n\mathbf{k}}
$$

yang diperoleh dari DFT. Kecepatan grup pita adalah

$$
\mathbf{v}_{n\mathbf{k}}
=
\frac{1}{\hbar}
\nabla_{\mathbf{k}}E_{n\mathbf{k}}.
$$

Besaran transport bergantung pada turunan pita terhadap vektor gelombang. Karena itu, perhitungan transport membutuhkan sampling titik-k yang jauh lebih rapat dibandingkan lintasan titik-k yang hanya digunakan untuk memplot struktur pita.

Secara skematis, tensor distribusi transport dapat ditulis sebagai

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

Momen transport adalah

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

Konduktivitas listrik diberikan oleh

$$
\boldsymbol{\sigma}
=
e^2\mathbf{L}^{(0)}.
$$

Tensor Seebeck adalah

$$
\mathbf{S}
=
-\frac{1}{eT}
\left(\mathbf{L}^{(0)}\right)^{-1}
\mathbf{L}^{(1)}.
$$

Konduktivitas termal elektronik pada kondisi arus listrik nol adalah

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

Dalam constant relaxation-time approximation,

$$
\frac{\sigma}{\tau}
$$

dan

$$
\frac{\kappa_e}{\tau}
$$

dapat dihitung tanpa mengetahui nilai \(\tau\).

Koefisien Seebeck tidak bergantung secara eksplisit pada nilai \(\tau\) yang konstan.

Power factor didefinisikan sebagai

$$
PF=S^2\sigma.
$$

Karena itu,

$$
\frac{PF}{\tau}
=
S^2\frac{\sigma}{\tau}.
$$

Figure of merit termoelektrik adalah

$$
ZT
=
\frac{S^2\sigma T}
{\kappa_e+\kappa_l},
$$

dengan \(\kappa_l\) adalah konduktivitas termal kisi.

BoltzTraP2 sendiri tidak memberikan \(ZT\) lengkap jika \(\tau\) dan \(\kappa_l\) belum ditentukan.

---

# 3. Instalasi Quantum ESPRESSO

Instruksi di bagian ini menggunakan Ubuntu atau Debian Linux.

## 3.1 Instal paket yang diperlukan

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

Periksa MPI:

```bash
mpirun --version
mpif90 --version
```

Periksa compiler Fortran:

```bash
gfortran --version
```

---

## 3.2 Unduh dan kompilasi Quantum ESPRESSO

Dokumentasi Quantum ESPRESSO 7.5 dapat digunakan sebagai acuan untuk input pada tutorial ini.

Misalkan arsip sumber telah disimpan sebagai:

```text
~/Downloads/qe-7.5.0.tar.gz
```

Ekstrak:

```bash
cd ~/Downloads
tar -xzf qe-7.5.0.tar.gz
```

Pindahkan:

```bash
mkdir -p ~/software
mv qe-7.5.0 ~/software/
```

Masuk ke direktori sumber:

```bash
cd ~/software/qe-7.5.0
```

Buat direktori build:

```bash
mkdir build
cd build
```

Konfigurasi dengan MPI:

```bash
../configure MPIF90=mpif90
```

Kompilasi menggunakan dua CPU:

```bash
make -j2 all
```

Tambahkan executable Quantum ESPRESSO ke `PATH`:

```bash
echo 'export PATH=$HOME/software/qe-7.5.0/build/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

Periksa:

```bash
which pw.x
which bands.x
which dos.x
```

---

## 3.3 Pengaturan paralelisasi

Gunakan satu thread OpenMP per proses MPI:

```bash
export OMP_NUM_THREADS=1
```

Kemudian jalankan Quantum ESPRESSO dengan:

```bash
mpirun -np 2 pw.x ...
```

---

# 4. Instalasi BoltzTraP2 dan paket plotting

Per Maret 2026, BoltzTraP2 memiliki rilis 26.3.1. Versi terbaru dapat diperiksa melalui halaman GitLab atau PyPI.

Buat virtual environment:

```bash
python3 -m venv ~/venvs/boltztrap2
```

Aktifkan:

```bash
source ~/venvs/boltztrap2/bin/activate
```

Perbarui perangkat instalasi:

```bash
python -m pip install --upgrade pip setuptools wheel
```

Instal BoltzTraP2:

```bash
python -m pip install BoltzTraP2
```

Instal paket plotting:

```bash
python -m pip install numpy matplotlib
```

Opsional:

```bash
python -m pip install pyfftw
```

Periksa:

```bash
btp2 -V
btp2 -h
```

BoltzTraP2 menyediakan subcommand seperti:

```text
interpolate
integrate
dope
plotbands
plot
describe
fermisurface_2d
```

Gunakan dua worker:

```bash
btp2 -n 2 ...
```

---

# 5. Membuat direktori proyek

Buat proyek:

```bash
mkdir -p ~/calculations/mos2_monolayer_thermoelectric
cd ~/calculations/mos2_monolayer_thermoelectric
```

Buat subdirektori:

```bash
mkdir -p \
    pseudo \
    tmp \
    input \
    output \
    bands \
    dos \
    boltztrap \
    scripts \
    figures
```

Struktur awal:

```text
mos2_monolayer_thermoelectric/
├── pseudo/
├── tmp/
├── input/
├── output/
├── bands/
├── dos/
├── boltztrap/
├── scripts/
└── figures/
```

---

# 6. Pseudopotensial

Sebagai contoh awal, gunakan pseudopotensial PBE PAW:

```text
Mo.pbe-spn-kjpaw_psl.1.0.0.UPF
S.pbe-n-kjpaw_psl.1.0.0.UPF
```

Salin ke:

```text
pseudo/
```

Sebagai contoh:

```bash
cp ~/Downloads/Mo.pbe-spn-kjpaw_psl.1.0.0.UPF pseudo/
cp ~/Downloads/S.pbe-n-kjpaw_psl.1.0.0.UPF pseudo/
```

Periksa:

```bash
ls pseudo/
```

Untuk penelitian, cutoff, pseudopotensial, spin-orbit coupling, dan parameter kisi harus diuji konvergensinya.

---

# 7. Struktur monolayer 1H-MoS₂

Monolayer 1H-MoS₂ memiliki satu atom Mo dan dua atom S per sel primitif.

Kita gunakan nilai awal:

$$
a=3.160\ {\rm \AA}
$$

dan tinggi supercell:

$$
L_z=20.0\ {\rm \AA}.
$$

Nilai \(L_z\) yang besar digunakan untuk memisahkan monolayer dari citra periodiknya sepanjang arah \(z\).

Geometri awal:

```text
Mo   0.0000000000   0.0000000000   0.5000000000
S    0.3333333333   0.6666666667   0.5782500000
S    0.3333333333   0.6666666667   0.4217500000
```

Dengan \(L_z=20\) Å, jarak vertikal setiap S terhadap bidang Mo adalah kira-kira

$$
0.07825\times 20
=
1.565\ {\rm \AA}.
$$

Ketebalan geometrik S-S adalah sekitar

$$
3.13\ {\rm \AA}.
$$

Untuk perhitungan produksi, struktur sebaiknya direlaksasi terlebih dahulu.

---

# 8. Langkah 1: perhitungan SCF

Buat:

```text
input/01_scf.in
```

dengan:

```text
&CONTROL
    calculation = 'scf'
    prefix      = 'mos2'
    pseudo_dir  = './pseudo/'
    outdir      = './tmp/'
    verbosity   = 'high'
/

&SYSTEM
    ibrav       = 4
    A           = 3.160
    C           = 20.000

    nat         = 3
    ntyp        = 2

    ecutwfc     = 70.0
    ecutrho     = 560.0

    occupations = 'fixed'
/

&ELECTRONS
    conv_thr         = 1.0d-10
    mixing_beta      = 0.30
    electron_maxstep = 200
    diagonalization  = 'david'
/

ATOMIC_SPECIES
Mo  95.95   Mo.pbe-spn-kjpaw_psl.1.0.0.UPF
S   32.06   S.pbe-n-kjpaw_psl.1.0.0.UPF

ATOMIC_POSITIONS crystal
Mo  0.0000000000  0.0000000000  0.5000000000
S   0.3333333333  0.6666666667  0.5782500000
S   0.3333333333  0.6666666667  0.4217500000

K_POINTS automatic
12 12 1 0 0 0
```

Perhatikan perbedaan utama dari sistem bulk:

```text
nat = 3
C = 20 Angstrom
K_POINTS = 12 x 12 x 1
```

Untuk sistem dua dimensi, hanya satu titik-k sepanjang arah vakum biasanya cukup.

---

## 8.1 Jalankan SCF

```bash
export OMP_NUM_THREADS=1

mpirun -np 2 pw.x \
    -in input/01_scf.in \
    > output/01_scf.out
```

Periksa:

```bash
tail -n 30 output/01_scf.out
```

Cari:

```bash
grep -i "JOB DONE" output/01_scf.out
```

Periksa konvergensi:

```bash
grep -i "convergence has been achieved" output/01_scf.out
```

Energi total:

```bash
grep "!" output/01_scf.out
```

Jumlah elektron:

```bash
grep -i "number of electrons" output/01_scf.out
```

Untuk pseudopotensial contoh, hasil biasanya memiliki 26 elektron valensi, sehingga untuk sistem non-spin-polarized terdapat kira-kira

$$
N_{\rm occ}
=
\frac{26}{2}
=
13
$$

pita terisi.

Nilai ini nantinya digunakan sebagai pemeriksaan pada skrip plotting struktur pita.

---

# 9. Langkah 2: struktur pita elektronik monolayer

Untuk monolayer heksagonal, gunakan lintasan:

$$
\Gamma\rightarrow M\rightarrow K\rightarrow\Gamma.
$$

Direct band gap monolayer MoS₂ diharapkan berada di \(K\).

Buat:

```text
input/02_nscf_bands.in
```

dengan:

```text
&CONTROL
    calculation = 'bands'
    prefix      = 'mos2'
    pseudo_dir  = './pseudo/'
    outdir      = './tmp/'
    verbosity   = 'high'
/

&SYSTEM
    ibrav       = 4
    A           = 3.160
    C           = 20.000

    nat         = 3
    ntyp        = 2

    ecutwfc     = 70.0
    ecutrho     = 560.0

    occupations = 'fixed'
    nbnd        = 40
/

&ELECTRONS
    conv_thr        = 1.0d-10
    diagonalization = 'david'
/

ATOMIC_SPECIES
Mo  95.95   Mo.pbe-spn-kjpaw_psl.1.0.0.UPF
S   32.06   S.pbe-n-kjpaw_psl.1.0.0.UPF

ATOMIC_POSITIONS crystal
Mo  0.0000000000  0.0000000000  0.5000000000
S   0.3333333333  0.6666666667  0.5782500000
S   0.3333333333  0.6666666667  0.4217500000

K_POINTS crystal_b
4
0.0000000000  0.0000000000  0.0000000000  40
0.5000000000  0.0000000000  0.0000000000  40
0.3333333333  0.3333333333  0.0000000000  40
0.0000000000  0.0000000000  0.0000000000   1
```

Di sini:

```text
Gamma = (0, 0, 0)
M     = (1/2, 0, 0)
K     = (1/3, 1/3, 0)
Gamma = (0, 0, 0)
```

Quantum ESPRESSO menjelaskan bahwa `crystal_b` digunakan untuk lintasan struktur pita dan koordinatnya diberikan relatif terhadap vektor kisi resiprokal.

---

## 9.1 Jalankan perhitungan bands

```bash
mpirun -np 2 pw.x \
    -in input/02_nscf_bands.in \
    > output/02_nscf_bands.out
```

Periksa:

```bash
tail -n 20 output/02_nscf_bands.out
```

---

# 10. Langkah 3: post-processing struktur pita dengan `bands.x`

Buat:

```text
input/03_bands_pp.in
```

dengan:

```text
&BANDS
    prefix  = 'mos2'
    outdir  = './tmp/'
    filband = './bands/mos2.bands.dat'
    lsym    = .false.
/
```

Jalankan:

```bash
mpirun -np 2 bands.x \
    -in input/03_bands_pp.in \
    > output/03_bands_pp.out
```

`bands.x` menghasilkan file:

```text
bands/mos2.bands.dat
```

dan, pada Quantum ESPRESSO modern, juga file:

```text
bands/mos2.bands.dat.gnu
```

File `.gnu` berisi energi dalam eV dan sangat praktis untuk diproses dengan Python.

Periksa:

```bash
ls -lh bands/
```

---

# 11. Langkah 4: NSCF mesh seragam rapat untuk DOS dan BoltzTraP2

Perhitungan transport tidak boleh memakai lintasan \(\Gamma-M-K-\Gamma\).

BoltzTraP2 membutuhkan eigenvalue pada mesh Brillouin-zone seragam karena kecepatan elektronik berasal dari

$$
\nabla_{\mathbf{k}}E_{n\mathbf{k}}.
$$

Buat:

```text
input/04_nscf_dos.in
```

dengan:

```text
&CONTROL
    calculation = 'nscf'
    prefix      = 'mos2'
    pseudo_dir  = './pseudo/'
    outdir      = './tmp/'
    verbosity   = 'high'
/

&SYSTEM
    ibrav       = 4
    A           = 3.160
    C           = 20.000

    nat         = 3
    ntyp        = 2

    ecutwfc     = 70.0
    ecutrho     = 560.0

    occupations = 'fixed'
    nbnd        = 40
/

&ELECTRONS
    conv_thr        = 1.0d-10
    diagonalization = 'david'
/

ATOMIC_SPECIES
Mo  95.95   Mo.pbe-spn-kjpaw_psl.1.0.0.UPF
S   32.06   S.pbe-n-kjpaw_psl.1.0.0.UPF

ATOMIC_POSITIONS crystal
Mo  0.0000000000  0.0000000000  0.5000000000
S   0.3333333333  0.6666666667  0.5782500000
S   0.3333333333  0.6666666667  0.4217500000

K_POINTS automatic
24 24 1 0 0 0
```

Untuk sistem 2D, grid awal:

```text
24 x 24 x 1
```

cukup masuk akal sebagai tahap pendahuluan.

Untuk hasil penelitian, uji setidaknya:

```text
18 x 18 x 1
24 x 24 x 1
30 x 30 x 1
36 x 36 x 1
```

dan periksa stabilitas:

$$
S,
\qquad
\sigma/\tau,
\qquad
\kappa_e/\tau,
\qquad
PF/\tau.
$$

---

## 11.1 Jalankan NSCF

```bash
mpirun -np 2 pw.x \
    -in input/04_nscf_dos.in \
    > output/04_nscf_dos.out
```

Periksa:

```bash
tail -n 20 output/04_nscf_dos.out
```

---

# 12. Langkah 5: hitung DOS

Untuk monolayer dengan satu titik-k pada arah \(z\), tutorial ini menggunakan Gaussian broadening eksplisit pada `dos.x`.

Buat:

```text
input/05_dos.in
```

dengan:

```text
&DOS
    prefix  = 'mos2'
    outdir  = './tmp/'
    fildos  = './dos/mos2.dos'

    bz_sum  = 'smearing'
    ngauss  = 0
    degauss = 0.005

    Emin    = -10.0
    Emax    =  10.0
    DeltaE  =   0.01
/
```

Perhatikan:

- `Emin`, `Emax`, dan `DeltaE` menggunakan eV.
- `degauss` menggunakan Ry.
- `degauss = 0.005 Ry` kira-kira setara dengan 0.068 eV.

Jalankan:

```bash
mpirun -np 2 dos.x \
    -in input/05_dos.in \
    > output/05_dos.out
```

Periksa:

```bash
head dos/mos2.dos
tail dos/mos2.dos
```

---

# 13. Menentukan energi Fermi atau energi referensi untuk plotting

Tujuan plotting adalah membuat:

$$
E_F=0.
$$

Artinya semua energi yang diplot digeser sebagai:

$$
E_{\rm plot}
=
E_{\rm QE}-E_F.
$$

Cari terlebih dahulu informasi energi pada output Quantum ESPRESSO:

```bash
grep -Ei "fermi|highest occupied|lowest unoccupied" \
    output/01_scf.out \
    output/02_nscf_bands.out \
    output/04_nscf_dos.out
```

Kemungkinan pertama adalah QE mencetak baris seperti:

```text
the Fermi energy is    X.XXXX ev
```

Jika demikian, gunakan nilai tersebut sebagai `FERMI_ENERGY_EV`.

Namun, untuk semikonduktor dengan

```text
occupations = 'fixed'
```

Quantum ESPRESSO dapat mencetak informasi seperti:

```text
highest occupied, lowest unoccupied level (ev):
```

tanpa mendefinisikan energi Fermi logam yang unik.

Untuk semikonduktor intrinsik, konvensi sederhana yang dapat digunakan sebagai energi referensi adalah titik tengah gap:

$$
E_F^{\rm ref}
=
\frac{E_{\rm VBM}+E_{\rm CBM}}{2}.
$$

Misalnya, jika output memberikan:

$$
E_{\rm VBM}=5.20\ {\rm eV}
$$

dan

$$
E_{\rm CBM}=6.90\ {\rm eV},
$$

maka:

$$
E_F^{\rm ref}
=
\frac{5.20+6.90}{2}
=
6.05\ {\rm eV}.
$$

Pada skrip Python, masukkan:

```python
FERMI_ENERGY_EV = 6.05
```

Nilai ini hanyalah contoh. Gunakan angka dari perhitungan Anda sendiri.

Penting untuk menggunakan **referensi energi yang sama** untuk:

1. struktur pita,
2. DOS,
3. sumbu potensial kimia yang ingin dibandingkan dengan struktur elektronik.

---

# 14. Plot struktur pita dan DOS dalam dua panel bersebelahan

Salin skrip berikut ke:

```text
scripts/plot_band_dos.py
```

```python
#!/usr/bin/env python3

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

BAND_FILE = Path("bands/mos2.bands.dat.gnu")
DOS_FILE = Path("dos/mos2.dos")

# GANTI dengan energi Fermi atau titik tengah gap dari output QE.
FERMI_ENERGY_EV = 0.0

N_OCCUPIED_BANDS = 13

HIGH_SYMMETRY_INDICES = [0, 40, 80, -1]
HIGH_SYMMETRY_LABELS = [r"$\Gamma$", "M", "K", r"$\Gamma$"]

ENERGY_WINDOW_EV = (-4.0, 4.0)

OUTPUT_PNG = Path("figures/mos2_band_dos.png")
OUTPUT_PDF = Path("figures/mos2_band_dos.pdf")


def read_qe_gnu_bands(filename):
    blocks = []
    current = []

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()

            if not s:
                if current:
                    blocks.append(np.asarray(current, dtype=float))
                    current = []
                continue

            if s.startswith("#"):
                continue

            fields = s.split()
            if len(fields) >= 2:
                current.append([float(fields[0]), float(fields[1])])

    if current:
        blocks.append(np.asarray(current, dtype=float))

    if not blocks:
        raise RuntimeError(f"Tidak ada data pita dalam {filename}")

    nk = min(len(block) for block in blocks)
    kdist = blocks[0][:nk, 0]
    energies = np.vstack([block[:nk, 1] for block in blocks])

    return kdist, energies


def resolve_indices(indices, nk):
    result = []
    for i in indices:
        j = nk + i if i < 0 else i
        if not 0 <= j < nk:
            raise IndexError(f"Indeks {i} tidak valid untuk nk={nk}")
        result.append(j)
    return result


def main():
    OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)

    kdist, bands_ev = read_qe_gnu_bands(BAND_FILE)
    bands_shifted = bands_ev - FERMI_ENERGY_EV

    hs_indices = resolve_indices(HIGH_SYMMETRY_INDICES, len(kdist))
    hs_positions = [kdist[i] for i in hs_indices]

    nbands = bands_ev.shape[0]

    print(f"E_F = {FERMI_ENERGY_EV:.8f} eV")
    print(f"Jumlah pita = {nbands}")
    print(f"Jumlah titik-k = {len(kdist)}")

    iv = N_OCCUPIED_BANDS - 1
    ic = N_OCCUPIED_BANDS

    if ic < nbands:
        vband = bands_ev[iv]
        cband = bands_ev[ic]

        ivbm = int(np.argmax(vband))
        icbm = int(np.argmin(cband))

        vbm = vband[ivbm]
        cbm = cband[icbm]
        gap_global = cbm - vbm

        k_index = hs_indices[2]
        direct_gap_k = cband[k_index] - vband[k_index]

        print(f"VBM = {vbm:.8f} eV, indeks k = {ivbm}")
        print(f"CBM = {cbm:.8f} eV, indeks k = {icbm}")
        print(f"Gap global = {gap_global:.8f} eV")
        print(f"Direct gap di K = {direct_gap_k:.8f} eV")

    dos_data = np.loadtxt(DOS_FILE, comments="#")

    if dos_data.ndim == 1:
        dos_data = dos_data.reshape(1, -1)

    dos_energy = dos_data[:, 0] - FERMI_ENERGY_EV
    dos_value = dos_data[:, 1]

    fig, (ax_band, ax_dos) = plt.subplots(
        1,
        2,
        figsize=(9.0, 6.0),
        sharey=True,
        gridspec_kw={
            "width_ratios": [2.4, 1.0],
            "wspace": 0.08,
        },
    )

    for band in bands_shifted:
        ax_band.plot(kdist, band, linewidth=1.0)

    for xpos in hs_positions:
        ax_band.axvline(xpos, linewidth=0.7, linestyle=":")

    ax_band.axhline(0.0, linewidth=0.9, linestyle="--")
    ax_band.set_xlim(kdist[0], kdist[-1])
    ax_band.set_ylim(*ENERGY_WINDOW_EV)
    ax_band.set_xticks(hs_positions)
    ax_band.set_xticklabels(HIGH_SYMMETRY_LABELS)
    ax_band.set_ylabel(r"$E-E_F$ (eV)")
    ax_band.set_xlabel("Lintasan titik-k")
    ax_band.set_title("Struktur pita elektronik")

    ax_dos.plot(dos_value, dos_energy, linewidth=1.2)
    ax_dos.axhline(0.0, linewidth=0.9, linestyle="--")
    ax_dos.set_xlabel("DOS (states/eV)")
    ax_dos.set_title("DOS")
    ax_dos.tick_params(axis="y", labelleft=False)

    fig.suptitle("Monolayer MoS$_2$")
    fig.tight_layout()

    fig.savefig(OUTPUT_PNG, dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PDF, bbox_inches="tight")

    plt.show()


if __name__ == "__main__":
    main()
```

Jalankan dari root proyek:

```bash
source ~/venvs/boltztrap2/bin/activate

python scripts/plot_band_dos.py
```

Hasil:

```text
figures/mos2_band_dos.png
figures/mos2_band_dos.pdf
```

Panel kiri menampilkan struktur pita, sedangkan panel kanan menampilkan DOS dengan sumbu energi yang sama.

Garis horizontal

$$
E-E_F=0
$$

adalah energi referensi Fermi.

---

# 15. Memeriksa direct gap di titik K

Pada input:

```text
Gamma -> M -> K -> Gamma
```

dengan masing-masing segmen memiliki 40 interval, indeks yang digunakan dalam skrip adalah:

```text
Gamma : 0
M     : 40
K     : 80
Gamma : titik terakhir
```

Skrip menggunakan:

```python
N_OCCUPIED_BANDS = 13
```

dan menghitung:

```text
VBM global
CBM global
gap global
direct gap pada K
```

Untuk mendapatkan direct gap pada \(K\), secara numerik kita ingin melihat:

$$
k_{\rm VBM}=K
$$

dan

$$
k_{\rm CBM}=K.
$$

Kemudian:

$$
E_g^{\rm direct}(K)
=
E_{\rm CBM}(K)-E_{\rm VBM}(K).
$$

Jika VBM dan CBM berada pada titik yang berbeda, hasil perhitungan tersebut tidak menunjukkan direct gap.

Struktur monolayer, parameter kisi, pseudopotensial, functional, dan SOC dapat mengubah detail band gap. Karena itu, direct-gap character harus diperiksa dari hasil aktual, bukan diasumsikan tanpa verifikasi.

---

# 16. Catatan mengenai PBE dan spin-orbit coupling

Monolayer MoS₂ memiliki pengaruh spin-orbit coupling yang cukup terlihat pada pita valensi dekat \(K\).

Tutorial utama menggunakan pseudopotensial scalar-relativistic karena lebih sederhana.

Untuk perhitungan tingkat penelitian, gunakan pseudopotensial fully relativistic dan tambahkan:

```text
noncolin = .true.
lspinorb = .true.
```

di `&SYSTEM`.

PBE juga umumnya tidak menghasilkan quasiparticle band gap yang kuantitatif.

Jika target penelitian sensitif terhadap band gap, pertimbangkan:

- HSE,
- GW,
- scissor correction yang memiliki dasar fisik.

BoltzTraP2 menyediakan opsi `--scissor` pada tahap integrasi.

---

# 17. Menyiapkan data Quantum ESPRESSO untuk BoltzTraP2

Setelah NSCF mesh seragam selesai, data XML terdapat pada:

```text
tmp/mos2.save/data-file-schema.xml
```

Buat direktori:

```bash
mkdir -p boltztrap/qe_data
```

Salin:

```bash
cp tmp/mos2.save/data-file-schema.xml \
   boltztrap/qe_data/
```

Periksa:

```bash
ls -lh boltztrap/qe_data/
```

BoltzTraP2 memiliki loader untuk XML Quantum ESPRESSO dan dapat membaca struktur, titik-k, eigenvalue, tingkat Fermi, dan jumlah elektron dari dataset tersebut.

---

# 18. Interpolasi BoltzTraP2

Aktifkan environment:

```bash
source ~/venvs/boltztrap2/bin/activate
```

Masuk ke direktori:

```bash
cd boltztrap
```

Jalankan:

```bash
btp2 -vv -n 2 interpolate \
    -m 5 \
    -e -0.15 \
    -E  0.15 \
    -o mos2.bt2 \
    ./qe_data
```

Parameter:

```text
-n 2
```

menggunakan dua worker.

Parameter:

```text
-m 5
```

meminta interpolasi yang lebih rapat dibandingkan data DFT.

Parameter:

```text
-e -0.15
-E  0.15
```

menggunakan satuan Hartree relatif terhadap Fermi level yang dibaca BoltzTraP2.

Karena:

$$
1\ {\rm Ha}
\approx
27.2114\ {\rm eV},
$$

maka:

$$
0.15\ {\rm Ha}
\approx
4.08\ {\rm eV}.
$$

Periksa:

```bash
btp2 describe mos2.bt2
```

---

# 19. Integrasi transport BoltzTraP2

Sebagai contoh, hitung temperatur:

$$
300,400,\ldots,1000\ {\rm K}.
$$

Jalankan:

```bash
btp2 -vv -n 2 integrate \
    mos2.bt2 \
    300:1001:100
```

BoltzTraP2 menggunakan constant relaxation-time approximation secara default.

Hasil utama:

```text
mos2.trace
mos2.condtens
mos2.halltens
mos2.btj
```

Untuk tutorial monolayer ini, file paling berguna untuk plotting tensor in-plane adalah:

```text
mos2.condtens
```

---

# 20. Struktur file `mos2.condtens`

BoltzTraP2 menulis kolom:

```text
0   Ef[Ry]
1   T[K]
2   N[e/uc]
```

kemudian 9 komponen tensor konduktivitas:

```text
3   sigma_xx/tau
4   sigma_yx/tau
5   sigma_zx/tau
6   sigma_xy/tau
7   sigma_yy/tau
8   sigma_zy/tau
9   sigma_xz/tau
10  sigma_yz/tau
11  sigma_zz/tau
```

kemudian 9 komponen tensor Seebeck:

```text
12  S_xx
13  S_yx
14  S_zx
15  S_xy
16  S_yy
17  S_zy
18  S_xz
19  S_yz
20  S_zz
```

kemudian 9 komponen tensor konduktivitas termal elektronik:

```text
21  kappa_xx/tau
22  kappa_yx/tau
23  kappa_zx/tau
24  kappa_xy/tau
25  kappa_yy/tau
26  kappa_zy/tau
27  kappa_xz/tau
28  kappa_yz/tau
29  kappa_zz/tau
```

Untuk monolayer heksagonal:

$$
\sigma_{xx}\approx\sigma_{yy},
$$

$$
S_{xx}\approx S_{yy},
$$

dan

$$
\kappa_{e,xx}\approx\kappa_{e,yy}.
$$

Karena itu, skrip menggunakan rata-rata in-plane:

$$
\sigma_{\parallel}
=
\frac{\sigma_{xx}+\sigma_{yy}}{2},
$$

$$
S_{\parallel}
=
\frac{S_{xx}+S_{yy}}{2},
$$

$$
\kappa_{e,\parallel}
=
\frac{\kappa_{e,xx}+\kappa_{e,yy}}{2}.
$$

Cara ini lebih sesuai untuk monolayer dibandingkan menggunakan rata-rata trace tiga dimensi karena komponen \(zz\) tidak menggambarkan transport utama di dalam bidang.

---

# 21. Potensial kimia pada file BoltzTraP2

Kolom pertama `mos2.condtens` adalah:

```text
Ef[Ry]
```

yang merupakan nilai potensial kimia dalam Ry.

Untuk plotting terhadap energi relatif terhadap referensi DFT:

$$
\mu_{\rm plot}
=
\mu-E_F.
$$

Konversinya:

$$
1\ {\rm Ry}
=
13.605693122994\ {\rm eV}.
$$

Maka di dalam skrip:

```python
mu_abs_ev = data[:, 0] * 13.605693122994
mu_rel_ev = mu_abs_ev - FERMI_ENERGY_EV
```

Gunakan nilai `FERMI_ENERGY_EV` yang sama dengan plot struktur pita dan DOS jika Anda ingin semua grafik memiliki referensi energi yang konsisten.

---

# 22. Skrip plotting sifat termoelektrik terhadap potensial kimia

Salin skrip berikut ke:

```text
scripts/plot_thermoelectric.py
```

```python
#!/usr/bin/env python3

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

CONDTENS_FILE = Path("boltztrap/mos2.condtens")

# GANTI dengan energi referensi DFT yang sama dengan plot band dan DOS.
FERMI_ENERGY_EV = 0.0

TEMPERATURES_K = [300.0, 500.0, 700.0, 900.0]
MU_WINDOW_EV = (-1.5, 1.5)

# None berarti plot sigma/tau, kappa_e/tau, dan PF/tau.
# Masukkan nilai numerik hanya jika tau diketahui atau diasumsikan.
TAU_SECONDS = None

# Normalisasi monolayer.
APPLY_2D_RESCALE = False
LZ_ANGSTROM = 20.0
D_EFFECTIVE_ANGSTROM = 6.15

OUTPUT_PNG = Path("figures/mos2_thermoelectric_vs_mu.png")
OUTPUT_PDF = Path("figures/mos2_thermoelectric_vs_mu.pdf")

RY_TO_EV = 13.605693122994


def read_condtens(filename):
    data = np.loadtxt(filename, comments="#")

    if data.ndim == 1:
        data = data.reshape(1, -1)

    if data.shape[1] < 30:
        raise RuntimeError(
            f"{filename} hanya memiliki {data.shape[1]} kolom."
        )

    return data


def in_plane_average(data, col_xx, col_yy):
    return 0.5 * (data[:, col_xx] + data[:, col_yy])


def main():
    OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)

    data = read_condtens(CONDTENS_FILE)

    mu_abs_ev = data[:, 0] * RY_TO_EV
    mu_rel_ev = mu_abs_ev - FERMI_ENERGY_EV
    temperature = data[:, 1]

    sigma_over_tau = in_plane_average(data, 3, 7)
    seebeck_v_per_k = in_plane_average(data, 12, 16)
    kappa_over_tau = in_plane_average(data, 21, 25)

    if APPLY_2D_RESCALE:
        factor = LZ_ANGSTROM / D_EFFECTIVE_ANGSTROM
        sigma_over_tau = sigma_over_tau * factor
        kappa_over_tau = kappa_over_tau * factor

    pf_over_tau = seebeck_v_per_k**2 * sigma_over_tau
    seebeck_uv_per_k = seebeck_v_per_k * 1.0e6

    if TAU_SECONDS is None:
        sigma_plot = sigma_over_tau
        kappa_plot = kappa_over_tau
        pf_plot = pf_over_tau

        sigma_ylabel = r"$\sigma_{\parallel}/\tau$ [$(\Omega\,m\,s)^{-1}$]"
        kappa_ylabel = r"$\kappa_{e,\parallel}/\tau$ [W m$^{-1}$ K$^{-1}$ s$^{-1}$]"
        pf_ylabel = r"$PF_{\parallel}/\tau$ [W m$^{-1}$ K$^{-2}$ s$^{-1}$]"
    else:
        sigma_plot = sigma_over_tau * TAU_SECONDS
        kappa_plot = kappa_over_tau * TAU_SECONDS
        pf_plot = pf_over_tau * TAU_SECONDS

        sigma_ylabel = r"$\sigma_{\parallel}$ [S m$^{-1}$]"
        kappa_ylabel = r"$\kappa_{e,\parallel}$ [W m$^{-1}$ K$^{-1}$]"
        pf_ylabel = r"$PF_{\parallel}$ [W m$^{-1}$ K$^{-2}$]"

    fig, axes = plt.subplots(
        2,
        2,
        figsize=(11.0, 8.0),
        sharex=True,
    )

    ax_s, ax_sigma, ax_kappa, ax_pf = axes.ravel()

    for target_T in TEMPERATURES_K:
        mask = np.isclose(
            temperature,
            target_T,
            rtol=0.0,
            atol=1.0e-8,
        )

        if not np.any(mask):
            print(f"T = {target_T:g} K tidak ditemukan.")
            continue

        x = mu_rel_ev[mask]
        s = seebeck_uv_per_k[mask]
        sig = sigma_plot[mask]
        kap = kappa_plot[mask]
        pf = pf_plot[mask]

        order = np.argsort(x)

        x = x[order]
        s = s[order]
        sig = sig[order]
        kap = kap[order]
        pf = pf[order]

        window = (
            (x >= MU_WINDOW_EV[0])
            &
            (x <= MU_WINDOW_EV[1])
        )

        x = x[window]
        s = s[window]
        sig = sig[window]
        kap = kap[window]
        pf = pf[window]

        label = f"{target_T:g} K"

        ax_s.plot(x, s, label=label)
        ax_sigma.plot(x, sig, label=label)
        ax_kappa.plot(x, kap, label=label)
        ax_pf.plot(x, pf, label=label)

    for ax in axes.ravel():
        ax.axvline(0.0, linewidth=0.9, linestyle="--")
        ax.set_xlim(*MU_WINDOW_EV)

    ax_s.axhline(0.0, linewidth=0.8, linestyle=":")
    ax_s.set_ylabel(r"$S_{\parallel}$ [$\mu$V/K]")
    ax_s.set_title("Koefisien Seebeck")

    ax_sigma.set_ylabel(sigma_ylabel)
    ax_sigma.set_title("Konduktivitas listrik")

    ax_kappa.set_ylabel(kappa_ylabel)
    ax_kappa.set_title("Konduktivitas termal elektronik")
    ax_kappa.set_xlabel(r"$\mu-E_F$ (eV)")

    ax_pf.set_ylabel(pf_ylabel)
    ax_pf.set_title("Power factor")
    ax_pf.set_xlabel(r"$\mu-E_F$ (eV)")

    for ax in axes.ravel():
        ax.legend(frameon=False)

    fig.suptitle(
        "Monolayer MoS$_2$: sifat termoelektrik terhadap potensial kimia"
    )
    fig.tight_layout()

    fig.savefig(OUTPUT_PNG, dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PDF, bbox_inches="tight")

    plt.show()


if __name__ == "__main__":
    main()
```

Jalankan dari root proyek:

```bash
python scripts/plot_thermoelectric.py
```

Hasil:

```text
figures/mos2_thermoelectric_vs_mu.png
figures/mos2_thermoelectric_vs_mu.pdf
```

Gambar memiliki empat panel:

```text
+-----------------------------+-----------------------------+
| Seebeck S(mu)               | sigma(mu)/tau              |
+-----------------------------+-----------------------------+
| kappa_e(mu)/tau             | PF(mu)/tau                 |
+-----------------------------+-----------------------------+
```

Setiap panel dapat memuat beberapa temperatur.

---

# 23. Interpretasi sumbu \(\mu-E_F\)

Pada plot termoelektrik:

$$
\mu-E_F=0
$$

berarti potensial kimia sama dengan energi referensi Fermi yang dipilih.

Untuk semikonduktor intrinsik dengan referensi titik tengah gap:

- \(\mu-E_F<0\) bergerak menuju pita valensi,
- \(\mu-E_F>0\) bergerak menuju pita konduksi.

Secara kualitatif:

```text
pita valensi              gap                 pita konduksi

       p-type                                      n-type
<---------------------------------------------------------->

                     mu - E_F = 0
```

Namun, hubungan antara \(\mu\) dan konsentrasi pembawa bergantung pada temperatur dan DOS.

Untuk analisis doping kuantitatif, gunakan `btp2 dope`.

---

# 24. Koefisien Seebeck

Skrip memplot:

$$
S_{\parallel}
=
\frac{S_{xx}+S_{yy}}{2}.
$$

BoltzTraP2 memberikan \(S\) dalam V/K.

Skrip mengubahnya menjadi:

$$
\mu{\rm V/K}
$$

melalui:

$$
S_{\mu{\rm V/K}}
=
10^6S_{\rm V/K}.
$$

Nilai positif biasanya berkaitan dengan hole-like transport dan nilai negatif biasanya berkaitan dengan electron-like transport.

---

# 25. Konduktivitas listrik

Dalam constant relaxation-time approximation, BoltzTraP2 menghasilkan:

$$
\frac{\sigma}{\tau}.
$$

Untuk monolayer:

$$
\frac{\sigma_{\parallel}}{\tau}
=
\frac{1}{2}
\left(
\frac{\sigma_{xx}}{\tau}
+
\frac{\sigma_{yy}}{\tau}
\right).
$$

Jika waktu relaksasi diketahui:

$$
\sigma_{\parallel}
=
\left(
\frac{\sigma_{\parallel}}{\tau}
\right)\tau.
$$

Pada skrip:

```python
TAU_SECONDS = None
```

berarti hasil diplot sebagai \(\sigma/\tau\).

Jika ada dasar fisik untuk:

```python
TAU_SECONDS = 1.0e-14
```

maka skrip akan memplot \(\sigma\).

Jangan menggunakan nilai \(\tau\) tanpa menjelaskan asalnya.

---

# 26. Konduktivitas termal elektronik

BoltzTraP2 menghasilkan:

$$
\frac{\kappa_e}{\tau}.
$$

Untuk monolayer:

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

Jika \(\tau\) diketahui:

$$
\kappa_{e,\parallel}
=
\left(
\frac{\kappa_{e,\parallel}}{\tau}
\right)\tau.
$$

---

# 27. Power factor

Power factor adalah:

$$
PF_{\parallel}
=
S_{\parallel}^2\sigma_{\parallel}.
$$

Jika \(\tau\) belum diketahui:

$$
\frac{PF_{\parallel}}{\tau}
=
S_{\parallel}^2
\frac{\sigma_{\parallel}}{\tau}.
$$

Skrip menghitung power factor langsung dari Seebeck dan konduktivitas in-plane.

---

# 28. Masalah normalisasi untuk material 2D

Bagian ini sangat penting untuk monolayer.

Quantum ESPRESSO dan BoltzTraP2 menggunakan sel periodik tiga dimensi.

Volume supercell adalah:

$$
V_{\rm cell}
=
A L_z.
$$

Karena \(L_z\) mengandung vakum, besaran volumetrik seperti:

$$
\sigma,
\qquad
\frac{\sigma}{\tau},
\qquad
\kappa_e,
\qquad
\frac{\kappa_e}{\tau},
\qquad
PF
$$

bergantung pada nilai \(L_z\) jika langsung dilaporkan dalam satuan 3D.

Koefisien Seebeck tidak mengalami masalah normalisasi yang sama.

Jika digunakan ketebalan efektif \(d_{\rm eff}\), besaran volumetrik dapat dikoreksi dengan:

$$
X_{\rm corrected}
=
X_{\rm supercell}
\frac{L_z}{d_{\rm eff}},
$$

untuk:

$$
X
=
\sigma,\,
\kappa_e,\,
PF.
$$

Skrip menyediakan:

```python
APPLY_2D_RESCALE = False
LZ_ANGSTROM = 20.0
D_EFFECTIVE_ANGSTROM = 6.15
```

Jika diubah menjadi:

```python
APPLY_2D_RESCALE = True
```

skrip mengalikan:

$$
\frac{L_z}{d_{\rm eff}}.
$$

Nilai:

```text
d_eff = 6.15 Angstrom
```

dalam skrip hanya contoh konvensi berbasis skala jarak ulang antarlapis bulk.

Nilai tersebut bukan ketebalan unik yang diwajibkan oleh teori.

Untuk publikasi, nyatakan dengan jelas:

1. nilai \(L_z\),
2. nilai \(d_{\rm eff}\),
3. apakah hasil dilaporkan sebagai besaran supercell 3D, besaran yang dinormalisasi terhadap ketebalan efektif, atau sheet quantity.

---

# 29. Menggunakan `btp2 dope`

Untuk sifat sebagai fungsi konsentrasi pembawa:

```bash
cd boltztrap
```

Jalankan:

```bash
btp2 -vv -n 2 dope \
    mos2.bt2 \
    300:901:100 \
    '1e18,1e19,1e20,-1e18,-1e19,-1e20'
```

BoltzTraP2 menerima doping dalam:

$$
{\rm cm^{-3}}.
$$

Untuk monolayer, satuan volumetrik ini juga bergantung pada definisi volume supercell.

Karena itu, untuk studi 2D sebaiknya pertimbangkan konversi ke sheet carrier density:

$$
n_{2D}
=
n_{3D}d_{\rm eff}
$$

atau gunakan konvensi volume yang dijelaskan secara eksplisit.

---

# 30. Uji konvergensi yang perlu dilakukan

## 30.1 Cutoff

Uji, misalnya:

```text
ecutwfc = 50 Ry
ecutwfc = 60 Ry
ecutwfc = 70 Ry
ecutwfc = 80 Ry
```

Periksa:

- energi total,
- parameter struktur,
- direct gap di \(K\),
- kelengkungan pita dekat VBM dan CBM.

Transport sensitif terhadap kelengkungan pita.

---

## 30.2 Vakum

Uji:

```text
Lz = 15 Angstrom
Lz = 20 Angstrom
Lz = 25 Angstrom
```

Direct band gap dan dispersi in-plane seharusnya stabil setelah interaksi antarcitra periodik cukup kecil.

Perlu diingat bahwa konduktivitas volumetrik mentah akan berubah dengan \(L_z\) karena definisi volume.

---

## 30.3 Mesh SCF

Uji:

```text
8 x 8 x 1
12 x 12 x 1
16 x 16 x 1
```

---

## 30.4 Mesh NSCF transport

Uji:

```text
18 x 18 x 1
24 x 24 x 1
30 x 30 x 1
36 x 36 x 1
```

Bandingkan:

$$
S(\mu,T),
$$

$$
\sigma(\mu,T)/\tau,
$$

$$
\kappa_e(\mu,T)/\tau,
$$

dan

$$
PF(\mu,T)/\tau.
$$

---

## 30.5 Jumlah pita

Uji:

```text
nbnd = 32
nbnd = 40
nbnd = 48
```

Pastikan jendela energi BoltzTraP2 berada di dalam rentang pita yang benar-benar dihitung.

---

## 30.6 Interpolasi BoltzTraP2

Bandingkan:

```bash
-m 3
-m 5
-m 7
```

Kurva transport seharusnya tidak berubah secara berarti setelah interpolasi cukup rapat.

---

# 31. Strategi praktis untuk hanya dua CPU

Tahap debugging:

```text
SCF              8 x 8 x 1
NSCF            12 x 12 x 1
nbnd            28-32
```

Tahap pendahuluan:

```text
SCF             12 x 12 x 1
NSCF            18 x 18 x 1
nbnd            36-40
```

Tahap produksi:

```text
SCF             12-16 x 12-16 x 1
NSCF            24 x 24 x 1 atau lebih rapat
nbnd            40 atau lebih
```

Semua QE:

```bash
mpirun -np 2 ...
```

Semua BoltzTraP2 yang mendukung worker:

```bash
btp2 -n 2 ...
```

---

# 32. Urutan perintah lengkap

Dari root proyek:

```bash
cd ~/calculations/mos2_monolayer_thermoelectric

export OMP_NUM_THREADS=1
```

SCF:

```bash
mpirun -np 2 pw.x \
    -in input/01_scf.in \
    > output/01_scf.out
```

Bands:

```bash
mpirun -np 2 pw.x \
    -in input/02_nscf_bands.in \
    > output/02_nscf_bands.out
```

Post-processing bands:

```bash
mpirun -np 2 bands.x \
    -in input/03_bands_pp.in \
    > output/03_bands_pp.out
```

NSCF rapat:

```bash
mpirun -np 2 pw.x \
    -in input/04_nscf_dos.in \
    > output/04_nscf_dos.out
```

DOS:

```bash
mpirun -np 2 dos.x \
    -in input/05_dos.in \
    > output/05_dos.out
```

Cari energi referensi:

```bash
grep -Ei "fermi|highest occupied|lowest unoccupied" output/*.out
```

Edit:

```text
scripts/plot_band_dos.py
```

dan isi:

```python
FERMI_ENERGY_EV = <nilai_dari_QE>
```

Plot struktur pita dan DOS:

```bash
python scripts/plot_band_dos.py
```

Siapkan XML:

```bash
mkdir -p boltztrap/qe_data

cp tmp/mos2.save/data-file-schema.xml \
   boltztrap/qe_data/
```

Interpolasi:

```bash
cd boltztrap

btp2 -vv -n 2 interpolate \
    -m 5 \
    -e -0.15 \
    -E 0.15 \
    -o mos2.bt2 \
    ./qe_data
```

Integrasi:

```bash
btp2 -vv -n 2 integrate \
    mos2.bt2 \
    300:1001:100
```

Kembali ke root:

```bash
cd ..
```

Edit:

```text
scripts/plot_thermoelectric.py
```

dan gunakan nilai referensi yang sama:

```python
FERMI_ENERGY_EV = <nilai_dari_QE>
```

Plot:

```bash
python scripts/plot_thermoelectric.py
```

---

# 33. Organisasi file akhir

```text
mos2_monolayer_thermoelectric/
│
├── pseudo/
│   ├── Mo.pbe-spn-kjpaw_psl.1.0.0.UPF
│   └── S.pbe-n-kjpaw_psl.1.0.0.UPF
│
├── input/
│   ├── 01_scf.in
│   ├── 02_nscf_bands.in
│   ├── 03_bands_pp.in
│   ├── 04_nscf_dos.in
│   └── 05_dos.in
│
├── output/
│   ├── 01_scf.out
│   ├── 02_nscf_bands.out
│   ├── 03_bands_pp.out
│   ├── 04_nscf_dos.out
│   └── 05_dos.out
│
├── tmp/
│   └── mos2.save/
│
├── bands/
│   ├── mos2.bands.dat
│   └── mos2.bands.dat.gnu
│
├── dos/
│   └── mos2.dos
│
├── scripts/
│   ├── plot_band_dos.py
│   └── plot_thermoelectric.py
│
├── figures/
│   ├── mos2_band_dos.png
│   ├── mos2_band_dos.pdf
│   ├── mos2_thermoelectric_vs_mu.png
│   └── mos2_thermoelectric_vs_mu.pdf
│
└── boltztrap/
    ├── qe_data/
    │   └── data-file-schema.xml
    ├── mos2.bt2
    ├── mos2.btj
    ├── mos2.trace
    ├── mos2.condtens
    └── mos2.halltens
```

---

# 34. Pemeriksaan hasil yang disarankan

Sebelum menafsirkan sifat termoelektrik, pastikan semua hal berikut terpenuhi.

### Struktur elektronik

Periksa bahwa:

$$
{\rm VBM}
$$

dan

$$
{\rm CBM}
$$

berada pada titik \(K\).

Kemudian:

$$
E_g
=
E_{\rm CBM}(K)-E_{\rm VBM}(K).
$$

### DOS

Pastikan DOS memiliki gap yang konsisten dengan struktur pita.

### Fermi reference

Pastikan struktur pita dan DOS menggunakan:

```python
FERMI_ENERGY_EV
```

yang sama.

### Transport

Pastikan plotting transport menggunakan referensi energi yang sama jika sumbu ingin dibandingkan langsung dengan struktur elektronik.

### Konvergensi

Pastikan hasil stabil terhadap:

- mesh titik-k,
- `nbnd`,
- multiplier interpolasi BoltzTraP2,
- cutoff,
- vakum.

### Normalisasi 2D

Jangan membandingkan nilai \(\sigma\), \(\kappa_e\), dan \(PF\) monolayer dari dua perhitungan yang menggunakan tinggi vakum berbeda tanpa melakukan normalisasi yang konsisten.

---

# 35. Ringkasan

Untuk monolayer MoS₂, alur kerja yang direkomendasikan adalah:

```text
SCF
 |
 v
Gamma-M-K-Gamma bands
 |
 v
bands.x
 |
 +----------------------+
 |                      |
 v                      v
band structure       dense NSCF
                        |
                 +------+------+
                 |             |
                 v             v
                DOS        BoltzTraP2
                 |             |
                 v             v
             dos.x        interpolate
                 |             |
                 +----+        v
                      |     integrate
                      |        |
                      v        v
            plot band + DOS  condtens
                               |
                               v
                       plot transport:
                       S(mu)
                       sigma(mu)/tau
                       kappa_e(mu)/tau
                       PF(mu)/tau
```

Untuk monolayer MoS₂, tiga hal perlu mendapat perhatian khusus:

1. **Direct gap harus diperiksa pada titik K**, bukan sekadar diasumsikan.
2. **Semua plot energi sebaiknya menggunakan referensi \(E_F=0\) yang konsisten**, dengan nilai referensi dimasukkan secara eksplisit ke variabel `FERMI_ENERGY_EV` pada skrip Python.
3. **Konduktivitas listrik, konduktivitas termal elektronik, dan power factor pada material 2D memerlukan perhatian terhadap normalisasi ketebalan**, karena BoltzTraP2 menggunakan volume supercell yang mencakup vakum.

Dengan alur ini, struktur elektronik dan sifat termoelektrik dapat dibandingkan pada satu sumbu energi yang konsisten, sehingga hubungan antara tepi pita, DOS, potensial kimia, koefisien Seebeck, konduktivitas, dan power factor menjadi jauh lebih mudah dianalisis.
