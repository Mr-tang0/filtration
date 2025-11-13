import os

import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QFileDialog, QGraphicsScene, QGraphicsPixmapItem
from matplotlib import pyplot as plt
import matplotlib

matplotlib.use('TkAgg')
from GUI.ui.Win_Test import Ui_Form as UI
import Core.Json2gvxrCalculator as Calculator


class CalculatorWorker(QThread):
    finished = pyqtSignal(object)  # 计算完成信号
    error = pyqtSignal(str)  # 错误信号

    def __init__(self, json_file):
        super().__init__()
        self.json_file = json_file

    def run(self):
        try:
            result = Calculator.GVXRCalculate(self.json_file)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


def float32_to_uint8(img: np.ndarray, offset: float = 1.0, logCount: int = 3) -> np.ndarray:
    try:
        offset = 1.0 if offset <= 0 else offset

        img = img.astype(np.float32)
        for i in range(logCount):
            img = np.log(img - img.min() + offset)  # 避免 log(0)

        img_min = img.min()
        img_max = img.max()
        if img_max - img_min == 0:
            img_norm = np.zeros_like(img, dtype=np.uint8)
        else:
            img_norm = ((img - img_min) / (img_max - img_min) * 255).astype(np.uint8)
        return img_norm
    except Exception as e:
        print("[ERROR] float32_to_uint8:", e)
        return None


def uint8_to_qImage(img_uint8: np.ndarray):
    h, w = img_uint8.shape
    qImage = QImage(
        img_uint8.data,
        w,
        h,
        w,  # bytesPerLine = width for uint8 gray
        QImage.Format_Grayscale8
    )
    return qImage


class Win_Test(QWidget):
    def __init__(self, parent=None):
        super(Win_Test, self).__init__(parent)
        self.ui = UI()
        self.ui.setupUi(self)
        self.UiSetup()
        self.calculator_thread = None
        self.calculator_result = None
        self.calculator_PICs = []

    def UiSetup(self):
        self.ui.choose_JSONFileName.clicked.connect(self.choose_JSONFileNameClicked)
        self.ui.calculate.clicked.connect(self.calculateClicked)
        self.ui.PICSlider.valueChanged.connect(self.PICSliderValueChanged)

    def resizeEvent(self, event):
        """当窗口大小改变时，调整图片显示"""
        super().resizeEvent(event)
        self.adjust_picture_view()

    def adjust_picture_view(self):
        """调整图片视图大小"""
        if self.ui.PICView.scene():
            self.ui.PICView.fitInView(self.ui.PICView.scene().sceneRect(), Qt.KeepAspectRatio)

    def choose_JSONFileNameClicked(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "选择JSON文件", "", "JSON Files (*.json)")
        if fileName != '':
            self.ui.JSONFileName.setText(fileName)

    def calculateClicked(self):
        fileName = self.ui.JSONFileName.text()
        if not os.path.exists(fileName):
            print("[ERROR] JSON文件不存在")
            return
        self.start_calculation(fileName)

    def start_calculation(self, json_file):
        # 创建并启动工作线程
        print("开始计算...", json_file)
        self.calculator_thread = CalculatorWorker(json_file)
        self.calculator_thread.finished.connect(self.on_calculation_finished)
        self.calculator_thread.error.connect(self.on_calculation_error)
        self.calculator_thread.start()

    def on_calculation_finished(self, result):
        # 处理计算结果
        print("计算完成:", result)
        self.calculator_result, _ = result
        self.calculator_PICs = Calculator.getTif(self.calculator_result)
        # 更新UI...
        print("Tif_s:", len(self.calculator_PICs))
        self.ui.PICSlider.setValue(0)
        self.ui.PICSlider.setMaximum(len(self.calculator_PICs) - 1)

        self.update_pic(self.calculator_PICs[0])

    def on_calculation_error(self, error_msg):
        # 处理错误
        print("计算出错:", error_msg)
        # 显示错误信息...

    def update_pic(self, tif_image: np.ndarray):
        try:
            tif_image = float32_to_uint8(tif_image)
            qImage = uint8_to_qImage(tif_image)

            scene = QGraphicsScene(self.ui.PICView)

            pixmap = QPixmap.fromImage(qImage)

            # 创建图像项并添加到场景
            pixmap_item = QGraphicsPixmapItem(pixmap)
            scene.addItem(pixmap_item)

            # 设置场景并调整视图
            self.ui.PICView.setScene(scene)
            self.ui.PICView.fitInView(scene.sceneRect(), Qt.KeepAspectRatio)
        except Exception as e:
            print("[ERROR] 更新图片出错:", e)

    def PICSliderValueChanged(self, value):
        try:
            if self.calculator_result is not None:
                self.update_pic(self.calculator_PICs[value])
        except Exception as e:
            print("[ERROR] 更新图片出错:", e)
