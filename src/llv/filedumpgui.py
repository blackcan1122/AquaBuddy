import sys, time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from pathlib import Path
from filedump_widget import FileDump


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = FileDump(sys.argv)
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec())