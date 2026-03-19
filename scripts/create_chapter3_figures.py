"""
Tạo các biểu đồ cho Chapter 3: Research Results
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
import io

# Fix encoding for Windows
if hasattr(sys.stdout, 'buffer') and not hasattr(sys.stdout, '_encoding_set'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stdout._encoding_set = True
    except (AttributeError, ValueError):
        pass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.preprocessing import DataPreprocessor
from scripts.run_event_study import EventStudy
from scripts.detect_events import GPREventDetector

class EventStudyWithMarketProxy(EventStudy):
    """EventStudy với khả năng chọn market proxy"""
    
    def __init__(self, *args, market_proxy='DXY', **kwargs):
        super().__init__(*args, **kwargs)
        # Override market series
        self.market_series = market_proxy
        self.market_returns = self._prepare_market_returns()

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Create output directory
output_dir = Path('results/chapter3_figures')
output_dir.mkdir(parents=True, exist_ok=True)

def load_data():
    """Load and preprocess data"""
    preprocessor = DataPreprocessor()
    data = preprocessor.load_data('data/raw/data.csv')
    
    # Filter date range
    data = data[(data.index >= '2015-01-01') & (data.index <= '2025-11-11')]
    
    return data

def load_events():
    """Load detected events"""
    events_path = Path('results/detected_events.csv')
    if not events_path.exists():
        print(f"Warning: {events_path} not found")
        return pd.DataFrame()
    
    events = pd.read_csv(events_path)
    if 'date' in events.columns:
        events['date'] = pd.to_datetime(events['date'], dayfirst=True, format='mixed', errors='coerce')
    return events

def plot_asset_prices(data):
    """
    Figure 3.1: Giá của 3 tài sản theo thời gian (giá thực tế USD)
    """
    print("Creating Figure 3.1: Asset Prices Over Time...")
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    assets = ['BTC', 'GOLD', 'OIL']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    asset_names = ['Bitcoin', 'Gold', 'Oil']
    units = ['USD', 'USD/oz', 'USD/barrel']
    
    for idx, (asset, color, name, unit) in enumerate(zip(assets, colors, asset_names, units)):
        if asset not in data.columns:
            continue
        
        prices = data[asset].dropna()
        
        # Use actual prices (not normalized)
        axes[idx].plot(prices.index, prices.values, 
                      color=color, linewidth=1.5, alpha=0.8)
        axes[idx].set_ylabel(f'{name} Price ({unit})', fontsize=11)
        axes[idx].set_title(f'{name} Price Evolution (2015-2024)', fontsize=12, fontweight='bold')
        axes[idx].grid(True, alpha=0.3)
        
        # Format y-axis to show numbers nicely
        axes[idx].ticklabel_format(style='plain', axis='y')
        # Use comma separator for thousands
        from matplotlib.ticker import FuncFormatter
        def format_func(x, p):
            return f'{x:,.0f}'
        axes[idx].yaxis.set_major_formatter(FuncFormatter(format_func))
    
    axes[-1].set_xlabel('Year', fontsize=11)
    plt.tight_layout()
    plt.savefig(output_dir / 'figure_3.1_asset_prices.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_dir / 'figure_3.1_asset_prices.png'}")

def plot_gpr_with_events(data, events):
    """
    Figure 3.2: GPR Index theo thời gian với events được đánh dấu
    """
    print("Creating Figure 3.2: GPR Index with Events...")
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Plot GPR
    if 'GPRD' in data.columns:
        gpr = data['GPRD'].dropna()
        ax.plot(gpr.index, gpr.values, color='#2C3E50', linewidth=1.5, alpha=0.7, label='GPR Index')
        
        # Add events
        if not events.empty and 'date' in events.columns:
            event_dates = events['date'].dropna()
            event_gpr = gpr.reindex(event_dates, method='nearest')
            
            ax.scatter(event_dates, event_gpr.values, 
                      color='red', s=50, alpha=0.6, zorder=5, 
                      label=f'Geopolitical Events (n={len(event_dates)})',
                      marker='v')
        
        # Add percentile lines
        p95 = gpr.quantile(0.95)
        p50 = gpr.quantile(0.50)
        ax.axhline(y=p95, color='orange', linestyle='--', linewidth=1, 
                  alpha=0.7, label=f'95th Percentile ({p95:.1f})')
        ax.axhline(y=p50, color='gray', linestyle='--', linewidth=0.8, 
                  alpha=0.5, label=f'Median ({p50:.1f})')
    
    ax.set_xlabel('Year', fontsize=11)
    ax.set_ylabel('GPR Index', fontsize=11)
    ax.set_title('Geopolitical Risk Index (GPR) with Detected Events (2015-2024)', 
                fontsize=12, fontweight='bold')
    ax.legend(loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / 'figure_3.2_gpr_with_events.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_dir / 'figure_3.2_gpr_with_events.png'}")

def plot_aar_caar():
    """
    Figure 3.3: AAR và CAAR theo thời gian trong event window
    Note: Time decay plots already exist in results/time_decay_analysis/
    This creates a combined AAR/CAAR plot for Chapter 3
    """
    print("Creating Figure 3.3: AAR and CAAR Over Event Window...")
    print("  Note: Individual time decay plots exist in results/time_decay_analysis/")
    
    # Load AAR data
    aar_path = Path('results/time_decay_analysis/aar_by_day.csv')
    if not aar_path.exists():
        print(f"  Warning: {aar_path} not found. Skipping AAR/CAAR plot.")
        return
    
    aar_data = pd.read_csv(aar_path, index_col=0)
    
    # Convert index to int if it's string
    if aar_data.index.dtype == 'object':
        aar_data.index = aar_data.index.astype(int)
    
    # Calculate CAAR from AAR (cumulative sum)
    caar_data = aar_data.cumsum()
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    assets = ['BTC', 'GOLD', 'OIL']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    asset_names = ['Bitcoin', 'Gold', 'Oil']
    
    # Plot AAR
    for asset, color, name in zip(assets, colors, asset_names):
        if asset in aar_data.columns:
            aar = aar_data[asset]
            axes[0].plot(aar.index.astype(int), aar.values, 
                        marker='o', markersize=4, linewidth=1.5, 
                        color=color, label=name, alpha=0.8)
    
    axes[0].axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    axes[0].axvline(x=0, color='red', linestyle='--', linewidth=1, alpha=0.7, label='Event Day (T0)')
    axes[0].set_ylabel('Average Abnormal Return (AAR, USD)', fontsize=11)
    axes[0].set_title('Average Abnormal Returns (AAR) by Day', fontsize=12, fontweight='bold')
    axes[0].legend(loc='best', fontsize=9)
    axes[0].grid(True, alpha=0.3)
    
    # Plot CAAR
    for asset, color, name in zip(assets, colors, asset_names):
        if asset in caar_data.columns:
            caar = caar_data[asset]
            axes[1].plot(caar.index.astype(int), caar.values, 
                        marker='s', markersize=4, linewidth=2, 
                        color=color, label=name, alpha=0.8)
    
    axes[1].axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    axes[1].axvline(x=0, color='red', linestyle='--', linewidth=1, alpha=0.7, label='Event Day (T0)')
    axes[1].set_xlabel('Days Relative to Event', fontsize=11)
    axes[1].set_ylabel('Cumulative Average Abnormal Return (CAAR, USD)', fontsize=11)
    axes[1].set_title('Cumulative Average Abnormal Returns (CAAR) by Day', fontsize=12, fontweight='bold')
    axes[1].legend(loc='best', fontsize=9)
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'figure_3.3_aar_caar.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_dir / 'figure_3.3_aar_caar.png'}")

def plot_aar_separate():
    """
    Figure riêng: AAR theo thời gian trong event window
    """
    print("Creating separate AAR figure...")
    
    # Load AAR data
    aar_path = Path('results/time_decay_analysis/aar_by_day.csv')
    if not aar_path.exists():
        print(f"  Warning: {aar_path} not found. Skipping AAR plot.")
        return
    
    aar_data = pd.read_csv(aar_path, index_col=0)
    
    # Convert index to int if it's string
    if aar_data.index.dtype == 'object':
        aar_data.index = aar_data.index.astype(int)
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    
    assets = ['BTC', 'GOLD', 'OIL']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    asset_names = ['Bitcoin', 'Gold', 'Oil']
    
    # Plot AAR
    for asset, color, name in zip(assets, colors, asset_names):
        if asset in aar_data.columns:
            aar = aar_data[asset]
            ax.plot(aar.index.astype(int), aar.values, 
                   marker='o', markersize=5, linewidth=2, 
                   color=color, label=name, alpha=0.8)
    
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.axvline(x=0, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='Event Day (T0)')
    ax.set_xlabel('Days Relative to Event', fontsize=12)
    ax.set_ylabel('Average Abnormal Return (AAR, USD)', fontsize=12)
    ax.set_title('Average Abnormal Returns (AAR) by Day', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'figure_aar_separate.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_dir / 'figure_aar_separate.png'}")

def plot_figure_3_6_aar():
    """
    Figure 3.6: Diễn biến AAR hàng ngày của các tài sản
    """
    print("Creating Figure 3.6: Daily AAR Evolution...")
    
    # Load AAR data
    aar_path = Path('results/time_decay_analysis/aar_by_day.csv')
    if not aar_path.exists():
        print(f"  Warning: {aar_path} not found. Skipping AAR plot.")
        return
    
    aar_data = pd.read_csv(aar_path, index_col=0)
    
    # Convert index to int if it's string
    if aar_data.index.dtype == 'object':
        aar_data.index = aar_data.index.astype(int)
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    
    assets = ['BTC', 'GOLD', 'OIL']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    asset_names = ['Bitcoin', 'Gold', 'Oil']
    
    # Plot AAR
    for asset, color, name in zip(assets, colors, asset_names):
        if asset in aar_data.columns:
            aar = aar_data[asset]
            ax.plot(aar.index.astype(int), aar.values * 100, 
                   marker='o', markersize=5, linewidth=2.5, 
                   color=color, label=name, alpha=0.8)
    
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.axvline(x=0, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='Event Day (T0)')
    ax.set_xlabel('Days Relative to Event', fontsize=12)
    ax.set_ylabel('Average Abnormal Return (AAR, %)', fontsize=12)
    ax.set_title('Diễn biến AAR hàng ngày của các tài sản', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'figure_3.6_aar_daily.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_dir / 'figure_3.6_aar_daily.png'}")

def plot_caar_separate():
    """
    Figure riêng: CAAR theo thời gian trong event window
    """
    print("Creating separate CAAR figure...")
    
    # Load AAR data
    aar_path = Path('results/time_decay_analysis/aar_by_day.csv')
    if not aar_path.exists():
        print(f"  Warning: {aar_path} not found. Skipping CAAR plot.")
        return
    
    aar_data = pd.read_csv(aar_path, index_col=0)
    
    # Convert index to int if it's string
    if aar_data.index.dtype == 'object':
        aar_data.index = aar_data.index.astype(int)
    
    # Calculate CAAR from AAR (cumulative sum)
    caar_data = aar_data.cumsum()
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    
    assets = ['BTC', 'GOLD', 'OIL']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    asset_names = ['Bitcoin', 'Gold', 'Oil']
    
    # Plot CAAR
    for asset, color, name in zip(assets, colors, asset_names):
        if asset in caar_data.columns:
            caar = caar_data[asset]
            ax.plot(caar.index.astype(int), caar.values, 
                   marker='s', markersize=5, linewidth=2.5, 
                   color=color, label=name, alpha=0.8)
    
    ax.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
    ax.axvline(x=0, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='Event Day (T0)')
    ax.set_xlabel('Days Relative to Event', fontsize=12)
    ax.set_ylabel('Cumulative Average Abnormal Return (CAAR, USD)', fontsize=12)
    ax.set_title('Cumulative Average Abnormal Returns (CAAR) by Day', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'figure_caar_separate.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_dir / 'figure_caar_separate.png'}")

def plot_caar_robustness_comparison(asset='GOLD', asset_name='Vàng', figure_num='3.4'):
    """
    So sánh đường CAAR giữa Mean Adjusted Model và Market Model cho một tài sản
    """
    print(f"Creating Figure {figure_num}: CAAR Robustness Comparison ({asset_name})...")
    
    # Load data - try data_with_sp500.csv first, then data.csv
    preprocessor = DataPreprocessor()
    data_path = Path('data/raw/data_with_sp500.csv')
    if not data_path.exists():
        data_path = Path('data/raw/data.csv')
    
    if not data_path.exists():
        print(f"  Warning: Data file not found. Skipping robustness comparison plot.")
        return
    
    try:
        data = preprocessor.load_data(str(data_path))
    except:
        data = pd.read_csv(data_path, index_col=0, parse_dates=True, dayfirst=True)
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index, dayfirst=True, errors='coerce')
    
    # Detect events
    detector = GPREventDetector(data)
    events = detector.detect_all_events()
    
    # Run Event Study với Mean Adjusted Model
    print(f"  Running Mean Adjusted Model for {asset}...")
    event_study_mean = EventStudy(
        data=data,
        assets=[asset],
        event_window=(-10, 10),
        estimation_window=120,
        model='mean'
    )
    events_dict_mean = event_study_mean.load_events_from_detector(events)
    results_mean = event_study_mean.analyze_all_events(events=events_dict_mean, use_auto_detection=False)
    stats_mean = event_study_mean.compute_aggregate_statistics(results_mean)
    
    # Check if SP500 exists in data
    has_sp500 = 'SP500' in data.columns
    if not has_sp500:
        print(f"  Warning: SP500 not found in data. Skipping Market Model plot.")
        return
    
    # Run Event Study với Market Model (S&P 500)
    print(f"  Running Market Model (S&P 500) for {asset}...")
    event_study_market = EventStudyWithMarketProxy(
        data=data,
        assets=[asset],
        event_window=(-10, 10),
        estimation_window=120,
        model='market',
        market_proxy='SP500'
    )
    events_dict_market = event_study_market.load_events_from_detector(events)
    results_market = event_study_market.analyze_all_events(events=events_dict_market, use_auto_detection=False)
    stats_market = event_study_market.compute_aggregate_statistics(results_market)
    
    # Extract CAAR data
    if asset not in stats_mean or asset not in stats_market:
        print(f"  Warning: {asset} data not found in statistics. Skipping plot.")
        return
    
    caar_mean = stats_mean[asset]['CAAR']
    caar_market = stats_market[asset]['CAAR']
    days = stats_mean[asset]['days']
    
    # Choose color based on asset
    colors = {
        'BTC': '#FF6B6B',  # Red
        'GOLD': '#4ECDC4',  # Teal
        'OIL': '#45B7D1'   # Blue
    }
    asset_color = colors.get(asset, '#4ECDC4')
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))
    
    # Plot CAAR Mean Adjusted Model (nét liền)
    ax.plot(days, caar_mean * 100, 
           marker='o', markersize=5, linewidth=2.5, 
           color=asset_color, label='Mean Adjusted Model', 
           linestyle='-', alpha=0.8)
    
    # Plot CAAR Market Model (nét đứt)
    ax.plot(days, caar_market * 100, 
           marker='s', markersize=5, linewidth=2.5, 
           color='#FF6B6B', label='Market Model (S&P 500)', 
           linestyle='--', alpha=0.8)
    
    # Add reference lines
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.3)
    ax.axvline(x=0, color='red', linestyle=':', linewidth=1.5, alpha=0.7, label='Event Day (T0)')
    
    # Labels and title
    ax.set_xlabel('Days Relative to Event', fontsize=12)
    ax.set_ylabel('Cumulative Average Abnormal Return (CAAR, %)', fontsize=12)
    ax.set_title(f'So sánh đường CAAR giữa Mô hình chính và Mô hình kiểm tra ({asset_name})', 
                fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Save figure
    filename = f'figure_{figure_num}_caar_robustness_{asset.lower()}.png'
    plt.tight_layout()
    plt.savefig(output_dir / filename, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_dir / filename}")

def plot_all_caar_robustness():
    """
    Tạo tất cả các hình so sánh CAAR robustness cho cả 3 tài sản
    """
    plot_caar_robustness_comparison('GOLD', 'Vàng', '3.4')
    plot_caar_robustness_comparison('BTC', 'Bitcoin', '3.4b')
    plot_caar_robustness_comparison('OIL', 'Dầu mỏ', '3.4c')

def plot_car_distribution():
    """
    Figure 3.4: Phân bố CAR của 3 tài sản
    """
    print("Creating Figure 3.4: CAR Distribution...")
    
    # Try to load events with CAR from enriched file first
    events_path = Path('results/detected_events_enriched.csv')
    if not events_path.exists():
        events_path = Path('results/detected_events.csv')
    
    if not events_path.exists():
        print(f"  Warning: {events_path} not found. Skipping CAR distribution plot.")
        return
    
    events = pd.read_csv(events_path)
    
    car_cols = [col for col in events.columns if col.startswith('CAR_') or 'CAR' in col.upper()]
    if not car_cols:
        print(f"  Warning: No CAR columns found. Skipping CAR distribution plot.")
        return
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    assets = ['BTC', 'GOLD', 'OIL']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    asset_names = ['Bitcoin', 'Gold', 'Oil']
    
    for idx, (asset, color, name) in enumerate(zip(assets, colors, asset_names)):
        car_col = f'CAR_{asset}'
        if car_col not in events.columns:
            continue
        
        car_values = events[car_col].dropna()  # Keep as decimal (USD)
        
        axes[idx].hist(car_values, bins=20, color=color, alpha=0.7, edgecolor='black', linewidth=0.5)
        axes[idx].axvline(x=0, color='black', linestyle='--', linewidth=1.5, alpha=0.7)
        axes[idx].axvline(x=car_values.mean(), color='red', linestyle='-', 
                         linewidth=2, label=f'Mean: {car_values.mean():.4f} USD')
        axes[idx].set_xlabel('CAR (USD)', fontsize=10)
        axes[idx].set_ylabel('Frequency', fontsize=10)
        axes[idx].set_title(f'{name} CAR Distribution', fontsize=11, fontweight='bold')
        axes[idx].legend(fontsize=9)
        axes[idx].grid(True, alpha=0.3, axis='y')
    
    plt.suptitle('Cumulative Abnormal Returns (CAR) Distribution by Asset', 
                fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'figure_3.4_car_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_dir / 'figure_3.4_car_distribution.png'}")

def plot_act_vs_threat():
    """
    Figure 3.5: So sánh ACT vs THREAT (nếu có dữ liệu)
    """
    print("Creating Figure 3.5: ACT vs THREAT Comparison...")
    
    act_threat_path = Path('results/act_threat_analysis/act_threat_results.csv')
    if not act_threat_path.exists():
        print(f"  Warning: {act_threat_path} not found. Skipping ACT vs THREAT plot.")
        return
    
    act_threat = pd.read_csv(act_threat_path)
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    assets = ['BTC', 'GOLD', 'OIL']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    asset_names = ['Bitcoin', 'Gold', 'Oil']
    
    for idx, (asset, color, name) in enumerate(zip(assets, colors, asset_names)):
        act_col = f'ACT_CAAR_{asset}'
        threat_col = f'THREAT_CAAR_{asset}'
        
        if act_col not in act_threat.columns or threat_col not in act_threat.columns:
            continue
        
        act_caar = act_threat[act_col].iloc[0] if len(act_threat) > 0 else 0
        threat_caar = act_threat[threat_col].iloc[0] if len(act_threat) > 0 else 0
        
        x = np.arange(2)
        values = [act_caar, threat_caar]
        bars = axes[idx].bar(x, values, color=[color, color], alpha=[0.8, 0.5], 
                           edgecolor='black', linewidth=1)
        
        axes[idx].axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        axes[idx].set_xticks(x)
        axes[idx].set_xticklabels(['ACT', 'THREAT'], fontsize=10)
        axes[idx].set_ylabel('CAAR (USD)', fontsize=10)
        axes[idx].set_title(f'{name}', fontsize=11, fontweight='bold')
        axes[idx].grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar, val in zip(bars, values):
            height = bar.get_height()
            axes[idx].text(bar.get_x() + bar.get_width()/2., height,
                         f'{val:.4f}', ha='center', va='bottom' if height >= 0 else 'top',
                         fontsize=9, fontweight='bold')
    
    plt.suptitle('CAAR Comparison: ACT vs THREAT Events', 
                fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'figure_3.5_act_vs_threat.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_dir / 'figure_3.5_act_vs_threat.png'}")

def plot_reaction_phases():
    """
    Figure 3.6: Phân tích các giai đoạn phản ứng (Pre-Event, Event Day, Post-Event)
    """
    print("Creating Figure 3.6: Reaction Phases Analysis...")
    
    phases_path = Path('results/reaction_phases_analysis/reaction_phases_summary.csv')
    if not phases_path.exists():
        print(f"  Warning: {phases_path} not found. Skipping reaction phases plot.")
        return
    
    phases = pd.read_csv(phases_path, index_col=0)
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    assets = ['BTC', 'GOLD', 'OIL']
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    asset_names = ['Bitcoin', 'Gold', 'Oil']
    phase_names = ['Pre-Event\n(T-10 to T-1)', 'Event Day\n(T0)', 'Post-Event\n(T+1 to T+10)']
    
    for idx, (asset, color, name) in enumerate(zip(assets, colors, asset_names)):
        phase_cols = [f'{phase}_{asset}_mean' for phase in ['PreEvent', 'EventDay', 'PostEvent']]
        
        if not all(col in phases.columns for col in phase_cols):
            continue
        
        values = [phases[col].iloc[0] if len(phases) > 0 else 0 for col in phase_cols]
        
        x = np.arange(3)
        bars = axes[idx].bar(x, values, color=color, alpha=0.7, 
                           edgecolor='black', linewidth=1)
        
        axes[idx].axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        axes[idx].set_xticks(x)
        axes[idx].set_xticklabels(phase_names, fontsize=9, rotation=0, ha='center')
        axes[idx].set_ylabel('Average Return (USD)', fontsize=10)
        axes[idx].set_title(f'{name}', fontsize=11, fontweight='bold')
        axes[idx].grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar, val in zip(bars, values):
            height = bar.get_height()
            axes[idx].text(bar.get_x() + bar.get_width()/2., height,
                         f'{val:.4f}', ha='center', va='bottom' if height >= 0 else 'top',
                         fontsize=9, fontweight='bold')
    
    plt.suptitle('Average Returns by Reaction Phase', 
                fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'figure_3.6_reaction_phases.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_dir / 'figure_3.6_reaction_phases.png'}")

def main():
    """Main function to create all figures"""
    print("="*80)
    print("CREATING FIGURES FOR CHAPTER 3")
    print("="*80)
    
    # Load data
    print("\nLoading data...")
    data = load_data()
    events = load_events()
    
    print(f"Data loaded: {len(data)} observations")
    print(f"Events loaded: {len(events)} events")
    
    # Create figures
    print("\n" + "="*80)
    plot_asset_prices(data)
    plot_gpr_with_events(data, events)
    plot_aar_caar()
    plot_aar_separate()
    plot_caar_separate()
    plot_figure_3_6_aar()
    plot_all_caar_robustness()
    plot_car_distribution()
    plot_act_vs_threat()
    plot_reaction_phases()
    
    print("\n" + "="*80)
    print(f"All figures saved to: {output_dir}")
    print("="*80)
    
    # List existing time decay plots
    time_decay_dir = Path('results/time_decay_analysis')
    if time_decay_dir.exists():
        print("\n" + "="*80)
        print("EXISTING TIME DECAY PLOTS (already available):")
        print("="*80)
        time_decay_plots = list(time_decay_dir.glob('*.png'))
        for plot in sorted(time_decay_plots):
            print(f"  - {plot.name}")
        print(f"\nTotal: {len(time_decay_plots)} time decay plots")
        print("="*80)

if __name__ == '__main__':
    main()

