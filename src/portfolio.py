"""
Multivariate Portfolio Optimization Module

This module implements:
1. Quantile and ES-based covariance estimation (Fissler & Ziegel, 2016)
2. DCC (Dynamic Conditional Correlation) model
3. Portfolio optimization strategies: MVP, MCP, MCoP
4. Hedging effectiveness measurement
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    import cvxpy as cp
    CVXPY_AVAILABLE = True
except ImportError:
    CVXPY_AVAILABLE = False
    warnings.warn("cvxpy not available. Some optimization methods may not work.")


class QuantileESLoss:
    """
    Joint quantile and Expected Shortfall (ES) loss framework
    Based on Fissler & Ziegel (2016)
    """
    
    @staticmethod
    def quantile_es_loss(y: np.ndarray, q_pred: np.ndarray, es_pred: np.ndarray,
                        tau: float) -> float:
        """
        Joint quantile and ES loss function
        
        Parameters:
        -----------
        y : np.ndarray
            Observed returns
        q_pred : np.ndarray
            Predicted quantile
        es_pred : np.ndarray
            Predicted ES
        tau : float
            Quantile level
            
        Returns:
        --------
        float
            Loss value
        """
        # Quantile loss component
        quantile_loss = np.mean(np.maximum(
            tau * (y - q_pred),
            (tau - 1) * (y - q_pred)
        ))
        
        # ES loss component
        es_loss = np.mean(
            (es_pred - q_pred + (1/tau) * np.maximum(q_pred - y, 0)) ** 2
        )
        
        return quantile_loss + es_loss


class DCCModel:
    """
    Dynamic Conditional Correlation (DCC) Model
    
    Models time-varying correlation structure
    """
    
    def __init__(self, p: int = 1, q: int = 1):
        """
        Initialize DCC model
        
        Parameters:
        -----------
        p : int
            ARCH order
        q : int
            GARCH order
        """
        self.p = p
        self.q = q
    
    def estimate_dcc(self, returns: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Estimate DCC model
        
        Parameters:
        -----------
        returns : pd.DataFrame
            Asset returns (n x k)
            
        Returns:
        --------
        tuple
            (H_t: covariance matrices, R_t: correlation matrices)
        """
        # Simplified DCC implementation
        # In practice, use arch library for full DCC-GARCH
        
        n, k = returns.shape
        H_t = []
        R_t = []
        
        # Estimate univariate GARCH volatilities (simplified)
        volatilities = pd.DataFrame(index=returns.index, columns=returns.columns)
        for col in returns.columns:
            # Simple EWMA volatility
            volatilities[col] = returns[col].ewm(span=60).std()
        
        # Estimate correlation using rolling window
        window = 60
        for i in range(window, n):
            window_returns = returns.iloc[i-window:i]
            
            # Correlation matrix
            R = window_returns.corr().values
            
            # Covariance matrix
            vol_vec = volatilities.iloc[i].values
            H = np.outer(vol_vec, vol_vec) * R
            
            H_t.append(H)
            R_t.append(R)
        
        # Pad with first values
        H_first = [H_t[0]] * window
        R_first = [R_t[0]] * window
        
        H_t = H_first + H_t
        R_t = R_first + R_t
        
        H_df = pd.DataFrame(
            [H.flatten() for H in H_t],
            index=returns.index
        )
        R_df = pd.DataFrame(
            [R.flatten() for R in R_t],
            index=returns.index
        )
        
        return H_df, R_df


class PortfolioOptimizer:
    """
    Portfolio optimization with multiple strategies
    """
    
    def __init__(self, assets: List[str]):
        """
        Initialize optimizer
        
        Parameters:
        -----------
        assets : list
            List of asset names
        """
        self.assets = assets
        self.n_assets = len(assets)
    
    def minimum_variance_portfolio(self, H_t: np.ndarray,
                                  constraints: Optional[Dict] = None) -> np.ndarray:
        """
        Minimum Variance Portfolio (MVP)
        
        Minimizes portfolio variance: min w' H w
        
        Parameters:
        -----------
        H_t : np.ndarray
            Covariance matrix (k x k)
        constraints : dict, optional
            Additional constraints (e.g., {'long_only': True, 'sum_to_one': True})
            
        Returns:
        --------
        np.ndarray
            Optimal weights
        """
        if constraints is None:
            constraints = {'long_only': True, 'sum_to_one': True}
        
        def objective(w):
            return w @ H_t @ w
        
        # Initial guess: equal weights
        w0 = np.ones(self.n_assets) / self.n_assets
        
        # Constraints
        cons = []
        if constraints.get('sum_to_one', True):
            cons.append({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
        
        bounds = []
        if constraints.get('long_only', True):
            bounds = [(0, 1) for _ in range(self.n_assets)]
        else:
            bounds = [(-1, 1) for _ in range(self.n_assets)]
        
        # Optimize
        result = minimize(objective, w0, method='SLSQP',
                         bounds=bounds, constraints=cons)
        
        return result.x
    
    def minimum_correlation_portfolio(self, R_t: np.ndarray,
                                     constraints: Optional[Dict] = None) -> np.ndarray:
        """
        Minimum Correlation Portfolio (MCP)
        
        Minimizes average pairwise correlation
        
        Parameters:
        -----------
        R_t : np.ndarray
            Correlation matrix (k x k)
        constraints : dict, optional
            Additional constraints
            
        Returns:
        --------
        np.ndarray
            Optimal weights
        """
        if constraints is None:
            constraints = {'long_only': True, 'sum_to_one': True}
        
        def objective(w):
            # Average pairwise correlation weighted by portfolio weights
            weighted_corr = 0
            for i in range(self.n_assets):
                for j in range(i + 1, self.n_assets):
                    weighted_corr += w[i] * w[j] * R_t[i, j]
            return weighted_corr
        
        w0 = np.ones(self.n_assets) / self.n_assets
        
        cons = []
        if constraints.get('sum_to_one', True):
            cons.append({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
        
        bounds = []
        if constraints.get('long_only', True):
            bounds = [(0, 1) for _ in range(self.n_assets)]
        else:
            bounds = [(-1, 1) for _ in range(self.n_assets)]
        
        result = minimize(objective, w0, method='SLSQP',
                         bounds=bounds, constraints=cons)
        
        return result.x
    
    def pairwise_connectedness_index(self, returns: pd.DataFrame,
                                    window: int = 60) -> pd.DataFrame:
        """
        Calculate Pairwise Connectedness Index (PCI)
        
        Measures spillover effects between assets
        
        Parameters:
        -----------
        returns : pd.DataFrame
            Asset returns
        window : int
            Rolling window size
            
        Returns:
        --------
        pd.DataFrame
            PCI matrix
        """
        n_assets = len(self.assets)
        pci_matrix = np.zeros((n_assets, n_assets))
        
        for i, asset1 in enumerate(self.assets):
            for j, asset2 in enumerate(self.assets):
                if i == j:
                    pci_matrix[i, j] = 1.0
                else:
                    # Calculate directional spillover
                    # Using variance decomposition from VAR
                    # Simplified: use correlation of squared returns
                    ret1_sq = returns[asset1].rolling(window).var()
                    ret2_sq = returns[asset2].rolling(window).var()
                    
                    # Correlation of volatilities as proxy for connectedness
                    valid_mask = ret1_sq.notna() & ret2_sq.notna()
                    if valid_mask.sum() > 10:
                        pci = ret1_sq[valid_mask].corr(ret2_sq[valid_mask])
                        pci_matrix[i, j] = abs(pci) if not np.isnan(pci) else 0
        
        return pd.DataFrame(pci_matrix, index=self.assets, columns=self.assets)
    
    def minimum_connectedness_portfolio(self, returns: pd.DataFrame,
                                       constraints: Optional[Dict] = None) -> np.ndarray:
        """
        Minimum Connectedness Portfolio (MCoP)
        
        Minimizes systemic connectedness and spillover effects
        
        Parameters:
        -----------
        returns : pd.DataFrame
            Asset returns
        constraints : dict, optional
            Additional constraints
            
        Returns:
        --------
        np.ndarray
            Optimal weights
        """
        if constraints is None:
            constraints = {'long_only': True, 'sum_to_one': True}
        
        # Calculate PCI matrix
        pci_matrix = self.pairwise_connectedness_index(returns).values
        
        def objective(w):
            # Minimize weighted connectedness
            connectedness = 0
            for i in range(self.n_assets):
                for j in range(self.n_assets):
                    if i != j:
                        connectedness += w[i] * w[j] * pci_matrix[i, j]
            return connectedness
        
        w0 = np.ones(self.n_assets) / self.n_assets
        
        cons = []
        if constraints.get('sum_to_one', True):
            cons.append({'type': 'eq', 'fun': lambda w: np.sum(w) - 1})
        
        bounds = []
        if constraints.get('long_only', True):
            bounds = [(0, 1) for _ in range(self.n_assets)]
        else:
            bounds = [(-1, 1) for _ in range(self.n_assets)]
        
        result = minimize(objective, w0, method='SLSQP',
                         bounds=bounds, constraints=cons)
        
        return result.x
    
    def compute_hedging_effectiveness(self, portfolio_returns: pd.Series,
                                    unhedged_returns: pd.Series) -> float:
        """
        Calculate Hedging Effectiveness (HE)
        
        HE = (Var_unhedged - Var_hedged) / Var_unhedged * 100
        
        Parameters:
        -----------
        portfolio_returns : pd.Series
            Hedged portfolio returns
        unhedged_returns : pd.Series
            Unhedged asset returns
            
        Returns:
        --------
        float
            Hedging effectiveness percentage
        """
        var_hedged = portfolio_returns.var()
        var_unhedged = unhedged_returns.var()
        
        if var_unhedged == 0:
            return 0.0
        
        he = (var_unhedged - var_hedged) / var_unhedged * 100
        return he
    
    def optimize_all_strategies(self, returns: pd.DataFrame,
                               H_t: Optional[pd.DataFrame] = None,
                               R_t: Optional[pd.DataFrame] = None,
                               constraints: Optional[Dict] = None) -> Dict[str, pd.DataFrame]:
        """
        Optimize all portfolio strategies
        
        Parameters:
        -----------
        returns : pd.DataFrame
            Asset returns
        H_t : pd.DataFrame, optional
            Time-varying covariance matrices
        R_t : pd.DataFrame, optional
            Time-varying correlation matrices
        constraints : dict, optional
            Optimization constraints
            
        Returns:
        --------
        dict
            Dictionary with weights for each strategy
        """
        if H_t is None or R_t is None:
            dcc = DCCModel()
            H_t, R_t = dcc.estimate_dcc(returns)
        
        results = {
            'MVP': [],
            'MCP': [],
            'MCoP': []
        }
        
        n_periods = len(returns)
        n_assets = len(self.assets)
        
        for t in range(n_periods):
            # Extract covariance and correlation matrices
            H_flat = H_t.iloc[t].values
            R_flat = R_t.iloc[t].values
            
            H_matrix = H_flat.reshape(n_assets, n_assets)
            R_matrix = R_flat.reshape(n_assets, n_assets)
            
            # MVP
            w_mvp = self.minimum_variance_portfolio(H_matrix, constraints)
            results['MVP'].append(w_mvp)
            
            # MCP
            w_mcp = self.minimum_correlation_portfolio(R_matrix, constraints)
            results['MCP'].append(w_mcp)
            
            # MCoP (uses full returns history up to time t)
            returns_window = returns.iloc[:t+1] if t > 0 else returns.iloc[:1]
            w_mcop = self.minimum_connectedness_portfolio(returns_window, constraints)
            results['MCoP'].append(w_mcop)
        
        # Convert to DataFrames
        for strategy in results:
            results[strategy] = pd.DataFrame(
                results[strategy],
                index=returns.index,
                columns=self.assets
            )
        
        return results

