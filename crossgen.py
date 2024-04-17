from PyQt5 import QtWidgets, QtGui, QtCore

class DotWindow(QtWidgets.QWidget):
    def __init__(self, color, size, shape, line_thickness, circle_style):
        super().__init__()
        self.color = QtGui.QColor(color)
        self.size = size
        self.shape = shape
        self.line_thickness = line_thickness
        self.circle_style = circle_style
        self.initUI()

    def initUI(self):
        self.setFixedSize(self.size, self.size)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.move(screen_center_x - self.size // 2, screen_center_y - self.size // 2)
        self.show()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(self.color, self.line_thickness))
        if self.shape == 'Round':
            if self.circle_style == 'Full':
                painter.setBrush(QtGui.QBrush(self.color))
            else:
                painter.setBrush(QtGui.QBrush(QtCore.Qt.transparent))
            painter.drawEllipse(0, 0, self.size, self.size)
        elif self.shape == 'Crosshair':
            painter.drawLine(self.size // 2, 0, self.size // 2, self.size)
            painter.drawLine(0, self.size // 2, self.size, self.size // 2)

class SettingsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.dot_window = None
        self.color = '#FF0000'  # Default color is red
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QVBoxLayout()

        self.color_button = QtWidgets.QPushButton('Choose Color', self)
        self.color_button.clicked.connect(self.open_color_picker)
        layout.addWidget(self.color_button)

        self.size_label = QtWidgets.QLabel('Dot Size (pixels):', self)
        layout.addWidget(self.size_label)

        self.size_spin = QtWidgets.QSpinBox(self)
        self.size_spin.setRange(5, 30)
        self.size_spin.setValue(8)
        layout.addWidget(self.size_spin)

        self.shape_combo = QtWidgets.QComboBox(self)
        self.shape_combo.addItems(['Round', 'Crosshair'])
        layout.addWidget(self.shape_combo)

        self.style_combo = QtWidgets.QComboBox(self)
        self.style_combo.addItems(['Full', 'Ring'])
        self.style_combo.setEnabled(False)  # Disable by default
        layout.addWidget(self.style_combo)

        self.thickness_combo = QtWidgets.QComboBox(self)
        self.thickness_combo.addItems(['Small (1px)', 'Medium (2px)', 'Large (3px)'])
        self.thickness_combo.setEnabled(False)  # Disable by default
        layout.addWidget(self.thickness_combo)

        # Enable thickness selection only if crosshair is selected or ring style for circle
        self.shape_combo.currentTextChanged.connect(self.toggle_options)

        self.create_button = QtWidgets.QPushButton('Create Dot', self)
        self.create_button.clicked.connect(self.create_dot)
        layout.addWidget(self.create_button)

        self.reset_button = QtWidgets.QPushButton('Reset Dot', self)
        self.reset_button.clicked.connect(self.reset_dot)
        layout.addWidget(self.reset_button)

        self.setLayout(layout)
        self.setWindowTitle('crossgen')
        self.show()

    def open_color_picker(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.color = color.name()

    def toggle_options(self, shape):
        if shape == "Crosshair":
            self.thickness_combo.setEnabled(True)
            self.style_combo.setEnabled(False)
        elif shape == "Round":
            self.style_combo.setEnabled(True)
            self.thickness_combo.setEnabled(True)  # Enable thickness selection for "Ring"
        else:
            self.thickness_combo.setEnabled(False)
            self.style_combo.setEnabled(False)

    def create_dot(self):
        if self.dot_window:
            self.dot_window.close()
        thickness = {'Small (1px)': 1, 'Medium (2px)': 2, 'Large (3px)': 3}.get(self.thickness_combo.currentText(), 1)
        circle_style = self.style_combo.currentText() if self.shape_combo.currentText() == "Round" else None
        self.dot_window = DotWindow(self.color, self.size_spin.value(), self.shape_combo.currentText(), thickness, circle_style)

    def reset_dot(self):
        if self.dot_window:
            self.dot_window.close()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    screen_size = app.primaryScreen().size()
    screen_center_x = screen_size.width() // 2
    screen_center_y = screen_size.height() // 2
    ex = SettingsWindow()
    app.exec_()
