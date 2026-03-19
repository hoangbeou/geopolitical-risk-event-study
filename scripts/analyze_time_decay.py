"""
Phân tích Time Decay và Persistence của phản ứng
Tính toán AAR theo từng ngày và persistence của phản ứng
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.preprocessing import DataPreprocessor
from scripts.run_event_study import EventStudy
from scripts.detect_events import GPREventDetector

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_event_results():
    """Load events và tính toán AR theo từng ngày"""
    print("="*70)
    print("PHÂN TÍCH TIME DECAY VÀ PERSISTENCE")
    print("="*70)
    
    # Load data
    print("\n1. Loading data...")
    preprocessor = DataPreprocessor()
    data = preprocessor.load_data('data/raw/data.csv')
    
    # Load detected events
    print("2. Loading detected events...")
    detector = GPREventDetector(data)
    events_df = detector.detect_all_events(
        spike_percentile=95,
        high_period_percentile=95,
        combine=True,
        require_gpr_increase=True
    )
    
    print(f"   Found {len(events_df)} events")
    
    # Initialize EventStudy
    event_study = EventStudy(
        data=data,
        assets=['BTC', 'GOLD', 'OIL'],
        event_window=(-10, 10),
        estimation_window=120,
        estimation_gap=1,
        model='mean'
    )
    
    # Calculate AR for each event and day
    print("3. Calculating AR for each event and day...")
    all_aar_data = []
    
    for idx, row in events_df.iterrows():
        event_date = pd.to_datetime(row['date'])
        event_num = idx + 1  # Use index + 1 as event number
        
        for asset in ['BTC', 'GOLD', 'OIL']:
            if asset not in data.columns:
                continue
            
            # Get returns for this asset
            returns = event_study.calculate_returns(data[asset])
            
            # Calculate CAR (which includes AR)
            car_result = event_study.calculate_car(returns, event_date)
            
            if car_result is None:
                continue
            
            # Extract AR and days
            ar_series = car_result['ar']
            days = car_result['days']
            
            # Combine AR with days
            for day, ar_value in zip(days, ar_series.values):
                all_aar_data.append({
                    'Event_Number': event_num,
                    'Date': event_date,
                    'Asset': asset,
                    'Day': int(day),
                    'AR': ar_value
                })
    
    aar_df = pd.DataFrame(all_aar_data)
    
    if len(aar_df) == 0:
        print("   Warning: No AR data calculated. Trying alternative method...")
        return None
    
    print(f"   Calculated AR for {len(aar_df)} event-day-asset combinations")
    return aar_df, events_df

def calculate_aar_by_day(aar_df):
    """Tính Average Abnormal Returns (AAR) theo từng ngày"""
    print("\n4. Calculating AAR by day...")
    
    # Group by Day and Asset, calculate mean AR
    aar_by_day = aar_df.groupby(['Day', 'Asset'])['AR'].mean().reset_index()
    aar_by_day = aar_by_day.pivot(index='Day', columns='Asset', values='AR')
    
    return aar_by_day

def calculate_persistence(aar_df, thresholds=[0.01, 0.02, 0.05]):
    """Tính persistence - số ngày AR vượt threshold"""
    print("\n5. Calculating persistence...")
    
    persistence_results = []
    
    for asset in ['BTC', 'GOLD', 'OIL']:
        asset_data = aar_df[aar_df['Asset'] == asset].copy()
        
        for threshold in thresholds:
            # Count days where |AR| > threshold for each event
            event_persistence = []
            
            for event_num in asset_data['Event_Number'].unique():
                event_data = asset_data[
                    (asset_data['Event_Number'] == event_num) & 
                    (asset_data['Day'] >= 0)  # Only post-event days
                ]
                
                # Count days with |AR| > threshold
                count = (event_data['AR'].abs() > threshold).sum()
                event_persistence.append(count)
            
            mean_persistence = np.mean(event_persistence) if event_persistence else 0
            
            persistence_results.append({
                'Asset': asset,
                'Threshold': f'{threshold*100:.0f}%',
                'Mean_Persistence_Days': mean_persistence
            })
    
    persistence_df = pd.DataFrame(persistence_results)
    persistence_df = persistence_df.pivot(index='Asset', columns='Threshold', values='Mean_Persistence_Days')
    
    return persistence_df

def visualize_time_decay(aar_by_day, output_dir):
    """Tạo visualizations cho time decay"""
    print("\n6. Creating visualizations...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. AAR by day
    ax1 = axes[0, 0]
    for asset in ['BTC', 'GOLD', 'OIL']:
        if asset in aar_by_day.columns:
            ax1.plot(aar_by_day.index, aar_by_day[asset] * 100, 
                    marker='o', linewidth=2, markersize=6, label=asset)
    
    ax1.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    ax1.axvline(x=0, color='k', linestyle='--', alpha=0.5, label='Event Day')
    ax1.set_xlabel('Day Relative to Event', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Average Abnormal Return (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Average Abnormal Returns (AAR) by Day', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(-10, 10)
    
    # 2. CAAR by day
    ax2 = axes[0, 1]
    caar_by_day = aar_by_day.cumsum()
    for asset in ['BTC', 'GOLD', 'OIL']:
        if asset in caar_by_day.columns:
            ax2.plot(caar_by_day.index, caar_by_day[asset] * 100,
                    marker='o', linewidth=2, markersize=6, label=asset)
    
    ax2.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    ax2.axvline(x=0, color='k', linestyle='--', alpha=0.5, label='Event Day')
    ax2.set_xlabel('Day Relative to Event', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Cumulative Average Abnormal Return (%)', fontsize=12, fontweight='bold')
    ax2.set_title('Cumulative Average Abnormal Returns (CAAR)', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(-10, 10)
    
    # 3. Persistence comparison (placeholder - will be filled after calculation)
    ax3 = axes[1, 0]
    ax3.text(0.5, 0.5, 'Persistence Analysis\n(Will be filled after calculation)',
            ha='center', va='center', fontsize=14, transform=ax3.transAxes)
    ax3.set_title('Persistence Comparison', fontsize=14, fontweight='bold')
    ax3.axis('off')
    
    # 4. Summary statistics
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # Calculate summary stats
    summary_data = []
    for asset in ['BTC', 'GOLD', 'OIL']:
        if asset in aar_by_day.columns:
            pre_event = aar_by_day.loc[-10:-1, asset].mean() * 100
            event_day = aar_by_day.loc[0, asset] * 100 if 0 in aar_by_day.index else 0
            post_event = aar_by_day.loc[1:10, asset].mean() * 100
            
            summary_data.append([
                asset,
                f'{pre_event:.2f}%',
                f'{event_day:.2f}%',
                f'{post_event:.2f}%'
            ])
    
    if summary_data:
        table = ax4.table(cellText=summary_data,
                         colLabels=['Asset', 'Pre-Event\n(-10 to -1)', 'Event Day\n(0)', 'Post-Event\n(+1 to +10)'],
                         cellLoc='center',
                         loc='center',
                         bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        for i in range(len(summary_data[0])):
            table[(0, i)].set_facecolor('#34495e')
            table[(0, i)].set_text_props(weight='bold', color='white')
    
    plt.suptitle('Time Decay Analysis: AAR and Persistence', fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    output_path = output_dir / 'time_decay_analysis.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"   ✓ Saved: {output_path}")
    plt.close()

def visualize_persistence(persistence_df, output_dir):
    """Visualize persistence results"""
    if persistence_df is None or len(persistence_df) == 0:
        print("   Warning: No persistence data to visualize")
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(persistence_df.index))
    width = 0.25
    
    for i, threshold in enumerate(persistence_df.columns):
        values = persistence_df[threshold].values
        ax.bar(x + i*width, values, width, label=f'AR > {threshold}', alpha=0.8)
    
    ax.set_xlabel('Asset', fontsize=12, fontweight='bold')
    ax.set_ylabel('Mean Persistence (Days)', fontsize=12, fontweight='bold')
    ax.set_title('Persistence of Abnormal Returns by Asset', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width)
    ax.set_xticklabels(persistence_df.index)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    output_path = output_dir / 'persistence_analysis.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"   ✓ Saved: {output_path}")
    plt.close()

def export_results(aar_by_day, persistence_df, output_dir):
    """Export kết quả"""
    print("\n7. Exporting results...")
    
    # Export AAR by day
    aar_by_day_pct = aar_by_day * 100
    aar_by_day_pct.to_csv(output_dir / 'aar_by_day.csv')
    print(f"   ✓ Saved: {output_dir / 'aar_by_day.csv'}")
    
    # Export persistence
    if persistence_df is not None and len(persistence_df) > 0:
        persistence_df.to_csv(output_dir / 'persistence_analysis.csv')
        print(f"   ✓ Saved: {output_dir / 'persistence_analysis.csv'}")
        
        # Print markdown table
        print("\n" + "="*70)
        print("BẢNG PERSISTENCE (Markdown):")
        print("="*70)
        print("\n| Asset | AR > 1% | AR > 2% | AR > 5% |")
        print("|-------|---------|---------|---------|")
        for asset in persistence_df.index:
            row = f"| {asset} |"
            for threshold in persistence_df.columns:
                value = persistence_df.loc[asset, threshold]
                row += f" {value:.1f} ngày |"
            print(row)
    
    # Print AAR summary
    print("\n" + "="*70)
    print("AAR SUMMARY:")
    print("="*70)
    print("\nDay | BTC (%) | GOLD (%) | OIL (%)")
    print("-" * 40)
    for day in sorted(aar_by_day.index):
        row = f"{day:3d} |"
        for asset in ['BTC', 'GOLD', 'OIL']:
            if asset in aar_by_day.columns:
                value = aar_by_day.loc[day, asset] * 100
                row += f" {value:7.2f} |"
            else:
                row += "    N/A |"
        print(row)

def main():
    """Main function"""
    print("STARTING TIME DECAY ANALYSIS...")
    output_dir = Path('results/time_decay_analysis')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load and calculate AR data
    result = load_event_results()
    if result is None:
        print("\n❌ Error: Could not calculate AR data")
        print("   Alternative: Use existing event study results if available")
        return
    
    aar_df, events_df = result
    
    # Calculate AAR by day
    aar_by_day = calculate_aar_by_day(aar_df)
    
    # Calculate persistence
    persistence_df = calculate_persistence(aar_df)
    
    # Visualize
    visualize_time_decay(aar_by_day, output_dir)
    visualize_persistence(persistence_df, output_dir)
    
    # Export
    export_results(aar_by_day, persistence_df, output_dir)
    
    print("\n" + "="*70)
    print("✓ HOÀN THÀNH PHÂN TÍCH TIME DECAY")
    print("="*70)

if __name__ == '__main__':
    main()

