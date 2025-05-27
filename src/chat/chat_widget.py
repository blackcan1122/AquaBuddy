from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
import random

class ChatArea(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self._text_var = ["Hey Lukas", "HEEEEEEEEY WAS GEHT ALTES HAUS\nSCHON LANG NICHT MEHR GESEHEN HAHAHAH\nLass mal wieder was saufen wie echte männer hahahahahahhahaha\nloremipsum blal bla ich hasse mein leben manchmal nicht hahahahah"]
        self.chat_widgets = []
        for i in range(100):
            chat = QtWidgets.QTextEdit()
            setattr(self, f'_testchat_{i}', chat)
            chat.padding = 8.0
            chat.setText(random.choice(self._text_var))
            #chat.setFixedHeight(chat.frameWidth() + chat.padding)
            self.layout.addWidget(chat)
            self.chat_widgets.append(chat)
        self.setLayout(self.layout)

    def showEvent(self, event):
        super().showEvent(event)
        for i in range(100):
            self.chat_widgets[i].setFixedHeight(self.chat_widgets[i].document().size().height() + self.chat_widgets[i].padding)


class InputTextField(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._maxHeight = 200
        self.textChanged.connect(self.adjust_height)
        self.adjust_height()

    def adjust_height(self):
        doc_height = self.document().size().height()
        margins = self.contentsMargins().top() + self.contentsMargins().bottom()
        height = int(doc_height + self.frameWidth() * 2 + margins)
        height = min(height, self._maxHeight)
        self.setFixedHeight(max(30, height))  # 30 is the minimum height

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
            # Handle sending the message on Enter key press without Shift
            self.parent().send_message()
            event.accept()
        else:
            super().keyPressEvent(event)

class ChatWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Application")
        self.resize(800, 600)

        # Layout
        layout = QtWidgets.QVBoxLayout(self)

        # Chat area
        self.chat_area = ChatArea()
        layout.addWidget(self.chat_area)
        self.chat_area.show()
        

        # Input area
        self.input_area = InputTextField(self)
        layout.addWidget(self.input_area)

        # Send button
        self.send_button = QtWidgets.QPushButton("Send", self)
        layout.addWidget(self.send_button)

        # Connect button click to send message
        #self.send_button.clicked.connect(self.send_message)