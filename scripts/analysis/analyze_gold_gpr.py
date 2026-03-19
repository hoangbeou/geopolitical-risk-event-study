"""
Script de doc va phan tich ket qua QQR 3D cho GOLD vs GPR
Chay script nay sau khi da chay main.py
"""

import numpy as np
import pandas as pd
import sys
import io

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from main import GeopoliticalRiskAnalysis

def analyze_gold_gpr_3d():
    """Phan tich ket qua QQR 3D cho GOLD vs GPR"""
    
    print("=" * 70)
    print("PHAN TICH KET QUA QQR 3D: GOLD vs GPR")
    print("=" * 70)
    print("\nDang tai du lieu va chay phan tich...")
    print("(Neu da co ket qua, co the load truc tiep)\n")
    
    # Khởi tạo và chạy phân tích
    analysis = GeopoliticalRiskAnalysis('data/data.csv', max_scale=9)
    
    # Chỉ chạy đến bước QQR (không cần chạy hết)
    btc_res, gold_res, oil_res, gpr_diff = analysis.load_and_preprocess()
    analysis.perform_wavelet_decomposition(btc_res, gold_res, oil_res, gpr_diff)
    analysis.perform_qqr_analysis()
    
    # Lay ket qua GOLD
    if 'GOLD' not in analysis.qqr_results:
        print("Loi: Khong tim thay ket qua QQR cho GOLD")
        return
    
    gold_qqr = analysis.qqr_results['GOLD']
    
    # Import hàm phân tích
    from read_qqr_results import analyze_qqr_3d_results
    
    # Phan tich
    analyze_qqr_3d_results(gold_qqr, 'GOLD')
    
    # Them phan tich chi tiet
    print("\n" + "=" * 70)
    print("6. HUONG DAN DOC BIEU DO 3D")
    print("=" * 70)
    
    print("""
De doc bieu do 3D QQR_GOLD.png:

1. XAC DINH CAC TRUC:
   - Truc X (ngang): GPR Quantile (tau_1) tu 0.05 den 0.95
   - Truc Y (sau): GOLD Quantile (tau_2) tu 0.05 den 0.95  
   - Truc Z (cao): Coefficient (he so QQR)

2. DOC MAU SAC:
   - DO = He so duong (GPR tang -> GOLD tang)
   - XANH = He so am (GPR tang -> GOLD giam)
   - TRANG/VANG = He so gan 0 (khong co moi quan he)

3. DOC DO CAO:
   - Do cao cua be mat = Gia tri he so
   - Cang cao = Tuong quan cang manh
   - Duong (cao) = Tuong quan duong
   - Am (thap) = Tuong quan am

4. SO SANH CAC SCALE:
   - Scale 1 (2-4 ngay): Phan ung ngan han
   - Scale 5 (32-64 ngay): Phan ung trung han
   - Scale 9 (512-1024 ngay): Phan ung dai han

5. CAC DIEM QUAN TRONG:
   - (0.95, 0.95): GPR cao, GOLD cao -> Safe haven?
   - (0.05, 0.05): GPR thap, GOLD thap -> Moi quan he co ban
   - (0.95, 0.05): GPR cao, GOLD thap -> Phan ung bat thuong?

Xem file HUONG_DAN_DOC_BIEU_DO_3D.md de biet chi tiet hon!
    """)


if __name__ == '__main__':
    analyze_gold_gpr_3d()

