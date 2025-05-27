from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from chat_widget import ChatWidget


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    main_window = ChatWidget()
    main_window.setWindowTitle("Chat Application")
    main_window.show()
    sys.exit(app.exec())