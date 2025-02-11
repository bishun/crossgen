from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QSettings, QPoint
import json
import os

class CrosshairCanvas(QtWidgets.QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.draggable = False
        self.drag_start = None
        self.initUI()

    def initUI(self):
        even_size = self.settings['size'] // 2 * 2  # Force even number
        self.setFixedSize(even_size, even_size)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMouseTracking(True)
        
        screen = QtWidgets.QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        default_x = screen_geometry.center().x() - self.settings['size'] // 2
        default_y = screen_geometry.center().y() - self.settings['size'] // 2
        
        saved_pos = self.settings.get('position', QPoint(default_x, default_y))
        self.move(saved_pos)
        self.show()

    def paintEvent(self, event):
        try:
            painter = QtGui.QPainter(self)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            
            pen = QtGui.QPen(QtGui.QColor(self.settings['color']))
            pen.setWidth(self.settings['thickness'])
            
            if self.settings.get('outline_enabled', False):
                outline_pen = QtGui.QPen(QtGui.QColor(self.settings['outline_color']))
                outline_pen.setWidth(self.settings['thickness'] + 2)
                painter.setPen(outline_pen)
                self.drawShape(painter)
            
            painter.setPen(pen)
            self.drawShape(painter)
        except Exception as e:
            print(f"Paint error: {str(e)}")

    def drawShape(self, painter):
        size = self.settings['size']
        shape = self.settings['shape']
        
        if shape == 'Round':
            style = self.settings.get('fill_style', 'Full')  # Changed to fill_style and added default
            if style == 'Full':
                painter.setBrush(QtGui.QBrush(QtGui.QColor(self.settings['color'])))
            else:
                painter.setBrush(QtGui.QBrush(Qt.transparent))
            painter.drawEllipse(0, 0, size - 1, size - 1)  # Adjusted size to prevent edge clipping
            
        elif shape == 'Crosshair':
            center = size // 2
            gap = self.settings.get('gap', 0)
            
            if gap > 0:
                painter.drawLine(center, 0, center, center - gap)
                painter.drawLine(center, center + gap, center, size)
                painter.drawLine(0, center, center - gap, center)
                painter.drawLine(center + gap, center, size, center)
            else:
                painter.drawLine(center, 0, center, size)
                painter.drawLine(0, center, size, center)
                
        elif shape == 'Dot Matrix':
            spacing = self.settings.get('dot_spacing', 4)
            dot_size = self.settings.get('dot_size', 2)
            for x in range(0, size, spacing):
                for y in range(0, size, spacing):
                    painter.drawPoint(x, y)
                    
        elif shape == 'Custom':
            points = self.settings.get('custom_points', [])
            
            if not points:
                print("No custom points found!")
                return

            try:
                path = QtGui.QPainterPath()
                path.moveTo(points[0][0], points[0][1])
                for point in points[1:]:
                    path.lineTo(point[0], point[1])
                path.closeSubpath()  # Ensures shape is closed

                painter.setPen(QtGui.QPen(QtGui.QColor(self.settings['color']), self.settings['thickness']))
                if self.settings.get('outline_enabled', False):
                    outline_pen = QtGui.QPen(QtGui.QColor(self.settings['outline_color']), self.settings['thickness'] + 2)
                    painter.setPen(outline_pen)
                    painter.drawPath(path)

                painter.setPen(QtGui.QPen(QtGui.QColor(self.settings['color']), self.settings['thickness']))
                painter.drawPath(path)
            
            except Exception as e:
                print(f"Error drawing custom shape: {e}")


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.settings.get('draggable', True):
            self.draggable = True
            self.drag_start = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.draggable and self.drag_start:
            self.move(event.globalPos() - self.drag_start)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.draggable = False
            self.settings['position'] = self.pos()

class AdvancedSettingsWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.crosshair = None
        self.settings = self.loadSettings()
        self.initUI()

    def initUI(self):
        layout = QtWidgets.QVBoxLayout()
        
        tabs = QtWidgets.QTabWidget()
        
        # Basic Settings Tab
        basic_tab = QtWidgets.QWidget()
        basic_layout = QtWidgets.QVBoxLayout()
        
        # Shape Selection
        shape_group = QtWidgets.QGroupBox("Shape Settings")
        shape_layout = QtWidgets.QVBoxLayout()
        
        self.shape_combo = QtWidgets.QComboBox()
        self.shape_combo.addItems(['Round', 'Crosshair', 'Dot Matrix', 'Custom'])
        shape_layout.addWidget(QtWidgets.QLabel("Shape:"))
        shape_layout.addWidget(self.shape_combo)
        
        # Fill Style for Round shape
        self.fill_style_combo = QtWidgets.QComboBox()
        self.fill_style_combo.addItems(['Full', 'Ring'])
        shape_layout.addWidget(QtWidgets.QLabel("Fill Style:"))
        shape_layout.addWidget(self.fill_style_combo)
        
        # Size Settings
        self.size_spin = QtWidgets.QSpinBox()
        self.size_spin.setRange(4, 100)
        self.size_spin.setSingleStep(2)  # Ensures only even numbers
        self.size_spin.setValue(self.settings.get('size', 8) // 2 * 2)  # Rounds to nearest even
        shape_layout.addWidget(QtWidgets.QLabel("Size:"))
        shape_layout.addWidget(self.size_spin)
        
        shape_group.setLayout(shape_layout)
        basic_layout.addWidget(shape_group)
        
        # Color Settings
        color_group = QtWidgets.QGroupBox("Color Settings")
        color_layout = QtWidgets.QVBoxLayout()
        
        self.color_button = QtWidgets.QPushButton('Primary Color')
        self.color_button.clicked.connect(lambda: self.openColorPicker('color'))
        color_layout.addWidget(self.color_button)
        
        self.outline_check = QtWidgets.QCheckBox('Enable Outline')
        self.outline_check.setChecked(self.settings.get('outline_enabled', False))
        color_layout.addWidget(self.outline_check)
        
        self.outline_color_button = QtWidgets.QPushButton('Outline Color')
        self.outline_color_button.clicked.connect(lambda: self.openColorPicker('outline_color'))
        color_layout.addWidget(self.outline_color_button)
        
        color_group.setLayout(color_layout)
        basic_layout.addWidget(color_group)
        
        basic_tab.setLayout(basic_layout)
        tabs.addTab(basic_tab, "Basic")
        
        # Advanced Settings Tab
        advanced_tab = QtWidgets.QWidget()
        advanced_layout = QtWidgets.QVBoxLayout()
        
        self.gap_spin = QtWidgets.QSpinBox()
        self.gap_spin.setRange(0, 20)
        self.gap_spin.setValue(self.settings.get('gap', 0))
        advanced_layout.addWidget(QtWidgets.QLabel("Center Gap:"))
        advanced_layout.addWidget(self.gap_spin)
        
        self.thickness_spin = QtWidgets.QSpinBox()
        self.thickness_spin.setRange(1, 10)
        self.thickness_spin.setValue(self.settings.get('thickness', 1))
        advanced_layout.addWidget(QtWidgets.QLabel("Line Thickness:"))
        advanced_layout.addWidget(self.thickness_spin)
        
        self.opacity_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(int(self.settings.get('opacity', 100)))
        advanced_layout.addWidget(QtWidgets.QLabel("Opacity:"))
        advanced_layout.addWidget(self.opacity_slider)
        
        advanced_tab.setLayout(advanced_layout)
        tabs.addTab(advanced_tab, "Advanced")
        
        layout.addWidget(tabs)
        
        # Control buttons
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
        self.setWindowTitle('Crossgen 1.1')
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
                'shape': 'Round',
                'thickness': 1,
                'fill_style': 'Full',  # Changed from style to fill_style
                'opacity': 100,
                'outline_enabled': False,
                'outline_color': '#000000',
                'gap': 0,
                'draggable': True
            }

    def saveSettings(self):
        settings = QSettings('EnhancedCrossgen', 'Preferences')
        settings.setValue('settings', json.dumps(self.settings))

    def updateSettingsAvailability(self, shape):
        self.fill_style_combo.setEnabled(shape == 'Round')
        self.gap_spin.setEnabled(shape == 'Crosshair')
        self.outline_check.setEnabled(shape in ['Round', 'Crosshair'])
        self.updateOutlineAvailability()

    def updateOutlineAvailability(self):
        self.outline_color_button.setEnabled(self.outline_check.isChecked())

    def openColorPicker(self, color_type):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.settings[color_type] = color.name()
            if self.crosshair:
                self.updateCrosshair()

    def updateCrosshair(self):
        try:
            # Update settings
            self.settings.update({
                'shape': self.shape_combo.currentText(),
                'size': self.size_spin.value() // 2 * 2,  # Force even number
                'thickness': self.thickness_spin.value(),
                'gap': self.gap_spin.value(),
                'opacity': self.opacity_slider.value(),
                'outline_enabled': self.outline_check.isChecked(),
                'fill_style': self.fill_style_combo.currentText()  # Added fill_style
            })
            
            # Create or update crosshair
            # Handle custom shape loading
            if self.settings['shape'] == 'Custom':
                file_dialog = QtWidgets.QFileDialog()
                file_path, _ = file_dialog.getOpenFileName(self, "Open Custom Shape", "", "JSON Files (*.json)")
                
                if file_path:
                    try:
                        with open(file_path, "r") as f:
                            self.settings['custom_points'] = json.load(f)
                    except Exception as e:
                        QtWidgets.QMessageBox.warning(self, 'Error', f'Failed to load custom shape: {str(e)}')

            # Create or update crosshair
            if self.crosshair:
                self.crosshair.close()
            self.crosshair = CrosshairCanvas(self.settings)
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
    ex = AdvancedSettingsWindow()
    app.exec_()
