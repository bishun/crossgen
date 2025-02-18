from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QSettings, QPoint
from PyQt5.QtWidgets import QComboBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
import json
import os

class CrosshairCanvas(QtWidgets.QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.initUI()

    def initUI(self):
        even_size = self.settings['size'] // 2 * 2  # Ensure even size
        self.setFixedSize(even_size, even_size)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(False)  # Make it non-interactable

        screen = QtWidgets.QApplication.primaryScreen().geometry()
        center_pos = QPoint(screen.center().x() - even_size // 2, screen.center().y() - even_size // 2)
        self.move(center_pos)
        self.show()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        # Only enable anti-aliasing for thicker lines or non-Crosshair shapes
        if self.settings['thickness'] > 1 or self.settings['shape'] != 'Crosshair':
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
        self.drawCrosshair(painter)

    def drawCrosshair(self, painter):
        size = self.settings['size'] if self.settings['size'] % 2 == 0 else self.settings['size'] + 1
        center = size // 2
        shape = self.settings['shape']

        if self.settings.get('outline_enabled', False):
            outline_pen = QtGui.QPen(QtGui.QColor(self.settings['outline_color']), 
                                    self.settings['thickness'] + 2)
            outline_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(outline_pen)
            self.drawShape(painter, shape, size, center, True)

        # Draw primary shape
        pen = QtGui.QPen(QtGui.QColor(self.settings['color']), self.settings['thickness'])
        if self.settings['thickness'] == 1:
            pen.setCosmetic(True)
            painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
        pen.setCapStyle(Qt.FlatCap)
        painter.setPen(pen)
        self.drawShape(painter, shape, size, center, False)

    def drawShape(self, painter, shape, size, center, is_outline):
        gap = self.settings.get('gap', 0)
        
        if shape == 'Crosshair':
            # Draw outline if enabled
            if self.settings.get('outline_enabled', False):
                outline_pen = QtGui.QPen(QtGui.QColor(self.settings['outline_color']), 
                                        self.settings['thickness'] + 2)
                outline_pen.setCapStyle(Qt.FlatCap)  # Use flat caps for consistent appearance
                painter.setPen(outline_pen)
                
                # Draw outline covering full length including edges
                painter.drawLine(QPoint(center, 0), QPoint(center, center - gap))  # Top half
                painter.drawLine(QPoint(center, center + gap), QPoint(center, size))  # Bottom half
                painter.drawLine(QPoint(0, center), QPoint(center - gap, center))  # Left half
                painter.drawLine(QPoint(center + gap, center), QPoint(size, center))  # Right half

            # Draw primary shape
            pen = QtGui.QPen(QtGui.QColor(self.settings['color']), self.settings['thickness'])
            if self.settings['thickness'] == 1:
                pen.setCosmetic(True)
                painter.setRenderHint(QtGui.QPainter.Antialiasing, False)
            pen.setCapStyle(Qt.FlatCap)  # Use flat caps for the main crosshair
            painter.setPen(pen)

            # Draw main crosshair with same coordinates as outline
            painter.drawLine(QPoint(center, 0), QPoint(center, center - gap))  # Top half
            painter.drawLine(QPoint(center, center + gap), QPoint(center, size))  # Bottom half
            painter.drawLine(QPoint(0, center), QPoint(center - gap, center))  # Left half
            painter.drawLine(QPoint(center + gap, center), QPoint(size, center))  # Right half
        elif shape == 'Circle':  # Changed from 'Round' to 'Circle'
            fill_style = self.settings.get('fill_style', 'Ring')
            
            # Draw outline if enabled
            if self.settings.get('outline_enabled', False):
                outline_pen = QtGui.QPen(QtGui.QColor(self.settings['outline_color']), 
                                        self.settings['thickness'] + 2)
                painter.setPen(outline_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(0, 0, size - 1, size - 1)

            # Draw primary shape
            pen = QtGui.QPen(QtGui.QColor(self.settings['color']), self.settings['thickness'])
            painter.setPen(pen)
            
            if fill_style == 'Full':
                brush = QtGui.QBrush(QtGui.QColor(self.settings['color']))
                painter.setBrush(brush)
            else:
                painter.setBrush(Qt.NoBrush)
            
            painter.drawEllipse(0, 0, size - 1, size - 1)
        elif shape == 'T-Shape':
            # Calculate proportional sizes
            gap = self.settings.get('gap', 4)
            dot_size = max(2, size // 16)
            line_length = size // 3

            if self.settings.get('outline_enabled', False) and is_outline:
                # Set outline pen
                outline_pen = QtGui.QPen(QtGui.QColor(self.settings['outline_color']), 
                                        self.settings['thickness'] + 2)
                outline_pen.setCapStyle(Qt.FlatCap)
                painter.setPen(outline_pen)
            
            # Draw horizontal lines (arms) with gap from center
            painter.drawLine(  # Left arm
                QPoint(center - gap - line_length, center),
                QPoint(center - gap, center)
            )
            painter.drawLine(  # Right arm
                QPoint(center + gap, center),
                QPoint(center + gap + line_length, center)
            )
            
            # Draw vertical line below center
            painter.drawLine(
                QPoint(center, center + gap),
                QPoint(center, center + gap + line_length)
            )
            
            # Draw center dot (only for main shape, not outline)
            if not is_outline:
                if self.settings['thickness'] == 1:
                    painter.drawPoint(QPoint(center, center))
                else:
                    painter.drawEllipse(
                        center - dot_size//2,
                        center - dot_size//2,
                        dot_size,
                        dot_size
                    )
        elif shape == 'X-Shape':
            # Calculate gap and line lengths
            gap = self.settings.get('gap', 4)
            line_length = size // 3  # Proportional line length
            
            if self.settings.get('outline_enabled', False) and is_outline:
                # Set outline pen
                outline_pen = QtGui.QPen(QtGui.QColor(self.settings['outline_color']), 
                                        self.settings['thickness'] + 2)
                outline_pen.setCapStyle(Qt.FlatCap)
                painter.setPen(outline_pen)
            
            # Draw diagonal lines with gap
            # Top-left to bottom-right line
            painter.drawLine(  # Upper segment
                QPoint(0, 0),
                QPoint(center - gap, center - gap)
            )
            painter.drawLine(  # Lower segment
                QPoint(center + gap, center + gap),
                QPoint(size, size)
            )
            
            # Top-right to bottom-left line
            painter.drawLine(  # Upper segment
                QPoint(size, 0),
                QPoint(center + gap, center - gap)
            )
            painter.drawLine(  # Lower segment
                QPoint(center - gap, center + gap),
                QPoint(0, size)
            )
        elif shape == 'Diamond':
            # Calculate proportional sizes
            gap = self.settings.get('gap', 4)
            dot_size = max(2, size // 16)
            line_length = size // 3

            # Set outline pen if enabled
            if self.settings.get('outline_enabled', False) and is_outline:
                outline_pen = QtGui.QPen(QtGui.QColor(self.settings['outline_color']), 
                                        self.settings['thickness'] + 2)
                outline_pen.setCapStyle(Qt.FlatCap)
                painter.setPen(outline_pen)
            else:
                # Set primary color pen
                pen = QtGui.QPen(QtGui.QColor(self.settings['color']), self.settings['thickness'])
                pen.setCapStyle(Qt.FlatCap)
                painter.setPen(pen)

            # Calculate diamond points with gap
            points = [
                QPoint(center, center - gap - line_length),  # Top
                QPoint(center + gap + line_length, center),  # Right
                QPoint(center, center + gap + line_length),  # Bottom
                QPoint(center - gap - line_length, center)   # Left
            ]

            # Draw four separate lines to create the diamond outline
            painter.drawLine(points[0], points[1])  # Top-right
            painter.drawLine(points[1], points[2])  # Right-bottom
            painter.drawLine(points[2], points[3])  # Bottom-left
            painter.drawLine(points[3], points[0])  # Left-top

            # Draw center dot (only for main shape, not outline)
            if not is_outline:
                if self.settings['thickness'] == 1:
                    painter.drawPoint(QPoint(center, center))
                else:
                    painter.drawEllipse(
                        center - dot_size//2,
                        center - dot_size//2,
                        dot_size,
                        dot_size
                    )
        elif shape == 'Dot Matrix':
            spacing = self.settings.get('dot_spacing', 4)
            for x in range(0, size, spacing):
                for y in range(0, size, spacing):
                    painter.drawPoint(x, y)
                    

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
        
        self.gap_spin.setRange(0, 20)
        self.gap_spin.setValue(self.settings.get('gap', 0))
        advanced_layout.addWidget(QtWidgets.QLabel("Center Gap:"))
        advanced_layout.addWidget(self.gap_spin)
        
        self.thickness_spin.setRange(1, 10)
        self.thickness_spin.setValue(self.settings.get('thickness', 1))
        advanced_layout.addWidget(QtWidgets.QLabel("Line Thickness:"))
        advanced_layout.addWidget(self.thickness_spin)
        
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(int(self.settings.get('opacity', 100)))
        advanced_layout.addWidget(QtWidgets.QLabel("Opacity:"))
        advanced_layout.addWidget(self.opacity_slider)
        
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
        self.setWindowTitle('Crossgen 1.2')
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
                'outline_enabled': False,
                'outline_color': '#000000',
                'gap': 0,
                'draggable': True,
                'monitor_index': 0,
                'resolution': 'Native',
                'custom_resolution': None
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
            # Update settings
            self.settings.update({
                'monitor_index': self.monitor_combo.currentIndex(),
                'resolution': self.resolution_combo.currentText(),
                'shape': self.shape_combo.currentText(),
                'size': self.size_spin.value() // 2 * 2,  # Force even number
                'thickness': self.thickness_spin.value(),
                'gap': self.gap_spin.value(),
                'opacity': self.opacity_slider.value(),
                'outline_enabled': self.outline_check.isChecked(),
                'fill_style': self.fill_style_combo.currentText()
            })

            # Close existing crosshair
            if self.crosshair:
                self.crosshair.close()

            # Get selected monitor and resolution
            monitor_index = self.settings['monitor_index']
            resolution_text = self.settings['resolution']
            
            # Simplified resolution handling
            if "Custom..." in resolution_text:
                if 'custom_resolution' in self.settings and self.settings['custom_resolution']:
                    width, height = self.settings['custom_resolution']
                else:
                    dialog = CustomResolutionDialog(self)
                    if dialog.exec_() == QDialog.Accepted:
                        try:
                            width = int(dialog.width_input.text())
                            height = int(dialog.height_input.text())
                            self.settings['custom_resolution'] = (width, height)
                        except ValueError:
                            raise ValueError("Invalid custom resolution values")
                    else:
                        # User cancelled, use native resolution
                        geometry = self.monitors[monitor_index]['geometry']
                        width, height = geometry.width(), geometry.height()
            else:
                # Native resolution
                geometry = self.monitors[monitor_index]['geometry']
                width, height = geometry.width(), geometry.height()

            # Move crosshair to selected monitor
            screen = QtWidgets.QApplication.screens()[monitor_index]
            screen_geometry = screen.geometry()
            
            self.crosshair = CrosshairCanvas(self.settings)
            center_x = screen_geometry.x() + (screen_geometry.width() - self.settings['size']) // 2
            center_y = screen_geometry.y() + (screen_geometry.height() - self.settings['size']) // 2
            self.crosshair.move(center_x, center_y)
            self.crosshair.setWindowOpacity(self.settings['opacity'] / 100)

            # Save settings
            self.saveSettings()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, 'Error', f'Failed to update crosshair: {str(e)}')

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
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons', 'crossgen.ico')
    if os.path.exists(icon_path):
        app_icon = QtGui.QIcon(icon_path)
        app.setWindowIcon(app_icon)
        # Also set for the window itself
        ex = AdvancedSettingsWindow()
        ex.setWindowIcon(app_icon)
    else:
        print(f"Icon file not found at: {icon_path}")
    app.exec_()
