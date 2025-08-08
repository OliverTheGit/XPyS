import numpy
import scipy.signal as signal
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt
import math


def calculate_fwhm(x, y, peak_index: int):
    peak_value = y[peak_index]
    half_peak_value = peak_value / 2

    # Find the closest point to the left of peak_index where y <= half_peak_value
    left_index = peak_index
    while left_index > 0 and y[left_index] > half_peak_value:
        left_index -= 1

    # Find the closest point to the right of peak_index where y <= half_peak_value
    right_index = peak_index
    while right_index < len(y) - 1 and y[right_index] > half_peak_value:
        right_index += 1

    # Get the x values corresponding to these points
    left_x = x[left_index]
    right_x = x[right_index]

    # FWHM is the difference between the right and left x values
    fwhm = right_x - left_x
    return fwhm, left_x, right_x


def best_guess(x: np.ndarray, y: np.ndarray, window_size=None):
    if window_size is None:
        window_size = math.floor(min(len(y) / 50, 5))
    y_smoothed = np.convolve(y, np.ones(window_size) / window_size, mode='same')
    peaks = signal.find_peaks(y)[0]

    largest_amplitude = 0
    biggest_peak_pos = 0
    biggest_peak_fwhm_left = 0
    biggest_peak_fwhm_right = 0
    for peak_index in peaks:
        _, left_x, right_x = calculate_fwhm(x, y, peak_index)
        if y[peak_index] > largest_amplitude:
            largest_amplitude = y[peak_index]
            biggest_peak_pos = x[peak_index]
            biggest_peak_fwhm_left = x[peak_index] - left_x
            biggest_peak_fwhm_right = right_x - x[peak_index]
    return largest_amplitude, biggest_peak_pos, biggest_peak_fwhm_left, biggest_peak_fwhm_right
