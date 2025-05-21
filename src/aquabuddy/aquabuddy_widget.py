import sys, time
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QLineEdit, QTextEdit,
                              QCheckBox, QRadioButton, QComboBox, QListWidget,
                              QSlider, QProgressBar, QMessageBox, QTabWidget)

class Aquabuddy(QtWidgets.QWidget):
    def __init__(self, params):
        super().__init__()
        self.params = params
        self.hello = "Hallo Welt"
        self.setMouseTracking(False)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_button_example(), "Buttons")
        self.tabs.addTab(self.create_text_example(), "Text Inputs")
        self.tabs.addTab(self.create_selection_example(), "Selections")
        self.tabs.addTab(self.create_slider_example(), "Sliders")
        self.tabs.addTab(self.create_drawing_example(), "Drawing")

        self.button = QtWidgets.QPushButton("Click me!")
        self.text = QtWidgets.QLabel(self.hello,
                                     alignment=QtCore.Qt.AlignCenter)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.tabs)
        self.layout.addWidget(self.text)
        self.layout.addWidget(self.button)


        self.button.clicked.connect(self.magic)
    
    def mousePressEvent(self, mouse_event):
        print(mouse_event.x())

    def mouseMoveEvent(self, QMouseEvent):
        print("Hey")

    def magic(self):
        if len(self.params) >= 2:
            self.text.setText(self.params[1])
        else:
            self.text.setText("Test")

    def create_drawing_example(self):
        # New drawing tab
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Create drawing widget and controls
        self.drawing_widget = DrawingWidget()
        btn_animate = QPushButton("Animate Shapes")
        btn_animate.clicked.connect(self.drawing_widget.update_offset)
        
        layout.addWidget(btn_animate)
        layout.addWidget(self.drawing_widget)
        widget.setLayout(layout)
        return widget
    
    def create_button_example(self):
        # Button Tab
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Basic button
        btn1 = QPushButton("Click Me!")
        btn1.clicked.connect(lambda: QMessageBox.information(self, "Info", "Button clicked!"))
        
        # Toggle button
        btn2 = QPushButton("Toggle Button")
        btn2.setCheckable(True)
        btn2.toggled.connect(lambda state: print(f"Toggle state: {state}"))
        
        # Disabled button
        btn3 = QPushButton("Disabled Button")
        btn3.setEnabled(False)
        
        layout.addWidget(btn1)
        layout.addWidget(btn2)
        layout.addWidget(btn3)
        widget.setLayout(layout)
        return widget
    
    def create_text_example(self):
        # Text Input Tab
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Line edit
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Enter text here...")
        
        # Text edit
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Multi-line text input...")
        
        # Display label
        self.display_label = QLabel("You entered: ")
        
        # Button to show input
        btn = QPushButton("Show Input")
        btn.clicked.connect(self.show_input)
        
        layout.addWidget(self.line_edit)
        layout.addWidget(self.text_edit)
        layout.addWidget(btn)
        layout.addWidget(self.display_label)
        widget.setLayout(layout)
        return widget
    
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


class DrawingWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 300)
        self.rect_offset = 0

    def update_offset(self):
        self.rect_offset = (self.rect_offset + 10) % 100
        self.update()  # Trigger repaint

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Draw red rectangle (animated)
        painter.setPen(QtGui.QPen(QtCore.Qt.red, 3))
        painter.drawRect(50 + self.rect_offset, 50, 100, 80)

        # Static shapes
        painter.setPen(QtGui.QPen(QtCore.Qt.blue, 2))
        painter.drawLine(200, 50, 300, 150)
        
        painter.setPen(QtGui.QPen(QtCore.Qt.green, 4))
        painter.drawEllipse(100, 200, 80, 80)  # Circle
        
        painter.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        painter.drawText(10, 20, "Drawing Primitives:")