"""
Data preprocessing module for geopolitical risk analysis

This module handles:
1. Log returns transformation for BTC, GOLD, OIL, DXY
2. First differences for GPR, DGS3MO, T10YIE
3. OLS prefiltering to remove macroeconomic noise
"""

import numpy as np
import pandas as pd
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

from .utils import log_returns, first_differences, align_dataframes


class DataPreprocessor:
    """
    Class for preprocessing financial and macroeconomic data
    """
    
    def __init__(self):
        self.control_vars = ['DXY', 'DGS3MO', 'T10YIE']
        self.asset_vars = ['BTC', 'GOLD', 'OIL']
        # Try to find GPR column (could be 'GPR' or 'GPR_TOTAL')
        self.gpr_var = None
        
    def load_data(self, file_path: str) -> pd.DataFrame:
        """
        Load data from CSV file
        
        Parameters:
        -----------
        file_path : str
            Path to CSV file
            
        Returns:
        --------
        pd.DataFrame
            Loaded data with datetime index
        """
        df = pd.read_csv(file_path, index_col=0, parse_dates=True, dayfirst=True)
        # Ensure index is DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, dayfirst=True, format='mixed')
        # Keep only weekdays (Mon-Fri)
        df = df[df.index.weekday < 5]
        # Filter date range: 2015-01-01 to 2025-11-11
        start_date = pd.Timestamp('2015-01-01')
        end_date = pd.Timestamp('2025-11-11')
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        return df.sort_index()
    
    def transform_returns(self, prices: pd.Series) -> pd.Series:
        """
        Transform prices to log returns
        
        Parameters:
        -----------
        prices : pd.Series
            Price series
            
        Returns:
        --------
        pd.Series
            Log returns
        """
        return log_returns(prices)
    
    def transform_levels(self, series: pd.Series) -> pd.Series:
        """
        Transform levels to first differences
        
        Parameters:
        -----------
        series : pd.Series
            Level series
            
        Returns:
        --------
        pd.Series
            First differences
        """
        return first_differences(series)
    
    def preprocess_data(self, data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Main preprocessing function
        
        Parameters:
        -----------
        data : pd.DataFrame
            Raw data with columns: BTC, GOLD, OIL, GPR, DXY, DGS3MO, T10YIE
            
        Returns:
        --------
        dict
            Dictionary containing:
            - 'returns': Log returns for assets and DXY
            - 'differenced': First differences for GPR, DGS3MO, T10YIE
            - 'residuals': OLS residuals for assets after controlling for macro variables
            - 'transformed_data': Complete transformed dataset
        """
        # Step 1: Transform asset prices to log returns
        returns_data = pd.DataFrame(index=data.index)
        
        for asset in self.asset_vars:
            if asset in data.columns:
                returns_data[f'{asset}_ret'] = self.transform_returns(data[asset])
        
        # DXY also uses log returns
        if 'DXY' in data.columns:
            returns_data['DXY_ret'] = self.transform_returns(data['DXY'])
        
        # Step 2: Transform GPR and control variables to first differences
        differenced_data = pd.DataFrame(index=data.index)
        
        # Find GPR column (could be 'GPRD', 'GPR', or 'GPR_TOTAL')
        gpr_col = None
        if 'GPRD' in data.columns:
            gpr_col = 'GPRD'
        elif 'GPR' in data.columns:
            gpr_col = 'GPR'
        elif 'GPR_TOTAL' in data.columns:
            gpr_col = 'GPR_TOTAL'
        
        if gpr_col is not None:
            differenced_data['GPR_diff'] = self.transform_levels(data[gpr_col])
        
        for var in ['DGS3MO', 'T10YIE']:
            if var in data.columns:
                differenced_data[f'{var}_diff'] = self.transform_levels(data[var])
        
        # Step 3: Align all series
        all_series = [returns_data, differenced_data]
        returns_data, differenced_data = align_dataframes(returns_data, differenced_data)
        
        # Step 4: Combine transformed data
        transformed_data = pd.concat([returns_data, differenced_data], axis=1).dropna()
        
        # Step 5: OLS Prefiltering - Regress asset returns on control variables
        residuals_data = pd.DataFrame(index=transformed_data.index)
        
        control_vars = ['DXY_ret', 'DGS3MO_diff', 'T10YIE_diff']
        available_controls = [var for var in control_vars if var in transformed_data.columns]
        
        if len(available_controls) > 0:
            X_controls = transformed_data[available_controls].values
            X_controls = add_constant(X_controls)
            
            for asset in self.asset_vars:
                asset_ret_col = f'{asset}_ret'
                if asset_ret_col in transformed_data.columns:
                    y = transformed_data[asset_ret_col].values
                    
                    # Remove NaN values
                    valid_mask = ~(np.isnan(y) | np.any(np.isnan(X_controls), axis=1))
                    y_clean = y[valid_mask]
                    X_clean = X_controls[valid_mask]
                    
                    if len(y_clean) > 0 and len(X_clean) > 0:
                        try:
                            # OLS regression
                            model = OLS(y_clean, X_clean).fit()
                            residuals = y_clean - model.fittedvalues
                            
                            # Create residuals series with proper index
                            residuals_series = pd.Series(
                                residuals, 
                                index=transformed_data.index[valid_mask]
                            )
                            residuals_data[f'{asset}_res'] = residuals_series
                        except Exception as e:
                            print(f"Warning: Could not compute residuals for {asset}: {e}")
                            residuals_data[f'{asset}_res'] = transformed_data[asset_ret_col]
        
        # Align residuals with transformed data
        if not residuals_data.empty:
            common_idx = transformed_data.index.intersection(residuals_data.index)
            residuals_data = residuals_data.loc[common_idx]
            transformed_data = transformed_data.loc[common_idx]
        
        return {
            'returns': returns_data,
            'differenced': differenced_data,
            'residuals': residuals_data,
            'transformed_data': transformed_data,
            'prefiltering_info': {
                'control_variables': available_controls,
                'assets_filtered': [col.replace('_res', '') for col in residuals_data.columns]
            }
        }
    
    def get_processed_series(self, preprocessed: Dict) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        Extract key series for analysis
        
        Parameters:
        -----------
        preprocessed : dict
            Output from preprocess_data()
            
        Returns:
        --------
        tuple
            (BTC_res, GOLD_res, OIL_res, GPR_diff)
        """
        residuals = preprocessed['residuals']
        differenced = preprocessed['differenced']
        
        btc_res = residuals.get('BTC_res', pd.Series(dtype=float))
        gold_res = residuals.get('GOLD_res', pd.Series(dtype=float))
        oil_res = residuals.get('OIL_res', pd.Series(dtype=float))
        gpr_diff = differenced.get('GPR_diff', pd.Series(dtype=float))
        
        # Align all series
        all_series = [s for s in [btc_res, gold_res, oil_res, gpr_diff] if not s.empty]
        if len(all_series) > 1:
            common_idx = all_series[0].index
            for s in all_series[1:]:
                common_idx = common_idx.intersection(s.index)
            
            btc_res = btc_res.loc[common_idx] if not btc_res.empty else btc_res
            gold_res = gold_res.loc[common_idx] if not gold_res.empty else gold_res
            oil_res = oil_res.loc[common_idx] if not oil_res.empty else oil_res
            gpr_diff = gpr_diff.loc[common_idx] if not gpr_diff.empty else gpr_diff
        
        return btc_res, gold_res, oil_res, gpr_diff

    def get_return_series(self, preprocessed: Dict) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        """
        Extract raw return series (before OLS prefiltering)

        Parameters:
        -----------
        preprocessed : dict
            Output from preprocess_data()

        Returns:
        --------
        tuple
            (BTC_ret, GOLD_ret, OIL_ret, GPR_diff)
        """
        returns = preprocessed['returns']
        differenced = preprocessed['differenced']

        btc_ret = returns.get('BTC_ret', pd.Series(dtype=float))
        gold_ret = returns.get('GOLD_ret', pd.Series(dtype=float))
        oil_ret = returns.get('OIL_ret', pd.Series(dtype=float))
        gpr_diff = differenced.get('GPR_diff', pd.Series(dtype=float))

        # Align all series
        all_series = [s for s in [btc_ret, gold_ret, oil_ret, gpr_diff] if not s.empty]
        if len(all_series) > 1:
            common_idx = all_series[0].index
            for s in all_series[1:]:
                common_idx = common_idx.intersection(s.index)

            btc_ret = btc_ret.loc[common_idx] if not btc_ret.empty else btc_ret
            gold_ret = gold_ret.loc[common_idx] if not gold_ret.empty else gold_ret
            oil_ret = oil_ret.loc[common_idx] if not oil_ret.empty else oil_ret
            gpr_diff = gpr_diff.loc[common_idx] if not gpr_diff.empty else gpr_diff

        return btc_ret, gold_ret, oil_ret, gpr_diff

