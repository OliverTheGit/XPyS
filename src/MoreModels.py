import numpy as np
from lmfit.lineshapes import  gaussian, split_lorentzian
from lmfitxps.lineshapes import fft_convolve
from lmfitxps import backgrounds
from lmfit import Model
import lmfit
from lmfit.models import guess_from_peak


def split_lorentz_conv_gauss(x,
                             amplitude: float,
                             center: float,
                             sigma: float,
                             sigma_r: float,
                             gaussian_sigma: float) -> float:
    is_binding_energy = x[-1] < x[0]
    conv_temp = fft_convolve(split_lorentzian(x, amplitude=1, center=center, sigma=sigma, sigma_r=sigma_r),
                             1 / (np.sqrt(2 * np.pi) * gaussian_sigma) * gaussian(x, amplitude=1, center=np.mean(x),
                                                                                  sigma=gaussian_sigma),
                             is_binding_energy=is_binding_energy)
    return amplitude * conv_temp / max(conv_temp)

class ConvGaussianSplitLorentz(lmfit.model.Model):
    __doc__ = ("""
       A model is a convolution of a Gaussian and a Split Lorentzian profile.
       This was entirely based on the lmfitxps models and is intended to mimic CasaXPS LA(alpha, beta, m)
       
       .. table:: Model-specific available parameters
        :widths: auto
        
        +----------------+---------------+----------------------------------------------------------------------------------------+
        | Parameters     |  Type         | Description                                                                            |
        +================+===============+========================================================================================+
        | x              | :obj:`array`  | 1D-array containing the x-values (energies) of the spectrum.                           |
        +----------------+---------------+----------------------------------------------------------------------------------------+
        | y              | :obj:`array`  | 1D-array containing the y-values (intensities) of the spectrum.                        |
        +----------------+---------------+----------------------------------------------------------------------------------------+
        | amplitude      | :obj:`float`  | amplitude :math:`A` of the peak profile                                                |
        +----------------+---------------+----------------------------------------------------------------------------------------+
        | center         | :obj:`float`  | Center of the peak profile.                                                            |
        +----------------+---------------+----------------------------------------------------------------------------------------+
        | sigma          | :obj:`float`  | Width of Lorentzian to left of centre                                                  |
        +----------------+---------------+----------------------------------------------------------------------------------------+
        | sigma_r        | :obj:`float`  | Width of Lorentzian to right of centre                                                 |
        +----------------+---------------+----------------------------------------------------------------------------------------+
        | gaussian_sigma | :obj:`float`  | Width of the gaussian convolution kernel                                               |
        +----------------+---------------+----------------------------------------------------------------------------------------+

       **LMFIT: Common models documentation**
    """"""""""""""""""""""""""""""""""""

    """ + lmfit.models.COMMON_INIT_DOC)

    def __init__(self, *args, **kwargs):
        super().__init__(split_lorentz_conv_gauss, *args, **kwargs)
        self._set_paramhints_prefix()

    def _set_paramhints_prefix(self):
        self.set_param_hint('amplitude', value=100, min=0)
        self.set_param_hint('sigma', value=0.2, min=0)
        self.set_param_hint('sigma_r', value=0.02)
        self.set_param_hint('gaussian_sigma', value=0.2, min=0)
        self.set_param_hint('center', value=100, min=0)
        g_fwhm_expr = '2*{pre:s}gaussian_sigma*1.17741'
        self.set_param_hint('gaussian_fwhm', expr=g_fwhm_expr.format(pre=self.prefix))

    def guess(self, data, x=None, **kwargs):
        """
        Hint
        ----

        Needs improvement and does not work great yet. E.g. using peakfind.


        Generates initial parameter values for the model based on the provided data and optional arguments.

        :param data: Array containing the data (=intensities) to fit.
        :type data: array-like
        :param x: Array containing the independent variable (=energy).
        :type x: array-like
        :param kwargs: Initial guesses for the parameters of the model function.

        :returns: Initial parameter values for the model.
        :rtype: lmfit.Parameters


        :note:
            The method requires the 'x' parameter to be provided.
        """
        if x is None:
            return
        lorentz_pars = guess_from_peak(Model(split_lorentzian), data, x, negative=False)
        gaussian_sigma = (lorentz_pars["sigma"].value + lorentz_pars["sigma"].value) / 2
        params = self.make_params(amplitude=lorentz_pars["amplitude"].value, sigma=lorentz_pars["sigma"].value,
                                  sigma_r=lorentz_pars["sigma_r"].value, gaussian_sigma=gaussian_sigma,
                                  center=lorentz_pars["center"].value)
        return lmfit.models.update_param_vals(params, self.prefix, **kwargs)


def calculate_shirley(x, y, avg_width: int = 1, offset_low = 0.0, offset_high = 0.0) -> np.ndarray:
    if avg_width >= len(y):
        avg_width = len(y) // 3  # fallback if too large (//=floordiv)

    # Get average of low/high end intensities
    left_avg = np.mean(y[:avg_width])
    right_avg = np.mean(y[-avg_width:])

    # Apply offsets
    left_val = left_avg + offset_low
    right_val = right_avg + offset_high

    # Create bounds tuple: ((x_low, y_low), (x_high, y_high))
    bounds = ((x[0], left_val), (x[-1], right_val))

    # tolerance and max iterations don't play well with optimisation stuff, so I'm hardcoding here
    # TODO: make Shirley tolerance and max_iter a settings thing, not hardcoded

    return backgrounds.shirley_calculate(x, y, bounds=bounds, tol=1e-6, maxit=100)

class Shirley(lmfit.model.Model):
    __doc__ = ("""
       A model that is a Shirley background implementation with parameters that can be optimised to adjust the end point values

        +----------------+---------------+----------------------------------------------------------------------------------------+
        | Parameters     |  Type         | Description                                                                            |
        +================+===============+========================================================================================+
        | x              | :obj:`array`  | 1D-array containing the x-values (energies) of the spectrum.                           |
        +----------------+---------------+----------------------------------------------------------------------------------------+
        | y              | :obj:`array`  | 1D-array containing the y-values (intensities) of the spectrum.                        |
        +----------------+---------------+----------------------------------------------------------------------------------------+
        | offset_low     | :obj:`float`  | amplitude offset at the low end of the spectrum                                        |
        +----------------+---------------+----------------------------------------------------------------------------------------+
        | offset_high    | :obj:`float`  | amplitude offset at the high end of the spectrum                                       |
        +----------------+---------------+----------------------------------------------------------------------------------------+
        | avg_width      | :obj:`float`  | Number of values to average over to get the high and low values at the ends            |
        +----------------+---------------+----------------------------------------------------------------------------------------+

       **LMFIT: Common models documentation**
    """"""""""""""""""""""""""""""""""""

    """ + lmfit.models.COMMON_INIT_DOC)

    def __init__(self, *args, **kwargs):
        super().__init__(calculate_shirley, *args, **kwargs)
        self._set_paramhints_prefix()
        self.independent_vars.append('y')

    def _set_paramhints_prefix(self):
        self.set_param_hint('offset_low', value=0)
        self.set_param_hint('offest_high', value=0)
        self.set_param_hint('avg_width', value=5)