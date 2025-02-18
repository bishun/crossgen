from collections import namedtuple
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QSettings, QPoint, QPointF
from PyQt5.QtWidgets import QComboBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
import json
import os
import math


def get_app_icon() -> QtGui.QIcon:
    """
    Resolves the application icon by checking the main icon path and a list of fallback paths.
    Returns a QIcon if found; otherwise, returns None.
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    main_icon_path = os.path.join(base_path, 'icons', 'crossgen.ico')
    fallback_paths = [
        os.path.join(os.getcwd(), 'icons', 'crossgen.ico'),
        os.path.join(os.getcwd(), 'crossgen.ico')
    ]
    
    if os.path.exists(main_icon_path):
        return QtGui.QIcon(main_icon_path)
    else:
        for path in fallback_paths:
            if os.path.exists(path):
                return QtGui.QIcon(path)
        print("Warning: Icon file not found in any location")
        return None

# Named tuple to store dimension calculations
Dimensions = namedtuple("Dimensions", ["size", "center", "gap", "size_f", "center_f", "gap_f", "dot_size"])

class CrosshairCanvas(QtWidgets.QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings.copy()  # Create a copy of settings
        self.initUI()

    def initUI(self):
        # Compute dimensions to set the fixed size of the widget
        dims = self._compute_dimensions()
        self.setFixedSize(dims.size, dims.size)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(False)

        # Position window at screen center
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        center_x = int(screen.center().x() - dims.size // 2)
        center_y = int(screen.center().y() - dims.size // 2)
        self.move(center_x, center_y)

    def _compute_dimensions(self) -> Dimensions:
        """
        Computes and returns dimensions with customizable dot size
        """
        size = max(8, self.settings.get('size', 8))
        if size % 2 != 0:
            size += 1
        center = size // 2
        gap = min(self.settings.get('gap', 0), center - 1)
        dot_size = self.settings.get('dot_size', max(2, size // 16))
        return Dimensions(
            size=size,
            center=center,
            gap=gap,
            size_f=float(size),
            center_f=float(center),
            gap_f=float(gap),
            dot_size=dot_size
        )

    def create_pen(self, is_outline: bool, shape: str) -> QtGui.QPen:
        """Returns a configured QPen with customizable line style"""
        pen = QtGui.QPen()
        
        if is_outline:
            width = (self.settings.get('outline_thickness', 1) 
                    if shape == 'Circle'
                    else self.settings.get('thickness', 1) + self.settings.get('outline_thickness', 1))
            color = self.settings.get('outline_color', '#000000')
        else:
            width = self.settings.get('thickness', 1)
            color = self.settings.get('color', '#FF0000')
        
        pen.setWidth(width)
        pen.setColor(QtGui.QColor(color))
        
        # Apply line style
        line_style = self.settings.get('line_style', 'Solid')
        if line_style == 'Dotted':
            pen.setStyle(Qt.DotLine)
        elif line_style == 'Dashed':
            pen.setStyle(Qt.DashLine)
        else:
            pen.setStyle(Qt.SolidLine)
        
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        return pen

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        dims = self._compute_dimensions()
        shape = self.settings.get('shape', 'Crosshair')

        # Draw outline first if enabled
        if self.settings.get('outline_enabled', False):
            painter.setOpacity(self.settings.get('outline_opacity', 100) / 100)
            self._draw_shape(painter, shape, dims, True)

        # Then draw main shape
        painter.setOpacity(self.settings.get('opacity', 100) / 100)
        self._draw_shape(painter, shape, dims, False)
        painter.end()

    def _draw_shape(self, painter, shape: str, dims: Dimensions, is_outline: bool):
        if shape == 'Crosshair':
            self._draw_crosshair(painter, dims, is_outline)
        elif shape == 'Circle':
            self._draw_circle(painter, dims, is_outline)
        elif shape == 'T-Shape':
            self._draw_t_shape(painter, dims, is_outline)
        elif shape == 'X-Shape':
            self._draw_x_shape(painter, dims, is_outline)
        elif shape == 'Diamond':
            self._draw_diamond(painter, dims, is_outline)

    def _draw_crosshair(self, painter, dims: Dimensions, is_outline: bool):
        pen = self.create_pen(is_outline, 'Crosshair')
        painter.setPen(pen)

        # Draw vertical lines
        painter.drawLine(QPointF(dims.center_f, 0), QPointF(dims.center_f, dims.center_f - dims.gap_f))
        painter.drawLine(QPointF(dims.center_f, dims.center_f + dims.gap_f), QPointF(dims.center_f, dims.size_f))
        # Draw horizontal lines
        painter.drawLine(QPointF(0, dims.center_f), QPointF(dims.center_f - dims.gap_f, dims.center_f))
        painter.drawLine(QPointF(dims.center_f + dims.gap_f, dims.center_f), QPointF(dims.size_f, dims.center_f))

        # Draw center dot if enabled and not drawing outline
        if not is_outline and self.settings.get('dot_enabled', True):
            dot_size = self.settings.get('dot_size', 2)
            if dot_size == 1:
                painter.drawPoint(QPointF(dims.center_f, dims.center_f))
            else:
                painter.drawEllipse(
                    QPointF(dims.center_f, dims.center_f),
                    dot_size / 2, dot_size / 2
                )

    def _draw_circle(self, painter, dims: Dimensions, is_outline: bool):
        # Force high quality rendering for circles
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        
        center_point = QPointF(dims.size / 2, dims.size / 2)
        radius = (dims.size - 2) / 2
        
        pen = self.create_pen(is_outline, 'Circle')
        painter.setPen(pen)
        
        if is_outline:
            painter.setBrush(Qt.NoBrush)
            outline_thickness = self.settings.get('outline_thickness', 1)
            painter.drawEllipse(
                center_point, 
                radius + outline_thickness / 2,
                radius + outline_thickness / 2
            )
        else:
            fill_style = self.settings.get('fill_style', 'Ring')
            if fill_style == 'Full':
                painter.setBrush(QtGui.QBrush(QtGui.QColor(self.settings['color'])))
            else:
                painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(center_point, radius, radius)
        
        if not is_outline and self.settings.get('dot_enabled', True):
            dot_size = self.settings.get('dot_size', 2)
            if dot_size == 1:
                painter.drawPoint(QPointF(dims.center_f, dims.center_f))
            else:
                painter.drawEllipse(
                    QPointF(dims.center_f, dims.center_f),
                    dot_size / 2, dot_size / 2
                )

    def _draw_t_shape(self, painter, dims: Dimensions, is_outline: bool):
        line_length = dims.size // 3
        dot_size = max(2, dims.size // 16)
        pen = self.create_pen(is_outline, 'T-Shape')
        painter.setPen(pen)

        # Horizontal lines of T
        painter.drawLine(
            QPointF(dims.center_f - dims.gap_f - line_length, dims.center_f),
            QPointF(dims.center_f - dims.gap_f, dims.center_f)
        )
        painter.drawLine(
            QPointF(dims.center_f + dims.gap_f, dims.center_f),
            QPointF(dims.center_f + dims.gap_f + line_length, dims.center_f)
        )
        # Vertical line of T
        painter.drawLine(
            QPointF(dims.center_f, dims.center_f + dims.gap_f),
            QPointF(dims.center_f, dims.center_f + dims.gap_f + line_length)
        )

        if not is_outline and self.settings.get('dot_enabled', True):
            dot_size = self.settings.get('dot_size', 2)
            if dot_size == 1:
                painter.drawPoint(QPointF(dims.center_f, dims.center_f))
            else:
                painter.drawEllipse(
                    QPointF(dims.center_f, dims.center_f),
                    dot_size / 2, dot_size / 2
                )

    def _draw_x_shape(self, painter, dims: Dimensions, is_outline: bool):
        line_length = dims.size_f / 3
        x_angle = self.settings.get('x_angle', 45)  # Get the angle from settings
        # Convert angle to radians and calculate factors
        angle_rad = math.radians(x_angle)
        angle_factor = math.sin(angle_rad)  # Will replace diagonal_factor
        
        pen = self.create_pen(is_outline, 'X-Shape')
        painter.setPen(pen)

        gap_offset = dims.gap_f * angle_factor
        
        # Calculate line endpoints using the angle
        dx = line_length * math.cos(angle_rad)
        dy = line_length * math.sin(angle_rad)
        
        # Top-left to center
        painter.drawLine(
            QPointF(dims.center_f - dx, dims.center_f - dy),
            QPointF(dims.center_f - gap_offset * math.cos(angle_rad), 
                    dims.center_f - gap_offset * math.sin(angle_rad))
        )
        # Center to bottom-right
        painter.drawLine(
            QPointF(dims.center_f + gap_offset * math.cos(angle_rad),
                    dims.center_f + gap_offset * math.sin(angle_rad)),
            QPointF(dims.center_f + dx, dims.center_f + dy)
        )
        # Top-right to center
        painter.drawLine(
            QPointF(dims.center_f + dx, dims.center_f - dy),
            QPointF(dims.center_f + gap_offset * math.cos(angle_rad),
                    dims.center_f - gap_offset * math.sin(angle_rad))
        )
        # Center to bottom-left
        painter.drawLine(
            QPointF(dims.center_f - gap_offset * math.cos(angle_rad),
                    dims.center_f + gap_offset * math.sin(angle_rad)),
            QPointF(dims.center_f - dx, dims.center_f + dy)
        )

        # Draw center dot if enabled and not drawing outline
        if not is_outline and self.settings.get('dot_enabled', True):
            dot_size = self.settings.get('dot_size', 2)
            if dot_size == 1:
                painter.drawPoint(QPointF(dims.center_f, dims.center_f))
            else:
                painter.drawEllipse(
                    QPointF(dims.center_f, dims.center_f),
                    dot_size / 2, dot_size / 2
                )

    def _draw_diamond(self, painter, dims: Dimensions, is_outline: bool):
        line_length = dims.size // 3
        dot_size = max(2, dims.size // 16)
        pen = self.create_pen(is_outline, 'Diamond')
        painter.setPen(pen)

        # Define diamond points with perfect symmetry
        points = [
            QPointF(dims.center_f, dims.center_f - (dims.gap_f + line_length)),  # Top
            QPointF(dims.center_f + (dims.gap_f + line_length), dims.center_f),  # Right
            QPointF(dims.center_f, dims.center_f + (dims.gap_f + line_length)),  # Bottom
            QPointF(dims.center_f - (dims.gap_f + line_length), dims.center_f)   # Left
        ]

        path = QtGui.QPainterPath()
        path.moveTo(points[0])
        for pt in points[1:]:
            path.lineTo(pt)
        path.lineTo(points[0])
        painter.drawPath(path)

        if not is_outline:
            if self.settings['thickness'] == 1:
                painter.drawPoint(QPointF(dims.center_f, dims.center_f))
            else:
                painter.drawEllipse(
                    QPointF(dims.center_f, dims.center_f),
                    dot_size / 2, dot_size / 2
                )
                
                    

class CustomResolutionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Custom Resolution")
        layout = QVBoxLayout()
        
        # Resolution inputs
        res_layout = QHBoxLayout()
        self.width_input = QLineEdit()
        self.height_input = QLineEdit()
        res_layout.addWidget(QLabel("Width:"))
        res_layout.addWidget(self.width_input)
        res_layout.addWidget(QLabel("Height:"))
        res_layout.addWidget(self.height_input)
        layout.addLayout(res_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

class AdvancedSettingsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.crosshair = None
        self.settings = self.loadSettings()
        self.monitors = self.getMonitors()
        self.initUI()

    def getMonitors(self):
        monitors = []
        for screen in QtWidgets.QApplication.screens():
            geometry = screen.geometry()
            name = screen.name()
            monitors.append({
                'name': name,
                'geometry': geometry,
                'resolutions': [
                    f"{geometry.width()}x{geometry.height()} (Native)",
                    "Custom..."
                ]
            })
        return monitors

    def initUI(self):
        # Setup icon if available.
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons', 'crossgen.ico')
        if (os.path.exists(icon_path)):
            app_icon = QtGui.QIcon(icon_path)
            self.setWindowIcon(app_icon)
        
        # Build main layout using helper methods.
        main_layout = QtWidgets.QVBoxLayout()
        tabs = self.setupTabs()
        main_layout.addWidget(tabs)
        buttons = self.setupControlButtons()
        main_layout.addLayout(buttons)
        self.setLayout(main_layout)
        
        self.setWindowTitle('Crossgen 1.4')
        self.setFixedWidth(400)
        
        # Initial update
        self.updateSettingsAvailability(self.shape_combo.currentText())
        self.show()

    def setupTabs(self):
        tabs = QtWidgets.QTabWidget()
        basic_tab = self.setupBasicTab()
        advanced_tab = self.setupAdvancedTab()
        tabs.addTab(basic_tab, "Basic")
        tabs.addTab(advanced_tab, "Advanced")
        return tabs

    def setupBasicTab(self):
        # Basic tab: shape and color settings.
        self.shape_combo = QtWidgets.QComboBox()
        self.shape_combo.addItems(['Crosshair', 'Circle', 'T-Shape', 'X-Shape', 'Diamond'])
        self.shape_combo.currentTextChanged.connect(self.updateSettingsAvailability)
        
        self.fill_style_combo = QtWidgets.QComboBox()
        self.fill_style_combo.addItems(['Full', 'Ring'])
        
        self.size_spin = QtWidgets.QSpinBox()
        self.size_spin.setRange(8, 100)
        self.size_spin.setSingleStep(2)
        self.size_spin.setValue(max(8, self.settings.get('size', 8) // 2 * 2))
        
        self.thickness_spin = QtWidgets.QSpinBox()
        self.thickness_spin.setRange(1, 10)
        self.thickness_spin.setValue(self.settings.get('thickness', 1))
        
        self.gap_spin = QtWidgets.QSpinBox()
        self.gap_spin.setRange(0, 20)
        self.gap_spin.setValue(self.settings.get('gap', 0))
        
        # Group for shape settings.
        shape_group = QtWidgets.QGroupBox("Shape Settings")
        shape_layout = QtWidgets.QVBoxLayout()
        shape_layout.addWidget(QtWidgets.QLabel("Shape:"))
        shape_layout.addWidget(self.shape_combo)
        shape_layout.addWidget(QtWidgets.QLabel("Fill Style:"))
        shape_layout.addWidget(self.fill_style_combo)
        shape_layout.addWidget(QtWidgets.QLabel("Size:"))
        shape_layout.addWidget(self.size_spin)
        shape_layout.addWidget(QtWidgets.QLabel("Line Thickness:"))
        shape_layout.addWidget(self.thickness_spin)
        shape_layout.addWidget(QtWidgets.QLabel("Center Gap:"))
        shape_layout.addWidget(self.gap_spin)
        
        shape_group.setLayout(shape_layout)
        
        # Color settings.
        self.color_button = QtWidgets.QPushButton('Primary Color')
        self.color_button.clicked.connect(lambda: self.openColorPicker('color'))
        
        self.outline_check = QtWidgets.QCheckBox('Enable Outline')
        self.outline_check.setChecked(self.settings.get('outline_enabled', False))
        self.outline_check.stateChanged.connect(self.updateOutlineAvailability)
        
        self.outline_color_button = QtWidgets.QPushButton('Outline Color')
        self.outline_color_button.setEnabled(self.outline_check.isChecked())
        self.outline_color_button.clicked.connect(lambda: self.openColorPicker('outline_color'))
        
        color_group = QtWidgets.QGroupBox("Color Settings")
        color_layout = QtWidgets.QVBoxLayout()
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(self.outline_check)
        color_layout.addWidget(self.outline_color_button)
        color_group.setLayout(color_layout)
        
        # Assemble the basic tab.
        basic_layout = QtWidgets.QVBoxLayout()
        basic_layout.addWidget(shape_group)
        basic_layout.addWidget(color_group)
        basic_tab = QtWidgets.QWidget()
        basic_tab.setLayout(basic_layout)
        
        return basic_tab

    def setupAdvancedTab(self):
        # Advanced tab: opacity and monitor settings.
        advanced_layout = QtWidgets.QVBoxLayout()
        
        # Initialize opacity slider
        self.opacity_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(int(self.settings.get('opacity', 100)))
        
        advanced_layout.addWidget(QtWidgets.QLabel("Crosshair Opacity:"))
        advanced_layout.addWidget(self.opacity_slider)
        
        self.outline_opacity_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.outline_opacity_slider.setRange(10, 100)
        self.outline_opacity_slider.setValue(int(self.settings.get('outline_opacity', 100)))
        
        self.outline_thickness_spin = QtWidgets.QSpinBox()
        self.outline_thickness_spin.setRange(1, 3)
        self.outline_thickness_spin.setValue(self.settings.get('outline_thickness', 1))
        
        # Monitor settings.
        self.monitor_combo = QtWidgets.QComboBox()
        for monitor in self.monitors:
            self.monitor_combo.addItem(monitor['name'])
        
        self.resolution_combo = QtWidgets.QComboBox()
        self.updateResolutionCombo(0)
        
        monitor_group = QtWidgets.QGroupBox("Monitor Settings")
        monitor_layout = QtWidgets.QVBoxLayout()
        monitor_layout.addWidget(QtWidgets.QLabel("Monitor:"))
        monitor_layout.addWidget(self.monitor_combo)
        monitor_layout.addWidget(QtWidgets.QLabel("Resolution:"))
        monitor_layout.addWidget(self.resolution_combo)
        monitor_group.setLayout(monitor_layout)
        
        # Assemble the advanced tab.
        advanced_layout.addWidget(QtWidgets.QLabel("Outline Opacity:"))
        advanced_layout.addWidget(self.outline_opacity_slider)
        advanced_layout.addWidget(QtWidgets.QLabel("Outline Thickness:"))
        advanced_layout.addWidget(self.outline_thickness_spin)
        
        # Add a new group for advanced shape settings
        advanced_shape_group = QtWidgets.QGroupBox("Advanced Shape Settings")
        advanced_shape_layout = QtWidgets.QVBoxLayout()
        
        # Add dot customization
        self.dot_enabled = QtWidgets.QCheckBox('Draw Center Dot')
        self.dot_enabled.setChecked(self.settings.get('dot_enabled', True))
        
        self.dot_size_spin = QtWidgets.QSpinBox()
        self.dot_size_spin.setRange(1, 20)
        self.dot_size_spin.setValue(self.settings.get('dot_size', 2))
        self.dot_size_spin.setEnabled(self.dot_enabled.isChecked())
        
        # Add line style options
        self.line_style_combo = QtWidgets.QComboBox()
        self.line_style_combo.addItems(['Solid', 'Dotted', 'Dashed'])
        
        # Add X angle control
        self.angle_spin = QtWidgets.QSpinBox()
        self.angle_spin.setRange(0, 90)
        self.angle_spin.setValue(self.settings.get('x_angle', 45))
        
        # Add widgets to advanced shape layout
        advanced_shape_layout.addWidget(self.dot_enabled)
        advanced_shape_layout.addWidget(QtWidgets.QLabel("Dot Size:"))
        advanced_shape_layout.addWidget(self.dot_size_spin)
        advanced_shape_layout.addWidget(QtWidgets.QLabel("Line Style:"))
        advanced_shape_layout.addWidget(self.line_style_combo)
        advanced_shape_layout.addWidget(QtWidgets.QLabel("X Angle:"))
        advanced_shape_layout.addWidget(self.angle_spin)
        advanced_shape_group.setLayout(advanced_shape_layout)
        
        # Connect signals
        self.dot_enabled.stateChanged.connect(self.dot_size_spin.setEnabled)
        self.dot_enabled.stateChanged.connect(self.updateCrosshair)
        self.dot_size_spin.valueChanged.connect(self.updateCrosshair)
        self.angle_spin.valueChanged.connect(self.updateCrosshair)
        self.line_style_combo.currentTextChanged.connect(self.updateCrosshair)
        
        # Add the new group to advanced layout before monitor_group
        advanced_layout.addWidget(advanced_shape_group)
        advanced_layout.addWidget(monitor_group)
        
        advanced_tab = QtWidgets.QWidget()
        advanced_tab.setLayout(advanced_layout)
        
        # Connect signals to updateCrosshair
        self.outline_opacity_slider.valueChanged.connect(self.updateCrosshair)
        self.outline_thickness_spin.valueChanged.connect(self.updateCrosshair)
        
        return advanced_tab

    def setupControlButtons(self):
        # Control buttons at the bottom.
        button_layout = QtWidgets.QHBoxLayout()
        
        self.apply_button = QtWidgets.QPushButton('Apply Changes')
        self.apply_button.clicked.connect(self.updateCrosshair)
        button_layout.addWidget(self.apply_button)
        
        self.save_button = QtWidgets.QPushButton('Save Preset')
        self.save_button.clicked.connect(self.savePreset)
        button_layout.addWidget(self.save_button)
        
        self.load_button = QtWidgets.QPushButton('Load Preset')
        self.load_button.clicked.connect(self.loadPreset)
        button_layout.addWidget(self.load_button)
        
        self.clear_button = QtWidgets.QPushButton('Clear Preset')
        self.clear_button.clicked.connect(self.clearPreset)
        button_layout.addWidget(self.clear_button)
        
        return button_layout


    def loadSettings(self):
        settings = QSettings('EnhancedCrossgen', 'Preferences')
        try:
            return json.loads(settings.value('settings', '{}'))
        except:
            return {
                'color': '#FF0000',
                'size': 8,
                'shape': 'Crosshair',  # Changed default shape to Crosshair
                'thickness': 1,
                'fill_style': 'Full',
                'opacity': 100,
                'outline_opacity': 100,
                'outline_enabled': False,
                'outline_color': '#000000',
                'gap': 0,
                'draggable': True,
                'monitor_index': 0,
                'resolution': 'Native',
                'custom_resolution': None,
                'outline_thickness': 1,  # Add this line
                'dot_enabled': True,
                'dot_size': 2,
                'line_style': 'Solid',
                'x_angle': 45,
            }

    def saveSettings(self):
        settings = QSettings('EnhancedCrossgen', 'Preferences')
        settings.setValue('settings', json.dumps(self.settings))

    def updateSettingsAvailability(self, shape):
        # Enable fill style only for Circle shape
        self.fill_style_combo.setEnabled(shape == 'Circle')
        
        # Enable gap for all shapes except Circle
        self.gap_spin.setEnabled(shape in ['Crosshair', 'T-Shape', 'X-Shape', 'Diamond'])
        
        # Enable X angle only for X-Shape
        self.angle_spin.setEnabled(shape == 'X-Shape')
        
        # Enable outline for all shapes
        self.outline_check.setEnabled(True)
        self.updateOutlineAvailability()

    def updateOutlineAvailability(self):
        self.outline_color_button.setEnabled(self.outline_check.isChecked())

    def openColorPicker(self, color_type):
        color = QtWidgets.QColorDialog.getColor()
        if (color.isValid()):
            self.settings[color_type] = color.name()
            if self.crosshair:
                self.updateCrosshair()

    def updateResolutionCombo(self, index):
        self.resolution_combo.clear()
        self.resolution_combo.addItems(self.monitors[index]['resolutions'])

    def handleResolutionChange(self, index):
        if self.resolution_combo.currentText() == "Custom...":
            dialog = CustomResolutionDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                try:
                    width = int(dialog.width_input.text())
                    height = int(dialog.height_input.text())
                    self.settings['custom_resolution'] = (width, height)
                    self.updateCrosshair()
                except ValueError:
                    QtWidgets.QMessageBox.warning(self, "Error", "Invalid resolution values")

    def updateCrosshair(self):
        self.settings.update({
            # ...existing settings...
            'x_angle': self.angle_spin.value(),
            'dot_enabled': self.dot_enabled.isChecked(),
            'dot_size': self.dot_size_spin.value() if self.dot_enabled.isChecked() else 0,
            'line_style': self.line_style_combo.currentText()
        })
        try:
            # Update settings from UI controls
            self.settings.update({
                'monitor_index': self.monitor_combo.currentIndex(),
                'resolution': self.resolution_combo.currentText(),
                'shape': self.shape_combo.currentText(),  # Make sure this is being set correctly
                'size': self.size_spin.value() // 2 * 2,
                'thickness': self.thickness_spin.value(),
                'gap': self.gap_spin.value(),
                'opacity': self.opacity_slider.value(),
                'outline_opacity': self.outline_opacity_slider.value(),
                'outline_enabled': self.outline_check.isChecked(),
                'fill_style': self.fill_style_combo.currentText(),
                'color': self.settings.get('color', '#FF0000'),
                'outline_color': self.settings.get('outline_color', '#000000'),
                'outline_thickness': self.outline_thickness_spin.value()
            })

            # Close existing crosshair if it exists
            if hasattr(self, 'crosshair') and self.crosshair:
                self.crosshair.close()

            # Create new crosshair with updated settings
            self.crosshair = CrosshairCanvas(self.settings)
            
            # Set window opacity
            self.crosshair.setWindowOpacity(self.settings['opacity'] / 100)
            
            # Position the crosshair
            screen = QtWidgets.QApplication.screens()[self.settings['monitor_index']]
            geometry = screen.geometry()
            x = int(geometry.x() + (geometry.width() - self.settings['size']) // 2)
            y = int(geometry.y() + (geometry.height() - self.settings['size']) // 2)
            self.crosshair.move(x, y)
            
            # Show the crosshair
            self.crosshair.show()
            
            # Save settings
            self.saveSettings()
            
        except Exception as e:
            import traceback
            error_msg = f'Failed to update crosshair: {str(e)}\n{traceback.format_exc()}'
            QtWidgets.QMessageBox.warning(self, 'Error', error_msg)

    def savePreset(self):
        name, ok = QtWidgets.QInputDialog.getText(self, 'Save Preset', 'Enter preset name:')
        if not ok or not name.strip():
            return  # Exit if no name is entered

        presets_dir = os.path.join(os.path.expanduser("~"), ".crossgen", "presets")
        os.makedirs(presets_dir, exist_ok=True)  # Ensure directory exists

        preset_path = os.path.join(presets_dir, f"{name.strip()}.json")

        try:
            with open(preset_path, "w") as f:
                json.dump(self.settings, f, indent=4)
            QtWidgets.QMessageBox.information(self, "Preset Saved", f"Preset '{name}' saved successfully!")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to save preset: {str(e)}")


    def loadPreset(self):
        presets_dir = os.path.join(os.path.expanduser("~"), ".crossgen", "presets")

        if not os.path.exists(presets_dir) or not os.listdir(presets_dir):
            QtWidgets.QMessageBox.warning(self, "Error", "No presets found!")
            return

        preset_files = [f.replace(".json", "") for f in os.listdir(presets_dir) if f.endswith(".json")]
        
        preset, ok = QtWidgets.QInputDialog.getItem(self, "Load Preset", "Select a preset:", preset_files, 0, False)
        
        if not ok or not preset:
            return  # User canceled selection

        preset_path = os.path.join(presets_dir, f"{preset}.json")

        try:
            with open(preset_path, "r") as f:
                self.settings = json.load(f)
            
            # Update UI elements to match loaded preset
            self.shape_combo.setCurrentText(self.settings['shape'])
            self.size_spin.setValue(self.settings['size'])
            self.thickness_spin.setValue(self.settings['thickness'])
            self.opacity_slider.setValue(self.settings['opacity'])
            self.fill_style_combo.setCurrentText(self.settings['fill_style'])
            self.outline_check.setChecked(self.settings['outline_enabled'])
            
            self.updateCrosshair()
            QtWidgets.QMessageBox.information(self, "Preset Loaded", f"Preset '{preset}' loaded successfully!")
        
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to load preset: {str(e)}")

    def clearPreset(self):
        presets_dir = os.path.join(os.path.expanduser("~"), ".crossgen", "presets")

        if not os.path.exists(presets_dir) or not os.listdir(presets_dir):
            QtWidgets.QMessageBox.warning(self, "Error", "No presets found to delete!")
            return

        preset_files = [f.replace(".json", "") for f in os.listdir(presets_dir) if f.endswith(".json")]
        
        preset, ok = QtWidgets.QInputDialog.getItem(self, "Clear Preset", "Select a preset to delete:", preset_files, 0, False)
        
        if not ok or not preset:
            return  # User canceled selection

        preset_path = os.path.join(presets_dir, f"{preset}.json")

        try:
            os.remove(preset_path)
            QtWidgets.QMessageBox.information(self, "Preset Deleted", f"Preset '{preset}' has been deleted successfully.")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to delete preset: {str(e)}")


    def closeEvent(self, event):
        if self.crosshair:
            self.crosshair.close()
        event.accept()

    def updateXAngleAvailability(self, shape):
        """Enable X Angle spinner only for X-Shape"""
        self.angle_spin.setEnabled(shape == 'X-Shape')

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    
    # Use the helper function to obtain the application icon
    app_icon = get_app_icon()
    if app_icon:
        app.setWindowIcon(app_icon)
    
    # Create and show the main window (AdvancedSettingsWindow should be imported or defined above)
    ex = AdvancedSettingsWindow()
    
    if app_icon:
        ex.setWindowIcon(app_icon)
        try:
            import ctypes
            myappid = 'crossgen.1.3.0'  # Arbitrary unique string for Windows taskbar icon grouping
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass
    
    app.exec_()
