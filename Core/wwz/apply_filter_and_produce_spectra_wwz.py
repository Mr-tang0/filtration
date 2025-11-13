# ============================================================
#  Confidential
#  File: apply_filter_and_plot.py
#  (c) 2025 Weizheng Wang. All rights reserved.
#
#  This source code is proprietary and confidential.
#  Unauthorized copying, distribution, or modification is strictly prohibited.
# ============================================================

import numpy as np
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('TkAgg')
import pandas as pd
from pathlib import Path
from scipy.interpolate import interp1d

# =========================
# 0) Basic settings
# =========================
SPECTRUM_PATH = Path("2MeV.txt")  # Input spectrum file with two columns: E[MeV], counts
OUTPUT_PREFIX = "2MeV_filtered"  # Output filename prefix

# Define the filter stack (can be multi-layer), thickness in mm
# Example: 1 mm Tungsten
filter_stack = [("W", 1.0)]  # e.g., [("Al", 2.0), ("Cu", 0.5), ("W", 1.0)]

# =========================
# 1) Load spectrum
# =========================
spec = np.loadtxt(SPECTRUM_PATH)
E_mev = spec[:, 0].astype(float)  # MeV
counts_in = spec[:, 1].astype(float)  # Relative or absolute photon counts
counts_in[counts_in < 0] = 0.0  # Clamp negative values
E_keV = E_mev * 1000.0

print("-" * 50)
print(f"Spectrum loaded from: {SPECTRUM_PATH}")
print(f"Energy bins (MeV): shape={E_mev.shape}, range=[{E_mev.min():.6g}, {E_mev.max():.6g}]")
print(f"Counts: shape={counts_in.shape}, total={counts_in.sum():.6e}")
print("-" * 50)

# =========================
# 2) Mass attenuation data and material library (W included)
# =========================
# Columns: [E(MeV), mu_over_rho(cm^2/g), (unused third column kept from source)]
tungsten_data = np.array([
    [1.00000E-03, 3.683E+03, 3.671E+03],
    [1.50000E-03, 1.643E+03, 1.632E+03],
    [1.80920E-03, 1.108E+03, 1.097E+03],
    [1.80920E-03, 1.327E+03, 1.311E+03],
    [1.84014E-03, 1.911E+03, 1.883E+03],
    [1.87160E-03, 2.901E+03, 2.853E+03],
    [1.87160E-03, 3.170E+03, 3.116E+03],
    [2.00000E-03, 3.922E+03, 3.853E+03],
    [2.28100E-03, 2.828E+03, 2.781E+03],
    [2.28100E-03, 3.279E+03, 3.226E+03],
    [2.42350E-03, 2.833E+03, 2.786E+03],
    [2.57490E-03, 2.445E+03, 2.407E+03],
    [2.57490E-03, 2.599E+03, 2.558E+03],
    [2.69447E-03, 2.339E+03, 2.301E+03],
    [2.81960E-03, 2.104E+03, 2.071E+03],
    [2.81960E-03, 2.194E+03, 2.160E+03],
    [3.00000E-03, 1.902E+03, 1.873E+03],
    [4.00000E-03, 9.564E+02, 9.405E+02],
    [5.00000E-03, 5.534E+02, 5.423E+02],
    [6.00000E-03, 3.514E+02, 3.428E+02],
    [8.00000E-03, 1.705E+02, 1.643E+02],
    [1.00000E-02, 9.691E+01, 9.204E+01],
    [1.02068E-02, 9.201E+01, 8.724E+01],
    [1.02068E-02, 2.334E+02, 1.966E+02],
    [1.08548E-02, 1.983E+02, 1.684E+02],
    [1.15440E-02, 1.689E+02, 1.444E+02],
    [1.15440E-02, 2.312E+02, 1.889E+02],
    [1.18186E-02, 2.268E+02, 1.797E+02],
    [1.20998E-02, 2.065E+02, 1.699E+02],
    [1.20998E-02, 2.382E+02, 1.948E+02],
    [1.50000E-02, 1.389E+02, 1.172E+02],
    [2.00000E-02, 6.573E+01, 5.697E+01],
    [3.00000E-02, 2.273E+01, 1.991E+01],
    [4.00000E-02, 1.067E+01, 9.240E+00],
    [5.00000E-02, 5.949E+00, 5.050E+00],
    [6.00000E-02, 3.713E+00, 3.070E+00],
    [6.95250E-02, 2.552E+00, 2.049E+00],
    [6.95250E-02, 1.123E+01, 3.212E+00],
    [8.00000E-02, 7.810E+00, 2.879E+00],
    [1.00000E-01, 4.438E+00, 2.100E+00],
    [1.50000E-01, 1.581E+00, 9.378E-01],
    [2.00000E-01, 7.844E-01, 4.913E-01],
    [3.00000E-01, 3.238E-01, 1.973E-01],
    [4.00000E-01, 1.925E-01, 1.100E-01],
    [5.00000E-01, 1.378E-01, 7.440E-02],
    [6.00000E-01, 1.093E-01, 5.673E-02],
    [8.00000E-01, 8.066E-02, 4.028E-02],
    [1.00000E+00, 6.618E-02, 3.276E-02],
    [1.25000E+00, 5.577E-02, 2.761E-02],
    [1.50000E+00, 5.000E-02, 2.484E-02],
    [2.00000E+00, 4.433E-02, 2.256E-02],
    [3.00000E+00, 4.075E-02, 2.236E-02],
    [4.00000E+00, 4.038E-02, 2.363E-02],
    [5.00000E+00, 4.103E-02, 2.510E-02],
    [6.00000E+00, 4.210E-02, 2.649E-02],
    [8.00000E+00, 4.472E-02, 2.886E-02],
    [1.00000E+01, 4.747E-02, 3.072E-02],
    [1.50000E+01, 5.384E-02, 3.360E-02],
    [2.00000E+01, 5.893E-02, 3.475E-02]
])

MATERIALS = {
    "W": {
        "rho": 19.35,  # g/cm^3
        "E_mev": tungsten_data[:, 0],  # MeV
        "mu_over_rho": tungsten_data[:, 1]  # cm^2/g
    },
    # You can add "Al"/"Cu"/"Ag"/"Ta"... here with their (E, mu_over_rho) and density
}


# =========================
# 3) Build μ(E) and transmission
# =========================
def make_mu_interp(E_tab_mev, mu_over_rho_tab, rho_g_cm3):
    """Return a callable mu(E) [cm^-1] using log-log interpolation on (E, mu/rho) and multiply by density."""
    E_tab = np.asarray(E_tab_mev, dtype=float)
    mu_over_rho_tab = np.asarray(mu_over_rho_tab, dtype=float)
    # Avoid log(<=0)
    E_tab = np.clip(E_tab, 1e-12, None)
    mu_over_rho_tab = np.clip(mu_over_rho_tab, 1e-30, None)
    f = interp1d(np.log(E_tab), np.log(mu_over_rho_tab),
                 kind="linear", fill_value="extrapolate", bounds_error=False)

    def mu_of_E(E_mev_query):
        E = np.asarray(E_mev_query, dtype=float)
        E = np.clip(E, 1e-12, None)
        mu_over_rho = np.exp(f(np.log(E)))  # cm^2/g
        return mu_over_rho * rho_g_cm3  # -> cm^-1

    return mu_of_E


def transmission_of_stack(E_mev, stack):
    """Compute total transmission T(E) across a multilayer filter stack using Beer–Lambert law."""
    T = np.ones_like(E_mev, dtype=float)
    for mat_key, t_mm in stack:
        mat = MATERIALS[mat_key]
        mu = make_mu_interp(mat["E_mev"], mat["mu_over_rho"], mat["rho"])
        t_cm = (t_mm or 0.0) / 10.0
        T *= np.exp(-mu(E_mev) * t_cm)
    return T


# =========================
# 4) Apply filtration
# =========================
T = transmission_of_stack(E_mev, filter_stack)
counts_out = counts_in * T

# =========================
# 5) Plot: non-normalized vs. normalized
# =========================
# 5.1 Non-normalized spectra
plt.figure(figsize=(8, 5))
plt.plot(E_keV, counts_in, label="Before filtration", lw=1.2)
plt.plot(E_keV, counts_out, label=f"After filtration ({' + '.join([f'{m}{mm}mm' for m, mm in filter_stack])})", lw=1.2)
plt.xlabel("Energy (keV)")
plt.ylabel("Photon intensity (a.u.)")
plt.title("Spectrum Before/After Filtration (No Normalization)")
plt.legend()
plt.tight_layout()
png_no_norm = f"{OUTPUT_PREFIX}_no_norm.png"
plt.savefig(png_no_norm, dpi=180)
plt.show()

print(f"Plot saved to: {png_no_norm}")
print("-" * 50)


# 5.2 Normalized to each curve's own max (compare shapes only)
def normalize_to_max(x):
    x = np.asarray(x, dtype=float)
    m = np.max(x) if np.max(x) > 0 else 1.0
    return x / m


plt.figure(figsize=(8, 5))
plt.plot(E_keV, normalize_to_max(counts_in), label="Before (normalized to its max)", lw=1.2)
plt.plot(E_keV, normalize_to_max(counts_out), label="After (normalized to its max)", lw=1.2)
plt.xlabel("Energy (keV)")
plt.ylabel("Relative intensity (max = 1)")
plt.title("Spectrum Before/After Filtration (Each Curve Normalized)")
plt.legend()
plt.tight_layout()
png_norm = f"{OUTPUT_PREFIX}_normalized.png"
plt.savefig(png_norm, dpi=180)
plt.show()

print(f"Plot saved to: {png_norm}")
print("-" * 50)


# =========================
# 6) Export data files
# =========================
def normalize_sum1(x):
    """Normalize an array so that sum = 1 (if sum > 0)."""
    s = np.sum(x)
    return x / s if s > 0 else x


out_df = pd.DataFrame({
    "Energy_keV": E_keV,
    "Counts_In": counts_in,
    "Counts_Out": counts_out,
    "Transmission": T,
    "Weights_In_Sum1": normalize_sum1(counts_in),
    "Weights_Out_Sum1": normalize_sum1(counts_out),
})
csv_name = f"{OUTPUT_PREFIX}_{'_'.join([f'{m}{int(round(mm))}mm' for m, mm in filter_stack])}.csv"
out_df.to_csv(csv_name, index=False)

print(f"CSV file saved to: {csv_name}")
print("-" * 50)

# =========================
# 7) Export gVXR arrays and 2-column TXT files
# =========================
weights_out_sum1 = normalize_sum1(counts_out)

print("energy_bins_keV shape:", E_keV.shape)
print("photon_weights_out_sum1 shape:", weights_out_sum1.shape)
# For gVXR, typically:
# gvxr.setEnergyBins(E_keV.tolist())
# gvxr.setPhotonCountEnergyBins(weights_out_sum1.tolist())

# Export two-column text files (Energy_keV + data)
stack_str = "_".join([f"{m}{int(round(mm))}mm" for m, mm in filter_stack])

txt_counts_name = f"{OUTPUT_PREFIX}_{stack_str}_keV_counts.txt"
txt_weights_name = f"{OUTPUT_PREFIX}_{stack_str}_keV_weights_sum1.txt"

# (1) Energy_keV vs Counts_Out (non-normalized)
np.savetxt(
    txt_counts_name,
    np.column_stack([E_keV, counts_out]),
    fmt="%.6f %.8e",
    header="Energy_keV  Counts_Out  (No normalization)",
    comments=""
)

print(f"Non-normalized spectrum saved to: {txt_counts_name}")
print("-" * 50)

# (2) Energy_keV vs normalized weights (sum = 1)
np.savetxt(
    txt_weights_name,
    np.column_stack([E_keV, weights_out_sum1]),
    fmt="%.6f %.8e",
    header="Energy_keV  Weight_Out_Sum1  (Sum to 1)",
    comments=""
)

print(f"Normalized spectrum weights saved to: {txt_weights_name}")
print("-" * 50)

# Final completion message
print("Attenuation & transmission simulation work is done!")
print("Wish you a good day :)")
print("-" * 50)
