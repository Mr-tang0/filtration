import json
import os
import time
from functools import partial

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from PyQt5.QtWidgets import QFileDialog, QWidget, QLabel, QPushButton, QHBoxLayout, QListWidgetItem, QRadioButton, \
    QMainWindow
from GUI.ui.Win_Filter import Ui_Form as UI

from Core.Materials import Material, MaterialStack
import Core.XFilter


class Win_ApplyFilter(QWidget):
    def __init__(self):
        super(Win_ApplyFilter, self).__init__()
        #  绘图
        self.ax = None
        self.toolbar = None
        self.canvas = None
        self.fig = None

        #  计算目标材料堆
        self.materialStack = MaterialStack()
        self.currentMaterial = None
        #  目标材料序列，本地文件
        self.targetMaterials = {}
        #  计算结果
        self.MaterialsResult = {}

        #  UI初始化
        self.ui = UI()
        self.ui.setupUi(self)
        self.UiSetup()
        self.displayPlot()

    def UiSetup(self):
        self.setWindowTitle("Apply Filter")

        self.ui.thickness.setText('1')
        with open('Core/element/symbol_key.json', 'r', encoding='utf-8') as f:
            self.targetMaterials = json.load(f)

        self.ui.materialList.addItems(self.targetMaterials.keys())
        self.ui.materialList.currentTextChanged.connect(
            partial(self.setCurrentMaterial, target=self.ui.materialList)
        )
        # 使用lambda表达式传递参数
        self.ui.material.textChanged.connect(
            partial(self.setCurrentMaterial, target=self.ui.material)
        )

        layout = self.ui.result_display.layout()
        if layout is None:
            from PyQt5.QtWidgets import QVBoxLayout
            layout = QVBoxLayout(self.ui.result_display)
            self.ui.result_display.setLayout(layout)
        # 创建新的Figure和Canvas
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self.ui.result_display)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.ax = self.fig.add_subplot(111)

        self.ui.addToMaterialStack.clicked.connect(self.addToMaterialStackClicked)
        self.ui.calculate.clicked.connect(self.ApplyFilterClicked)

        self.ui.NormalizedButtonGroup.buttonClicked.connect(self.normalizeButtonGroupClicked)

        self.ui.choose_tungsten_data_file.clicked.connect(self.choose_tungsten_data_fileClicked)
        self.ui.choose_save_result_path.clicked.connect(self.choose_save_result_pathClicked)
        self.ui.choose_SPECTRUM_PATH.clicked.connect(self.choose_SPECTRUM_PATHClicked)

        self.ui.save.clicked.connect(self.saveClicked)
        self.ui.savePIC.clicked.connect(self.savePICClicked)

    def resizeEvent(self, a0):
        # print("resizeEvent", a0.size())
        pass

    def choose_tungsten_data_fileClicked(self):
        try:
            fileName, _ = QFileDialog.getOpenFileName(self, 'Open file', '')
            if fileName == '':
                return
            self.ui.tungsten_data_file.setText(fileName)
        except Exception as e:
            print("Error reading density file from chooseTungstenDataFileClicked:", e)
        pass

    def choose_save_result_pathClicked(self):
        file_path = QFileDialog.getExistingDirectory(self, "Choose save result path")
        self.ui.save_result_path.setText(file_path)
        pass

    def choose_SPECTRUM_PATHClicked(self):
        try:
            fileName, _ = QFileDialog.getOpenFileName(self, 'Choose SPECTRUM_PATH', '')
            if fileName == '':
                return
            self.ui.SPECTRUM_PATH.setText(fileName)
        except Exception as e:
            print("Error reading SPECTRUM_PATH from choose_SPECTRUM_PATHClicked:", e)
        pass

    def saveClicked(self):
        try:
            file_path = self.ui.save_result_path.text()
            file_name = self.ui.save_result_name.text()
            if file_path == '':
                print("Invalid save result path:", file_path)
                return

            out_df = pd.DataFrame({
                "Energy_keV": self.MaterialsResult.get("E_keV"),
                "Counts_In": self.MaterialsResult.get("counts_in"),
                "Counts_Out": self.MaterialsResult.get("counts_out"),
                "Transmission": self.MaterialsResult["Transmission"],
                "Weights_In_Sum1": Core.XFilter.normalize_sum1(self.MaterialsResult.get("counts_in")),
                "Weights_Out_Sum1": Core.XFilter.normalize_sum1(self.MaterialsResult.get("counts_out")),
            })
            csv_name = f"{file_name}_{'_'.join([f'{material.material}{int(round(material.thickness))}mm' for material in self.materialStack])}.csv"
            csv_name = os.path.join(file_path, csv_name)

            while os.path.exists(csv_name):
                csv_name = os.path.join(file_path,
                                        f"{file_name}_{'_'.join([f'{material.material}{int(round(material.thickness))}mm' for material in self.materialStack])}_{int(round(time.time()))}.csv")

            out_df.to_csv(csv_name, index=False)

            # Export two-column text files (Energy_keV + data)
            stack_str = "_".join(
                [f"{material.material}{int(round(material.thickness))}mm" for material in self.materialStack])

            # (1) Energy_keV vs Counts_Out (non-normalized)
            txt_counts_name = f"{file_name}_{stack_str}_keV_counts.csv"
            out_df = pd.DataFrame({
                "Energy_keV": self.MaterialsResult.get("E_keV"),
                "Counts_Out": self.MaterialsResult.get("counts_out(No normalization)")
            })
            while os.path.exists(txt_counts_name):
                txt_counts_name = os.path.join(file_path,
                                               f"{file_name}_{stack_str}_keV_counts_{int(round(time.time()))}.csv")
            out_df.to_csv(txt_counts_name, index=False)

            # (2) Energy_keV vs normalized weights (sum = 1)
            txt_weights_name = f"{file_name}_{stack_str}_keV_weights_sum1.csv"
            out_df = pd.DataFrame({
                "Energy_keV": self.MaterialsResult.get("E_keV"),
                "Weights_Out_Sum1": Core.XFilter.normalize_sum1(self.MaterialsResult.get("counts_out"))
            })
            while os.path.exists(txt_weights_name):
                txt_weights_name = os.path.join(file_path,
                                                f"{file_name}_{stack_str}"
                                                f"_keV_weights_sum1_{int(round(time.time()))}.csv")
            out_df.to_csv(txt_weights_name, index=False)

        except Exception as e:
            print("Error reading save result path from saveClicked:", e)

    def savePICClicked(self):
        try:
            fileName = QFileDialog.getSaveFileName(self, "Save figure", "", "PNG(*.png);;JPG(*.jpg)")
            if fileName[0] == '':
                return
            self.fig.savefig(fileName[0])
        except Exception as e:
            print("Error reading save result path from savePICClicked:", e)
        pass

    def addToMaterialStackClicked(self):
        try:
            self.currentMaterial = Material(
                material=self.ui.material.text(),
                thickness=float(self.ui.thickness.text()),
                density=float(self.ui.density.text()),
                tungsten_file=self.ui.tungsten_data_file.text()
            )
            self.materialStack.appendMaterial(self.currentMaterial)

            self.freshMaterialStack()

            # print("addToMaterialStack", self.currentMaterial, self.materialStack)
        except Exception as e:
            print("Error reading density file from addToMaterialStackClicked:", e)
        pass

    def ApplyFilterClicked(self):
        # Input spectrum file with two columns: E[MeV], counts
        SPECTRUM_PATH = self.ui.SPECTRUM_PATH.text()

        SPECTRUM_PATH = "Core/2MeV.txt" if SPECTRUM_PATH == "" else SPECTRUM_PATH

        spec = np.loadtxt(SPECTRUM_PATH)
        E_mev = spec[:, 0].astype(float)  # MeV
        counts_in = spec[:, 1].astype(float)  # Relative or absolute photon counts
        counts_in[counts_in < 0] = 0.0  # Clamp negative values
        E_keV = E_mev * 1000.0

        T = Core.XFilter.transmission_of_stack(E_mev, self.materialStack)
        counts_out = counts_in * T

        self.MaterialsResult["E_keV"] = E_keV
        self.MaterialsResult["counts_in"] = counts_in
        self.MaterialsResult["counts_out"] = counts_out
        self.MaterialsResult["Transmission"] = T

        self.normalizeButtonGroupClicked(
            self.ui.Unnormalized if self.ui.Unnormalized.isChecked() else self.ui.Normalized)

        pass

    def normalizeButtonGroupClicked(self, button: QRadioButton):
        try:
            self.clearPlot()
            if button == self.ui.Unnormalized:
                self.displayPlot(x_data=self.MaterialsResult.get("E_keV"),
                                 y_data=self.MaterialsResult.get("counts_in"),
                                 label_name="Before filtration",
                                 color="r")
                self.displayPlot(x_data=self.MaterialsResult.get("E_keV"),
                                 y_data=self.MaterialsResult.get("counts_out"),
                                 x_label="Energy [keV]",
                                 y_label="Photon intensity (a.u.)",
                                 label_name=f"After filtration ({' + '.join([f'{material.material}{material.thickness}mm' for material in self.materialStack])})",
                                 color="b")
            elif button == self.ui.Normalized:
                self.displayPlot(x_data=self.MaterialsResult.get("E_keV"),
                                 y_data=Core.XFilter.normalize_to_max(self.MaterialsResult.get("counts_in")),
                                 label_name="Before (normalized to its max)",
                                 color="r")
                self.displayPlot(x_data=self.MaterialsResult.get("E_keV"),
                                 y_data=Core.XFilter.normalize_to_max(self.MaterialsResult.get("counts_out")),
                                 x_label="Energy [keV]",
                                 y_label="Relative intensity (max = 1)",
                                 label_name="After (normalized to its max)",
                                 color="b")
        except Exception as e:
            print("Error normalizeButtonGroupClicked:", e)

    def freshMaterialStack(self):
        self.ui.MaterialStack.clear()
        for i, material in enumerate(self.materialStack):
            widget = QWidget()

            # 创建标签和按钮
            label = QLabel(f"层: {i + 1}  材料: {material.material} 厚: {material.thickness}mm")
            delete_button = QPushButton("删除")
            delete_button.clicked.connect(
                lambda checked, index=i: {self.materialStack.removeMaterial(index), self.freshMaterialStack()})

            # 创建布局
            layout = QHBoxLayout()
            layout.addWidget(label)
            layout.addStretch()
            layout.addWidget(delete_button)
            widget.setLayout(layout)
            # 创建 QListWidgetItem
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())

            # 将 widget 添加到 QListWidget 中
            self.ui.MaterialStack.addItem(item)
            self.ui.MaterialStack.setItemWidget(item, widget)

    def setCurrentMaterial(self, materialName, target):
        try:
            if target == self.ui.materialList:
                self.ui.material.setText(materialName)
            elif target == self.ui.material:
                self.ui.materialList.setCurrentText(materialName)

            if materialName in self.targetMaterials:
                num = self.targetMaterials[materialName]["atomic_number"]
                # 格式化数字，不足两位补0
                num = f'{num:02d}'
                file = f'Core/element/{num}.csv'
                self.ui.tungsten_data_file.setText(file)
                self.ui.density.setText(str(self.targetMaterials[materialName]["density"]))
            else:
                self.ui.material.setText('')
        except Exception as e:
            print("Error reading density file from setCurrentMaterial:", e)

    def displayPlot(self, x_data=None, y_data=None,
                    x_label: str = 'X',
                    y_label: str = 'Y',
                    title: str = '',
                    label_name: str = '',
                    color: str = 'b'):
        try:
            # 获取或创建布局
            layout = self.ui.result_display.layout()
            if layout is None:
                from PyQt5.QtWidgets import QVBoxLayout
                layout = QVBoxLayout(self.ui.result_display)
                self.ui.result_display.setLayout(layout)

                # 保留现有图形，添加新数据系列
            if not hasattr(self, 'ax'):
                self.fig = Figure(figsize=(5, 4), dpi=100)
                self.canvas = FigureCanvas(self.fig)
                self.toolbar = NavigationToolbar(self.canvas, self.ui.result_display)

                layout.addWidget(self.toolbar)
                layout.addWidget(self.canvas)
                self.ax = self.fig.add_subplot(111)

                # 绘制数据
            self.ax.set_xlabel(x_label)
            self.ax.set_ylabel(y_label)
            self.ax.set_title(title)

            if y_data is not None:
                self.ax.plot(x_data, y_data, label=label_name, color=color)

                self.ax.legend()

                # 收集所有数据系列的范围
                all_x_data = []
                all_y_data = []

                # 遍历所有已绘制的线条获取数据
                for line in self.ax.lines:
                    line_x = line.get_xdata()
                    line_y = line.get_ydata()
                    if len(line_x) > 0 and len(line_y) > 0:
                        all_x_data.extend(line_x)
                        all_y_data.extend(line_y)

                # 根据所有数据设置坐标轴范围
                if all_x_data:
                    x_margin = (max(all_x_data) - min(all_x_data)) * 0.05  # 添加5%边距
                    self.ax.set_xlim(min(all_x_data) - x_margin, max(all_x_data) + x_margin)

                if all_y_data:
                    y_margin = (max(all_y_data) - min(all_y_data)) * 0.05  # 添加5%边距
                    self.ax.set_ylim(min(all_y_data) - y_margin, max(all_y_data) + y_margin)

            self.canvas.draw()
        except Exception as e:
            print("Error displaying plot:", e)

    def clearPlot(self):
        """清除绘图区域，但保留工具栏按钮"""
        try:
            # 只清除图表内容，保留figure和axes
            if hasattr(self, 'ax'):
                # 清除所有绘制的线条
                for line in self.ax.lines[:]:  # 使用[:]避免迭代时修改列表
                    line.remove()
                    # 清除所有绘制的图例
                if self.ax.legend_:
                    self.ax.legend_.remove()
                    # 重置坐标轴标签和标题
                self.ax.set_xlabel('X')
                self.ax.set_ylabel('Y')
                self.ax.set_title('TITLE')
                # 重新绘制空白画布
                self.canvas.draw()
            else:
                # 如果还没有创建图表，则创建初始图表
                self.displayPlot()
        except Exception as e:
            print("Error clearing plot:", e)
