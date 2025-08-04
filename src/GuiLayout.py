import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QSlider, QGroupBox, QGridLayout, QMenuBar, QMenu
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

def load_data(filepath):
    # Dummy loader: replace with your real implementation
    x = np.linspace(0, 100, 1000)
    y = np.sin(x / 10) + np.random.normal(0, 0.1, len(x))
    return x, y

def calculate_peaks(x, params1, params2, params3):
    # Dummy peak calculator: replace with your real implementation
    peaks = np.zeros_like(x)
    peaks += params1[0] * np.exp(-(x - params1[1]) ** 2 / (2 * params1[2] ** 2))  # Gaussian
    peaks += params2[0] * np.exp(-(x - params2[1]) ** 2 / (2 * params2[2] ** 2))  # Gaussian
    peaks += params3[0] * np.exp(-(x - params3[1]) ** 2 / (2 * params3[2] ** 2))  # Gaussian
    return peaks

def optimise_parameters(x, y):
    # Dummy optimizer: replace with your real implementation
    return [5, 1, 1], [1, 50, 5, 1, 1], [2, 50, 5, 1]

class PeakFitter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Peak Fitting App")

        self.x = np.array([])
        self.y = np.array([])

        self.params1 = [5, 1, 1]
        self.params2 = [1, 50, 5, 1, 1]
        self.params3 = [2, 50, 5, 1]

        self.init_ui()

    def init_ui(self):
        # === Central Widget ===
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # === Matplotlib Canvas ===
        self.canvas = FigureCanvas(Figure(figsize=(6, 4)))
        self.ax = self.canvas.figure.add_subplot(111)
        layout.addWidget(self.canvas)

        # === Controls ===
        controls = QHBoxLayout()

        # Sliders
        controls.addWidget(self.create_slider_group("Params1", self.params1, self.update_plot))
        controls.addWidget(self.create_slider_group("Params2", self.params2, self.update_plot))
        controls.addWidget(self.create_slider_group("Params3", self.params3, self.update_plot))

        # Button
        self.optimise_btn = QPushButton("Optimise Parameters")
        self.optimise_btn.clicked.connect(self.optimise)
        controls.addWidget(self.optimise_btn)

        layout.addLayout(controls)

        # === Menu ===
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        open_action = QAction("Open...", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

    def create_slider_group(self, name, param_list, callback):
        group_box = QGroupBox(name)
        layout = QGridLayout()
        self.sliders = getattr(self, 'sliders', {})
        self.sliders[name] = []

        for i, val in enumerate(param_list):
            label = QLabel(f"{val:.2f}")
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(1000)
            slider.setValue(int(val * 10))
            slider.valueChanged.connect(lambda val, i=i, label=label, name=name: self.slider_changed(name, i, val, label, callback))
            layout.addWidget(QLabel(f"{name}[{i}]:"), i, 0)
            layout.addWidget(slider, i, 1)
            layout.addWidget(label, i, 2)
            self.sliders[name].append(slider)

        group_box.setLayout(layout)
        return group_box

    def slider_changed(self, group, idx, value, label, callback):
        label.setText(f"{value / 10:.2f}")
        getattr(self, group.lower())[idx] = value / 10
        callback()

    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Data File", "", "Data Files (*.txt *.csv *.dat);;All Files (*)")
        if filepath:
            self.x, self.y = load_data(filepath)
            self.update_plot()

    def update_plot(self):
        if self.x.size == 0:
            return
        self.ax.clear()
        self.ax.plot(self.x, self.y, label="Data")

        peak = calculate_peaks(self.x, self.params1, self.params2, self.params3)
        self.ax.plot(self.x, peak, label="Fit", color='red')

        self.ax.legend()
        self.canvas.draw()

    def optimise(self):
        if self.x.size == 0:
            return
        self.params1, self.params2, self.params3 = optimise_parameters(self.x, self.y)

        # Update sliders
        for i, val in enumerate(self.params1):
            self.sliders['Params1'][i].setValue(int(val * 10))
        for i, val in enumerate(self.params2):
            self.sliders['Params2'][i].setValue(int(val * 10))
        for i, val in enumerate(self.params3):
            self.sliders['Params3'][i].setValue(int(val * 10))

        self.update_plot()