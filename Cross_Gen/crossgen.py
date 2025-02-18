from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QSettings, QPoint, QPointF
from PyQt5.QtWidgets import QComboBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
import json
import os

class CrosshairColors:
    PRIMARY = 'red'
    OUTLINE = 'black'

class CrosshairCanvas(QtWidgets.QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings.copy()  # Create a copy of settings
        self.initUI()
        self.gap = self.settings.get('gap', 0)  # Ensure gap is initialized

    def initUI(self):
        print("Initializing CrosshairCanvas with size:", self.settings['size'])
        # Calculate even size with strict minimum of 8
        self.size = max(8, self.settings['size'])
        if self.size % 2 != 0:
            self.size += 1
        self.center = self.size // 2
        self.gap = min(self.settings.get('gap', 0), self.center - 1)
        
        # Set window properties
        self.setFixedSize(self.size, self.size)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(False)

        # Position window at screen center
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        center_x = int(screen.center().x() - self.size // 2)
        center_y = int(screen.center().y() - self.size // 2)
        self.move(center_x, center_y)

    def _create_outline_pen(self):
        pen = QtGui.QPen(QtGui.QColor(self.settings['outline_color']))
        # Use outline_thickness setting instead of fixed increment
        pen.setWidth(self.settings['thickness'] + self.settings.get('outline_thickness', 1))
        pen.setCapStyle(Qt.FlatCap)
        return pen

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        shape = self.settings.get('shape', 'Crosshair')
        size = self.settings['size']
        center = size // 2
        
        # Draw outline first if enabled
        if self.settings.get('outline_enabled', False):
            painter.setOpacity(self.settings.get('outline_opacity', 100) / 100)
            self._draw_shape(painter, shape, size, center, True)

        # Then draw main shape
        painter.setOpacity(self.settings.get('opacity', 100) / 100)
        pen = QtGui.QPen(QtGui.QColor(self.settings['color']), 
                        self.settings['thickness'])
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        self._draw_shape(painter, shape, size, center, False)
        
        painter.end()

    def _draw_shape(self, painter, shape, size, center, is_outline):
        print(f"Drawing shape: {shape} with size: {size} and center: {center}")
        # Convert center to float for consistent point handling
        center_f = float(center)
        size_f = float(size)
        gap_f = float(self.gap)
        
        if shape == 'Crosshair':
            self._draw_crosshair(painter, size, center, is_outline)
        elif shape == 'Circle':
            self._draw_circle(painter, size, center, is_outline)
        elif shape == 'T-Shape':
            self._draw_t_shape(painter, size, center, is_outline)
        elif shape == 'X-Shape':
            self._draw_x_shape(painter, size, center, is_outline)
        elif shape == 'Diamond':
            self._draw_diamond(painter, size, center, is_outline)

    def _draw_crosshair(self, painter, size, center, is_outline):
        """Draw crosshair with proper outline and main shape ordering"""
        # Convert to float for precise drawing and ensure minimum size
        center_f = float(center)
        size_f = float(max(8, size))  # Ensure minimum size of 8
        gap_f = float(min(self.gap, center - 1))  # Prevent gap from exceeding center
        
        if is_outline:
            outline_pen = self._create_outline_pen()
            outline_pen.setCapStyle(Qt.RoundCap)
            outline_pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(outline_pen)
        else:
            pen = QtGui.QPen(QtGui.QColor(self.settings['color']), 
                            self.settings['thickness'])
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)

        # Draw the crosshair lines with size checks
        if size_f >= 8:  # Only draw if we have minimum size
            # Vertical lines
            painter.drawLine(QPointF(center_f, 0), 
                            QPointF(center_f, center_f - gap_f))
            painter.drawLine(QPointF(center_f, center_f + gap_f), 
                            QPointF(center_f, size_f))
            
            # Horizontal lines
            painter.drawLine(QPointF(0, center_f), 
                            QPointF(center_f - gap_f, center_f))
            painter.drawLine(QPointF(center_f + gap_f, center_f), 
                            QPointF(size_f, center_f))

            # Draw center dot for small sizes
            if size_f <= 12 and not is_outline:
                painter.drawPoint(QPointF(center_f, center_f))

    def _draw_circle(self, painter, size, center, is_outline):
        """Draw a circle with consistent smooth edges for both outline and main shape"""
        # Force high quality rendering for circles
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing, True)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        
        # Calculate exact center and radius using floating point
        center_point = QPointF(size/2, size/2)
        radius = (size-2)/2  # Base radius
        
        if is_outline:
            # Set up outline pen with smooth edges
            outline_pen = QtGui.QPen(QtGui.QColor(self.settings['outline_color']))
            outline_thickness = self.settings.get('outline_thickness', 1)
            outline_pen.setWidth(outline_thickness)
            outline_pen.setCapStyle(Qt.RoundCap)
            outline_pen.setJoinStyle(Qt.RoundJoin)
            
            # Draw two circles for outline effect
            painter.setPen(outline_pen)
            painter.setBrush(Qt.NoBrush)
            
            # Outer circle
            painter.drawEllipse(center_point, 
                              radius + outline_thickness/2,
                              radius + outline_thickness/2)
            
        else:
            # Set up main shape pen
            pen = QtGui.QPen(QtGui.QColor(self.settings['color']), 
                            self.settings['thickness'])
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            
            # Handle fill style
            fill_style = self.settings.get('fill_style', 'Ring')
            if (fill_style == 'Full'):
                brush = QtGui.QBrush(QtGui.QColor(self.settings['color']))
                painter.setBrush(brush)
            else:
                painter.setBrush(Qt.NoBrush)
            
            # Draw main circle
            painter.drawEllipse(center_point, radius, radius)

    def _draw_t_shape(self, painter, size, center, is_outline):
        """Draw a perfectly centered and symmetrical T-shape"""
        # Convert to float for precise calculations
        center_f = float(center)
        size_f = float(size)
        gap_f = float(self.gap)
        line_length = size // 3
        dot_size = max(2, size // 16)

        if is_outline:
            painter.setPen(self._create_outline_pen())
        else:
            pen = QtGui.QPen(QtGui.QColor(self.settings['color']), 
                            self.settings['thickness'])
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)

        # Draw horizontal line of T
        painter.drawLine(
            QPointF(center_f - gap_f - line_length, center_f),
            QPointF(center_f - gap_f, center_f)
        )
        painter.drawLine(
            QPointF(center_f + gap_f, center_f),
            QPointF(center_f + gap_f + line_length, center_f)
        )
        
        # Draw vertical line of T
        painter.drawLine(
            QPointF(center_f, center_f + gap_f),
            QPointF(center_f, center_f + gap_f + line_length)
        )

        # Draw center dot if not outline
        if not is_outline:
            if self.settings['thickness'] == 1:
                painter.drawPoint(QPointF(center_f, center_f))
            else:
                painter.drawEllipse(
                    QPointF(center_f, center_f),
                    dot_size/2, dot_size/2
                )

    def _draw_x_shape(self, painter, size, center, is_outline):
        """Draw a perfectly centered and symmetrical X-shape"""
        # Convert values to float for precise calculations
        center_f = float(center)
        size_f = float(size)
        gap_f = float(self.gap)
        
        # Calculate line length as 1/3 of size for better proportions
        line_length = size_f / 3
        
        # Calculate diagonal offset for 45-degree lines
        # Using math.sqrt(2)/2 ≈ 0.707 for precise 45-degree angle
        diagonal_factor = 0.707
        
        if is_outline:
            pen = self._create_outline_pen()
        else:
            pen = QtGui.QPen(QtGui.QColor(self.settings['color']), 
                            self.settings['thickness'])
        
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)

        # Calculate gap offset for 45-degree lines
        gap_offset = gap_f * diagonal_factor
        
        # Draw the four segments of the X with proper gap
        # Top-left to center
        painter.drawLine(
            QPointF(center_f - line_length * diagonal_factor, 
                    center_f - line_length * diagonal_factor),
            QPointF(center_f - gap_offset, center_f - gap_offset)
        )
        
        # Center to bottom-right
        painter.drawLine(
            QPointF(center_f + gap_offset, center_f + gap_offset),
            QPointF(center_f + line_length * diagonal_factor, 
                    center_f + line_length * diagonal_factor)
        )
        
        # Top-right to center
        painter.drawLine(
            QPointF(center_f + line_length * diagonal_factor, 
                    center_f - line_length * diagonal_factor),
            QPointF(center_f + gap_offset, center_f - gap_offset)
        )
        
        # Center to bottom-left
        painter.drawLine(
            QPointF(center_f - gap_offset, center_f + gap_offset),
            QPointF(center_f - line_length * diagonal_factor, 
                    center_f + line_length * diagonal_factor)
        )

        # Draw center dot if not outline and appropriate size/thickness
        if not is_outline:
            dot_size = max(2, size // 16)  # Scale dot size with crosshair size
            if self.settings['thickness'] == 1:
                painter.drawPoint(QPointF(center_f, center_f))
            else:
                painter.drawEllipse(
                    QPointF(center_f, center_f),
                    dot_size/2, dot_size/2
                )

    def _draw_diamond(self, painter, size, center, is_outline):
        """Draw a perfectly centered and symmetrical diamond shape"""
        # Convert values to float for precise calculations
        center_f = float(center)
        size_f = float(size)
        gap_f = float(self.gap)
        line_length = size // 3  # Scale based on size
        dot_size = max(2, size // 16)

        if is_outline:
            painter.setPen(self._create_outline_pen())
        else:
            pen = QtGui.QPen(QtGui.QColor(self.settings['color']), 
                            self.settings['thickness'])
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)

        # Calculate diamond points with perfect symmetry
        points = [
            QPointF(center_f, center_f - (gap_f + line_length)),  # Top
            QPointF(center_f + (gap_f + line_length), center_f),  # Right
            QPointF(center_f, center_f + (gap_f + line_length)),  # Bottom
            QPointF(center_f - (gap_f + line_length), center_f)   # Left
        ]

        # Draw diamond shape
        path = QtGui.QPainterPath()
        path.moveTo(points[0])
        for i in range(1, len(points)):
            path.lineTo(points[i])
        path.lineTo(points[0])  # Close the shape
        painter.drawPath(path)

        # Draw center dot if not outline
        if not is_outline:
            if self.settings['thickness'] == 1:
                painter.drawPoint(QPointF(center_f, center_f))
            else:
                painter.drawEllipse(
                    QPointF(center_f, center_f),
                    dot_size/2, dot_size/2
                )

    def _draw_dot_matrix(self, painter, size, center, is_outline):
        spacing = self.settings.get('dot_spacing', 4)
        for x in range(0, size, spacing):
            for y in range(0, size, spacing):
                painter.drawPoint(QPointF(x, y))
                    
    def drawShape(self, painter, shape, size, center, is_outline):
        # This is now an alias for _draw_shape for backward compatibility
        self._draw_shape(painter, shape, size, center, is_outline)

class SettingsManager:
    def __init__(self):
        self.settings = QSettings('EnhancedCrossgen', 'Preferences')

    def load(self):
        try:
            return json.loads(self.settings.value('settings', '{}'))
        except:
            return {'color': '#FF0000', 'size': 8, 'shape': 'Round', 'thickness': 1, 'gap': 0}

    def save(self, settings):
        self.settings.setValue('settings', json.dumps(settings))                    
                    

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
        # Initialize all UI elements first
        
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons', 'crossgen.ico')
        if (os.path.exists(icon_path)):
            app_icon = QtGui.QIcon(icon_path)
            self.setWindowIcon(app_icon)

        self.shape_combo = QtWidgets.QComboBox()
        self.fill_style_combo = QtWidgets.QComboBox()
        self.size_spin = QtWidgets.QSpinBox()
        self.color_button = QtWidgets.QPushButton('Primary Color')
        self.outline_check = QtWidgets.QCheckBox('Enable Outline')
        self.outline_color_button = QtWidgets.QPushButton('Outline Color')  # Initialize before connecting signals
        self.gap_spin = QtWidgets.QSpinBox()
        self.thickness_spin = QtWidgets.QSpinBox()
        self.opacity_slider = QtWidgets.QSlider(Qt.Horizontal)

        # Now connect signals after all elements are initialized
        self.shape_combo.currentTextChanged.connect(self.updateSettingsAvailability)
        self.outline_check.stateChanged.connect(self.updateOutlineAvailability)
        
        # Continue with the rest of the UI setup...
        layout = QtWidgets.QVBoxLayout()
        
        tabs = QtWidgets.QTabWidget()
        
        # Basic Settings Tab
        basic_tab = QtWidgets.QWidget()
        basic_layout = QtWidgets.QVBoxLayout()
        
        # Shape Selection
        shape_group = QtWidgets.QGroupBox("Shape Settings")
        shape_layout = QtWidgets.QVBoxLayout()
        
        self.shape_combo.addItems([
            'Crosshair',
            'Circle', 
            'T-Shape',
            'X-Shape',
            'Diamond'
        ])
        shape_layout.addWidget(QtWidgets.QLabel("Shape:"))
        shape_layout.addWidget(self.shape_combo)
        
        # Fill Style for Round shape
        self.fill_style_combo.addItems(['Full', 'Ring'])
        shape_layout.addWidget(QtWidgets.QLabel("Fill Style:"))
        shape_layout.addWidget(self.fill_style_combo)
        
        # Size Settings
        self.size_spin.setRange(8, 100)  # Start from 8 instead of 4
        self.size_spin.setSingleStep(2)  # Ensures only even numbers
        self.size_spin.setValue(max(8, self.settings.get('size', 8) // 2 * 2))  # Minimum size of 8
        shape_layout.addWidget(QtWidgets.QLabel("Size:"))
        shape_layout.addWidget(self.size_spin)
        
        # Move thickness and gap settings to basic tab
        self.thickness_spin.setRange(1, 10)
        self.thickness_spin.setValue(self.settings.get('thickness', 1))
        shape_layout.addWidget(QtWidgets.QLabel("Line Thickness:"))
        shape_layout.addWidget(self.thickness_spin)
        
        self.gap_spin.setRange(0, 20)
        self.gap_spin.setValue(self.settings.get('gap', 0))
        shape_layout.addWidget(QtWidgets.QLabel("Center Gap:"))
        shape_layout.addWidget(self.gap_spin)
        
        shape_group.setLayout(shape_layout)
        basic_layout.addWidget(shape_group)
        
        # Color Settings
        color_group = QtWidgets.QGroupBox("Color Settings")
        color_layout = QtWidgets.QVBoxLayout()
        
        self.color_button.clicked.connect(lambda: self.openColorPicker('color'))
        color_layout.addWidget(self.color_button)
        
        self.outline_check.stateChanged.connect(self.updateOutlineAvailability)
        self.outline_check.setChecked(self.settings.get('outline_enabled', False))
        color_layout.addWidget(self.outline_check)
        
        self.outline_color_button.clicked.connect(lambda: self.openColorPicker('outline_color'))
        self.outline_color_button.setEnabled(self.outline_check.isChecked())  # Set initial enabled state
        color_layout.addWidget(self.outline_color_button)
        
        color_group.setLayout(color_layout)
        basic_layout.addWidget(color_group)
        
        basic_tab.setLayout(basic_layout)
        tabs.addTab(basic_tab, "Basic")
        
        # Advanced Settings Tab
        advanced_tab = QtWidgets.QWidget()
        advanced_layout = QtWidgets.QVBoxLayout()
        
        # Remove thickness and gap settings from advanced tab
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(int(self.settings.get('opacity', 100)))
        advanced_layout.addWidget(QtWidgets.QLabel("Opacity:"))
        advanced_layout.addWidget(self.opacity_slider)

        self.outline_opacity_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.outline_opacity_slider.setRange(10, 100)
        self.outline_opacity_slider.setValue(int(self.settings.get('outline_opacity', 100)))
        self.outline_opacity_slider.valueChanged.connect(self.updateCrosshair)  # Add this line
        advanced_layout.addWidget(QtWidgets.QLabel("Outline Opacity:"))
        advanced_layout.addWidget(self.outline_opacity_slider)

        self.outline_thickness_spin = QtWidgets.QSpinBox()
        self.outline_thickness_spin.setRange(1, 3)
        self.outline_thickness_spin.setValue(self.settings.get('outline_thickness', 1))
        self.outline_thickness_spin.valueChanged.connect(self.updateCrosshair)
        advanced_layout.addWidget(QtWidgets.QLabel("Outline Thickness:"))
        advanced_layout.addWidget(self.outline_thickness_spin)
        
        # Move Monitor Settings to Advanced Tab
        monitor_group = QtWidgets.QGroupBox("Monitor Settings")
        monitor_layout = QtWidgets.QVBoxLayout()

        # Monitor selection
        self.monitor_combo = QComboBox()
        for monitor in self.monitors:
            self.monitor_combo.addItem(monitor['name'])
        monitor_layout.addWidget(QLabel("Monitor:"))
        monitor_layout.addWidget(self.monitor_combo)

        # Resolution selection
        self.resolution_combo = QComboBox()
        self.updateResolutionCombo(0)
        monitor_layout.addWidget(QLabel("Resolution:"))
        monitor_layout.addWidget(self.resolution_combo)

        monitor_group.setLayout(monitor_layout)
        advanced_layout.addWidget(monitor_group)  # Add to advanced tab instead of basic tab

        advanced_tab.setLayout(advanced_layout)
        tabs.addTab(advanced_tab, "Advanced")
        
        layout.addWidget(tabs)
        
        # Control buttons
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
        self.clear_button.clicked.connect(self.clearPreset)  # Connect new function
        button_layout.addWidget(self.clear_button)

        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.setWindowTitle('Crossgen 1.3')
        self.setFixedWidth(400)
        
        # Connect signals
        self.shape_combo.currentTextChanged.connect(self.updateSettingsAvailability)
        self.outline_check.stateChanged.connect(self.updateOutlineAvailability)
        
        # Initial update
        self.updateSettingsAvailability(self.shape_combo.currentText())
        self.show()

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
                'outline_thickness': 1  # Add this line
            }

    def saveSettings(self):
        settings = QSettings('EnhancedCrossgen', 'Preferences')
        settings.setValue('settings', json.dumps(self.settings))

    def updateSettingsAvailability(self, shape):
        # Enable fill style only for Circle shape
        self.fill_style_combo.setEnabled(shape == 'Circle')
        
        # Enable gap for all shapes
        self.gap_spin.setEnabled(shape in ['Crosshair', 'T-Shape', 'X-Shape', 'Diamond'])
        
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

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    
    # Set up icon path - look in same directory as script first
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons', 'crossgen.ico')
    
    # Fallback paths if main path doesn't exist
    fallback_paths = [
        os.path.join(os.getcwd(), 'icons', 'crossgen.ico'),
        os.path.join(os.getcwd(), 'crossgen.ico')
    ]
    
    # Try main path first, then fallbacks
    if os.path.exists(icon_path):
        app_icon = QtGui.QIcon(icon_path)
    else:
        # Try fallback paths
        for path in fallback_paths:
            if os.path.exists(path):
                icon_path = path
                app_icon = QtGui.QIcon(path)
                break
        else:
            print("Warning: Icon file not found in any location")
            app_icon = None
    
    # Apply icon if we found one
    if app_icon:
        # Set application icon (shows in taskbar)
        app.setWindowIcon(app_icon)
        
        # Create and show main window
        ex = AdvancedSettingsWindow()
        
        # Set window-specific icon (shows in titlebar)
        ex.setWindowIcon(app_icon)
        
        # Optional: Set taskbar icon for Windows
        try:
            import ctypes
            myappid = 'crossgen.1.3.0'  # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
    else:
        ex = AdvancedSettingsWindow()
    
    app.exec_()
