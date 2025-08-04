import sys
import os
from sys import prefix

import numpy as np
import matplotlib.pyplot as plt
import lmfit
import matplotlib as mpl
import lmfitxps.models
import MoreModels

from DataImport import load_specslab_xy_with_error_bars, load_specslab_xy

examples_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'examples'))
data = load_specslab_xy(os.path.join(examples_path, 'Cathode Constituents Carbon Black C1S22.xy'), apply_transmission=True)

x = data[:,0]
y = data[:,1]

background = lmfitxps.models.ShirleyBG(independent_vars=["y"], prefix="shirley_")
asymmetric_peak = MoreModels.ConvGaussianSplitLorentz(independent_vars=["x"], prefix="asymm_")
voigt_peak = lmfit.models.VoigtModel(independent_vars=["x"], prefix="voigt_")
fit_model = background + asymmetric_peak + voigt_peak

params = lmfit.Parameters()
params.add('shirley_k', value=0.002)
params.add('shirley_const', value=100)
params.add('asymm_amplitude', value=2500)
params.add('asymm_center', value=1202.3)
params.add('asymm_sigma', value=0.7)
params.add('asymm_sigma_r', value=1)
params.add('asymm_gaussian_sigma', value=10)
params.add('voigt_amplitude', value=1000)
params.add('voigt_center', value=1201.8)
params.add('voigt_sigma', value=5)
params.add('voigt_gamma', value=2)

result = fit_model.fit(y, params, y=y, x=x, weights=1 /(np.sqrt(y)))
comps = result.eval_components(x=x, y=y)
print(result.fit_report())