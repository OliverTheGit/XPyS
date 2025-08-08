import os.path

import lmfit
import numpy as np
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
    QPushButton, QFileDialog
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import CustomWidgets
import DataImport
import MoreModels
import lmfitxps.models


class PeakFitter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Peak Fitting App")

        self.x = np.array([])
        self.y = np.array([])
        self.err_bars = np.array([])

        self.components = {}

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

        # # Sliders
        # vp = CustomWidgets.PeakDataModel(lmfit.models.VoigtModel(prefix="Voigt1_"))
        # cgp = CustomWidgets.PeakDataModel(MoreModels.ConvGaussianSplitLorentz(prefix="ConvGauss1_"))
        # bkg = CustomWidgets.PeakDataModel(lmfit.Model(MoreModels.calculate_shirley,prefix="Shirley_", independent_vars=['x','y']))
        #
        # peak_group_voigt = CustomWidgets.QModelParamGroup(vp)
        # peak_group_cgp = CustomWidgets.QModelParamGroup(cgp)
        # param_group_bkg = CustomWidgets.QModelParamGroup(bkg)
        #
        # peak_group_voigt.paramChanged.connect(self.update_plot)
        # peak_group_cgp.paramChanged.connect(self.update_plot)
        # param_group_bkg.paramChanged.connect(self.update_plot)
        #
        # peak_group_voigt.request_deletion.connect(self.delete_model)
        # peak_group_cgp.request_deletion.connect(self.delete_model)
        # param_group_bkg.request_deletion.connect(self.delete_model)
        #
        # self.components = {"Voigt1_": peak_group_voigt, "ConvGauss1_": peak_group_cgp, "Shirley_": param_group_bkg}
        # for m in self.components.values():
        #     controls.addWidget(m)

        # # Button
        # self.optimise_btn = QPushButton("Optimise Parameters")
        # self.optimise_btn.clicked.connect(self.optimise)
        # controls.addWidget(self.optimise_btn)

        layout.addLayout(controls)

        # === Menu ===
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        open_action = QAction("Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        spectrum_menu = menubar.addMenu("Spectrum")
        add_peak_action = QAction("Add peak")
        add_peak_action.setShortcut(CustomWidgets.platform_ctrl_or_cmd("A"))
        add_peak_action.triggered.connect(self.open_file)
        spectrum_menu.addAction(add_peak_action)

        optimise_action = QAction("Optimise Parameters")
        optimise_action.setShortcut(CustomWidgets.platform_ctrl_or_cmd("Shift+O"))
        optimise_action.triggered.connect(self.optimise)
        spectrum_menu.addAction(optimise_action)

    def slider_changed(self, group, idx, value, callback):
        getattr(self, group.lower())[idx] = value
        callback()

    def delete_model(self, name):
        if name not in self.components.keys():
            raise ValueError(f"{name} not in self.models")
        model_to_delete = self.components.pop(name)
        model_to_delete.hide()
        model_to_delete.deleteLater()
        self.update_plot()

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
            for model in self.components.values():
                assert isinstance(model, CustomWidgets.QModelParamGroup)
                self.plot_peak_model(model.data_model)
        else:
            model = self.components.get(name)
            if model is None:
                raise ValueError(f"{name} not a recognised peak model")
            self.plot_peak_model(model.data_model)

        self.plot_envelope()

        self.ax.legend()
        self.canvas.draw_idle()

    def plot_peak_model(self, peak_model):
        peak_name = peak_model.get_name()
        model_y = peak_model.evaluate(self.x, y=self.y)  # TODO: options for finer x to look prettier?
        if peak_name in self.model_lines.keys():
            self.model_lines[peak_name].set_xdata(self.x)
            self.model_lines[peak_name].set_ydata(model_y)
        else:
            self.model_lines[peak_name] = self.ax.plot(self.x, model_y, label=peak_name.title())[0]

    def plot_envelope(self):
        envelope_y = np.zeros_like(self.x)
        for model in self.components.values():
            needs_y = 'y' in model.data_model.eval_requirements()
            temp_kwargs = {'y': self.y} if needs_y else {}
            envelope_y += model.data_model.evaluate(self.x, **temp_kwargs)
        if "Envelope" in self.model_lines:
            self.model_lines["Envelope"].set_xdata(self.x)
            self.model_lines["Envelope"].set_ydata(envelope_y)
        else:
            self.model_lines["Envelope"] = self.ax.plot(self.x, envelope_y, label="Envelope")[0]

    def optimise(self):
        if self.x.size == 0:
            return

        models = [m.data_model for m in self.components.values()]
        result = MoreModels.optimise_multiple_models(self.x, self.y, models)
        assert isinstance(result, lmfit.model.ModelResult)
        summary = result.summary()
        a=1
        for pref, comp in self.components.items():
            for k,v in summary["best_values"].items():
                if k.startswith(pref):
                    comp.set_param_directly(k, v)

