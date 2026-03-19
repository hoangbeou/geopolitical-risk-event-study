"""
Script để kiểm tra các vấn đề tiềm ẩn của phương pháp
1. Tương quan GPR với các biến kiểm soát
2. So sánh QQR trên returns vs residuals
3. Phân tích sub-period (crisis vs normal)
"""

import numpy as np
import pandas as pd
import sys
import io
from scipy.stats import pearsonr
from main import GeopoliticalRiskAnalysis
from src.qqr import WaveletQQR

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_correlation_issues():
    """Kiem tra tuong quan GPR voi cac bien kiem soat"""
    
    print("=" * 80)
    print("KIEM TRA 1: TUONG QUAN GPR VOI CAC BIEN KIEM SOAT")
    print("=" * 80)
    print("\nNeu tuong quan cao -> OLS filtering loai bo mot phan anh huong cua GPR!\n")
    
    # Load data
    analysis = GeopoliticalRiskAnalysis('data/data.csv', max_scale=9)
    data = analysis.preprocessor.load_data('data/data.csv')
    
    # Get GPR
    gpr_col = None
    if 'GPR' in data.columns:
        gpr_col = 'GPR'
    elif 'GPR_TOTAL' in data.columns:
        gpr_col = 'GPR_TOTAL'
    
    if gpr_col is None:
        print("Loi: Khong tim thay cot GPR")
        return
    
    # Transform GPR to first differences
    gpr_diff = data[gpr_col].diff().dropna()
    
    # Get control variables
    controls = {}
    if 'DXY' in data.columns:
        controls['DXY'] = np.log(data['DXY'] / data['DXY'].shift(1)).dropna()
    if 'DGS3MO' in data.columns:
        controls['DGS3MO'] = data['DGS3MO'].diff().dropna()
    if 'T10YIE' in data.columns:
        controls['T10YIE'] = data['T10YIE'].diff().dropna()
    
    # Align series
    common_idx = gpr_diff.index
    for name, series in controls.items():
        common_idx = common_idx.intersection(series.index)
    
    gpr_aligned = gpr_diff.loc[common_idx]
    controls_aligned = {name: series.loc[common_idx] for name, series in controls.items()}
    
    print(f"Number of observations: {len(gpr_aligned)}")
    print(f"Date range: {gpr_aligned.index.min()} to {gpr_aligned.index.max()}\n")
    
    # Calculate correlations
    correlations = {}
    for name, series in controls_aligned.items():
        # Remove NaN
        valid_mask = ~(np.isnan(gpr_aligned) | np.isnan(series))
        gpr_clean = gpr_aligned[valid_mask]
        series_clean = series[valid_mask]
        
        if len(gpr_clean) > 10:
            corr, p_val = pearsonr(gpr_clean, series_clean)
            correlations[name] = {'corr': corr, 'p_value': p_val}
            
            print(f"{name}:")
            print(f"  Correlation: {corr:.4f}")
            print(f"  P-value: {p_val:.6f}")
            
            if abs(corr) > 0.3:
                print(f"  -> TUONG QUAN CAO! OLS filtering co the loai bo mot phan anh huong cua GPR")
            elif abs(corr) > 0.1:
                print(f"  -> Tuong quan trung binh")
            else:
                print(f"  -> Tuong quan thap, OLS filtering OK")
            print()
    
    # Conclusion
    print("=" * 80)
    print("KET LUAN:")
    high_corr = [name for name, result in correlations.items() if abs(result['corr']) > 0.3]
    if high_corr:
        print(f"✗ CO VAN DE: {', '.join(high_corr)} co tuong quan cao voi GPR")
        print("  -> OLS filtering loai bo mot phan anh huong cua GPR!")
        print("  -> Ket qua QQR tren residuals yeu hon thuc te")
    else:
        print("✓ KHONG CO VAN DE: Tuong quan thap, OLS filtering OK")
    print("=" * 80)
    
    return correlations


def compare_returns_vs_residuals():
    """So sanh QQR tren returns vs residuals"""
    
    print("\n" + "=" * 80)
    print("KIEM TRA 2: SO SANH QQR TREN RETURNS VS RESIDUALS")
    print("=" * 80)
    print("\nNeu he so returns >> residuals -> Phuong phap co van de!\n")
    
    # Load and preprocess
    analysis = GeopoliticalRiskAnalysis('data/data.csv', max_scale=9)
    data = analysis.preprocessor.load_data('data/data.csv')
    
    # Get GPR
    gpr_col = None
    if 'GPR' in data.columns:
        gpr_col = 'GPR'
    elif 'GPR_TOTAL' in data.columns:
        gpr_col = 'GPR_TOTAL'
    
    if gpr_col is None:
        print("Loi: Khong tim thay cot GPR")
        return
    
    # Preprocess
    preprocessed = analysis.preprocessor.preprocess_data(data)
    
    # Get GPR differences
    gpr_diff = preprocessed['differenced'].get('GPR_diff', pd.Series())
    
    # Get asset returns (original) and residuals
    assets = ['BTC', 'GOLD', 'OIL']
    
    results_comparison = {}
    
    for asset in assets:
        # Original returns
        ret_col = f'{asset}_ret'
        asset_returns = preprocessed['returns'].get(ret_col, pd.Series())
        
        # Residuals (after OLS filtering)
        res_col = f'{asset}_res'
        asset_residuals = preprocessed['residuals'].get(res_col, pd.Series())
        
        # Align series
        common_idx = gpr_diff.index.intersection(asset_returns.index)
        if len(common_idx) == 0:
            continue
        
        common_idx_res = gpr_diff.index.intersection(asset_residuals.index)
        if len(common_idx_res) == 0:
            continue
        
        gpr_aligned = gpr_diff.loc[common_idx].dropna()
        returns_aligned = asset_returns.loc[common_idx].dropna()
        
        gpr_aligned_res = gpr_diff.loc[common_idx_res].dropna()
        residuals_aligned = asset_residuals.loc[common_idx_res].dropna()
        
        # Final alignment
        final_idx = gpr_aligned.index.intersection(returns_aligned.index)
        final_idx_res = gpr_aligned_res.index.intersection(residuals_aligned.index)
        
        if len(final_idx) < 100 or len(final_idx_res) < 100:
            continue
        
        gpr_final = gpr_aligned.loc[final_idx].values
        returns_final = returns_aligned.loc[final_idx].values
        
        gpr_final_res = gpr_aligned_res.loc[final_idx_res].values
        residuals_final = residuals_aligned.loc[final_idx_res].values
        
        # Calculate simple correlation (as proxy for QQR coefficient)
        # This is a simplified version - real QQR would be more complex
        
        # Remove NaN and infinite
        mask = np.isfinite(gpr_final) & np.isfinite(returns_final)
        gpr_clean = gpr_final[mask]
        returns_clean = returns_final[mask]
        
        mask_res = np.isfinite(gpr_final_res) & np.isfinite(residuals_final)
        gpr_clean_res = gpr_final_res[mask_res]
        residuals_clean = residuals_final[mask_res]
        
        if len(gpr_clean) > 100 and len(gpr_clean_res) > 100:
            # Calculate correlation
            corr_returns, _ = pearsonr(gpr_clean, returns_clean)
            corr_residuals, _ = pearsonr(gpr_clean_res, residuals_clean)
            
            # Calculate ratio
            ratio = abs(corr_returns) / abs(corr_residuals) if abs(corr_residuals) > 1e-10 else 0
            
            results_comparison[asset] = {
                'corr_returns': corr_returns,
                'corr_residuals': corr_residuals,
                'ratio': ratio
            }
            
            print(f"{asset}:")
            print(f"  Correlation (Returns): {corr_returns:.6f}")
            print(f"  Correlation (Residuals): {corr_residuals:.6f}")
            print(f"  Ratio (Returns/Residuals): {ratio:.2f}x")
            
            if ratio > 1.5:
                print(f"  -> PHUONG PHAP CO VAN DE! He so returns lon hon nhieu so voi residuals")
                print(f"     -> OLS filtering lam mat mot phan anh huong cua GPR")
            elif ratio > 1.1:
                print(f"  -> Co su khac biet nho")
            else:
                print(f"  -> Khong co su khac biet ro rang")
            print()
    
    # Conclusion
    print("=" * 80)
    print("KET LUAN:")
    high_ratio = [asset for asset, result in results_comparison.items() 
                  if result['ratio'] > 1.5]
    if high_ratio:
        print(f"✗ CO VAN DE: {', '.join(high_ratio)} co he so returns >> residuals")
        print("  -> OLS filtering lam mat mot phan anh huong cua GPR!")
        print("  -> Ket qua QQR tren residuals yeu hon thuc te")
    else:
        print("✓ KHONG CO VAN DE RO RANG")
    print("=" * 80)
    
    return results_comparison


def analyze_sub_periods():
    """Phan tich theo sub-period (crisis vs normal)"""
    
    print("\n" + "=" * 80)
    print("KIEM TRA 3: PHAN TICH THEO SUB-PERIOD (CRISIS VS NORMAL)")
    print("=" * 80)
    print("\nNeu he so crisis >> normal -> Moi quan he chi ro trong khung hoang!\n")
    
    # Define crisis periods
    crisis_periods = [
        ('2014-01-01', '2015-12-31', 'Ukraine Crisis'),
        ('2022-01-01', '2022-12-31', 'Russia-Ukraine War')
    ]
    
    normal_periods = [
        ('2016-01-01', '2021-12-31', 'Normal Period 1'),
        ('2023-01-01', '2025-11-11', 'Normal Period 2')
    ]
    
    # Load data
    analysis = GeopoliticalRiskAnalysis('data/data.csv', max_scale=9)
    data = analysis.preprocessor.load_data('data/data.csv')
    
    # Get GPR
    gpr_col = None
    if 'GPR' in data.columns:
        gpr_col = 'GPR'
    elif 'GPR_TOTAL' in data.columns:
        gpr_col = 'GPR_TOTAL'
    
    if gpr_col is None:
        print("Loi: Khong tim thay cot GPR")
        return
    
    # Preprocess
    preprocessed = analysis.preprocessor.preprocess_data(data)
    
    # Get series
    gpr_diff = preprocessed['differenced'].get('GPR_diff', pd.Series())
    assets = ['BTC', 'GOLD', 'OIL']
    
    results_by_period = {}
    
    for asset in assets:
        res_col = f'{asset}_res'
        asset_residuals = preprocessed['residuals'].get(res_col, pd.Series())
        
        if asset_residuals.empty:
            continue
        
        # Align
        common_idx = gpr_diff.index.intersection(asset_residuals.index)
        if len(common_idx) < 100:
            continue
        
        gpr_aligned = gpr_diff.loc[common_idx].dropna()
        residuals_aligned = asset_residuals.loc[common_idx].dropna()
        
        final_idx = gpr_aligned.index.intersection(residuals_aligned.index)
        
        gpr_final = gpr_aligned.loc[final_idx]
        residuals_final = residuals_aligned.loc[final_idx]
        
        asset_results = {}
        
        # Crisis periods
        crisis_corrs = []
        for start, end, label in crisis_periods:
            mask = (gpr_final.index >= start) & (gpr_final.index <= end)
            gpr_period = gpr_final[mask]
            residuals_period = residuals_final[mask]
            
            if len(gpr_period) > 50:
                mask_valid = np.isfinite(gpr_period.values) & np.isfinite(residuals_period.values)
                if mask_valid.sum() > 50:
                    corr, _ = pearsonr(gpr_period.values[mask_valid], 
                                     residuals_period.values[mask_valid])
                    crisis_corrs.append(abs(corr))
                    asset_results[label] = abs(corr)
        
        # Normal periods
        normal_corrs = []
        for start, end, label in normal_periods:
            mask = (gpr_final.index >= start) & (gpr_final.index <= end)
            gpr_period = gpr_final[mask]
            residuals_period = residuals_final[mask]
            
            if len(gpr_period) > 50:
                mask_valid = np.isfinite(gpr_period.values) & np.isfinite(residuals_period.values)
                if mask_valid.sum() > 50:
                    corr, _ = pearsonr(gpr_period.values[mask_valid], 
                                     residuals_period.values[mask_valid])
                    normal_corrs.append(abs(corr))
                    asset_results[label] = abs(corr)
        
        if crisis_corrs and normal_corrs:
            avg_crisis = np.mean(crisis_corrs)
            avg_normal = np.mean(normal_corrs)
            ratio = avg_crisis / avg_normal if avg_normal > 1e-10 else 0
            
            results_by_period[asset] = {
                'avg_crisis': avg_crisis,
                'avg_normal': avg_normal,
                'ratio': ratio
            }
            
            print(f"{asset}:")
            print(f"  Average correlation (Crisis): {avg_crisis:.6f}")
            print(f"  Average correlation (Normal): {avg_normal:.6f}")
            print(f"  Ratio (Crisis/Normal): {ratio:.2f}x")
            
            if ratio > 1.5:
                print(f"  -> Moi quan he ro rang hon trong khung hoang!")
                print(f"     -> GPR chi anh huong manh khi co su kien lon")
            elif ratio > 1.1:
                print(f"  -> Co su khac biet nho")
            else:
                print(f"  -> Khong co su khac biet ro rang")
            print()
    
    # Conclusion
    print("=" * 80)
    print("KET LUAN:")
    high_ratio = [asset for asset, result in results_by_period.items() 
                  if result['ratio'] > 1.5]
    if high_ratio:
        print(f"✓ PHAT HIEN: {', '.join(high_ratio)} co moi quan he ro rang hon trong khung hoang")
        print("  -> GPR chi anh huong manh khi co su kien lon")
        print("  -> Trong dieu kien binh thuong, moi quan he yeu")
    else:
        print("? Khong co su khac biet ro rang giua crisis va normal periods")
    print("=" * 80)
    
    return results_by_period


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("KIEM TRA CAC VAN DE TIEM AN CUA PHUONG PHAP")
    print("=" * 80)
    print("\nGiai thich tai sao ket qua yeu:")
    print("1. OLS filtering loai bo mot phan anh huong cua GPR?")
    print("2. QQR tren residuals yeu hon returns?")
    print("3. Moi quan he chi ro trong khung hoang?")
    print("\n" + "=" * 80 + "\n")
    
    # Check 1: Correlation
    correlations = check_correlation_issues()
    
    # Check 2: Returns vs Residuals
    comparison = compare_returns_vs_residuals()
    
    # Check 3: Sub-periods
    subperiods = analyze_sub_periods()
    
    # Final summary
    print("\n" + "=" * 80)
    print("TOM TAT KET QUA KIEM TRA")
    print("=" * 80)
    
    print("\n1. Tuong quan GPR voi cac bien kiem soat:")
    if correlations:
        for name, result in correlations.items():
            status = "CAO" if abs(result['corr']) > 0.3 else "THAP"
            print(f"   {name}: {result['corr']:.4f} ({status})")
    
    print("\n2. So sanh Returns vs Residuals:")
    if comparison:
        for asset, result in comparison.items():
            status = "CO VAN DE" if result['ratio'] > 1.5 else "OK"
            print(f"   {asset}: Ratio = {result['ratio']:.2f}x ({status})")
    
    print("\n3. Phan tich Sub-periods:")
    if subperiods:
        for asset, result in subperiods.items():
            status = "RO RANG HON TRONG CRISIS" if result['ratio'] > 1.5 else "KHONG KHAC BIET"
            print(f"   {asset}: Ratio = {result['ratio']:.2f}x ({status})")
    
    print("\n" + "=" * 80)
    print("KHUYEN NGHI:")
    print("=" * 80)
    print("\nNeu co van de:")
    print("1. Bo OLS pre-filtering hoac bao gom GPR trong OLS")
    print("2. Phan tich QQR tren returns goc thay vi residuals")
    print("3. Phan tich rieng cho crisis periods")
    print("4. So sanh voi phuong phap khac")
    print("\n" + "=" * 80)

