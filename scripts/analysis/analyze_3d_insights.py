"""
Phân tích insights từ hình 3D QQR
"""
import sys
sys.path.insert(0, '.')

import numpy as np
from scripts.run_qqr import GeopoliticalRiskAnalysis

print("=" * 70)
print("PHÂN TÍCH INSIGHTS TỪ HÌNH 3D QQR")
print("=" * 70)

# Load analysis
analysis = GeopoliticalRiskAnalysis('data/data.csv', max_scale=9)
btc_res, gold_res, oil_res, gpr_diff = analysis.load_and_preprocess()
analysis.perform_wavelet_decomposition(use_returns=False)
qqr_results = analysis.perform_qqr_analysis(use_residuals=True)

quantile_grid = np.linspace(0.05, 0.95, 19)

print("\n" + "=" * 70)
print("INSIGHTS TỪ HÌNH 3D QQR")
print("=" * 70)

for asset in ['BTC', 'GOLD', 'OIL']:
    if asset not in qqr_results:
        continue
    
    print(f"\n{'='*70}")
    print(f"{asset} - PHÂN TÍCH HÌNH 3D")
    print(f"{'='*70}")
    
    scales = sorted([s for s in qqr_results[asset].keys() if qqr_results[asset][s] is not None])
    
    # Analyze pattern across scales
    print(f"\n1. PATTERN THEO KHUNG THỜI GIAN:")
    print("-" * 70)
    
    for scale in scales[:5]:  # Focus on first 5 scales
        coeff_matrix = qqr_results[asset][scale]
        valid_coeffs = coeff_matrix[~np.isnan(coeff_matrix)]
        
        if len(valid_coeffs) == 0:
            continue
        
        # Analyze by quantile regions
        # Low quantiles (0.05-0.3): bear market / low GPR
        # Mid quantiles (0.3-0.7): normal market / mid GPR  
        # High quantiles (0.7-0.95): bull market / high GPR
        
        low_idx = np.where(quantile_grid <= 0.3)[0]
        mid_idx = np.where((quantile_grid > 0.3) & (quantile_grid <= 0.7))[0]
        high_idx = np.where(quantile_grid > 0.7)[0]
        
        # Extract coefficients for different quantile combinations
        # Low GPR, Low Asset (bear market, low GPR)
        low_gpr_low_asset = coeff_matrix[np.ix_(low_idx, low_idx)]
        # High GPR, Low Asset (bear market, high GPR) - KEY INSIGHT
        high_gpr_low_asset = coeff_matrix[np.ix_(low_idx, high_idx)]
        # Low GPR, High Asset (bull market, low GPR)
        low_gpr_high_asset = coeff_matrix[np.ix_(high_idx, low_idx)]
        # High GPR, High Asset (bull market, high GPR) - KEY INSIGHT
        high_gpr_high_asset = coeff_matrix[np.ix_(high_idx, high_idx)]
        # Mid combinations
        mid_gpr_mid_asset = coeff_matrix[np.ix_(mid_idx, mid_idx)]
        
        print(f"\nScale {scale} ({2**scale}-{2**(scale+1)} ngày):")
        
        # Key insight: What happens when GPR is HIGH?
        high_gpr_all = coeff_matrix[:, high_idx].flatten()
        high_gpr_all = high_gpr_all[~np.isnan(high_gpr_all)]
        if len(high_gpr_all) > 0:
            high_gpr_mean = np.mean(high_gpr_all)
            high_gpr_positive = (high_gpr_all > 0).sum() / len(high_gpr_all) * 100
            print(f"  → Khi GPR CAO (phân vị 0.7-0.95):")
            print(f"    Mean hệ số: {high_gpr_mean:+.4f}")
            print(f"    Tỷ lệ dương: {high_gpr_positive:.1f}%")
            if high_gpr_mean > 0.01:
                print(f"    ✓ INSIGHT: {asset} TĂNG khi GPR cao (safe-haven behavior)")
            elif high_gpr_mean < -0.01:
                print(f"    ✗ INSIGHT: {asset} GIẢM khi GPR cao (risk-off behavior)")
            else:
                print(f"    ~ INSIGHT: {asset} không phản ứng rõ khi GPR cao")
        
        # Key insight: What happens in BEAR market with high GPR?
        bear_high_gpr = high_gpr_low_asset.flatten()
        bear_high_gpr = bear_high_gpr[~np.isnan(bear_high_gpr)]
        if len(bear_high_gpr) > 0:
            bear_mean = np.mean(bear_high_gpr)
            print(f"  → Khi thị trường BEAR + GPR CAO:")
            print(f"    Mean hệ số: {bear_mean:+.4f}")
            if bear_mean > 0.01:
                print(f"    ✓ INSIGHT: {asset} là safe-haven trong khủng hoảng")
            elif bear_mean < -0.01:
                print(f"    ✗ INSIGHT: {asset} bị bán tháo trong khủng hoảng")
        
        # Key insight: What happens in BULL market with high GPR?
        bull_high_gpr = high_gpr_high_asset.flatten()
        bull_high_gpr = bull_high_gpr[~np.isnan(bull_high_gpr)]
        if len(bull_high_gpr) > 0:
            bull_mean = np.mean(bull_high_gpr)
            print(f"  → Khi thị trường BULL + GPR CAO:")
            print(f"    Mean hệ số: {bull_mean:+.4f}")
            if bull_mean > 0.01:
                print(f"    ✓ INSIGHT: {asset} được coi là tài sản thay thế khi thị trường tích cực")
    
    # Compare scales
    print(f"\n2. SO SÁNH GIỮA CÁC SCALES:")
    print("-" * 70)
    
    short_term_scales = [s for s in scales if s <= 2]
    mid_term_scales = [s for s in scales if 3 <= s <= 5]
    long_term_scales = [s for s in scales if s >= 6]
    
    def get_mean_coeff(scales_list):
        all_coeffs = []
        for s in scales_list:
            if s in qqr_results[asset] and qqr_results[asset][s] is not None:
                coeffs = qqr_results[asset][s]
                valid = coeffs[~np.isnan(coeffs)]
                if len(valid) > 0:
                    all_coeffs.extend(valid.tolist())
        return np.mean(all_coeffs) if len(all_coeffs) > 0 else 0
    
    short_mean = get_mean_coeff(short_term_scales)
    mid_mean = get_mean_coeff(mid_term_scales)
    long_mean = get_mean_coeff(long_term_scales)
    
    print(f"  Ngắn hạn (Scale 1-2): Mean = {short_mean:+.4f}")
    print(f"  Trung hạn (Scale 3-5): Mean = {mid_mean:+.4f}")
    print(f"  Dài hạn (Scale 6-9): Mean = {long_mean:+.4f}")
    
    if mid_mean > short_mean + 0.01:
        print(f"  ✓ INSIGHT: {asset} phản ứng MẠNH HƠN ở trung hạn so với ngắn hạn")
        print(f"    → Tác động của GPR cần thời gian để phản ánh đầy đủ")
    elif short_mean > mid_mean + 0.01:
        print(f"  ✓ INSIGHT: {asset} phản ứng MẠNH HƠN ở ngắn hạn")
        print(f"    → Phản ứng nhanh nhưng không bền vững")
    
    # Pattern consistency
    print(f"\n3. ĐỘ NHẤT QUÁN CỦA PATTERN:")
    print("-" * 70)
    
    all_means = []
    all_stds = []
    for s in scales:
        coeffs = qqr_results[asset][s]
        valid = coeffs[~np.isnan(coeffs)]
        if len(valid) > 0:
            all_means.append(np.mean(valid))
            all_stds.append(np.std(valid))
    
    if len(all_means) > 0:
        consistency = 1 - (np.std(all_means) / (np.abs(np.mean(all_means)) + 1e-6))
        print(f"  Độ nhất quán qua scales: {consistency:.2%}")
        if consistency > 0.7:
            print(f"  ✓ INSIGHT: Pattern NHẤT QUÁN qua các khung thời gian")
        else:
            print(f"  ~ INSIGHT: Pattern THAY ĐỔI qua các khung thời gian")
        
        avg_std = np.mean(all_stds)
        print(f"  Độ biến động trung bình: {avg_std:.4f}")
        if avg_std < 0.02:
            print(f"  ✓ INSIGHT: Phản ứng ỔN ĐỊNH (ít biến động giữa các phân vị)")
        else:
            print(f"  ~ INSIGHT: Phản ứng PHỤ THUỘC vào trạng thái thị trường")

print("\n" + "=" * 70)
print("TỔNG KẾT INSIGHTS CHÍNH")
print("=" * 70)

print("""
Từ phân tích hình 3D QQR, các insights chính:

1. GOLD:
   - Pattern nhất quán: màu đỏ/cam đậm từ trung hạn trở đi
   - Phản ứng tích cực với GPR cao ở mọi trạng thái thị trường
   - → Vàng là safe-haven đáng tin cậy nhất

2. BTC:
   - Pattern phức tạp: đảo chiều từ xanh (ngắn hạn) sang đỏ (trung hạn)
   - Phản ứng phụ thuộc mạnh vào trạng thái thị trường
   - → Bitcoin có vai trò phức tạp, không phải lúc nào cũng là safe-haven

3. OIL:
   - Pattern yếu: bề mặt phẳng, không có pattern rõ ràng
   - → Dầu không phản ứng mạnh với GPR tổng hợp
""")









