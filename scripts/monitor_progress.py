"""
Script để theo dõi tiến độ pipeline liên tục
"""

import time
import subprocess
from pathlib import Path
from datetime import datetime

def check_files():
    """Đếm số files trong results"""
    results_dir = Path('results')
    if not results_dir.exists():
        return 0, {}
    
    files = list(results_dir.rglob('*'))
    file_list = [f for f in files if f.is_file()]
    
    # Phân loại theo extension
    by_ext = {}
    for f in file_list:
        ext = f.suffix.lower()
        by_ext[ext] = by_ext.get(ext, 0) + 1
    
    return len(file_list), by_ext

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

def get_latest_files(n=5):
    """Lấy n files mới nhất"""
    results_dir = Path('results')
    if not results_dir.exists():
        return []
    
    files = [f for f in results_dir.rglob('*') if f.is_file()]
    files_with_time = [(f, f.stat().st_mtime) for f in files]
    files_with_time.sort(key=lambda x: x[1], reverse=True)
    
    return files_with_time[:n]

def main():
    """Main monitoring loop"""
    print("=" * 80)
    print("THEO DÕI TIẾN ĐỘ PIPELINE - CẬP NHẬT MỖI 30 GIÂY")
    print("=" * 80)
    print("Nhấn Ctrl+C để dừng\n")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # Check files
            file_count, by_ext = check_files()
            
            # Check processes
            process_count = check_processes()
            
            # Get latest files
            latest = get_latest_files(5)
            
            # Print status
            print(f"\n[{timestamp}] Lần kiểm tra #{iteration}")
            print("-" * 80)
            print(f"📁 Tổng số files: {file_count}")
            if by_ext:
                print(f"   Breakdown: {', '.join([f'{ext}: {count}' for ext, count in sorted(by_ext.items(), key=lambda x: x[1], reverse=True)[:5]])}")
            print(f"🔄 Python processes đang chạy: {process_count}")
            
            if latest:
                print(f"\n📄 Files mới nhất:")
                for filepath, mtime in latest:
                    age_sec = time.time() - mtime
                    if age_sec < 60:
                        age_str = f"{int(age_sec)}s"
                    elif age_sec < 3600:
                        age_str = f"{int(age_sec/60)}m"
                    else:
                        age_str = f"{int(age_sec/3600)}h"
                    
                    rel_path = filepath.relative_to(Path('results'))
                    print(f"   [{age_str:>6s} ago] {rel_path}")
            
            # Check completion
            expected_files = {
                'Event Study': ['Event_Study_Event_1.png', 'event_study_summary.txt'],
                'QQR': ['QQR_BTC.png', 'analysis_summary.txt']
            }
            
            print(f"\n✅ Hoàn thành:")
            for step, files in expected_files.items():
                found = 0
                for filename in files:
                    if (Path('results') / filename).exists():
                        found += 1
                if found == len(files):
                    print(f"   ✓ {step}")
                elif found > 0:
                    print(f"   ⏳ {step} ({found}/{len(files)})")
                else:
                    print(f"   ⏸️  {step}")
            
            print("\n" + "=" * 80)
            print("Chờ 30 giây... (Ctrl+C để dừng)")
            
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\nĐã dừng theo dõi.")

if __name__ == '__main__':
    main()



