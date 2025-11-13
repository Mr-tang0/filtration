import numpy as np
import matplotlib

matplotlib.use('TkAgg')
from matplotlib import pyplot as plt

from scipy.interpolate import interp1d
import pandas as pd
from datetime import date

# Define the attenuation coefficient data for tungsten (W)
# [Energy (MeV), Mass Attenuation Coefficient (cm^2/g), Coherent-Corrected MAC (cm^2/g)]
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

df = pd.DataFrame(tungsten_data, columns=['Energy', 'MAC', 'Coherent-Corrected MAC'])

# 保存为 CSV 文件
filename = "../../test/tungsten_attenuation_data.csv"
df.to_csv(filename, index=False)

print(f"数据已保存至 {filename}")

tungsten_density = 19.35  # density, g/cm^3

energy_values = tungsten_data[:, 0]
mass_attenuation_coefficients = tungsten_data[:, 1]
interp_func = interp1d(energy_values, mass_attenuation_coefficients, kind='linear', fill_value="extrapolate")


def tungsten_mu(energies):
    energies = np.atleast_1d(energies)  # Ensure input is an array
    mu_values = np.zeros_like(energies)  # Initialize the output array
    for i, energy in enumerate(energies):
        # Calculate the mass attenuation coefficient (mu/rho) using the interpolation function
        mass_attenuation_coefficient = interp_func(energy)
        # Convert to linear attenuation coefficient (mu) using the formula: mu = (mu/rho) * rho
        linear_attenuation_coefficient = mass_attenuation_coefficient * tungsten_density
        mu_values[i] = linear_attenuation_coefficient
    return mu_values


Target_material = 'W'  # material chemical formula
thickness = 50  # material thickness, in mm
energy = np.arange(1000, 2000000 + 1000, 1000)  #ev
mu_array = tungsten_mu(energy / 1e6)

trans = np.exp(-0.1 * thickness * mu_array)
atten = 1 - trans

plt.plot(energy / 1e6, trans, label='transmitted', color='blue')
plt.plot(energy / 1e6, atten, label='attenuated', color='red')
plt.legend()
plt.xlabel('Energy (MeV)')
plt.ylabel('tranmitted/attenuated fraction')
plt.title(f'attenuation & transmission for {Target_material} with thickness of {thickness} mm')
plt.show()

# Get today's date
today_str = date.today().strftime('%Y-%m-%d')

# Prepare data (using energy in MeV to match the plot)
energy_mev = energy / 1e6

# Create Pandas DataFrames
df_atten = pd.DataFrame({'Energy (MeV)': energy_mev, 'Attenuation Fraction': atten})
df_trans = pd.DataFrame({'Energy (MeV)': energy_mev, 'Transmission Fraction': trans})

# Define filenames
file_atten = f"{today_str} attenuation for {Target_material} with thickness of {thickness} mm.xlsx"
file_trans = f"{today_str} transmission for {Target_material} with thickness of {thickness} mm.xlsx"

# Save DataFrames to Excel files
df_atten.to_excel(file_atten, index=False)
df_trans.to_excel(file_trans, index=False)

print("-" * 50)
print(f"Attenuation data saved to: {file_atten}")
print(f"Transmission data saved to: {file_trans}")

print("-" * 50)
print("attenuation & transmission simulation work is done!")
print("Wish you a good day :)")
print("-" * 50)
