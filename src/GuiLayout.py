import os.path

import lmfit
import numpy as np
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
    QPushButton, QFileDialog
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import CustomWidgets
import DataImport
import MoreModels


def optimise_parameters(x, y):
    # Dummy optimizer: replace with your real implementation
    return [5, 1, 1], [1, 50, 5, 1, 1], [2, 50, 5, 1]


class PeakFitter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Peak Fitting App")

        self.x = np.array([])
        self.y = np.array([])
        self.err_bars = np.array([])

        self.components = [lmfit.models.VoigtModel(prefix="Voigt1_"),
                           MoreModels.ConvGaussianSplitLorentz(prefix="ConvGauss1_")]

        self.init_ui()

    def init_ui(self):
        # === Central Widget ===
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # === Matplotlib Canvas ===
        self.canvas = FigureCanvas(Figure(figsize=(6, 4)))
        self.ax = self.canvas.figure.add_subplot(111)
        self.model_lines = {}
        layout.addWidget(self.canvas)

        # === Controls ===
        controls = QHBoxLayout()

        # Sliders
        vp = lmfit.models.VoigtModel(prefix="Voigt1_")
        cgp = MoreModels.ConvGaussianSplitLorentz(prefix="ConvGauss1_")
        bkg = MoreModels.Shirley(prefix="Shirley_")

        peak_group_voigt = CustomWidgets.QModelParamGroup(CustomWidgets.PeakDataModel(vp))
        peak_group_cgp = CustomWidgets.QModelParamGroup(CustomWidgets.PeakDataModel(cgp))
        param_group_bkg = CustomWidgets.QModelParamGroup(CustomWidgets.PeakDataModel(bkg))

        peak_group_voigt.paramChanged.connect(self.update_plot)
        peak_group_cgp.paramChanged.connect(self.update_plot)
        param_group_bkg.paramChanged.connect(self.update_plot)

        self.models = {"Voigt1_": peak_group_voigt, "ConvGauss1_": peak_group_cgp, "Shirley_": param_group_bkg}
        for m in self.models.values():
            controls.addWidget(m)

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

    def slider_changed(self, group, idx, value, callback):
        getattr(self, group.lower())[idx] = value
        callback()

    def open_file(self):
        # commented out to quickly load test data during development
        # filepath, _ = QFileDialog.getOpenFileName(self, "Open Data File", "",
        #                                           "Data Files (*.txt *.csv *.dat *.xy);;All Files (*)")
        filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'examples', 'Cathode Constituents Carbon Black C1S22.xy'))
        if filepath:
            _, ext = os.path.splitext(filepath)
            # incl_errs = False
            # if ext == ".xy":
            #     result = QMessageBox.question(None, "", "Do you want to include error bars?",
            #                                   QMessageBox.StandardButton.Yes |
            #                                   QMessageBox.StandardButton.No |
            #                                   QMessageBox.StandardButton.Cancel)
            #     if result == QMessageBox.StandardButton.Yes:
            #         incl_errs = True
            #     elif result == QMessageBox.StandardButton.Cancel:
            #         return
            # if incl_errs:
            #     data, self.err_bars = DataImport.load_specslab_xy_with_error_bars(filepath)
            # else:
            data = DataImport.load_specslab_xy(filepath)
            self.err_bars = None

            self.x = data[:, 0]
            self.y = data[:, 1]
            self.update_plot()

    def update_plot(self, name=""):
        if self.x.size == 0:
            return

        if name == "":
            self.ax.clear()
            self.ax.plot(self.x, self.y, 'kx', label="Data")
            self.model_lines = {}
            for model in self.models.values():
                assert isinstance(model, CustomWidgets.QModelParamGroup)
                self.plot_peak_model(model.peak_model)
        else:
            model = self.models.get(name)
            if model is None:
                raise ValueError(f"{name} not a recognised peak model")
            self.plot_peak_model(model.peak_model)

        self.plot_envelope()

        self.ax.legend()
        self.canvas.draw_idle()

    def plot_peak_model(self, peak_model):
        peak_name = peak_model.get_name()
        needs_y = 'y' in peak_model.eval_requirements()
        temp_kwargs = {'y': self.y} if needs_y else {}
        model_y = peak_model.evaluate(self.x, **temp_kwargs)  # TODO: options for finer x to look prettier?
        if peak_name in self.model_lines.keys():
            self.model_lines[peak_name].set_xdata(self.x)
            self.model_lines[peak_name].set_ydata(model_y)
        else:
            self.model_lines[peak_name] = self.ax.plot(self.x, model_y, label=peak_name.title())[0]

    def plot_envelope(self):
        envelope_y = np.zeros_like(self.x)
        for model in self.models.values():
            needs_y = 'y' in model.peak_model.eval_requirements()
            temp_kwargs = {'y': self.y} if needs_y else {}
            envelope_y += model.peak_model.evaluate(self.x, **temp_kwargs)
        if "Envelope" in self.model_lines:
            self.model_lines["Envelope"].set_xdata(self.x)
            self.model_lines["Envelope"].set_ydata(envelope_y)
        else:
            self.model_lines["Envelope"] = self.ax.plot(self.x, envelope_y, label="Envelope")[0]

    def optimise(self):
        if self.x.size == 0:
            return
        return
