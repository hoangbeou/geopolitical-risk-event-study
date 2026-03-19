"""
Create choropleth map (color-coded by country) with event frequency table
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Country name mapping (for consistency)
COUNTRY_MAPPING = {
    'United States': 'USA',
    'United Kingdom': 'UK',
    'Gaza': 'Palestine',
    'Gaza Strip': 'Palestine',
    'West Bank': 'Palestine',
    'Kyiv': 'Ukraine',
    'Kiev': 'Ukraine',
    'Donetsk': 'Ukraine',
    'Crimea': 'Ukraine',
    'Kashmir': 'India',  # Disputed, but for mapping
    'Kabul': 'Afghanistan',
    'Baghdad': 'Iraq',
    'Damascus': 'Syria',
    'Tehran': 'Iran',
    'Jerusalem': 'Israel',
    'Aleppo': 'Syria',
    'Mosul': 'Iraq',
}


def load_and_aggregate_by_country():
    """Load events and aggregate by country"""
    df = pd.read_csv('results/events_classified_act_threat.csv')
    df['date'] = pd.to_datetime(df['date'])
    
    # Process locations
    country_data = []
    
    for idx, row in df.iterrows():
        locations = str(row['Detected_Locations'])
        
        if locations == 'nan' or locations == '':
            continue
        
        locs = [l.strip() for l in locations.split(',')]
        
        for loc in locs:
            # Map to country
            country = COUNTRY_MAPPING.get(loc, loc)
            
            country_data.append({
                'country': country,
                'date': row['date'],
                'gpr_diff': row['gpr_diff'],
                'BTC_CAR': row.get('BTC_CAR', np.nan),
                'GOLD_CAR': row.get('GOLD_CAR', np.nan),
                'OIL_CAR': row.get('OIL_CAR', np.nan),
                'Event_Type': row.get('Event_Type', 'Unknown')
            })
    
    country_df = pd.DataFrame(country_data)
    
    # Aggregate by country
    country_stats = country_df.groupby('country').agg({
        'date': 'count',
        'gpr_diff': 'mean',
        'BTC_CAR': 'mean',
        'GOLD_CAR': 'mean',
        'OIL_CAR': 'mean'
    }).round(4)
    
    country_stats.columns = ['Event_Count', 'Avg_GPR_Diff', 'Avg_BTC_CAR', 'Avg_GOLD_CAR', 'Avg_OIL_CAR']
    country_stats = country_stats.sort_values('Event_Count', ascending=False)
    
    return country_stats


def create_frequency_table_plot(country_stats):
    """Create beautiful table plot showing event frequency by country"""
    print("Creating event frequency table...")
    
    # Get top 20 countries
    top20 = country_stats.head(20).copy()
    top20['Avg_BTC_CAR_%'] = (top20['Avg_BTC_CAR'] * 100).round(2)
    top20['Avg_GOLD_CAR_%'] = (top20['Avg_GOLD_CAR'] * 100).round(2)
    top20['Avg_OIL_CAR_%'] = (top20['Avg_OIL_CAR'] * 100).round(2)
    
    # Create figure with table
    fig, (ax_table, ax_bar) = plt.subplots(1, 2, figsize=(20, 12), 
                                            gridspec_kw={'width_ratios': [1.2, 1]})
    
    # Hide axes for table
    ax_table.axis('tight')
    ax_table.axis('off')
    
    # Prepare table data
    table_data = []
    for idx, (country, row) in enumerate(top20.iterrows(), 1):
        table_data.append([
            idx,
            country,
            int(row['Event_Count']),
            f"{row['Avg_BTC_CAR_%']:+.2f}%",
            f"{row['Avg_GOLD_CAR_%']:+.2f}%",
            f"{row['Avg_OIL_CAR_%']:+.2f}%"
        ])
    
    # Create table
    table = ax_table.table(
        cellText=table_data,
        colLabels=['#', 'Country', 'Events', 'BTC CAR', 'GOLD CAR', 'OIL CAR'],
        cellLoc='center',
        loc='center',
        colWidths=[0.08, 0.25, 0.12, 0.18, 0.18, 0.18]
    )
    
    # Style table
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.2)
    
    # Color header
    for i in range(6):
        cell = table[(0, i)]
        cell.set_facecolor('#4472C4')
        cell.set_text_props(weight='bold', color='white', fontsize=11)
    
    # Color cells based on values
    for i in range(1, len(table_data) + 1):
        # Rank column
        table[(i, 0)].set_facecolor('#E7E6E6')
        
        # Country column
        table[(i, 1)].set_facecolor('#F2F2F2')
        table[(i, 1)].set_text_props(ha='left')
        
        # Event count
        table[(i, 2)].set_facecolor('#FFF2CC')
        table[(i, 2)].set_text_props(weight='bold')
        
        # CAR columns - color by positive/negative
        for col_idx in [3, 4, 5]:  # BTC, GOLD, OIL
            value_str = table_data[i-1][col_idx]
            value = float(value_str.replace('%', ''))
            
            if value > 2:
                table[(i, col_idx)].set_facecolor('#C6EFCE')  # Green
            elif value < -2:
                table[(i, col_idx)].set_facecolor('#FFC7CE')  # Red
            else:
                table[(i, col_idx)].set_facecolor('#FFEB9C')  # Yellow
    
    ax_table.set_title('Top 20 Countries by GPR Event Frequency (2015-2025)',
                      fontsize=14, fontweight='bold', pad=20)
    
    # Bar chart on right
    countries = top20.index[:15]
    counts = top20['Event_Count'][:15].values
    
    bars = ax_bar.barh(range(len(countries)), counts, color='#4472C4', alpha=0.8,
                       edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for i, (bar, count) in enumerate(zip(bars, counts)):
        ax_bar.text(count + 0.5, i, str(int(count)), 
                   va='center', fontsize=10, fontweight='bold')
    
    ax_bar.set_yticks(range(len(countries)))
    ax_bar.set_yticklabels(countries, fontsize=10)
    ax_bar.set_xlabel('Number of Events', fontsize=12, fontweight='bold')
    ax_bar.set_title('Event Frequency Distribution', fontsize=13, fontweight='bold')
    ax_bar.grid(True, alpha=0.3, axis='x')
    ax_bar.invert_yaxis()
    
    plt.tight_layout()
    
    output_dir = Path('results/maps')
    plt.savefig(output_dir / 'event_frequency_table.png', 
               dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Saved: {output_dir / 'event_frequency_table.png'}")


def create_choropleth_style_visualization():
    """Create choropleth-style visualization"""
    print("Creating choropleth-style visualization...")
    
    country_stats = load_and_aggregate_by_country()
    
    # Create figure with 3 subplots (one for each asset)
    fig, axes = plt.subplots(3, 1, figsize=(18, 16))
    
    assets = ['Avg_BTC_CAR', 'Avg_GOLD_CAR', 'Avg_OIL_CAR']
    titles = ['Bitcoin - Average CAR by Country', 
             'Gold - Average CAR by Country',
             'Oil - Average CAR by Country']
    
    for idx, (asset, title) in enumerate(zip(assets, titles)):
        ax = axes[idx]
        
        # Get top 25 countries
        top25 = country_stats.nlargest(25, 'Event_Count')
        
        countries = top25.index
        values = top25[asset] * 100  # Convert to percentage
        counts = top25['Event_Count']
        
        # Create horizontal bar chart (choropleth-style)
        colors = []
        for val in values:
            if val > 2:
                colors.append('#2ECC71')  # Green (positive)
            elif val < -2:
                colors.append('#E74C3C')  # Red (negative)
            else:
                colors.append('#F39C12')  # Orange (neutral)
        
        bars = ax.barh(range(len(countries)), values, color=colors, alpha=0.8,
                      edgecolor='black', linewidth=1)
        
        # Add value labels and event counts
        for i, (bar, val, count) in enumerate(zip(bars, values, counts)):
            # Value label
            x_pos = val + (1 if val > 0 else -1)
            ax.text(x_pos, i, f'{val:+.2f}%', 
                   va='center', ha='left' if val > 0 else 'right',
                   fontsize=9, fontweight='bold')
            
            # Event count label (on the bar)
            ax.text(0, i, f'({int(count)})', 
                   va='center', ha='center',
                   fontsize=8, color='white', fontweight='bold',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
        
        ax.set_yticks(range(len(countries)))
        ax.set_yticklabels(countries, fontsize=10)
        ax.set_xlabel('Average CAR (%)', fontsize=12, fontweight='bold')
        ax.set_title(title, fontsize=13, fontweight='bold', pad=10)
        ax.axvline(x=0, color='black', linestyle='-', linewidth=2)
        ax.grid(True, alpha=0.3, axis='x')
        ax.invert_yaxis()
        
        # Add legend
        green_patch = mpatches.Patch(color='#2ECC71', label='Positive (>+2%)', alpha=0.8)
        orange_patch = mpatches.Patch(color='#F39C12', label='Neutral (-2% to +2%)', alpha=0.8)
        red_patch = mpatches.Patch(color='#E74C3C', label='Negative (<-2%)', alpha=0.8)
        ax.legend(handles=[green_patch, orange_patch, red_patch], 
                 loc='lower right', fontsize=9)
    
    plt.suptitle('Choropleth-Style Analysis: Average Asset Response by Country\n(Number in parentheses = Event Count)',
                fontsize=15, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    output_dir = Path('results/maps')
    plt.savefig(output_dir / 'choropleth_style_analysis.png', 
               dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Saved: {output_dir / 'choropleth_style_analysis.png'}")


def main():
    """Main function"""
    print("="*100)
    print("CREATING CHOROPLETH-STYLE MAPS WITH FREQUENCY TABLE")
    print("="*100)
    print()
    
    # Load and aggregate
    country_stats = load_and_aggregate_by_country()
    print(f"Aggregated data for {len(country_stats)} countries")
    print()
    
    # Save country statistics
    output_dir = Path('results/maps')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    country_stats.to_csv(output_dir / 'country_statistics.csv', encoding='utf-8-sig')
    print(f"Saved: {output_dir / 'country_statistics.csv'}")
    print()
    
    # Create frequency table plot
    create_frequency_table_plot(country_stats)
    print()
    
    # Create choropleth-style visualization
    create_choropleth_style_visualization()
    print()
    
    print("="*100)
    print("CHOROPLETH MAPS COMPLETE!")
    print("="*100)
    print()
    print("Files created:")
    print("  - results/maps/country_statistics.csv (full data)")
    print("  - results/maps/event_frequency_table.png (table + bar chart)")
    print("  - results/maps/choropleth_style_analysis.png (3 asset maps)")
    print()


if __name__ == "__main__":
    main()

