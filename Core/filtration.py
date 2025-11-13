import numpy as np
from scipy.interpolate import interp1d
import pandas as pd


class Material:
    def __init__(self, material: str, thickness: float, density: float):

        self.material = material  # 材料类型

        self.thickness = thickness  # 厚度，单位mm

        self.tungsten_density = density  # 密度 g/cm^3

        #  衰减数据 [Energy (MeV),Mass Attenuation Coefficient (cm^2/g), Coherent-Corrected MAC (cm^2/g)]
        self.tungsten_data = None

        #  衰减文件里的逐列
        self.energy = None
        self.mass_attenuation_coefficients = None
        self.coherent_corrected_MAC = None

    def MaterialInit(self, tungsten_file: str):
        try:
            if tungsten_file.endswith('.csv'):
                self.tungsten_data = pd.read_csv(tungsten_file)
            elif tungsten_file.endswith(('.xlsx', '.xls')):
                self.tungsten_data = pd.read_excel(tungsten_file)
            else:
                print("Unsupported file format. Please use .csv, .xlsx, or .xls files.")
                return

            if self.tungsten_data is not None:
                self.energy = self.tungsten_data['Energy'].values
                self.mass_attenuation_coefficients = self.tungsten_data['MAC'].values
                self.coherent_corrected_MAC = self.tungsten_data['Coherent-Corrected MAC'].values
            else:
                print("Error reading density data.")
                return

        except FileNotFoundError:
            print("Density file not found.")
            return
        except Exception as e:
            print("Error reading density file:", e)
            return

    #  this function : tungsten_mu(energies) energies:EnergyRange/1e6
    def filtrationCalculate(self, EnergyRange):
        try:
            interp_func = interp1d(self.energy, self.mass_attenuation_coefficients, kind='linear',
                                   fill_value="extrapolate")

            energies = np.atleast_1d(EnergyRange / 1e6)  # Ensure input is an array
            mu_values = np.zeros_like(energies)  # Initialize the output array
            for i, energy in enumerate(energies):
                # Calculate the mass attenuation coefficient (mu/rho) using the interpolation function
                mass_attenuation_coefficient = interp_func(energy)
                # Convert to linear attenuation coefficient (mu) using the formula: mu = (mu/rho) * rho
                linear_attenuation_coefficient = mass_attenuation_coefficient * self.tungsten_density
                mu_values[i] = linear_attenuation_coefficient

            transmitted = np.exp(-0.1 * self.thickness * mu_values)
            attenuated = 1 - transmitted

            return mu_values, transmitted, attenuated

        except Exception as e:
            print("Error calculating filtration:", e)
            return None, None, None
