import sys, time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from pathlib import Path
from aquabuddy_widget import *


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = Aquabuddy(sys.argv)
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec())