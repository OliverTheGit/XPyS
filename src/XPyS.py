import sys
import os
from sys import prefix

import numpy as np
import matplotlib.pyplot as plt
import lmfit
import matplotlib as mpl
import lmfitxps.backgrounds
import MoreModels
from DataImport import load_specslab_xy_with_error_bars, load_specslab_xy

from PyQt6.QtWidgets import QApplication
from GuiLayout import PeakFitter
#
# examples_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'examples'))
# data = load_specslab_xy(os.path.join(examples_path, 'Cathode Constituents Carbon Black C1S22.xy'), apply_transmission=True)
#
# x = data[:,0]
# y = data[:,1]
#
# background = lmfitxps.backgrounds.shirley_calculate(x, y, maxit=100)
# asymmetric_peak = MoreModels.ConvGaussianSplitLorentz(independent_vars=["x"], prefix="asymm_")
# voigt_peak = lmfit.models.VoigtModel(independent_vars=["x"], prefix="voigt_")
# fit_model = asymmetric_peak + voigt_peak
#
# params = lmfit.Parameters()
# params.add('asymm_amplitude', value=2500, min=0)
# params.add('asymm_center', value=1202.3)
# params.add('asymm_sigma', value=0.7, min=0)
# params.add('asymm_sigma_r', value=1, min=0)
# params.add('asymm_gaussian_sigma', value=10, min=0)
# params.add('voigt_amplitude', value=1000, min=0)
# params.add('voigt_center', value=1201.8)
# params.add('voigt_sigma', value=5, min=0)
# params.add('voigt_gamma', value=2, min=0)
#
# result = fit_model.fit(y, params, x=x, weights=1 /(np.sqrt(y)))
# comps = result.eval_components(x=x, y=y)
# print(result.fit_report())
#
# fig, (ax1, ax2) = plt.subplots(nrows=2,gridspec_kw={'height_ratios': [1, 1]}, sharex=True)
# fig.patch.set_facecolor('#FCFCFC')
# cmap = mpl.colormaps['tab20']
# ax1.plot(x, result.best_fit, label='Best Fit', color=cmap(0))
# ax1.plot(x, y, 'x', markersize=4, label='Data Points', color=cmap(2))
#
# ax1.plot(x, background, label='Shirley background', color='black')
# ax1.plot(x, comps['asymm_'] + background, color=cmap(4), label="Asymmetric peak")
# ax1.plot(x, comps['voigt_'] + background, color=cmap(5), label="Voigt peak")
#
# #ax1.fill_between(x, comps['asymm_'] + background, background, alpha=0.5,color=cmap(5))
# ax1.legend()
# ax1.set_xlabel('kinetic energy in eV')
# ax1.set_ylabel('intensity in arb. units')
# # Set ticks only inside
# ax1.tick_params(axis='x', which='both',top=True, direction='in')
# ax1.tick_params(axis='y', which='both', right=True,direction='in')
# ax2.tick_params(axis='x', which='both',top=True, direction='in')
# ax2.tick_params(axis='y', which='both', right=True, direction='in')
#
# ax1.set_yticklabels([])
# ax1.set_title(f'Asymmetric LA')
# fig.subplots_adjust(hspace=0)
# ax1.set_xlim(np.min(x), np.max(x))
# # Residual plot
# residual = result.residual
# ax2.plot(x, residual)
# ax2.set_xlabel('kinetic energy in eV')
# ax2.set_ylabel('Residual')
#
# fig.show()
# plt.show(block=True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PeakFitter()
    window.show()
    sys.exit(app.exec())