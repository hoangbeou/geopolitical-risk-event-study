"""
Cập nhật main.py để tự động tạo bảng kết quả
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import GeopoliticalRiskAnalysis
from generate_results_tables import generate_all_tables

def run_analysis_with_tables():
    """Chạy phân tích và tự động tạo bảng kết quả"""
    
    data_path = 'data/data.csv'
    output_dir = 'results'
    max_scale = 9
    
    print("=" * 60)
    print("CHẠY PHÂN TÍCH VÀ TẠO BẢNG KẾT QUẢ")
    print("=" * 60)
    
    # Run analysis
    analysis = GeopoliticalRiskAnalysis(data_path, max_scale=max_scale)
    results = analysis.run_full_analysis()
    
    # Generate tables
    print("\n" + "=" * 60)
    print("TẠO CÁC BẢNG KẾT QUẢ")
    print("=" * 60)
    generate_all_tables(results)
    
    return results

if __name__ == '__main__':
    results = run_analysis_with_tables()
    print("\n✓ Hoàn tất! Tất cả kết quả và bảng đã được lưu trong thư mục results/")

