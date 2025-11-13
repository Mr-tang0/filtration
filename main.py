import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QPushButton

from GUI.Func_Win_filtration import Win_filtration
from GUI.Func_Win_ApplyFilter import Win_ApplyFilter
from GUI.Func_Win_Test import Win_Test

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    w = Win_ApplyFilter()
    w.show()

    sys.exit(app.exec_())
