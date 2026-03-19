"""
Example usage of the Geopolitical Risk Analysis framework

This script demonstrates how to use the analysis tools step by step.
"""

import numpy as np
import pandas as pd
from src.preprocessing import DataPreprocessor
from src.wavelet_analysis import WaveletAnalyzer
from src.qqr import WaveletQQR
from src.dependence import DependenceAnalyzer
from src.portfolio import PortfolioOptimizer, DCCModel


def example_preprocessing():
    """Example: Data preprocessing"""
    print("Example 1: Data Preprocessing")
    print("-" * 40)
    
    # Initialize preprocessor
    preprocessor = DataPreprocessor()
    
    # Load data (replace with your data path)
    # data = preprocessor.load_data('data/your_data.csv')
    
    # For demonstration, create sample data
    dates = pd.date_range('2015-01-01', '2025-11-11', freq='B')  # Business days
    n = len(dates)
    
    # Generate synthetic data
    np.random.seed(42)
    data = pd.DataFrame({
        'BTC': 300 + np.cumsum(np.random.randn(n) * 10),
        'GOLD': 1200 + np.cumsum(np.random.randn(n) * 5),
        'OIL': 50 + np.cumsum(np.random.randn(n) * 2),
        'GPR': 100 + np.cumsum(np.random.randn(n) * 2),
        'DXY': 90 + np.cumsum(np.random.randn(n) * 0.3),
        'DGS3MO': 0.05 + np.random.randn(n) * 0.01,
        'T10YIE': 2.0 + np.random.randn(n) * 0.1
    }, index=dates)
    
    # Preprocess
    preprocessed = preprocessor.preprocess_data(data)
    
    # Extract series
    btc_res, gold_res, oil_res, gpr_diff = \
        preprocessor.get_processed_series(preprocessed)
    
    print(f"BTC residuals: {len(btc_res)} observations")
    print(f"GOLD residuals: {len(gold_res)} observations")
    print(f"OIL residuals: {len(oil_res)} observations")
    print(f"GPR differences: {len(gpr_diff)} observations")
    
    return btc_res, gold_res, oil_res, gpr_diff


def example_wavelet_analysis(btc_res, gpr_diff):
    """Example: Wavelet decomposition"""
    print("\nExample 2: Wavelet Analysis")
    print("-" * 40)
    
    # Initialize analyzer
    analyzer = WaveletAnalyzer(wavelet='db4', max_scale=9)
    
    # Decompose series
    series_dict = {
        'BTC': btc_res,
        'GPR': gpr_diff
    }
    
    decompositions = analyzer.analyze_multiple_series(series_dict)
    
    btc_decomp = decompositions['BTC']
    gpr_decomp = decompositions['GPR']
    
    print(f"BTC decomposition: {len(btc_decomp['scales'])} scales")
    print(f"Scale periods (days): {btc_decomp['scale_periods']}")
    
    # Calculate cross-scale correlation
    for scale in [1, 3, 5, 7, 9]:
        corr = analyzer.get_cross_scale_correlation(
            btc_decomp, gpr_decomp, scale
        )
        print(f"  Scale {scale} correlation: {corr:.4f}")
    
    return btc_decomp, gpr_decomp


def example_qqr(btc_decomp, gpr_decomp):
    """Example: Wavelet QQR"""
    print("\nExample 3: Wavelet Quantile-on-Quantile Regression")
    print("-" * 40)
    
    # Initialize QQR
    qqr = WaveletQQR()
    
    # Define quantile grid
    quantile_grid = np.linspace(0.05, 0.95, 19)
    
    # Fit QQR at a specific scale
    scale = 5
    coeff_matrix = qqr.fit_wavelet_scale(
        gpr_decomp, btc_decomp, scale, quantile_grid
    )
    
    print(f"QQR coefficient matrix at scale {scale}:")
    print(f"  Shape: {coeff_matrix.shape}")
    print(f"  Mean coefficient: {np.nanmean(coeff_matrix):.4f}")
    print(f"  Min coefficient: {np.nanmin(coeff_matrix):.4f}")
    print(f"  Max coefficient: {np.nanmax(coeff_matrix):.4f}")
    
    return coeff_matrix


def example_dependence_measures(btc_decomp, gpr_decomp):
    """Example: Dependence measures"""
    print("\nExample 4: Dependence Measures")
    print("-" * 40)
    
    # Initialize analyzer
    analyzer = DependenceAnalyzer(max_lag=20, alpha=0.05)
    
    # Compute all measures
    scales = [1, 3, 5, 7, 9]
    results = analyzer.analyze_all_measures(
        btc_decomp, gpr_decomp, scales, tau_x=0.05, tau_y=0.05
    )
    
    print("CES values across scales:")
    for scale in scales:
        ces = results['ces'].get(scale, np.nan)
        if not np.isnan(ces):
            print(f"  Scale {scale}: {ces:.4f}")
    
    print("\nWCQ at lag 0:")
    for scale in scales:
        wcq = results['wcq'].get(scale, pd.Series())
        if isinstance(wcq, pd.Series) and len(wcq) > 0:
            wcq_lag0 = wcq.get(0, np.nan)
            if not np.isnan(wcq_lag0):
                print(f"  Scale {scale}: {wcq_lag0:.4f}")
    
    return results


def example_portfolio_optimization(btc_res, gold_res, oil_res):
    """Example: Portfolio optimization"""
    print("\nExample 5: Portfolio Optimization")
    print("-" * 40)
    
    # Prepare returns
    returns_df = pd.DataFrame({
        'BTC': btc_res,
        'GOLD': gold_res,
        'OIL': oil_res
    }).dropna()
    
    if len(returns_df) < 60:
        print("Insufficient data for portfolio optimization")
        return None
    
    # Initialize optimizer
    assets = ['BTC', 'GOLD', 'OIL']
    optimizer = PortfolioOptimizer(assets)
    
    # Estimate DCC
    print("Estimating DCC model...")
    dcc = DCCModel()
    H_t, R_t = dcc.estimate_dcc(returns_df)
    
    # Optimize portfolios
    print("Computing optimal weights...")
    portfolio_weights = optimizer.optimize_all_strategies(
        returns_df, H_t, R_t,
        constraints={'long_only': True, 'sum_to_one': True}
    )
    
    # Display average weights
    print("\nAverage portfolio weights:")
    for strategy, weights in portfolio_weights.items():
        avg_weights = weights.mean()
        print(f"\n{strategy}:")
        for asset, weight in avg_weights.items():
            print(f"  {asset}: {weight:.4f}")
    
    # Calculate portfolio returns
    portfolio_returns = {}
    for strategy, weights in portfolio_weights.items():
        portfolio_returns[strategy] = (returns_df * weights).sum(axis=1)
    
    # Hedging effectiveness
    print("\nHedging Effectiveness:")
    unhedged_ret = returns_df.mean(axis=1)
    for strategy, port_ret in portfolio_returns.items():
        he = optimizer.compute_hedging_effectiveness(port_ret, unhedged_ret)
        print(f"  {strategy}: {he:.2f}%")
    
    return portfolio_weights, portfolio_returns


def main():
    """Run all examples"""
    print("=" * 60)
    print("GEOPOLITICAL RISK ANALYSIS - EXAMPLE USAGE")
    print("=" * 60)
    
    # Example 1: Preprocessing
    btc_res, gold_res, oil_res, gpr_diff = example_preprocessing()
    
    # Example 2: Wavelet analysis
    btc_decomp, gpr_decomp = example_wavelet_analysis(btc_res, gpr_diff)
    
    # Example 3: QQR
    qqr_matrix = example_qqr(btc_decomp, gpr_decomp)
    
    # Example 4: Dependence measures
    dep_results = example_dependence_measures(btc_decomp, gpr_decomp)
    
    # Example 5: Portfolio optimization
    port_results = example_portfolio_optimization(btc_res, gold_res, oil_res)
    
    print("\n" + "=" * 60)
    print("EXAMPLES COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main()

