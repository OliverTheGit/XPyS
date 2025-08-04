import numpy as np
from lmfit.lineshapes import  gaussian, split_lorentzian
from lmfitxps.lineshapes import fft_convolve
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
       A model based on a convolution of a Gaussian and a Split Lorentzian profile.
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
