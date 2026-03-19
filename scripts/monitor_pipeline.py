"""
Script theo dõi tiến độ pipeline
"""

import time
import subprocess
from pathlib import Path
from datetime import datetime

def check_files():
    """Kiểm tra files đã được tạo"""
    results_dir = Path('results')
    if not results_dir.exists():
        return {}
    
    files = {}
    
    # Event Study files
    event_files = list(results_dir.rglob('*Event_Study*'))
    event_summary = results_dir / 'event_study' / 'event_study_summary.txt'
    event_classification = results_dir / 'event_study' / 'event_classification.csv'
    identified_events = results_dir / 'event_study' / 'identified_events.json'
    
    files['event_study'] = {
        'plots': len(event_files),
        'summary': event_summary.exists(),
        'classification': event_classification.exists(),
        'identified': identified_events.exists()
    }
    
    # Advanced Visualizations
    adv_viz_files = list((results_dir / 'event_study' / 'advanced_visualizations').rglob('*')) if (results_dir / 'event_study' / 'advanced_visualizations').exists() else []
    files['advanced_viz'] = len(adv_viz_files)
    
    # Regional Analysis
    regional_files = list((results_dir / 'event_study' / 'advanced_visualizations').rglob('*regional*')) if (results_dir / 'event_study' / 'advanced_visualizations').exists() else []
    files['regional'] = len(regional_files)
    
    # Pattern Visualization
    pattern_files = list((results_dir / 'event_study' / 'pattern_visualizations').rglob('*')) if (results_dir / 'event_study' / 'pattern_visualizations').exists() else []
    files['pattern'] = len(pattern_files)
    
    return files

def check_processes():
    """Kiểm tra Python processes"""
    try:
        result = subprocess.run(
            ['powershell', '-Command', 
             'Get-Process python -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count'],
            capture_output=True,
            text=True,
            timeout=5
        )
        count = int(result.stdout.strip()) if result.stdout.strip() else 0
        return count
    except:
        return 0

def main():
    """Main monitoring"""
    print("=" * 80)
    print("THEO DÕI TIẾN ĐỘ PIPELINE")
    print("=" * 80)
    print()
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            files = check_files()
            process_count = check_processes()
            
            print(f"\n[{timestamp}] Lần kiểm tra #{iteration}")
            print("-" * 80)
            print(f"🔄 Python processes: {process_count}")
            print()
            
            # Event Study
            print("📊 Event Study Analysis:")
            es = files.get('event_study', {})
            if isinstance(es, dict):
                print(f"   - Plots: {es.get('plots', 0)}")
                print(f"   - Summary: {'✓' if es.get('summary') else '✗'}")
                print(f"   - Classification: {'✓' if es.get('classification') else '✗'}")
                print(f"   - Identified events: {'✓' if es.get('identified') else '✗'}")
            else:
                print(f"   - Files: {es}")
            
            # Advanced Visualizations
            print(f"\n📈 Advanced Visualizations: {files.get('advanced_viz', 0)} files")
            
            # Regional Analysis
            print(f"🌍 Regional Analysis: {files.get('regional', 0)} files")
            
            # Pattern Visualization
            print(f"🔍 Pattern Visualization: {files.get('pattern', 0)} files")
            
            # Check completion
            event_complete = (isinstance(es, dict) and 
                           es.get('summary') and 
                           es.get('classification') and 
                           es.get('identified') and 
                           es.get('plots', 0) > 0)
            
            if event_complete and process_count == 0:
                print("\n✅ Event Study Analysis hoàn thành!")
                print("   Có thể tiếp tục với Advanced Visualizations, Regional Analysis, Pattern Visualization")
            
            print("\n" + "=" * 80)
            print("Chờ 30 giây... (Ctrl+C để dừng)")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\nĐã dừng theo dõi.")

if __name__ == '__main__':
    main()


