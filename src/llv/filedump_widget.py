import sys, time
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QLineEdit, QTextEdit,
                              QCheckBox, QRadioButton, QComboBox, QListWidget,
                              QSlider, QProgressBar, QMessageBox, QTabWidget,QFileDialog)
from PySide6.QtGui import QFont, QFontDatabase

from filedump import dump_file

class FileDump(QtWidgets.QWidget):
    def __init__(self, params):
        super().__init__()
        self.params = params
        self.initialized = False
        self.setMouseTracking(False)
        
        self._resize_done = QtCore.QTimer(
            self, interval=150, singleShot=True)
        self._resize_done.timeout.connect(self.update_text)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_text_example(), "Text Inputs")

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.tabs)
        
    def create_text_example(self):
        # Text Input Tab
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Line edit
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Enter text here...")

        # Button to open file dialog
        self.open_button = QPushButton("Select Files...")
        self.open_button.clicked.connect(self.open_file_dialog)
        layout.addWidget(self.open_button)

        # Text area to show file contents
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        mono = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        mono.setPointSize(12)
        self.text_area.setFont(mono)
        self.text_area.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.text_area)
        

        widget.setLayout(layout)
        return widget
    
    def update_text(self):
        if (self.file_paths is None):
            return
        self.text_area.clear()
        for path in self.file_paths:
            self.text_area.append(dump_file(path,0,None,None, (self.window().width())//50))
    
    def resizeEvent(self, ev: QtGui.QResizeEvent) -> None:
        self.window_size = ev.size()
        if (self.initialized):
            self._resize_done.start()
        super().resizeEvent(ev)
    
    def open_file_dialog(self):
        # Allow selecting multiple files; set filter as needed
        self.file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Choose files to load",
            "",  # start directory
            "All Files (*);;Text Files (*.txt)"
        )
        if not self.file_paths:
            return

        # Clear previous text
        self.text_area.clear()

        # Load each file and append its contents
        for path in self.file_paths:
            self.text_area.append(dump_file(path,0,None,None, (self.window().width())//50))
        self.initialized = True
             
    def create_selection_example(self):
        # Selection Widgets Tab
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Checkboxes
        checkbox1 = QCheckBox("Option 1")
        checkbox2 = QCheckBox("Option 2")
        checkbox2.setChecked(True)
        
        # Radio buttons
        radio_group = QWidget()
        radio_layout = QHBoxLayout()
        self.radio1 = QRadioButton("Radio 1")
        self.radio2 = QRadioButton("Radio 2")
        self.radio1.setChecked(True)
        radio_layout.addWidget(self.radio1)
        radio_layout.addWidget(self.radio2)
        radio_group.setLayout(radio_layout)
        
        
        # Combo box
        self.combo = QComboBox()
        self.combo.addItems(["Item 1", "Item 2", "Item 3"])
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.addItems(["List Item 1", "List Item 2", "List Item 3"])
        
        layout.addWidget(checkbox1)
        layout.addWidget(checkbox2)
        layout.addWidget(radio_group)
        layout.addWidget(self.combo)
        layout.addWidget(self.list_widget)
        widget.setLayout(layout)
        return widget
    
    def create_slider_example(self):
        # Slider and Progress Bar Tab
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Slider
        self.slider = QSlider()
        self.slider.setOrientation(QtCore.Qt.Orientation.Horizontal)  # 1 = Horizontal
        self.slider.setRange(0, 100)
        self.slider.setValue(50)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setValue(50)
        
        # Connect slider to progress bar
        self.slider.valueChanged.connect(self.progress.setValue)
        
        layout.addWidget(self.slider)
        layout.addWidget(self.progress)
        widget.setLayout(layout)
        return widget
    
    def show_input(self):
        line_text = self.line_edit.text()
        text_content = self.text_edit.toPlainText()
        self.display_label.setText(f"Line Edit: {line_text}\nText Edit:\n{text_content}")