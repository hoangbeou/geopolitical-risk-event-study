"""
Chạy riêng phần phân tích các giai đoạn phản ứng giá
"""

import sys
import io
from pathlib import Path

# Fix encoding
if hasattr(sys.stdout, 'buffer') and not hasattr(sys.stdout, '_encoding_set'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stdout._encoding_set = True
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.preprocessing import DataPreprocessor
from scripts.run_event_study import EventStudy

def main():
    print("=" * 80)
    print("PHAN TICH CAC GIAI DOAN PHAN UNG GIA")
    print("=" * 80)
    
    # Load data
    preprocessor = DataPreprocessor()
    data_path = Path('data/raw/data.csv')
    data = preprocessor.load_data(str(data_path))
    
    # Initialize Event Study
    event_study = EventStudy(data, assets=['BTC', 'GOLD', 'OIL'])
    
    # Analyze all events (quick, no plotting)
    print("\nDang phan tich cac su kien...")
    results = event_study.analyze_all_events(use_auto_detection=True)
    
    # Analyze reaction phases
    print("\nDang phan tich cac giai doan phan ung gia...")
    phase_results = event_study.analyze_reaction_phases(results, output_dir='results')
    
    print("\n" + "=" * 80)
    print("HOAN THANH PHAN TICH CAC GIAI DOAN PHAN UNG GIA")
    print("=" * 80)

if __name__ == '__main__':
    main()

