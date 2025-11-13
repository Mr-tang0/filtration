import numpy as np
from scipy.interpolate import interp1d
try:
    from .Materials import Material, MaterialStack
except ImportError:
    from Materials import Material, MaterialStack


def filtrationCalculate(material: Material, EnergyRange: np.ndarray):
    try:
        interp_func = interp1d(material.energy, material.mass_attenuation_coefficients, kind='linear',
                               fill_value="extrapolate")

        energies = np.atleast_1d(EnergyRange / 1e6)  # Ensure input is an array
        mu_values = np.zeros_like(energies)  # Initialize the output array
        for i, energy in enumerate(energies):
            # Calculate the mass attenuation coefficient (mu/rho) using the interpolation function
            mass_attenuation_coefficient = interp_func(energy)
            # Convert to linear attenuation coefficient (mu) using the formula: mu = (mu/rho) * rho
            linear_attenuation_coefficient = mass_attenuation_coefficient * material.tungsten_density
            mu_values[i] = linear_attenuation_coefficient

        transmitted = np.exp(-0.1 * material.thickness * mu_values)
        attenuated = 1 - transmitted

        return mu_values, transmitted, attenuated

    except Exception as e:
        print("Error calculating filtration:", e)
        return None, None, None


def make_mu_interp(E_tab_mev, mu_over_rho_tab, rho_g_cm3):
    """Return a callable mu(E) [cm^-1] using log-log interpolation on (E, mu/rho) and multiply by density."""
    """返回一个可调用的μ(E) [cm^-1]，使用(E, μ/ρ)的对数-对数插值并乘以密度。"""
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


def transmission_of_stack(e_mev, stack: MaterialStack):
    """Compute total transmission T(E) across a multilayer filter stack using Beer–Lambert law."""
    """使用贝尔-兰伯斯定律计算多层滤芯堆栈的 transmission T(E)。"""
    T_ = np.ones_like(e_mev, dtype=float)
    for material in stack:
        mu = make_mu_interp(material.energy, material.mass_attenuation_coefficients, material.tungsten_density)
        t_cm = (material.thickness or 0.0) / 10.0
        T_ *= np.exp(-mu(e_mev) * t_cm)
    return T_


def normalize_to_max(x):
    """ Normalized to each curve's own max (compare shapes only) """
    x = np.asarray(x, dtype=float)
    m = np.max(x) if np.max(x) > 0 else 1.0
    return x / m


def normalize_sum1(x):
    """Normalize an array so that sum = 1 (if sum > 0)."""
    s = np.sum(x)
    return x / s if s > 0 else x



import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('TkAgg')
import pandas as pd
from pathlib import Path
from scipy.interpolate import interp1d


if __name__ == "__main__":

    SPECTRUM_PATH = Path("2MeV.txt")  # Input spectrum file with two columns: E[MeV], counts
    OUTPUT_PREFIX = "2MeV_filtered"  # Output filename prefix

    # Define the filter stack (can be multi-layer), thickness in mm
    # Example: 1 mm Tungsten

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

    material_W = Material("W", 1, 19.35, f'E:\AppFile\code\python/filtration\Core\element/74.csv')
    filter_stack = MaterialStack([material_W])

    T = transmission_of_stack(E_mev, filter_stack)
    counts_out = counts_in * T

    # =========================
    # 5) Plot: non-normalized vs. normalized
    # =========================
    # 5.1 Non-normalized spectra
    plt.figure(figsize=(8, 5))
    plt.plot(E_keV, counts_in, label="Before filtration", lw=1.2)
    plt.plot(E_keV, counts_out,
             label=f"After filtration ({' + '.join([f'{material.material}{material.thickness}mm' for material in filter_stack])})",
             lw=1.2)
    plt.xlabel("Energy (keV)")
    plt.ylabel("Photon intensity (a.u.)")
    plt.title("Spectrum Before/After Filtration (No Normalization)")
    plt.legend()
    plt.tight_layout()
    png_no_norm = f"{OUTPUT_PREFIX}_no_norm.png"
    # plt.savefig(png_no_norm, dpi=180)
    plt.show()

    print(f"Plot saved to: {png_no_norm}")
    print("-" * 50)

    plt.figure(figsize=(8, 5))
    plt.plot(E_keV, normalize_to_max(counts_in), label="Before (normalized to its max)", lw=1.2)
    plt.plot(E_keV, normalize_to_max(counts_out), label="After (normalized to its max)", lw=1.2)
    plt.xlabel("Energy (keV)")
    plt.ylabel("Relative intensity (max = 1)")
    plt.title("Spectrum Before/After Filtration (Each Curve Normalized)")
    plt.legend()
    plt.tight_layout()
    png_norm = f"{OUTPUT_PREFIX}_normalized.png"
    # plt.savefig(png_norm, dpi=180)
    plt.show()

    print(f"Plot saved to: {png_norm}")
    print("-" * 50)
