import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QMessageBox, QLineEdit, QSlider, QHBoxLayout, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal

class QSliderLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        line_edit_style = ("QLineEdit {background: transparent; border: 1px solid transparent;} "
                           "QLineEdit:focus {background: white; border: 1px solid gray; border-radius: 3px;}")
        self.setStyleSheet(line_edit_style)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.textChanged.connect(self.set_to_font_width)
        self.editingFinished.connect(self.set_to_font_width)

    def set_to_font_width(self, text=None, padding=12):
        fm = self.fontMetrics()
        if text is None:
            text = self.text() or "0"
        width = fm.horizontalAdvance(text) + padding
        self.setFixedWidth(width)


class QAdjustableSlider(QWidget):
    valueChanged = pyqtSignal(float)
    def __init__(self, min_val=0.0, max_val=100.0, step=0.1, initial=0.0, decimals=2, parent=None):
        super().__init__(parent)

        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.decimals = decimals
        self._internal_update = False

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setVerticalSpacing(0)  # reduce space between rows

        # Slider in top-left cell
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(int((max_val - min_val) / step))
        self.slider.setValue(int((initial - min_val) / step))
        self.slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.slider, 0, 0)

        # Current value edit in top-right cell
        self.value_edit = QSliderLineEdit(f"{initial:.{decimals}f}")
        self.value_edit.set_to_font_width()
        self.value_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.value_edit, 0, 1)

        # Bottom row: container widget with min/max edits and spacer
        limits_widget = QWidget()
        limits_layout = QHBoxLayout(limits_widget)
        limits_layout.setContentsMargins(0, 0, 0, 0)

        self.min_edit = QSliderLineEdit(f"{min_val:.{decimals}f}")
        self.min_edit.setFixedHeight(13)
        limits_layout.addWidget(self.min_edit, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        limits_layout.addStretch()

        self.max_edit = QSliderLineEdit(f"{max_val:.{decimals}f}")
        self.max_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.max_edit.setFixedHeight(13)
        limits_layout.addWidget(self.max_edit, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        layout.addWidget(limits_widget, 1, 0)

        # Empty placeholder on bottom-right cell for alignment
        layout.addWidget(QWidget(), 1, 1)

        # Connections
        self.slider.valueChanged.connect(self.on_slider_changed)
        self.value_edit.editingFinished.connect(self.on_value_edit_finished)
        self.min_edit.editingFinished.connect(self.on_min_edit_finished)
        self.max_edit.editingFinished.connect(self.on_max_edit_finished)

    def on_slider_changed(self, slider_val):
        if self._internal_update:
            return
        self._internal_update = True
        value = self.min_val + slider_val * self.step
        self.value_edit.setText(f"{value:.{self.decimals}f}")
        self.value_edit.set_to_font_width()
        self.valueChanged.emit(value)
        self._internal_update = False

    def on_value_edit_finished(self):
        if self._internal_update:
            return
        try:
            text_val = float(self.value_edit.text())
        except ValueError:
            self.reset_value_edit()
            return

        if text_val > self.max_val:
            self.max_edit.setText(str(text_val))
            self.on_max_edit_finished()
        elif text_val < self.min_val:
            self.min_edit.setText((str(text_val)))
            self.on_min_edit_finished()

        value = max(self.min_val, min(self.max_val, text_val))

        self._internal_update = True
        self.value_edit.setText(f"{value:.{self.decimals}f}")
        slider_pos = int(round((value - self.min_val) / self.step))
        self.slider.setValue(slider_pos)
        self.valueChanged.emit(value)
        self._internal_update = False

    def on_min_edit_finished(self):
        try:
            new_min = float(self.min_edit.text())
        except ValueError:
            self.reset_min_edit()
            return

        if new_min >= self.max_val:
            QMessageBox.warning(self, "Invalid Input", "Minimum must be less than maximum.")
            self.reset_min_edit()
            return

        self.min_val = new_min
        self.update_slider_range()

    def on_max_edit_finished(self):
        try:
            new_max = float(self.max_edit.text())
        except ValueError:
            self.reset_max_edit()
            return

        if new_max <= self.min_val:
            QMessageBox.warning(self, "Invalid Input", "Maximum must be greater than minimum.")
            self.reset_max_edit()
            return

        self.max_val = new_max
        self.update_slider_range()

    def update_slider_range(self):
        # Update slider range based on current min_val and max_val
        self._internal_update = True
        self.slider.setMinimum(0)
        self.slider.setMaximum(int(round((self.max_val - self.min_val) / self.step)))

        # Clamp current value to new limits
        current_val = self.value()
        if current_val < self.min_val:
            current_val = self.min_val
        elif current_val > self.max_val:
            current_val = self.max_val

        # Update slider and value edit
        slider_pos = int(round((current_val - self.min_val) / self.step))
        self.slider.setValue(slider_pos)
        self.value_edit.setText(f"{current_val:.{self.decimals}f}")

        # Update min/max edits to show correctly formatted values
        self.min_edit.setText(f"{self.min_val:.{self.decimals}f}")
        self.max_edit.setText(f"{self.max_val:.{self.decimals}f}")

        self._internal_update = False

    def reset_min_edit(self):
        self.min_edit.setText(f"{self.min_val:.{self.decimals}f}")

    def reset_max_edit(self):
        self.max_edit.setText(f"{self.max_val:.{self.decimals}f}")

    def reset_value_edit(self):
        value = self.value()
        self.value_edit.setText(f"{value:.{self.decimals}f}")
        self.value_edit.set_to_font_width()

    def value(self):
        try:
            return float(self.value_edit.text())
        except ValueError:
            return self.min_val


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("QAdjustableSlider Demo")
    layout = QVBoxLayout(window)

    slider_widget = QAdjustableSlider(min_val=0, max_val=5, step=0.01, initial=2.5)
    layout.addWidget(slider_widget)

    label = QLabel()
    layout.addWidget(label)
    def spam(val):
        label.setText(f"Slider value is: {val}")

    slider_widget.valueChanged.connect(lambda v: spam(v))

    window.show()
    sys.exit(app.exec())
