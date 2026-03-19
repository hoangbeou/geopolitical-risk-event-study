"""Chỉ chạy phần tạo country-level heatmap để cập nhật bản đồ"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.create_advanced_visualizations import AdvancedVisualizations

if __name__ == '__main__':
    print("="*70)
    print("CẬP NHẬT COUNTRY-LEVEL HEATMAP")
    print("="*70)
    
    visualizer = AdvancedVisualizations()
    visualizer.create_country_level_heatmap()
    
    print("\n" + "="*70)
    print("✓ HOÀN THÀNH")
    print("="*70)
    print(f"\nFile đã được lưu tại: {visualizer.output_dir / 'country_level_heatmap.html'}")


