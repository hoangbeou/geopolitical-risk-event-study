"""
Script để phân tích ý nghĩa của GPR với 3 tài sản (BTC, GOLD, OIL)
Kiểm tra mối quan hệ có ý nghĩa thống kê không
"""

import numpy as np
import pandas as pd
import sys
import io
from scipy import stats
from main import GeopoliticalRiskAnalysis

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def analyze_gpr_significance():
    """Phan tich y nghia cua GPR voi 3 tai san"""
    
    print("=" * 80)
    print("PHAN TICH Y NGHIA CUA GPR VOI 3 TAI SAN (BTC, GOLD, OIL)")
    print("=" * 80)
    
    # Khoi tao va chay phan tich
    print("\nDang tai du lieu va chay phan tich...\n")
    analysis = GeopoliticalRiskAnalysis('data/data.csv', max_scale=9)
    
    # Chay den buoc QQR
    btc_res, gold_res, oil_res, gpr_diff = analysis.load_and_preprocess()
    analysis.perform_wavelet_decomposition(btc_res, gold_res, oil_res, gpr_diff)
    analysis.perform_qqr_analysis()
    
    assets = ['BTC', 'GOLD', 'OIL']
    
    print("\n" + "=" * 80)
    print("1. PHAN TICH TONG QUAN CAC HE SO QQR")
    print("=" * 80)
    
    results_summary = {}
    
    for asset in assets:
        if asset not in analysis.qqr_results:
            continue
        
        qqr_results = analysis.qqr_results[asset]
        scales = sorted([s for s in qqr_results.keys() if qqr_results[s] is not None])
        
        # Thu thap tat ca he so
        all_coeffs = []
        for scale in scales:
            coeff_matrix = qqr_results[scale]
            valid_coeffs = coeff_matrix[~np.isnan(coeff_matrix)]
            all_coeffs.extend(valid_coeffs)
        
        if len(all_coeffs) > 0:
            all_coeffs = np.array(all_coeffs)
            mean_coeff = np.mean(all_coeffs)
            std_coeff = np.std(all_coeffs)
            median_coeff = np.median(all_coeffs)
            min_coeff = np.min(all_coeffs)
            max_coeff = np.max(all_coeffs)
            
            # Tinh ty le he so duong
            positive_ratio = np.sum(all_coeffs > 0) / len(all_coeffs)
            
            # Tinh ty le he so co y nghia (|coeff| > 0.001)
            significant_ratio = np.sum(np.abs(all_coeffs) > 0.001) / len(all_coeffs)
            
            # Test thong ke: kiem tra xem mean co khac 0 khong
            t_stat, p_value = stats.ttest_1samp(all_coeffs, 0)
            
            results_summary[asset] = {
                'mean': mean_coeff,
                'std': std_coeff,
                'median': median_coeff,
                'min': min_coeff,
                'max': max_coeff,
                'positive_ratio': positive_ratio,
                'significant_ratio': significant_ratio,
                't_stat': t_stat,
                'p_value': p_value,
                'n': len(all_coeffs)
            }
            
            print(f"\n{asset}:")
            print(f"  So quan sat: {len(all_coeffs):,}")
            print(f"  Mean coefficient: {mean_coeff:.6f}")
            print(f"  Median coefficient: {median_coeff:.6f}")
            print(f"  Std deviation: {std_coeff:.6f}")
            print(f"  Min coefficient: {min_coeff:.6f}")
            print(f"  Max coefficient: {max_coeff:.6f}")
            print(f"  He so duong: {positive_ratio*100:.1f}%")
            print(f"  He so co y nghia (|coeff| > 0.001): {significant_ratio*100:.1f}%")
            print(f"  T-test: t = {t_stat:.4f}, p-value = {p_value:.6f}")
            
            # Danh gia y nghia
            if p_value < 0.01:
                significance = "RAT Y NGHIA (p < 0.01)"
            elif p_value < 0.05:
                significance = "Y NGHIA (p < 0.05)"
            elif p_value < 0.10:
                significance = "Y NGHIA YEUM (p < 0.10)"
            else:
                significance = "KHONG Y NGHIA (p >= 0.10)"
            
            print(f"  → Ket luan: {significance}")
            
            if abs(mean_coeff) < 0.0001:
                strength = "RAT YEU"
            elif abs(mean_coeff) < 0.001:
                strength = "YEU"
            elif abs(mean_coeff) < 0.01:
                strength = "TRUNG BINH"
            else:
                strength = "MANH"
            
            direction = "DUONG" if mean_coeff > 0 else "AM"
            print(f"  → Cuong do: {strength} ({direction})")
    
    # 2. So sanh giua 3 tai san
    print("\n" + "=" * 80)
    print("2. SO SANH GIUA 3 TAI SAN")
    print("=" * 80)
    
    if len(results_summary) >= 2:
        assets_list = list(results_summary.keys())
        
        print("\n2.1. So sanh Mean Coefficient:")
        sorted_assets = sorted(assets_list, key=lambda x: abs(results_summary[x]['mean']), reverse=True)
        for asset in sorted_assets:
            mean = results_summary[asset]['mean']
            print(f"  {asset}: {mean:.6f} {'(duong)' if mean > 0 else '(am)'}")
        
        print("\n2.2. So sanh P-value (y nghia thong ke):")
        sorted_assets = sorted(assets_list, key=lambda x: results_summary[x]['p_value'])
        for asset in sorted_assets:
            p_val = results_summary[asset]['p_value']
            if p_val < 0.01:
                sig = "***"
            elif p_val < 0.05:
                sig = "**"
            elif p_val < 0.10:
                sig = "*"
            else:
                sig = ""
            print(f"  {asset}: p = {p_val:.6f} {sig}")
        
        print("\n2.3. So sanh Ty le He so Co y nghia:")
        sorted_assets = sorted(assets_list, key=lambda x: results_summary[x]['significant_ratio'], reverse=True)
        for asset in sorted_assets:
            ratio = results_summary[asset]['significant_ratio']
            print(f"  {asset}: {ratio*100:.1f}%")
    
    # 3. Phan tich theo Scale
    print("\n" + "=" * 80)
    print("3. PHAN TICH THEO SCALE (Xem Scale nao co y nghia nhat)")
    print("=" * 80)
    
    for asset in assets:
        if asset not in analysis.qqr_results:
            continue
        
        qqr_results = analysis.qqr_results[asset]
        scales = sorted([s for s in qqr_results.keys() if qqr_results[s] is not None])
        
        print(f"\n{asset}:")
        scale_means = {}
        
        for scale in scales:
            coeff_matrix = qqr_results[scale]
            valid_coeffs = coeff_matrix[~np.isnan(coeff_matrix)]
            
            if len(valid_coeffs) > 0:
                mean_coeff = np.mean(valid_coeffs)
                abs_mean = np.abs(mean_coeff)
                scale_means[scale] = abs_mean
                
                # Test thong ke
                t_stat, p_value = stats.ttest_1samp(valid_coeffs, 0)
                
                sig = ""
                if p_value < 0.01:
                    sig = "***"
                elif p_value < 0.05:
                    sig = "**"
                elif p_value < 0.10:
                    sig = "*"
                
                period = f"{2**scale}-{2**(scale+1)} days"
                print(f"  Scale {scale} ({period:15s}): mean = {mean_coeff:8.6f}, p = {p_value:.6f} {sig}")
        
        # Tim scale co y nghia nhat
        if scale_means:
            best_scale = max(scale_means.keys(), key=lambda x: scale_means[x])
            print(f"  → Scale co cuong do cao nhat: Scale {best_scale} (mean abs = {scale_means[best_scale]:.6f})")
    
    # 4. Ket luan tong the
    print("\n" + "=" * 80)
    print("4. KET LUAN TONG THE")
    print("=" * 80)
    
    print("\n4.1. GPR co y nghia voi 3 tai san khong?")
    
    significant_assets = []
    weak_assets = []
    no_significance_assets = []
    
    for asset in assets:
        if asset in results_summary:
            p_val = results_summary[asset]['p_value']
            mean = results_summary[asset]['mean']
            abs_mean = abs(mean)
            
            if p_val < 0.05 and abs_mean > 0.0001:
                significant_assets.append(asset)
            elif p_val < 0.10 or abs_mean > 0.0001:
                weak_assets.append(asset)
            else:
                no_significance_assets.append(asset)
    
    if significant_assets:
        print(f"  ✓ CO Y NGHIA: {', '.join(significant_assets)}")
        print(f"    → GPR co anh huong ro rang den cac tai san nay")
    
    if weak_assets:
        print(f"  ? Y NGHIA YEUM: {', '.join(weak_assets)}")
        print(f"    → GPR co anh huong nho den cac tai san nay")
    
    if no_significance_assets:
        print(f"  ✗ KHONG Y NGHIA: {', '.join(no_significance_assets)}")
        print(f"    → GPR khong co anh huong ro rang den cac tai san nay")
    
    print("\n4.2. Tai san nao phan ung manh nhat voi GPR?")
    if results_summary:
        sorted_by_abs_mean = sorted(results_summary.keys(), 
                                   key=lambda x: abs(results_summary[x]['mean']), 
                                   reverse=True)
        for i, asset in enumerate(sorted_by_abs_mean[:3], 1):
            mean = results_summary[asset]['mean']
            abs_mean = abs(mean)
            print(f"  {i}. {asset}: |mean| = {abs_mean:.6f} ({'duong' if mean > 0 else 'am'})")
    
    print("\n4.3. Khung thoi gian nao quan trong nhat?")
    # Tim scale co y nghia nhat cho moi tai san
    for asset in assets:
        if asset not in analysis.qqr_results:
            continue
        
        qqr_results = analysis.qqr_results[asset]
        scales = sorted([s for s in qqr_results.keys() if qqr_results[s] is not None])
        
        scale_abs_means = {}
        for scale in scales:
            coeff_matrix = qqr_results[scale]
            valid_coeffs = coeff_matrix[~np.isnan(coeff_matrix)]
            if len(valid_coeffs) > 0:
                scale_abs_means[scale] = abs(np.mean(valid_coeffs))
        
        if scale_abs_means:
            best_scale = max(scale_abs_means.keys(), key=lambda x: scale_abs_means[x])
            period = f"{2**best_scale}-{2**(best_scale+1)} days"
            print(f"  {asset}: Scale {best_scale} ({period})")
    
    # 5. Danh gia tong the
    print("\n" + "=" * 80)
    print("5. DANH GIA TONG THE")
    print("=" * 80)
    
    total_significant = len(significant_assets)
    total_weak = len(weak_assets)
    total_no_sig = len(no_significance_assets)
    
    print(f"\nSo tai san co y nghia: {total_significant}/3")
    print(f"So tai san co y nghia yeum: {total_weak}/3")
    print(f"So tai san khong y nghia: {total_no_sig}/3")
    
    if total_significant >= 2:
        print("\n✓ KET LUAN: GPR CO Y NGHIA voi da so tai san")
        print("  → GPR la bien quan trong de phan tich cac tai san nay")
    elif total_significant == 1:
        print("\n? KET LUAN: GPR co y nghia voi mot tai san")
        print("  → GPR co anh huong khong dong deu")
    elif total_weak >= 2:
        print("\n? KET LUAN: GPR co y nghia YEUM voi nhieu tai san")
        print("  → GPR co anh huong nho, can xem xet them")
    else:
        print("\n✗ KET LUAN: GPR KHONG CO Y NGHIA ro rang")
        print("  → GPR khong phai la bien quan trong trong phan tich nay")
        print("  → Co the do:")
        print("    - Moi quan he rat yeu")
        print("    - Can them bien khac")
        print("    - Can phuong phap khac")
    
    print("\n" + "=" * 80)
    print("Luu y:")
    print("- Cac he so QQR rat nho co the la binh thuong neu mo hinh da loai bo nhieu")
    print("- Y nghia thuc te quan trong hon y nghia thong ke")
    print("- Can xem xet them cac bien khac va mo hinh khac")
    print("=" * 80)


if __name__ == '__main__':
    analyze_gpr_significance()

