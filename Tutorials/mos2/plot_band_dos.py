#!/usr/bin/env python3

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# USER SETTINGS
# ============================================================

BAND_FILE = Path("mos2.bands.dat.gnu")
DOS_FILE = Path("mos2.dos")

# Replace this number with the Fermi energy or reference energy
# obtained from your Quantum ESPRESSO outputs, in eV.
#
# Search with, for example:
#
# grep -Ei "fermi|highest occupied|lowest unoccupied" \
#     mos2.scf.out mos2.nscfbands.out mos2.nscf.out
#
# For a fixed-occupation semiconductor, a convenient intrinsic
# reference is:
#
# E_F = (E_VBM + E_CBM) / 2
#
FERMI_ENERGY_EV = 0.0

# For the pseudopotentials used in this tutorial, the monolayer
# normally has 26 valence electrons. In a non-spin-polarized
# calculation this corresponds to 13 occupied bands.
N_OCCUPIED_BANDS = 13

# Gamma -> M -> K -> Gamma, with 40 intervals per segment.
HIGH_SYMMETRY_INDICES = [0, 40, 80, -1]
HIGH_SYMMETRY_LABELS = [r"$\Gamma$", "M", "K", r"$\Gamma$"]

ENERGY_WINDOW_EV = (-4.0, 4.0)

OUTPUT_PNG = Path("figures/mos2_band_dos.png")
OUTPUT_PDF = Path("figures/mos2_band_dos.pdf")


def read_qe_gnu_bands(filename):
    """Read a *.gnu band file produced by Quantum ESPRESSO bands.x."""
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
        raise RuntimeError(f"No band data could be read from {filename}")

    nk = min(len(block) for block in blocks)

    if any(len(block) != nk for block in blocks):
        print(
            "WARNING: some band blocks have different lengths. "
            f"All blocks will be truncated to nk = {nk}."
        )

    kdist = blocks[0][:nk, 0]
    energies = np.vstack([block[:nk, 1] for block in blocks])

    return kdist, energies


def resolve_indices(indices, nk):
    resolved = []

    for i in indices:
        j = nk + i if i < 0 else i

        if j < 0 or j >= nk:
            raise IndexError(
                f"High-symmetry index {i} is invalid for nk = {nk}."
            )

        resolved.append(j)

    return resolved


def main():
    if not BAND_FILE.exists():
        raise FileNotFoundError(
            f"{BAND_FILE} was not found. Run bands.x first."
        )

    if not DOS_FILE.exists():
        raise FileNotFoundError(
            f"{DOS_FILE} was not found. Run dos.x first."
        )

    OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)

    kdist, bands_ev = read_qe_gnu_bands(BAND_FILE)
    bands_shifted = bands_ev - FERMI_ENERGY_EV

    nk = len(kdist)
    hs_indices = resolve_indices(HIGH_SYMMETRY_INDICES, nk)
    hs_positions = [kdist[i] for i in hs_indices]

    nbands = bands_ev.shape[0]

    print(f"Number of k points on the path = {nk}")
    print(f"Number of bands read           = {nbands}")
    print(f"Reference E_F                  = {FERMI_ENERGY_EV:.8f} eV")

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

        print()
        print("Band-edge check:")
        print(f"VBM = {vbm:.8f} eV at k-index {ivbm}")
        print(f"CBM = {cbm:.8f} eV at k-index {icbm}")
        print(f"Global gap      = {gap_global:.8f} eV")
        print(f"Direct gap at K = {direct_gap_k:.8f} eV")
        print(
            "If the VBM and CBM indices both coincide with K, "
            "the calculated band structure shows a direct gap at K."
        )

    dos_data = np.loadtxt(DOS_FILE, comments="#")

    if dos_data.ndim == 1:
        dos_data = dos_data.reshape(1, -1)

    if dos_data.shape[1] < 2:
        raise RuntimeError(
            "The DOS file must contain at least energy and DOS columns."
        )

    dos_energy = dos_data[:, 0] - FERMI_ENERGY_EV
    dos_value = dos_data[:, 1]

    fig, (ax_band, ax_dos) = plt.subplots(
        1,
        2,
        figsize=(9.0, 6.0),
        sharey=True,
        gridspec_kw={"width_ratios": [2.4, 1.0], "wspace": 0.08},
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
    ax_band.set_xlabel("k-point path")
    ax_band.set_title("Electronic band structure")

    ax_dos.plot(dos_value, dos_energy, linewidth=1.2)
    ax_dos.axhline(0.0, linewidth=0.9, linestyle="--")
    ax_dos.set_xlabel("DOS (states/eV)")
    ax_dos.set_title("DOS")
    ax_dos.tick_params(axis="y", labelleft=False)

    fig.suptitle("Monolayer MoS$_2$")
    fig.tight_layout()

    fig.savefig(OUTPUT_PNG, dpi=300, bbox_inches="tight")
    fig.savefig(OUTPUT_PDF, bbox_inches="tight")

    print()
    print(f"PNG figure written to: {OUTPUT_PNG}")
    print(f"PDF figure written to: {OUTPUT_PDF}")

    plt.show()


if __name__ == "__main__":
    main()
