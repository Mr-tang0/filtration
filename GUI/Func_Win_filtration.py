import json
import os
from functools import partial
import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from PyQt5.QtWidgets import QFileDialog, QWidget
from GUI.ui.Win_Filtration import Ui_Form as UI

from Core.Materials import Material
import Core.XFilter


class Win_filtration(QWidget):
    def __init__(self):
        super(Win_filtration, self).__init__()
        #  绘图
        self.ax = None
        self.toolbar = None
        self.canvas = None
        self.fig = None

        #  计算目标材料
        self.material = None
        #  目标材料序列，本地文件
        self.targetMaterials = {}

        #  UI初始化
        self.ui = UI()
        self.ui.setupUi(self)
        self.UiSetup()
        self.displayPlot()

    def UiSetup(self):
        """
        初始化UI
        """
        self.setWindowTitle("Filteration Calculator")
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

        #  按钮信号连接
        self.ui.choose_tungsten_data_file.clicked.connect(self.chooseTungstenDataFileClicked)
        self.ui.calculate.clicked.connect(self.calculateClicked)
        self.ui.clearPIC.clicked.connect(self.clearPlot)

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

    def chooseTungstenDataFileClicked(self):
        try:
            fileName, _ = QFileDialog.getOpenFileName(self, 'Open file', '')
            if fileName == '':
                return
            self.ui.tungsten_data_file.setText(fileName)
        except Exception as e:
            print("Error reading density file from chooseTungstenDataFileClicked:", e)

    def calculateClicked(self):
        try:
            exists = os.path.exists(self.ui.tungsten_data_file.text())
            if not exists:
                print("Density file not found.")
                return

            materialType = self.ui.material.text()
            thickness = float(self.ui.thickness.text())
            tungsten_density = float(self.ui.density.text())

            self.material = Material(materialType, thickness, tungsten_density)

            self.material.MaterialInit(tungsten_file=self.ui.tungsten_data_file.text())

            energy = np.arange(1000, 2000000 + 1000, 1000)
            mu_array, trans, atten = Core.XFilter.filtrationCalculate(self.material, energy)

            self.clearPlot()
            # 透射率曲线
            self.displayPlot(
                x_data=energy / 1e6,
                y_data=trans,
                x_label='Energy (MeV)',
                y_label='transmitted/attenuated fraction',
                title=f'attenuation & transmission for {materialType} with thickness of {thickness} mm',
                label_name='transmitted'
            )

            # 衰减率曲线
            self.displayPlot(
                x_data=energy / 1e6,
                y_data=atten,
                x_label='Energy (MeV)',
                y_label='transmitted/attenuated fraction',
                title=f'attenuation & transmission for {materialType} with thickness of {thickness} mm',
                label_name='attenuated'
            )
        except Exception as e:
            print("Error calculating filtration:", e)

    def displayPlot(self, x_data=None, y_data=None,
                    x_label: str = 'X',
                    y_label: str = 'Y',
                    title: str = '',
                    label_name: str = ''):
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
                self.ax.plot(x_data, y_data, label=label_name)
                self.ax.legend()
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
