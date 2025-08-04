import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import lmfit
from lmfitxps import models, XPSFitter
import matplotlib as mpl
from lmfitxps.models import ShirleyBG

from DataImport import load_specslab_xy_with_error_bars, load_specslab_xy

examples_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'examples'))
data = load_specslab_xy(examples_path, apply_transmission=True)

x = data[:,0]
y = data[:,1]

fitter = XPSFitter(x,y)
background = ShirleyBG(independent_vars=["y"], prefix="shirley_")
peak1