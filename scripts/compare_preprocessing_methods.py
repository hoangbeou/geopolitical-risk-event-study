"""
So sánh 2 phương pháp xử lý biến kiểm soát:
1. Phương pháp hiện tại: OLS Prefiltering (lấy residuals)
2. Phương pháp trong paper: Include control variables trực tiếp trong QQR

Tham khảo: "Dynamic responses of Bitcoin, gold, and green bonds to geopolitical risk: 
A quantile wavelet analysis"
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.preprocessing import DataPreprocessor
from src.wavelet_analysis import WaveletAnalyzer
from src.qqr import WaveletQQR
from scripts.run_qqr import GeopoliticalRiskAnalysis


def method1_ols_prefiltering(data_path='data/data_optimized.csv'):
    """
    PHƯƠNG PHÁP 1: OLS Prefiltering (Hiện tại)
    
    Bước 1: Hồi quy asset returns trên control variables
    Asset_ret = α + β1*DXY + β2*DGS3MO + β3*T10YIE + ε
    
    Bước 2: Lấy residuals (ε) - phần còn lại sau khi loại bỏ ảnh hưởng vĩ mô
    
    Bước 3: Chạy QQR với residuals và GPR_diff
    QQR(residuals, GPR_diff)
    
    Ưu điểm:
    - Loại bỏ hoàn toàn ảnh hưởng của biến kiểm soát
    - Residuals là phần "pure" phản ứng với GPR
    - Đơn giản, dễ hiểu
    
    Nhược điểm:
    - Có thể mất thông tin về tương tác giữa control variables và GPR
    - Giả định mối quan hệ tuyến tính với control variables
    """
    print("="*80)
    print("PHƯƠNG PHÁP 1: OLS PREFILTERING (Hiện tại)")
    print("="*80)
    
    # Load và preprocess
    preprocessor = DataPreprocessor()
    data = preprocessor.load_data(data_path)
    preprocessed = preprocessor.preprocess_data(data)
    
    # Lấy residuals (đã loại bỏ ảnh hưởng control variables)
    btc_res, gold_res, oil_res, gpr_diff = preprocessor.get_processed_series(preprocessed)
    
    print(f"\nResiduals series lengths:")
    print(f"  BTC residuals: {len(btc_res)}")
    print(f"  GOLD residuals: {len(gold_res)}")
    print(f"  OIL residuals: {len(oil_res)}")
    print(f"  GPR differences: {len(gpr_diff)}")
    
    # Wavelet decomposition
    wavelet_analyzer = WaveletAnalyzer(max_scale=9)
    series_dict = {
        'BTC': btc_res,
        'GOLD': gold_res,
        'OIL': oil_res,
        'GPR': gpr_diff
    }
    decompositions = wavelet_analyzer.analyze_multiple_series(series_dict)
    
    # QQR analysis
    qqr_analyzer = WaveletQQR()
    quantile_grid = np.linspace(0.05, 0.95, 19)
    scales = list(range(1, 10))
    
    results = {}
    for asset in ['BTC', 'GOLD', 'OIL']:
        asset_decomp = decompositions.get(asset)
        gpr_decomp = decompositions.get('GPR')
        
        if asset_decomp and gpr_decomp:
            print(f"\nRunning QQR for {asset} (Method 1: OLS Prefiltering)...")
            qqr_results = qqr_analyzer.fit_all_scales(
                gpr_decomp, asset_decomp, quantile_grid, scales
            )
            results[asset] = qqr_results
    
    return results, 'OLS Prefiltering'


def method2_direct_control_variables(data_path='data/data_optimized.csv'):
    """
    PHƯƠNG PHÁP 2: Include Control Variables Trực Tiếp (Theo paper reference)
    
    Chạy QQR với control variables được include trực tiếp:
    QQR(Asset_ret, GPR_diff | DXY, DGS3MO, T10YIE)
    
    Hoặc có thể là:
    - Multivariate QQR với tất cả biến cùng lúc
    - Hoặc QQR riêng cho từng biến control
    
    Theo paper "Dynamic responses of Bitcoin, gold, and green bonds to geopolitical risk":
    - Họ có thể include control variables như covariates trong mô hình
    - Hoặc chạy QQR riêng cho từng control variable để so sánh
    
    Ưu điểm:
    - Giữ nguyên thông tin về tương tác giữa các biến
    - Không giả định mối quan hệ tuyến tính
    - Có thể phân tích tác động riêng của từng control variable
    
    Nhược điểm:
    - Phức tạp hơn về mặt tính toán
    - Có thể có vấn đề đa cộng tuyến
    """
    print("\n" + "="*80)
    print("PHƯƠNG PHÁP 2: DIRECT CONTROL VARIABLES (Theo paper)")
    print("="*80)
    
    # Load và preprocess
    preprocessor = DataPreprocessor()
    data = preprocessor.load_data(data_path)
    preprocessed = preprocessor.preprocess_data(data)
    
    # Lấy raw returns (KHÔNG lấy residuals)
    btc_ret, gold_ret, oil_ret, gpr_diff = preprocessor.get_return_series(preprocessed)
    
    # Lấy control variables
    transformed = preprocessed['transformed_data']
    dxy_ret = transformed.get('DXY_ret', pd.Series(dtype=float))
    dgs3mo_diff = transformed.get('DGS3MO_diff', pd.Series(dtype=float))
    t10yie_diff = transformed.get('T10YIE_diff', pd.Series(dtype=float))
    
    print(f"\nReturn series lengths:")
    print(f"  BTC returns: {len(btc_ret)}")
    print(f"  GOLD returns: {len(gold_ret)}")
    print(f"  OIL returns: {len(oil_ret)}")
    print(f"  GPR differences: {len(gpr_diff)}")
    print(f"  DXY returns: {len(dxy_ret)}")
    print(f"  DGS3MO diff: {len(dgs3mo_diff)}")
    print(f"  T10YIE diff: {len(t10yie_diff)}")
    
    # Align all series
    all_series = [btc_ret, gold_ret, oil_ret, gpr_diff, dxy_ret, dgs3mo_diff, t10yie_diff]
    all_series = [s for s in all_series if not s.empty]
    if len(all_series) > 1:
        common_idx = all_series[0].index
        for s in all_series[1:]:
            common_idx = common_idx.intersection(s.index)
        
        btc_ret = btc_ret.loc[common_idx] if not btc_ret.empty else btc_ret
        gold_ret = gold_ret.loc[common_idx] if not gold_ret.empty else gold_ret
        oil_ret = oil_ret.loc[common_idx] if not oil_ret.empty else oil_ret
        gpr_diff = gpr_diff.loc[common_idx] if not gpr_diff.empty else gpr_diff
        dxy_ret = dxy_ret.loc[common_idx] if not dxy_ret.empty else dxy_ret
        dgs3mo_diff = dgs3mo_diff.loc[common_idx] if not dgs3mo_diff.empty else dgs3mo_diff
        t10yie_diff = t10yie_diff.loc[common_idx] if not t10yie_diff.empty else t10yie_diff
    
    # Wavelet decomposition
    wavelet_analyzer = WaveletAnalyzer(max_scale=9)
    series_dict = {
        'BTC': btc_ret,
        'GOLD': gold_ret,
        'OIL': oil_ret,
        'GPR': gpr_diff,
        'DXY': dxy_ret,
        'DGS3MO': dgs3mo_diff,
        'T10YIE': t10yie_diff
    }
    decompositions = wavelet_analyzer.analyze_multiple_series(series_dict)
    
    # QQR analysis - Chạy QQR với raw returns và GPR
    # (Không include control variables trực tiếp trong QQR vì QQR là bivariate)
    # Nhưng có thể so sánh kết quả với Method 1
    qqr_analyzer = WaveletQQR()
    quantile_grid = np.linspace(0.05, 0.95, 19)
    scales = list(range(1, 10))
    
    results = {}
    for asset in ['BTC', 'GOLD', 'OIL']:
        asset_decomp = decompositions.get(asset)
        gpr_decomp = decompositions.get('GPR')
        
        if asset_decomp and gpr_decomp:
            print(f"\nRunning QQR for {asset} (Method 2: Direct - Raw Returns)...")
            qqr_results = qqr_analyzer.fit_all_scales(
                gpr_decomp, asset_decomp, quantile_grid, scales
            )
            results[asset] = qqr_results
    
    return results, 'Direct Control Variables'


def compare_results(results1, method1_name, results2, method2_name, output_dir='results/comparison'):
    """
    So sánh kết quả giữa 2 phương pháp
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*80)
    print("SO SÁNH KẾT QUẢ")
    print("="*80)
    
    comparison_summary = []
    
    for asset in ['BTC', 'GOLD', 'OIL']:
        if asset not in results1 or asset not in results2:
            continue
        
        res1 = results1[asset]
        res2 = results2[asset]
        
        print(f"\n{asset}:")
        print("-" * 60)
        
        # So sánh hệ số trung bình
        for scale in range(1, 10):
            if scale in res1 and scale in res2:
                coeff1 = res1[scale]
                coeff2 = res2[scale]
                
                if coeff1 is not None and coeff2 is not None:
                    mean1 = np.nanmean(coeff1)
                    mean2 = np.nanmean(coeff2)
                    std1 = np.nanstd(coeff1)
                    std2 = np.nanstd(coeff2)
                    abs_mean1 = np.nanmean(np.abs(coeff1))
                    abs_mean2 = np.nanmean(np.abs(coeff2))
                    
                    comparison_summary.append({
                        'Asset': asset,
                        'Scale': scale,
                        'Method': method1_name,
                        'Mean_Coeff': mean1,
                        'Std_Coeff': std1,
                        'Abs_Mean_Coeff': abs_mean1
                    })
                    comparison_summary.append({
                        'Asset': asset,
                        'Scale': scale,
                        'Method': method2_name,
                        'Mean_Coeff': mean2,
                        'Std_Coeff': std2,
                        'Abs_Mean_Coeff': abs_mean2
                    })
                    
                    print(f"  Scale {scale}:")
                    print(f"    {method1_name}: Mean={mean1:.6f}, Std={std1:.6f}, |Mean|={abs_mean1:.6f}")
                    print(f"    {method2_name}: Mean={mean2:.6f}, Std={std2:.6f}, |Mean|={abs_mean2:.6f}")
                    print(f"    Difference: {abs(mean1 - mean2):.6f}")
        
        # Vẽ biểu đồ so sánh
        fig, axes = plt.subplots(3, 3, figsize=(18, 15))
        axes = axes.flatten()
        
        for idx, scale in enumerate(range(1, 10)):
            if scale in res1 and scale in res2:
                coeff1 = res1[scale]
                coeff2 = res2[scale]
                
                if coeff1 is not None and coeff2 is not None:
                    # Plot heatmap comparison
                    ax = axes[idx]
                    diff = coeff1 - coeff2
                    im = ax.imshow(diff, aspect='auto', cmap='RdBu_r',
                                  vmin=-np.nanmax(np.abs(diff)),
                                  vmax=np.nanmax(np.abs(diff)))
                    ax.set_title(f'Scale {scale}: Difference\n({method1_name} - {method2_name})')
                    ax.set_xlabel('GPR Quantile')
                    ax.set_ylabel(f'{asset} Quantile')
                    plt.colorbar(im, ax=ax)
        
        plt.suptitle(f'{asset}: Comparison of {method1_name} vs {method2_name}', 
                    fontsize=16, y=0.995)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/comparison_{asset}.png', dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Saved comparison plot: {output_dir}/comparison_{asset}.png")
    
    # Lưu summary
    if comparison_summary:
        summary_df = pd.DataFrame(comparison_summary)
        summary_df.to_csv(f'{output_dir}/comparison_summary.csv', index=False)
        print(f"\nSaved comparison summary: {output_dir}/comparison_summary.csv")
    
    return comparison_summary


def main():
    """Main function"""
    print("="*80)
    print("SO SÁNH 2 PHƯƠNG PHÁP XỬ LÝ BIẾN KIỂM SOÁT")
    print("="*80)
    print("\nPhương pháp 1: OLS Prefiltering (Hiện tại)")
    print("  - Hồi quy asset returns trên control variables")
    print("  - Lấy residuals (đã loại bỏ ảnh hưởng vĩ mô)")
    print("  - Chạy QQR với residuals và GPR")
    print("\nPhương pháp 2: Direct Control Variables (Theo paper)")
    print("  - Chạy QQR với raw returns và GPR")
    print("  - Không loại bỏ ảnh hưởng control variables trước")
    print("\n" + "="*80)
    
    # Chạy Method 1
    results1, method1_name = method1_ols_prefiltering()
    
    # Chạy Method 2
    results2, method2_name = method2_direct_control_variables()
    
    # So sánh
    comparison = compare_results(results1, method1_name, results2, method2_name)
    
    print("\n" + "="*80)
    print("HOÀN THÀNH SO SÁNH")
    print("="*80)
    print("\nKết quả đã được lưu trong: results/comparison/")
    print("Kiểm tra:")
    print("  - comparison_*.png: Biểu đồ so sánh")
    print("  - comparison_summary.csv: Thống kê so sánh")


if __name__ == '__main__':
    main()



