"""
Script đơn giản để chạy phân tích tự động
"""

import sys
import os
from pathlib import Path

# Add repo root to path for script imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.run_event_study import main as event_study_main

def main():
    """Chạy phân tích Event Study (không còn QQR/portfolio)."""

    data_path = 'data/data_optimized.csv'
    output_dir = 'results'

    print("=" * 60)
    print("BAT DAU PHAN TICH EVENT STUDY")
    print("=" * 60)
    print(f"File du lieu: {data_path}")
    print(f"Thu muc ket qua: {output_dir}")
    print("=" * 60)

    # Tạo thư mục results nếu chưa có
    Path(output_dir).mkdir(exist_ok=True)

    try:
        # Run Event Study workflow
        results = event_study_main()

        print("\n" + "=" * 60)
        print("PHAN TICH EVENT STUDY HOAN TAT!")
        print("=" * 60)
        print(f"\nKet qua da duoc luu trong thu muc: {output_dir}/")

        return results

    except Exception as e:
        print(f"\nLOI: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    main()

