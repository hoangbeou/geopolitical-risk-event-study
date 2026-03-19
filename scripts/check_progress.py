"""
Script để kiểm tra tiến độ chạy pipeline
"""

import os
from pathlib import Path
from datetime import datetime
import time

def check_progress():
    """Kiểm tra tiến độ và in ra báo cáo"""
    results_dir = Path('results')
    
    print("=" * 80)
    print(f"KIỂM TRA TIẾN ĐỘ PIPELINE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # Đếm files
    if results_dir.exists():
        all_files = list(results_dir.rglob('*'))
        files = [f for f in all_files if f.is_file()]
        dirs = [d for d in all_files if d.is_dir()]
        
        print(f"📁 Thư mục results: {len(dirs)} thư mục, {len(files)} files")
        print()
    else:
        print("⚠️  Thư mục results chưa tồn tại")
        return
    
    # Kiểm tra từng bước
    steps = {
        'Event Study': {
            'files': ['Event_Study_Event_1.png', 'Event_Study_Average_CAR.png', 'event_study_summary.txt'],
            'dir': 'event_study'
        },
        'QQR Analysis': {
            'files': ['QQR_BTC.png', 'QQR_3D_BTC.png', 'analysis_summary.txt'],
            'dir': None
        },
        'Portfolio Optimization': {
            'files': ['Portfolio_Weights.png'],
            'dir': None
        },
        'ACT/THREAT Analysis': {
            'files': ['boxplot_act_vs_threat.png', 'summary_report.txt'],
            'dir': 'event_study/act_threat_analysis'
        },
        'Advanced Visualizations': {
            'files': ['candlestick_BTC_top5.png', 'boxplot_car_by_type.png'],
            'dir': 'event_study/advanced_visualizations'
        },
        'Regional Analysis': {
            'files': ['regional_car_comparison.png', 'regional_act_threat_heatmap.png'],
            'dir': 'event_study/advanced_visualizations'
        },
        'Pattern Visualization': {
            'files': ['pattern_comparison.png', 'btc_gold_scatter.png'],
            'dir': 'event_study/pattern_visualizations'
        }
    }
    
    print("📊 TIẾN ĐỘ TỪNG BƯỚC:")
    print("-" * 80)
    
    for step_name, step_info in steps.items():
        found = 0
        total = len(step_info['files'])
        
        base_dir = results_dir
        if step_info['dir']:
            base_dir = results_dir / step_info['dir']
        
        for filename in step_info['files']:
            filepath = base_dir / filename
            if filepath.exists():
                found += 1
                # Get file time
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                age_min = (datetime.now() - mtime).total_seconds() / 60
                status = "✓"
            else:
                status = "✗"
        
        progress = f"{found}/{total}"
        if found == total:
            status_icon = "✅"
        elif found > 0:
            status_icon = "⏳"
        else:
            status_icon = "⏸️"
        
        print(f"{status_icon} {step_name:30s} {progress:>6s} files")
    
    print()
    print("📁 CHI TIẾT FILES:")
    print("-" * 80)
    
    # List files by type
    file_types = {}
    for file in files:
        ext = file.suffix.lower()
        if ext not in file_types:
            file_types[ext] = []
        file_types[ext].append(file)
    
    for ext, file_list in sorted(file_types.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {ext or '(no ext)':10s}: {len(file_list):4d} files")
    
    print()
    print("🕐 FILES MỚI NHẤT:")
    print("-" * 80)
    
    # Get 10 newest files
    files_with_time = [(f, datetime.fromtimestamp(f.stat().st_mtime)) for f in files]
    files_with_time.sort(key=lambda x: x[1], reverse=True)
    
    for filepath, mtime in files_with_time[:10]:
        age = datetime.now() - mtime
        if age.total_seconds() < 60:
            age_str = f"{int(age.total_seconds())}s ago"
        elif age.total_seconds() < 3600:
            age_str = f"{int(age.total_seconds()/60)}m ago"
        else:
            age_str = f"{int(age.total_seconds()/3600)}h ago"
        
        rel_path = filepath.relative_to(results_dir)
        print(f"  {age_str:>8s} - {rel_path}")
    
    print()
    print("=" * 80)

if __name__ == '__main__':
    check_progress()



