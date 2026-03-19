"""
Wavelet Quantile-based Dependence Measures

This module implements:
1. Wavelet Cross-Quantilogram (WCQ) - for lead-lag dynamics
2. Conditional Expected Shortfall (CES) - for tail risk assessment
3. Extreme Downside Correlation (EDC) - for co-crashing risk
"""

import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Dict, Tuple, Optional, List
import warnings
warnings.filterwarnings('ignore')


class WaveletCrossQuantilogram:
    """
    Wavelet Cross-Quantilogram (WCQ)
    
    Extension of Cross-Quantilogram (Han et al., 2016) to wavelet domain.
    Measures cross-correlation of quantile-exceedance processes.
    """
    
    def __init__(self, max_lag: int = 20):
        """
        Initialize WCQ
        
        Parameters:
        -----------
        max_lag : int
            Maximum lag to consider
        """
        self.max_lag = max_lag
    
    def quantile_exceedance(self, series: np.ndarray, tau: float) -> np.ndarray:
        """
        Create quantile-exceedance indicator
        
        Parameters:
        -----------
        series : np.ndarray
            Time series
        tau : float
            Quantile level
            
        Returns:
        --------
        np.ndarray
            Binary indicator (1 if series <= quantile, 0 otherwise)
        """
        quantile = np.quantile(series, tau)
        return (series <= quantile).astype(float)
    
    def cross_quantilogram(self, x: np.ndarray, y: np.ndarray,
                          tau_x: float, tau_y: float, lag: int = 0) -> float:
        """
        Calculate cross-quantilogram at specific lag
        
        Parameters:
        -----------
        x : np.ndarray
            First series
        y : np.ndarray
            Second series
        tau_x : float
            Quantile level for x
        tau_y : float
            Quantile level for y
        lag : int
            Lag (positive: x leads y, negative: y leads x)
            
        Returns:
        --------
        float
            Cross-quantilogram coefficient
        """
        # Create quantile-exceedance indicators
        x_exceed = self.quantile_exceedance(x, tau_x)
        y_exceed = self.quantile_exceedance(y, tau_y)
        
        # Align series based on lag
        if lag >= 0:
            x_aligned = x_exceed[:-lag] if lag > 0 else x_exceed
            y_aligned = y_exceed[lag:]
        else:
            x_aligned = x_exceed[-lag:]
            y_aligned = y_exceed[:lag]
        
        # Ensure same length
        min_len = min(len(x_aligned), len(y_aligned))
        x_aligned = x_aligned[:min_len]
        y_aligned = y_aligned[:min_len]
        
        # Calculate correlation
        if min_len < 2:
            return np.nan
        
        # Center the indicators
        x_centered = x_aligned - np.mean(x_aligned)
        y_centered = y_aligned - np.mean(y_aligned)
        
        # Cross-quantilogram
        numerator = np.sum(x_centered * y_centered)
        denominator = np.sqrt(np.sum(x_centered**2) * np.sum(y_centered**2))
        
        if denominator == 0:
            return np.nan
        
        return numerator / denominator
    
    def compute_wcq(self, x: np.ndarray, y: np.ndarray,
                   tau_x: float, tau_y: float) -> pd.Series:
        """
        Compute WCQ for all lags
        
        Parameters:
        -----------
        x : np.ndarray
            First series
        y : np.ndarray
            Second series
        tau_x : float
            Quantile level for x
        tau_y : float
            Quantile level for y
            
        Returns:
        --------
        pd.Series
            WCQ values for each lag
        """
        lags = range(-self.max_lag, self.max_lag + 1)
        wcq_values = []
        
        for lag in lags:
            wcq = self.cross_quantilogram(x, y, tau_x, tau_y, lag)
            wcq_values.append(wcq)
        
        return pd.Series(wcq_values, index=lags)
    
    def compute_wavelet_wcq(self, x_decomp: Dict, y_decomp: Dict,
                           scale: int, tau_x: float, tau_y: float) -> pd.Series:
        """
        Compute WCQ for wavelet-decomposed series at specific scale
        
        Parameters:
        -----------
        x_decomp : dict
            Wavelet decomposition of x
        y_decomp : dict
            Wavelet decomposition of y
        scale : int
            Scale number
        tau_x : float
            Quantile level for x
        tau_y : float
            Quantile level for y
            
        Returns:
        --------
        pd.Series
            WCQ values
        """
        # Extract detail coefficients
        x_detail = x_decomp['details'][f'd_{scale}'].values
        y_detail = y_decomp['details'][f'd_{scale}'].values
        
        # Remove NaN
        valid_mask = np.isfinite(x_detail) & np.isfinite(y_detail)
        x_clean = x_detail[valid_mask]
        y_clean = y_detail[valid_mask]
        
        return self.compute_wcq(x_clean, y_clean, tau_x, tau_y)


class ConditionalExpectedShortfall:
    """
    Conditional Expected Shortfall (CES)
    
    Evaluates expected loss of one asset conditional on extreme movements
    of another variable. Extends traditional ES to bivariate tail risk context.
    """
    
    def __init__(self, alpha: float = 0.05):
        """
        Initialize CES
        
        Parameters:
        -----------
        alpha : float
            Tail probability level (default: 0.05 for 5% tail)
        """
        self.alpha = alpha
    
    def compute_ces(self, asset_returns: np.ndarray, 
                   conditioning_var: np.ndarray,
                   tail_direction: str = 'lower') -> float:
        """
        Compute Conditional Expected Shortfall
        
        Parameters:
        -----------
        asset_returns : np.ndarray
            Asset return series
        conditioning_var : np.ndarray
            Conditioning variable (e.g., GPR)
        tail_direction : str
            'lower' for downside risk, 'upper' for upside
            
        Returns:
        --------
        float
            CES value
        """
        # Align series
        min_len = min(len(asset_returns), len(conditioning_var))
        asset_aligned = asset_returns[:min_len]
        cond_aligned = conditioning_var[:min_len]
        
        # Remove NaN
        valid_mask = np.isfinite(asset_aligned) & np.isfinite(cond_aligned)
        asset_clean = asset_aligned[valid_mask]
        cond_clean = cond_aligned[valid_mask]
        
        if len(asset_clean) < 10:
            return np.nan
        
        # Determine threshold for conditioning variable
        if tail_direction == 'lower':
            threshold = np.quantile(cond_clean, self.alpha)
            condition_mask = cond_clean <= threshold
        else:
            threshold = np.quantile(cond_clean, 1 - self.alpha)
            condition_mask = cond_clean >= threshold
        
        # Calculate ES conditional on extreme conditioning variable
        conditional_returns = asset_clean[condition_mask]
        
        if len(conditional_returns) == 0:
            return np.nan
        
        # ES is the mean of returns in the tail
        if tail_direction == 'lower':
            # For downside risk, we care about negative returns
            tail_returns = conditional_returns[conditional_returns < 0]
            if len(tail_returns) == 0:
                return 0.0
            return np.mean(tail_returns)
        else:
            # For upside, we might want positive returns
            tail_returns = conditional_returns[conditional_returns > 0]
            if len(tail_returns) == 0:
                return 0.0
            return np.mean(tail_returns)
    
    def compute_wavelet_ces(self, asset_decomp: Dict, gpr_decomp: Dict,
                           scale: int, tail_direction: str = 'lower') -> float:
        """
        Compute CES for wavelet-decomposed series
        
        Parameters:
        -----------
        asset_decomp : dict
            Asset return decomposition
        gpr_decomp : dict
            GPR decomposition
        scale : int
            Scale number
        tail_direction : str
            'lower' or 'upper'
            
        Returns:
        --------
        float
            CES value
        """
        asset_detail = asset_decomp['details'][f'd_{scale}'].values
        gpr_detail = gpr_decomp['details'][f'd_{scale}'].values
        
        return self.compute_ces(asset_detail, gpr_detail, tail_direction)


class ExtremeDownsideCorrelation:
    """
    Extreme Downside Correlation (EDC)
    
    Quantifies co-crashing risk in the lower tail of joint distribution.
    Measures correlation when both assets experience extreme negative returns.
    """
    
    def __init__(self, alpha: float = 0.05):
        """
        Initialize EDC
        
        Parameters:
        -----------
        alpha : float
            Tail probability level
        """
        self.alpha = alpha
    
    def compute_edc(self, returns1: np.ndarray, returns2: np.ndarray) -> float:
        """
        Compute Extreme Downside Correlation
        
        Parameters:
        -----------
        returns1 : np.ndarray
            First asset returns
        returns2 : np.ndarray
            Second asset returns
            
        Returns:
        --------
        float
            EDC value
        """
        # Align series
        min_len = min(len(returns1), len(returns2))
        r1_aligned = returns1[:min_len]
        r2_aligned = returns2[:min_len]
        
        # Remove NaN
        valid_mask = np.isfinite(r1_aligned) & np.isfinite(r2_aligned)
        r1_clean = r1_aligned[valid_mask]
        r2_clean = r2_aligned[valid_mask]
        
        if len(r1_clean) < 10:
            return np.nan
        
        # Identify extreme downside events for both assets
        threshold1 = np.quantile(r1_clean, self.alpha)
        threshold2 = np.quantile(r2_clean, self.alpha)
        
        # Both assets in lower tail simultaneously
        extreme_mask = (r1_clean <= threshold1) & (r2_clean <= threshold2)
        
        if np.sum(extreme_mask) < 2:
            return np.nan
        
        # Calculate correlation in extreme downside region
        r1_extreme = r1_clean[extreme_mask]
        r2_extreme = r2_clean[extreme_mask]
        
        if np.std(r1_extreme) == 0 or np.std(r2_extreme) == 0:
            return np.nan
        
        correlation = np.corrcoef(r1_extreme, r2_extreme)[0, 1]
        return correlation
    
    def compute_wavelet_edc(self, decomp1: Dict, decomp2: Dict,
                           scale: int) -> float:
        """
        Compute EDC for wavelet-decomposed series
        
        Parameters:
        -----------
        decomp1 : dict
            First asset decomposition
        decomp2 : dict
            Second asset decomposition
        scale : int
            Scale number
            
        Returns:
        --------
        float
            EDC value
        """
        detail1 = decomp1['details'][f'd_{scale}'].values
        detail2 = decomp2['details'][f'd_{scale}'].values
        
        return self.compute_edc(detail1, detail2)
    
    def compute_pairwise_edc(self, decompositions: Dict[str, Dict],
                            scale: int) -> pd.DataFrame:
        """
        Compute pairwise EDC matrix for multiple assets
        
        Parameters:
        -----------
        decompositions : dict
            Dictionary of asset names to decompositions
        scale : int
            Scale number
            
        Returns:
        --------
        pd.DataFrame
            EDC matrix
        """
        assets = list(decompositions.keys())
        n = len(assets)
        edc_matrix = np.zeros((n, n))
        
        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets):
                if i == j:
                    edc_matrix[i, j] = 1.0
                else:
                    edc = self.compute_wavelet_edc(
                        decompositions[asset1],
                        decompositions[asset2],
                        scale
                    )
                    edc_matrix[i, j] = edc
        
        return pd.DataFrame(edc_matrix, index=assets, columns=assets)


class DependenceAnalyzer:
    """
    High-level interface for all dependence measures
    """
    
    def __init__(self, max_lag: int = 20, alpha: float = 0.05):
        """
        Initialize analyzer
        
        Parameters:
        -----------
        max_lag : int
            Maximum lag for WCQ
        alpha : float
            Tail probability for CES and EDC
        """
        self.wcq = WaveletCrossQuantilogram(max_lag=max_lag)
        self.ces = ConditionalExpectedShortfall(alpha=alpha)
        self.edc = ExtremeDownsideCorrelation(alpha=alpha)
    
    def analyze_all_measures(self, asset_decomp: Dict, gpr_decomp: Dict,
                            scales: List[int], tau_x: float = 0.05,
                            tau_y: float = 0.05) -> Dict:
        """
        Compute all dependence measures for all scales
        
        Parameters:
        -----------
        asset_decomp : dict
            Asset decomposition
        gpr_decomp : dict
            GPR decomposition
        scales : list
            List of scales
        tau_x : float
            Quantile for GPR
        tau_y : float
            Quantile for asset
            
        Returns:
        --------
        dict
            Dictionary with WCQ, CES, and EDC results
        """
        results = {
            'wcq': {},
            'ces': {},
            'edc': {}
        }
        
        for scale in scales:
            try:
                # WCQ
                wcq_series = self.wcq.compute_wavelet_wcq(
                    gpr_decomp, asset_decomp, scale, tau_x, tau_y
                )
                results['wcq'][scale] = wcq_series
                
                # CES
                ces_value = self.ces.compute_wavelet_ces(
                    asset_decomp, gpr_decomp, scale
                )
                results['ces'][scale] = ces_value
                
            except Exception as e:
                print(f"Warning: Could not compute measures at scale {scale}: {e}")
        
        return results

