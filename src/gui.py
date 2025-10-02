import sys
import os
import shutil
import tempfile
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGroupBox, QLabel, QComboBox,
                             QSpinBox, QPushButton, QProgressBar,
                             QFileDialog, QMessageBox, QTextEdit, QGridLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPainter
from PyQt5.QtCore import pyqtProperty
from generator import MelodyGenerator


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 650
MIN_WIDTH = 600
MIN_HEIGHT = 500
LAYOUT_MARGINS = 30
LAYOUT_SPACING = 15


class FadeWidget(QWidget):
    """Custom widget with fade animation support"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._opacity = 1.0
        self.background_pixmap = None

    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
        
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setOpacity(self._opacity)
        if self.background_pixmap is not None:
            painter.drawPixmap(0, 0, self.background_pixmap)

    def setBackgroundPixmap(self, pixmap):
        self.background_pixmap = pixmap


class GenerateThread(QThread):
    """Thread for generating melodies in the background"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, generator, key, mode, measures, bpm, output_dir):
        super().__init__()
        self.generator = generator
        self.key = key
        self.mode = mode
        self.measures = measures
        self.bpm = bpm
        self.output_dir = output_dir

    def run(self):
        try:
            output_path = os.path.join(self.output_dir, f'melody_{self.key}_{self.mode}_{self.bpm}bpm.mid')
            result_path = self.generator.generate_melody(
                key=self.key, 
                mode=self.mode, 
                measures=self.measures, 
                bpm=self.bpm,
                output_path=output_path
            )
            self.finished.emit(result_path)
        except Exception as e:
            self.error.emit(str(e))


class MelodyGeneratorApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.generator = MelodyGenerator()
        self.current_midi_path = None
        self._current_thread = None
        
        self.output_dir = tempfile.mkdtemp(prefix="melodies_")
        os.makedirs(self.output_dir, exist_ok=True)

        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Melody Generator")
        self.setGeometry(300, 300, WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)

        central_widget = FadeWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(LAYOUT_MARGINS, LAYOUT_MARGINS, 
                                      LAYOUT_MARGINS, LAYOUT_MARGINS)
        main_layout.setSpacing(LAYOUT_SPACING)

        title = QLabel("Melody Generator")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                font-size: 28px; 
                font-weight: bold; 
                color: white;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 rgba(90, 100, 220, 0.3), 
                                            stop:1 rgba(220, 100, 220, 0.3));
                border-radius: 15px;
                padding: 15px;
                margin: 5px;
            }
        """)
        main_layout.addWidget(title)

        settings_group = QGroupBox("Settings")
        settings_layout = QHBoxLayout(settings_group)
        settings_layout.setSpacing(18)
        settings_layout.setContentsMargins(18, 10, 18, 10)

        key_label = QLabel("Key:")
        key_label.setStyleSheet("font-size: 15px; color: #1976d2;")
        self.key_combo = QComboBox()
        self.key_combo.addItems(['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'])
        self.key_combo.setMinimumWidth(70)
        self.key_combo.setMinimumHeight(36)
        self.key_combo.setStyleSheet("font-size: 16px; padding: 4px 12px;")

        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet("font-size: 15px; color: #1976d2;")
        self.mode_combo = QComboBox()
        mode_names = [
            'Major', 'Natural Minor', 'Harmonic Minor', 'Pentatonic Major',
            'Pentatonic Minor', 'Dorian', 'Phrygian', 'Lydian', 'Mixolydian',
            'Aeolian', 'Locrian'
        ]
        self.mode_combo.addItems(mode_names)
        self.mode_combo.setMinimumWidth(180)
        self.mode_combo.setMinimumHeight(36)
        self.mode_combo.setStyleSheet("font-size: 16px; padding: 4px 12px;")
        self.mode_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        tempo_label = QLabel("Tempo:")
        tempo_label.setStyleSheet("font-size: 15px; color: #1976d2;")
        self.tempo_mode_combo = QComboBox()
        self.tempo_mode_combo.addItems(["Largo (60 BPM)", "Andante (90 BPM)", "Allegro (120 BPM)"])
        self.tempo_mode_combo.setMinimumWidth(130)
        self.tempo_mode_combo.setMinimumHeight(36)
        self.tempo_mode_combo.setStyleSheet("font-size: 16px; padding: 4px 18px;")

        self.tempo_label = QLabel("120")
        self.tempo_label.setStyleSheet("color: #88aaff; font-weight: bold; font-size: 16px; margin-left: 8px;")

        measures_label = QLabel("Bars:")
        measures_label.setStyleSheet("font-size: 15px; color: #1976d2;")
        self.measures_spin = QSpinBox()
        self.measures_spin.setRange(1, 16)
        self.measures_spin.setValue(4)
        self.measures_spin.setMinimumWidth(70)
        self.measures_spin.setMinimumHeight(36)
        self.measures_spin.setStyleSheet("font-size: 16px; padding: 4px 12px;")

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(6)
        grid.addWidget(key_label, 0, 0)
        grid.addWidget(self.key_combo, 0, 1)
        grid.addWidget(mode_label, 0, 2)
        grid.addWidget(self.mode_combo, 0, 3)
        grid.addWidget(tempo_label, 0, 4)
        grid.addWidget(self.tempo_mode_combo, 0, 5)
        grid.addWidget(self.tempo_label, 0, 6)
        grid.addWidget(measures_label, 0, 7)
        grid.addWidget(self.measures_spin, 0, 8)
        grid.setColumnStretch(9, 1)
        settings_layout.addLayout(grid)

        self.tempo_mode_combo.currentIndexChanged.connect(self.on_tempo_mode_changed)
        self.update_tempo_label(120)

        main_layout.addWidget(settings_group)

        button_layout = QHBoxLayout()

        self.generate_btn = QPushButton("Generate Melody")
        self.generate_btn.clicked.connect(self.generate_melody)
        self.generate_btn.setObjectName("generateButton")
        button_layout.addWidget(self.generate_btn)

        self.save_btn = QPushButton("Save as MIDI")
        self.save_btn.clicked.connect(self.save_melody)
        self.save_btn.setEnabled(False)
        self.save_btn.setObjectName("saveButton")
        button_layout.addWidget(self.save_btn)

        main_layout.addLayout(button_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        status_group = QGroupBox("Generation Status")
        status_layout = QVBoxLayout(status_group)
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(120)
        self.status_text.setReadOnly(True)
        status_layout.addWidget(self.status_text)
        main_layout.addWidget(status_group)

        desc_label = QLabel("This software can randomly generate melody MIDI files in various modes, suitable for music creation, learning and inspiration. Supports custom modes and tempo ranges.")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #1976d2; font-size: 13px; margin: 8px 0 0 0;")
        main_layout.addWidget(desc_label)

        github_label = QLabel('<a href="https://github.com/yiyangbear">My GitHub</a>')
        github_label.setAlignment(Qt.AlignCenter)
        github_label.setOpenExternalLinks(True)
        github_label.setStyleSheet("color: #1976d2; font-size: 14px; margin-bottom: 6px;")
        main_layout.addWidget(github_label)

        info_label = QLabel("Random Melody Generator v1.0 | Designed for music creation enthusiasts")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("color: #1976d2; font-size: 11px; margin-top: 10px;")
        main_layout.addWidget(info_label)
        
        self.log("Welcome to Random Melody Generator!")
        self.log("Tip: Select parameters and click 'Generate Melody' to start creation")

    def on_tempo_mode_changed(self, idx):
        """Handle tempo mode selection change"""
        if idx == 0:
            self.tempo_label.setText("60")
        elif idx == 1:
            self.tempo_label.setText("90")
        elif idx == 2:
            self.tempo_label.setText("120")

    def apply_styles(self):
        """Apply application styles"""
        style_sheet = """
        QMainWindow {
            background: #eaf2fb;
            color: #1a237e;
        }
        #centralWidget {
            background: #f5faff;
            border-radius: 16px;
            border: 1px solid #b3c6e6;
        }
        QGroupBox {
            color: #1a237e;
            font-size: 14px;
            font-weight: bold;
            border: 1px solid #b3c6e6;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
            background: #f0f6ff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 5px 15px;
            background: #1976d2;
            color: white;
            border-radius: 8px;
        }
        QLabel {
            color: #1a237e;
            font-size: 13px;
        }
        QPushButton {
            background-color: #1976d2;
            border: none;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            padding: 10px 15px;
            font-size: 14px;
        }
        QPushButton:hover {
            background-color: #1565c0;
        }
        QPushButton:pressed {
            background-color: #0d47a1;
        }
        QPushButton:disabled {
            background-color: #b3c6e6;
            color: #e3eaf6;
        }
        QComboBox {
            background-color: #e3eaf6;
            border: 1px solid #b3c6e6;
            border-radius: 5px;
            color: #1a237e;
            padding: 5px;
            min-width: 80px;
        }
        QComboBox QAbstractItemView {
            background-color: #e3eaf6;
            border: 1px solid #b3c6e6;
            color: #1a237e;
            selection-background-color: #1976d2;
        }
        QProgressBar {
            border: 1px solid #b3c6e6;
            border-radius: 5px;
            text-align: center;
            color: #1976d2;
            background-color: #e3eaf6;
        }
        QProgressBar::chunk {
            background-color: #1976d2;
            border-radius: 4px;
        }
        QTextEdit {
            background-color: #e3eaf6;
            border: 1px solid #b3c6e6;
            border-radius: 5px;
            color: #1a237e;
            font-size: 12px;
            padding: 8px;
        }
        QSpinBox {
            background-color: #e3eaf6;
            border: 1px solid #b3c6e6;
            border-radius: 5px;
            color: #1a237e;
            padding: 5px;
        }
        """
        self.setStyleSheet(style_sheet)

    def update_tempo_label(self, value):
        """Update tempo label with current value"""
        self.tempo_label.setText(str(value))

    def log(self, message):
        """Add message to status log"""
        self.status_text.append(f"<span style='color: #88ccff;'>{message}</span>")
        self.status_text.verticalScrollBar().setValue(
            self.status_text.verticalScrollBar().maximum()
        )

    def generate_melody(self):
        """Start melody generation process"""
        self.generate_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        key = self.key_combo.currentText()
        mode = self.mode_combo.currentText()
        measures = self.measures_spin.value()

        tempo_idx = self.tempo_mode_combo.currentIndex()
        if tempo_idx == 0:
            bpm = 60
        elif tempo_idx == 1:
            bpm = 90
        elif tempo_idx == 2:
            bpm = 120

        self.log(f"Generating melody: {key} {mode}, {measures} bars, {bpm}BPM")

        self._current_thread = GenerateThread(self.generator, key, mode, measures, bpm, self.output_dir)
        self._current_thread.finished.connect(self.on_generation_finished)
        self._current_thread.error.connect(self.on_generation_error)
        self._current_thread.start()

    def on_generation_finished(self, file_path):
        """Handle successful melody generation"""
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.save_btn.setEnabled(True)
        self.current_midi_path = file_path

        self.log(f"Melody generated successfully!")
        self.log(f"File location: {file_path}")

        self.animate_success()

    def on_generation_error(self, error_msg):
        """Handle melody generation error"""
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.log(f"Generation failed: {error_msg}")

        QMessageBox.critical(self, "Error", f"Error generating melody:\n{error_msg}")

    def animate_success(self):
        """Animate success feedback"""
        success_animation = QPropertyAnimation(self, b"windowOpacity")
        success_animation.setDuration(300)
        success_animation.setKeyValueAt(0.3, 0.8)
        success_animation.setKeyValueAt(0.6, 1.0)
        success_animation.start()

    def save_melody(self):
        """Save generated melody to user-selected location"""
        if self.current_midi_path:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save MIDI File",
                os.path.expanduser("~/Desktop/My Melody.mid"),
                "MIDI Files (*.mid)"
            )
            if file_path:
                shutil.copy2(self.current_midi_path, file_path)
                self.log(f"Melody saved to: {file_path}")

                QMessageBox.information(
                    self,
                    "Save Successful",
                    f"Melody saved to:\n{file_path}\n\nYou can open this file with any music software."
                )

    def closeEvent(self, event):
        """Clean up on application close"""
        try:
            import shutil
            shutil.rmtree(self.output_dir, ignore_errors=True)
        except:
            pass
        event.accept()


def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Random Melody Generator")
    app.setApplicationVersion("1.0")

    font = QFont("Arial", 10)
    app.setFont(font)

    window = MelodyGeneratorApp()
    window.show()

    fade_animation = QPropertyAnimation(window, b"windowOpacity")
    fade_animation.setDuration(500)
    fade_animation.setStartValue(0.0)
    fade_animation.setEndValue(1.0)
    fade_animation.setEasingCurve(QEasingCurve.OutCubic)
    fade_animation.start()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()