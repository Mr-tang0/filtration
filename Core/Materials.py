import pandas as pd


class Material:
    def __init__(self, material: str, thickness: float, density: float, tungsten_file: str = None):

        self.material = material  # 材料类型

        self.thickness = thickness  # 厚度，单位mm

        self.tungsten_density = density  # 密度 g/cm^3

        #  衰减数据 [Energy (MeV),Mass Attenuation Coefficient (cm^2/g), Coherent-Corrected MAC (cm^2/g)]
        self.tungsten_data = None

        #  衰减文件里的逐列
        self.energy = None
        self.mass_attenuation_coefficients = None
        self.coherent_corrected_MAC = None

        self.MaterialInit(tungsten_file)

    def __str__(self):
        return f"{self.material} ({self.thickness}mm)"

    def MaterialInit(self, tungsten_file: str):
        try:
            if tungsten_file is None:
                return

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


class MaterialStack:
    def __init__(self, material_stack: list = None):
        self.material_stack = material_stack

    def __str__(self):
        msg = ""
        for i, material in enumerate(self.material_stack):
            msg += f"{i+1}: {material}\n"
        return msg

    def __iter__(self):
        return iter(self.material_stack)

    def insertMaterial(self, location: int, material: Material):
        if self.material_stack is None:
            self.material_stack = []
        if location < 0 or location > len(self.material_stack):
            print("Invalid location. Please enter a valid index.")
            return
        self.material_stack.insert(location, material)

    def removeMaterial(self, location: int):
        if self.material_stack is None:
            self.material_stack = []

        if location < 0 or location >= len(self.material_stack):
            print("Invalid location. Please enter a valid index.")
            return
        removed_material = self.material_stack.pop(location)
        return removed_material

    def appendMaterial(self, material: Material):
        if self.material_stack is None:
            self.material_stack = []
        self.material_stack.append(material)


# cu = Material('Cu', 50, 8.96)
# h = Material('H', 50, 1)
# materialStack = MaterialStack([cu, h])
#
# for m in materialStack:
#     print(m)
