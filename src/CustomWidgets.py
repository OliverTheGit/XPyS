from argparse import ArgumentError
from dataclasses import dataclass
import platform

import lmfit.models
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QPoint
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QMessageBox, QLineEdit, QSlider, QHBoxLayout, QSizePolicy, QGridLayout,
    QGroupBox, QFormLayout, QMenu, QSpacerItem
)
from lmfit.models import VoigtModel


@dataclass
class BoundedValue:
    value: float
    min_val: float
    max_val: float

    def set_value(self, new_value):
        if new_value < self.min_val:
            self.value = self.min_val
        elif new_value > self.max_val:
            self.value = self.max_val
        else:
            self.value = new_value

    def set_lims(self, new_lims):
        if new_lims[1] > new_lims[0]:
            self.min_val = new_lims[0]
            self.max_val = new_lims[1]
            self.set_value(self.value)

    def set_min(self, new_min):
        if new_min < self.max_val:
            self.min_val = new_min
            self.set_value(self.value)

    def set_max(self, new_max):
        if new_max > self.min_val:
            self.max_val = new_max
            self.set_value(self.value)

    def to_slider_dict(self):
        return {'value': self.value, 'min': self.min_val, 'max': self.max_val}

    @classmethod
    def from_slider_dict(cls, data: dict):
        """
        Create an instance from a dictionary.
        Expects keys: 'value', 'min', 'max'.
        """
        if "value" in data.keys():
            if ("min" not in data.keys()) and ("max" not in data.keys()):
                if data["value"] == 0:
                    data["min"] = -1
                    data["max"] = 1
                else:
                    data["min"] = min(0, data["value"] * 2)
                    data["max"] = max(0, data["value"] * 2)
            elif "min" not in data.keys():
                data["min"] = data["max"] - abs(data["value"] * 2)
            elif "max" not in data.keys():
                data["max"] = data["min"] + abs(data["value"] * 2)
        elif "min" in data.keys():
            # value isn't in dict
            if "max" not in data.keys():
                if data["min"] >= 0:
                    data["max"] = (data["min"] + 0.5) * 2
                else:
                    data["max"] = 0
            data["value"] = 0.5 * (data["min"] + data["max"])
        elif "max" in data.keys():
            # value isn't in dict
            if "min" not in data.keys():
                if data["max"] >= 0:
                    data["min"] = (data["max"] - 1) / 2
                else:
                    data["min"] = 0
            data["value"] = 0.5 * (data["min"] + data["max"])
        else:
            raise ArgumentError(None, "Dictionary had none of \"min\", \"max\", or \"value\"")

        return cls(
            value=data.get('value'),
            min_val=data.get('min'),
            max_val=data.get('max'),
        )


class QSliderLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        line_edit_style = ("QLineEdit {background: transparent; border: 1px solid transparent;} "
                           "QLineEdit:focus {background: white; border: 1px solid gray; border-radius: 3px;}")
        self.setStyleSheet(line_edit_style)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        #if platform.system() != "Darwin":
            # seems to be automatic behaviour on Mac is better
        self.textChanged.connect(self.set_to_font_width)
        self.editingFinished.connect(self.set_to_font_width)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.hasFocus():
                self.clearFocus()
                self.set_to_font_width()
        super().keyPressEvent(event)

    def set_to_font_width(self, text=None, padding=12):
        fm = self.fontMetrics()
        if text is None:
            text = self.text() or "0"
        width = fm.horizontalAdvance(text) + padding
        self.setFixedWidth(width)


class QAdjustableSlider(QWidget):
    valueChanged = pyqtSignal(float)
    limit_changed = pyqtSignal(float, float)  # min value, max value

    def __init__(self, min_val=0.0, max_val=100.0, step=0.01, initial=0.0, decimals=2, parent=None):
        super().__init__(parent)

        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self.decimals = decimals
        self._internal_update = False

        grid_layout = QGridLayout(self)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setVerticalSpacing(0)  # reduce space between rows

        # Slider in top-left cell
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(int((max_val - min_val) / self.step))
        self.slider.setValue(int((initial - min_val) / self.step))
        self.slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        grid_layout.addWidget(self.slider, 0, 0)

        # Current value edit in top-right cell
        self.value_edit = QSliderLineEdit(f"{initial:.{decimals}f}")
        self.value_edit.set_to_font_width()
        self.value_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        grid_layout.addWidget(self.value_edit, 0, 1)

        # Bottom row: container widget with min/max edits and spacer
        limits_layout = QHBoxLayout()
        limits_layout.setContentsMargins(0, 0, 0, 0)

        self.min_edit = QSliderLineEdit(f"{min_val:.{decimals}f}")
        self.min_edit.setFixedHeight(13)
        limits_layout.addWidget(self.min_edit, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        spacerItem = QSpacerItem(40, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        limits_layout.addItem(spacerItem)

        self.max_edit = QSliderLineEdit(f"{max_val:.{decimals}f}")
        self.max_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.max_edit.setFixedHeight(13)
        limits_layout.addWidget(self.max_edit, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        grid_layout.addLayout(limits_layout, 1, 0)

        # Empty placeholder on bottom-right cell for alignment
        grid_layout.addWidget(QWidget(), 1, 1)

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

        self.limit_changed.emit(self.min_val, self.max_val)
        self._internal_update = False

    def reset_min_edit(self):
        self.min_edit.setText(f"{self.min_val:.{self.decimals}f}")

    def reset_max_edit(self):
        self.max_edit.setText(f"{self.max_val:.{self.decimals}f}")

    def reset_value_edit(self):
        value = self.value()
        self.value_edit.setText(f"{value:.{self.decimals}f}")
        self.value_edit.set_to_font_width()

    def set_from_bounded_value(self, bounded_value):
        assert isinstance(bounded_value, BoundedValue)
        self.slider.setValue(bounded_value.value)
        self.min_edit.setText(str(bounded_value.min_val))
        self.max_edit.setText(str(bounded_value.max_val))

    def value(self):
        try:
            return float(self.value_edit.text())
        except ValueError:
            return self.min_val


class PeakDataModel(QObject):
    param_changed = pyqtSignal(str, object)  # param_name, new_value for the slider
    name_changed = pyqtSignal(str)  # new_value

    def __init__(self, peak_model: lmfit.Model):
        super().__init__()
        self.peak_model = peak_model
        self._params = {}  # {str: BoundedValue}
        self._peak_name = peak_model.prefix
        self._internal_update = False

        param_hints = getattr(peak_model, "param_hints", {})
        for param_name in peak_model.param_names:
            # adding detail to the param_hints to get a fully fleshed out dict params = {name: {min: , max:, value: }}
            if param_name.removeprefix(peak_model.prefix) in peak_model.independent_vars:
                continue

            hint = param_hints.get(param_name.removeprefix(peak_model.prefix), {})
            if hint == {}:
                hint["value"] = peak_model.def_vals.get(param_name.removeprefix(peak_model.prefix), 1)
            try:
                value = BoundedValue.from_slider_dict(hint)
                self._params[param_name] = value
            except ArgumentError:
                pass

    def set_name(self, name):
        if self._internal_update:
            return
        self._internal_update = True
        self._peak_name = name
        self.name_changed.emit(name)
        self._internal_update = False

    def get_name(self):
        return self._peak_name

    def get_all_params(self):
        return self._params

    def get_param(self, name):
        return self._params[name]

    def set_param(self, name, value: BoundedValue):
        if self._internal_update:
            return
        self._internal_update = True
        if name in self._params:
            self._params[name] = value
            self.param_changed.emit(name, value)

        self._internal_update = False

    def make_model_parameters(self, model_params=None):
        if model_params is None:
            model_params = lmfit.Parameters()
        for k, v in self._params.items():
            assert isinstance(v, BoundedValue)
            model_params.add(k, min=v.min_val, max=v.max_val, value=v.value)
        return model_params

    def eval_requirements(self) -> list:
        return self.peak_model.independent_vars

    def evaluate(self, x, **kwargs):
        return self.peak_model.eval(params=self.make_model_parameters(), x=x, **kwargs)

    def get_model_and_params_for_fitting(self, model_params=None):
        return self.peak_model, self.make_model_parameters(model_params)


class QModelParamGroup(QGroupBox):
    paramChanged = pyqtSignal(str)
    request_deletion = pyqtSignal(str)

    def __init__(self, peak_model: PeakDataModel, parent=None):
        super().__init__(parent)
        self.data_model = peak_model
        self.setTitle(self.data_model.get_name())
        self._internal_update = False

        form_layout = QFormLayout()

        self.sliders = {}

        for name, value in peak_model.get_all_params().items():
            # Custom slider
            assert isinstance(value, BoundedValue)
            slider = QAdjustableSlider(min_val=value.min_val, max_val=value.max_val, initial=value.value)
            slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.sliders[name] = slider

            # Label with the parameter name
            label = QLabel(name.removeprefix(self.data_model.get_name()).title())
            label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

            # Connect slider value changes to model
            slider.valueChanged.connect(lambda val, n=name: self._update_model_value(n, val))
            slider.limit_changed.connect(lambda min_val, max_val, n=name:
                                         self._update_model_lims(n, (min_val, max_val))
                                         )

            form_layout.addRow(label, slider)

        self.setLayout(form_layout)

        # Connect model changes to slider updates
        self.data_model.param_changed.connect(self._on_param_changed)

        # Enable context menu events
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def set_param_directly(self, name, value):
        slider = self.sliders.get(name)
        if slider is not None:
            assert isinstance(slider, QAdjustableSlider)
            if isinstance(value, BoundedValue):
                slider.max_edit.setText(str(value.max_val))
                slider.max_edit.editingFinished.emit()
                slider.min_edit.setText(str(value.min_val))
                slider.min_edit.editingFinished.emit()
                slider.value_edit.setText(str(value.value))
                slider.value_edit.editingFinished.emit()
            else:
                slider.value_edit.setText(str(value))
                slider.value_edit.editingFinished.emit()

    def _on_param_changed(self, name, value):
        if self._internal_update:
            return
        self._internal_update = True
        slider = self.sliders.get(name)
        if slider:
            slider.slider.setValue(value["value"])
            slider.min_edit.setText(str(value["min"]))
            slider.max_edit.setText(str(value["max"]))
        self._internal_update = False

    def _update_model_value(self, name, value):
        if self._internal_update:
            return
        self._internal_update = True
        curr_bv = self.data_model.get_param(name)
        curr_bv.set_value(value)
        self.data_model.set_param(name, curr_bv)
        self.paramChanged.emit(self.data_model.get_name())
        self._internal_update = False

    def _update_model_lims(self, name, value):
        if self._internal_update:
            return
        self._internal_update = True
        curr_bv = self.data_model.get_param(name)
        curr_bv.set_lims(value)
        self.data_model.set_param(name, curr_bv)
        self._internal_update = False

    def show_context_menu(self, position: QPoint):
        menu = QMenu(self)
        delete_action = menu.addAction("Delete...")
        action = menu.exec(self.mapToGlobal(position))
        if action == delete_action:
            if QMessageBox.question(self, "Confirm", "Delete this feature?") == QMessageBox.StandardButton.Yes:
                self.request_deletion.emit(self.data_model.get_name())


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # Add a few deletable boxes
        for i in range(3):
            box = QModelParamGroup(PeakDataModel(VoigtModel(prefix="V")))
            layout.addWidget(box)

        self.setWindowTitle("Right-click Deletable GroupBox")


if __name__ == "__main__":
    app = QApplication([])
    w = MainWindow()
    w.show()
    app.exec()
