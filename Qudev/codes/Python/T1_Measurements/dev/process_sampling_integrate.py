import os
import random
import re

import numpy as np
import pandas as pd

try:
    from scipy.optimize import curve_fit
except ModuleNotFoundError:
    curve_fit = None


# =====================================================
# USER SETTINGS
# =====================================================
directory_to_scan = "."

list_readout_window = [1000e-9]
list_read_start = [300e-9]

# Used only if tau cannot be read from the filename.
tau_minimum = 2
tau_maximum = 5000
n_tau = 40
tau_fallback = np.geomspace(tau_minimum, tau_maximum, n_tau)

# Random sampling settings.
n_random_reps_default = 20
random_seed = 42
replace = False

# Set False if you only want integrated signal files without fitting.
do_fit = True


# =====================================================
# INPUT HELPERS
# =====================================================
def ask_text(prompt, default=None):
    if default is None:
        value = input(f"{prompt}: ").strip()
        return value

    value = input(f"{prompt} [{default}]: ").strip()
    return value if value else str(default)


def ask_int(prompt, default=None):
    while True:
        value = ask_text(prompt, default)
        try:
            return int(value)
        except ValueError:
            print("Please enter an integer.")


# =====================================================
# FILE AND FOLDER HELPERS
# =====================================================
def sanitize_name(name):
    name = str(name).strip()
    name = re.sub(r"[^\w.-]+", "_", name)
    return name.strip("_") or "dataset"


def is_output_folder(name):
    output_prefixes = (
        "averaged_results",
        "integrated_results",
        "processed_regular_integrated",
        "processed_random_integrated",
        "random_mixed",
        "integrated_random",
    )
    return name.startswith(output_prefixes)


def folder_contains_rep_folders(folder):
    if not os.path.isdir(folder):
        return False

    return any(
        os.path.isdir(os.path.join(folder, name)) and name.startswith("rep_")
        for name in os.listdir(folder)
    )


def list_acquisition_folders(directory_path):
    """
    Find folders that directly contain rep_X folders.
    If the current directory itself contains rep_X folders, it is processed too.
    """
    acquisition_folders = []

    if folder_contains_rep_folders(directory_path):
        acquisition_folders.append(directory_path)

    for name in os.listdir(directory_path):
        full_path = os.path.join(directory_path, name)

        if not os.path.isdir(full_path):
            continue
        if name.startswith(".") or is_output_folder(name):
            continue
        if folder_contains_rep_folders(full_path):
            acquisition_folders.append(full_path)

    return sorted(set(acquisition_folders), key=lambda path: os.path.abspath(path))


def list_rep_folders(acquisition_folder):
    return sorted(
        [
            os.path.join(acquisition_folder, name)
            for name in os.listdir(acquisition_folder)
            if os.path.isdir(os.path.join(acquisition_folder, name))
            and name.startswith("rep_")
        ],
        key=lambda path: int(os.path.basename(path).split("_")[1]),
    )


def extract_tau_us(filename, fallback=np.nan):
    """
    Extract tau in microseconds.
    Works for names such as tau_2us_0.csv and tau_x_100uS_0.csv.
    """
    match = re.search(r"tau.*?([0-9]+(?:\.[0-9]+)?)\s*(?:uS|us)", filename)
    if match:
        return float(match.group(1))
    return fallback


def tau_sort_key(filename):
    tau_value = extract_tau_us(filename, fallback=np.inf)
    index_match = re.search(r"_([0-9]+)\.csv$", filename)
    tau_index = int(index_match.group(1)) if index_match else np.inf
    return tau_value, tau_index, filename


def list_tau_files(rep_folder):
    return sorted(
        [f for f in os.listdir(rep_folder) if f.startswith("tau_") and f.endswith(".csv")],
        key=tau_sort_key,
    )


def get_tau_reference(rep_folders):
    for rep_folder in rep_folders:
        tau_files = list_tau_files(rep_folder)
        if tau_files:
            return tau_files

    raise FileNotFoundError("No tau CSV files were found in any rep_X folder.")


def get_column(df, possible_names):
    normalized = {str(col).strip().lower(): col for col in df.columns}

    for name in possible_names:
        key = name.strip().lower()
        if key in normalized:
            return normalized[key]

    raise KeyError(f"None of these columns were found: {possible_names}")


# =====================================================
# SIGNAL PROCESSING
# =====================================================
def integrate_one_waveform(file_path, read_start, readout_window):
    df = pd.read_csv(file_path)

    time_col = get_column(df, ["Time (s)", "Time"])
    voltage_col = get_column(df, ["Voltage (V)", "Voltage"])

    read_end = read_start + readout_window
    reading = df[(df[time_col] >= read_start) & (df[time_col] < read_end)]

    if len(reading) < 2:
        raise ValueError(
            f"Not enough points inside {read_start:g} to {read_end:g} s for {file_path}"
        )

    return np.trapezoid(reading[voltage_col], reading[time_col])


def calculate_r2(y_exp, y_fit):
    ss_res = np.sum((y_exp - y_fit) ** 2)
    ss_tot = np.sum((y_exp - np.mean(y_exp)) ** 2)
    return np.nan if ss_tot == 0 else 1 - ss_res / ss_tot


def exp_decay(t, I0, A, T1):
    return I0 * (1 + A * np.exp(-t / T1))


def safe_sigma(values):
    sigma = np.asarray(values, dtype=float)
    valid = np.isfinite(sigma) & (sigma > 0)

    if np.any(valid):
        fallback = np.nanmedian(sigma[valid])
    else:
        fallback = 1.0

    sigma[~valid] = fallback
    return sigma


def fit_integrated_signal(df_summary):
    if curve_fit is None:
        return None, None, {
            "Fit Status": "Skipped: scipy is not installed",
            "I0": np.nan,
            "A": np.nan,
            "T1 (s)": np.nan,
            "T1 error (s)": np.nan,
            "R2": np.nan,
        }

    df_fit = df_summary.sort_values("Tau (us)").reset_index(drop=True).copy()

    tau_us = df_fit["Tau (us)"].to_numpy(dtype=float)
    signal = df_fit["Signal"].to_numpy(dtype=float)
    signal_err = safe_sigma(df_fit["Signal Error"].to_numpy(dtype=float))
    t = tau_us * 1e-6

    I0_guess = signal[-1]
    A_guess = (signal[0] / signal[-1]) - 1 if signal[-1] != 0 else 1.0
    T1_guess = np.median(t)

    try:
        params, cov = curve_fit(
            exp_decay,
            t,
            signal,
            p0=[I0_guess, A_guess, T1_guess],
            sigma=signal_err,
            absolute_sigma=True,
            bounds=([0, -np.inf, 0], [np.inf, np.inf, np.inf]),
            maxfev=20000,
        )

        I0, A, T1 = params
        T1_err = np.sqrt(np.diag(cov))[2]
        y_fit = exp_decay(t, *params)
        r2 = calculate_r2(signal, y_fit)

        df_fit["Signal Fitted"] = y_fit
        df_fit["Fit Residual"] = signal - y_fit
        df_fit["Sigma Used"] = signal_err

        fit_summary = {
            "Fit Status": "Success",
            "I0": I0,
            "A": A,
            "T1 (s)": T1,
            "T1 error (s)": T1_err,
            "R2": r2,
        }

        return df_fit, pd.DataFrame([fit_summary]), fit_summary

    except RuntimeError:
        fit_summary = {
            "Fit Status": "Fit failed",
            "I0": np.nan,
            "A": np.nan,
            "T1 (s)": np.nan,
            "T1 error (s)": np.nan,
            "R2": np.nan,
        }
        return df_fit, pd.DataFrame([fit_summary]), fit_summary


def process_rep_set(dataset_name, rep_folders, output_dir, read_start, readout_window):
    """
    For every tau:
    1. integrate each raw waveform -> S1, S2, ..., SN
    2. Signal = mean(S1...SN)
    3. Signal Error = std(S1...SN) / sqrt(N)
    """
    os.makedirs(output_dir, exist_ok=True)

    tau_files_ref = get_tau_reference(rep_folders)
    summary_rows = []
    repetition_rows = []

    for tau_idx, tau_file in enumerate(tau_files_ref):
        integrated_values = []
        used_reps = []

        tau_us = extract_tau_us(
            tau_file,
            fallback=tau_fallback[tau_idx] if tau_idx < len(tau_fallback) else np.nan,
        )

        for rep_folder in rep_folders:
            file_path = os.path.join(rep_folder, tau_file)

            if not os.path.exists(file_path):
                print(f"Warning: {file_path} not found, skipping.")
                continue

            try:
                signal_int = integrate_one_waveform(file_path, read_start, readout_window)
            except (ValueError, KeyError) as exc:
                print(f"Warning: {exc}")
                continue

            integrated_values.append(signal_int)
            used_reps.append(rep_folder)

            repetition_rows.append(
                {
                    "Dataset": dataset_name,
                    "Tau File": tau_file,
                    "Tau (us)": tau_us,
                    "Rep Path": rep_folder,
                    "Integrated Signal": signal_int,
                }
            )

        if not integrated_values:
            print(f"Warning: no usable data found for {dataset_name} | {tau_file}")
            continue

        values = np.asarray(integrated_values, dtype=float)
        signal_mean = np.mean(values)
        signal_std = np.std(values, ddof=1) if len(values) > 1 else 0.0
        signal_sem = signal_std / np.sqrt(len(values)) if len(values) > 1 else 0.0

        summary_rows.append(
            {
                "Dataset": dataset_name,
                "Tau File": tau_file,
                "Tau (us)": tau_us,
                "Signal": signal_mean,
                "Signal Error": signal_sem,
                "Signal STD": signal_std,
                "Signal SEM": signal_sem,
                "N": len(values),
                "Used Reps": ", ".join(used_reps),
            }
        )

    df_summary = pd.DataFrame(summary_rows)
    df_repetitions = pd.DataFrame(repetition_rows)

    if df_summary.empty:
        raise ValueError(f"No integrated data were produced for dataset: {dataset_name}")

    df_fit = None
    df_fit_summary = None
    fit_summary = {}

    if do_fit:
        df_fit, df_fit_summary, fit_summary = fit_integrated_signal(df_summary)

    width_ns = readout_window * 1e9
    start_ns = read_start * 1e9
    safe_dataset_name = sanitize_name(dataset_name)
    base_name = f"{safe_dataset_name}_width{width_ns:.0f}ns_start{start_ns:.0f}ns"

    excel_path = os.path.join(output_dir, f"{base_name}.xlsx")
    csv_path = os.path.join(output_dir, f"{base_name}_summary.csv")

    df_summary.to_csv(csv_path, index=False)

    with pd.ExcelWriter(excel_path) as writer:
        df_summary.to_excel(writer, sheet_name="summary", index=False)
        df_repetitions.to_excel(writer, sheet_name="per_repetition", index=False)

        if do_fit and df_fit is not None:
            df_fit.to_excel(writer, sheet_name="fit_data", index=False)
            df_fit_summary.to_excel(writer, sheet_name="fit_summary", index=False)

    result = {
        "Dataset": dataset_name,
        "N Tau": len(df_summary),
        "Window width (ns)": width_ns,
        "Read start (ns)": start_ns,
        "Output Excel": excel_path,
        "Output CSV": csv_path,
    }
    result.update(fit_summary)

    print(f"Saved: {excel_path}")
    return result


# =====================================================
# SAMPLING MODES
# =====================================================
def run_regular(acquisition_folders):
    output_dir = os.path.join(directory_to_scan, "processed_regular_integrated")
    all_results = []

    for acquisition_folder in acquisition_folders:
        dataset_name = os.path.basename(os.path.abspath(acquisition_folder))
        if acquisition_folder == directory_to_scan:
            dataset_name = "regular"

        rep_folders = list_rep_folders(acquisition_folder)
        print(f"\n=== Processing regular dataset: {dataset_name} ({len(rep_folders)} reps) ===")

        for width in list_readout_window:
            for start in list_read_start:
                result = process_rep_set(dataset_name, rep_folders, output_dir, start, width)
                all_results.append(result)

    save_run_summary(all_results, output_dir, "regular_run_summary.xlsx")


def run_random(acquisition_folders):
    n_combinations = ask_int("How many random combinations do you want?")
    n_random_reps = ask_int(
        "How many rep folders should be used in each combination?",
        default=n_random_reps_default,
    )

    if random_seed is not None:
        random.seed(random_seed)
        np.random.seed(random_seed)

    all_rep_folders = []
    for acquisition_folder in acquisition_folders:
        all_rep_folders.extend(list_rep_folders(acquisition_folder))

    if not all_rep_folders:
        raise FileNotFoundError("No rep_X folders were found.")

    if not replace and len(all_rep_folders) < n_random_reps:
        raise ValueError(
            f"Only {len(all_rep_folders)} rep folders were found, but "
            f"{n_random_reps} are required when replace=False."
        )

    output_dir = os.path.join(
        directory_to_scan,
        f"processed_random_integrated_{n_combinations}_comb",
    )
    os.makedirs(output_dir, exist_ok=True)

    all_results = []
    selected_rows = []

    for combo_idx in range(1, n_combinations + 1):
        selected_reps = list(
            np.random.choice(all_rep_folders, size=n_random_reps, replace=replace)
        )

        dataset_name = f"random_combination_{combo_idx:02d}"
        print(
            f"\n=== Processing {dataset_name}: "
            f"{len(selected_reps)} mixed reps from {len(all_rep_folders)} total reps ==="
        )

        for rep_folder in selected_reps:
            selected_rows.append(
                {
                    "Dataset": dataset_name,
                    "Acquisition": os.path.basename(os.path.dirname(rep_folder)),
                    "Rep": os.path.basename(rep_folder),
                    "Rep Path": rep_folder,
                }
            )

        for width in list_readout_window:
            for start in list_read_start:
                result = process_rep_set(dataset_name, selected_reps, output_dir, start, width)
                all_results.append(result)

    pd.DataFrame(selected_rows).to_excel(
        os.path.join(output_dir, "selected_repetitions_summary.xlsx"),
        index=False,
    )
    save_run_summary(all_results, output_dir, "random_run_summary.xlsx")


def save_run_summary(all_results, output_dir, filename):
    if not all_results:
        return

    summary_path = os.path.join(output_dir, filename)
    pd.DataFrame(all_results).to_excel(summary_path, index=False)
    print(f"\nSummary saved: {summary_path}")


# =====================================================
# MAIN
# =====================================================
def main():
    sampling_method = ask_text("Choose sampling method (regular/random)").lower()
    if sampling_method not in ["regular", "random"]:
        raise ValueError("Sampling method must be 'regular' or 'random'.")

    acquisition_folders = list_acquisition_folders(directory_to_scan)
    if not acquisition_folders:
        raise FileNotFoundError(
            "No folders containing rep_X folders were found. "
            "Run this script from the parent folder of your acquisitions."
        )

    print("\nFound folders containing rep_X folders:")
    for folder in acquisition_folders:
        print(f"  - {folder}")

    if do_fit and curve_fit is None:
        print("\nSciPy is not installed, so fitting will be skipped.")

    if sampling_method == "regular":
        run_regular(acquisition_folders)
    else:
        run_random(acquisition_folders)

    print("\n=== Finished ===")


if __name__ == "__main__":
    main()
