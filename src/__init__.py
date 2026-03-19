"""
Geopolitical Risk Analysis Package

A comprehensive econometric framework for analyzing relationships between
geopolitical risk and financial assets using wavelet and quantile methods.
"""

from .preprocessing import DataPreprocessor
from .wavelet_analysis import MODWT, WaveletAnalyzer

__version__ = '1.0.0'
__all__ = [
    'DataPreprocessor',
    'MODWT',
    'WaveletAnalyzer'
]

