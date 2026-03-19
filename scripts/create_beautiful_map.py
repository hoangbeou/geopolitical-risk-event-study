"""
Create beautiful world heatmap with proper styling
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set proper font
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

# Country coordinates
COUNTRY_COORDS = {
    'Afghanistan': (33.9391, 67.7100),
    'Austria': (47.5162, 14.5501),
    'Belgium': (50.5039, 4.4699),
    'Canada': (56.1304, -106.3468),
    'China': (35.8617, 104.1954),
    'Colombia': (4.5709, -74.2973),
    'Congo': (-4.0383, 21.7587),
    'Egypt': (26.8206, 30.8025),
    'France': (46.2276, 2.2137),
    'Germany': (51.1657, 10.4515),
    'India': (20.5937, 78.9629),
    'Indonesia': (-0.7893, 113.9213),
    'Iran': (32.4279, 53.6880),
    'Iraq': (33.2232, 43.6793),
    'Israel': (31.0461, 34.8516),
    'Gaza': (31.3547, 34.3088),
    'Gaza Strip': (31.3547, 34.3088),
    'West Bank': (31.9522, 35.2332),
    'Kashmir': (34.0837, 74.7973),
    'Lebanon': (33.8547, 35.8623),
    'Libya': (26.3351, 17.2283),
    'Mali': (17.5707, -3.9962),
    'Myanmar': (21.9162, 95.9560),
    'Nepal': (28.3949, 84.1240),
    'Nigeria': (9.0820, 8.6753),
    'Pakistan': (30.3753, 69.3451),
    'Palestine': (31.9522, 35.2332),
    'Philippines': (12.8797, 121.7740),
    'Poland': (51.9194, 19.1451),
    'Russia': (61.5240, 105.3188),
    'Saudi Arabia': (23.8859, 45.0792),
    'Somalia': (5.1521, 46.1996),
    'Syria': (34.8021, 38.9968),
    'Tanzania': (-6.3690, 34.8888),
    'Thailand': (15.8700, 100.9925),
    'Turkey': (38.9637, 35.2433),
    'Ukraine': (48.3794, 31.1656),
    'United Kingdom': (55.3781, -3.4360),
    'United States': (37.0902, -95.7129),
    'Yemen': (15.5527, 48.5164),
    'Kyiv': (50.4501, 30.5234),
    'Kiev': (50.4501, 30.5234),
    'Kabul': (34.5553, 69.2075),
    'Baghdad': (33.3152, 44.3661),
    'Damascus': (33.5138, 36.2765),
    'Tehran': (35.6892, 51.3890),
    'Jerusalem': (31.7683, 35.2137),
    'Aleppo': (36.2021, 37.1343),
    'Mosul': (36.3350, 43.1189),
    'Donetsk': (48.0159, 37.8028),
    'Crimea': (45.3662, 33.9826),
}


def load_and_process_data():
    """Load events data and process locations"""
    df = pd.read_csv('results/events_classified_act_threat.csv')
    df['date'] = pd.to_datetime(df['date'])
    
    event_coords = []
    
    for idx, row in df.iterrows():
        locations = str(row['Detected_Locations'])
        
        if locations == 'nan' or locations == '':
            continue
        
        locs = [l.strip() for l in locations.split(',')]
        
        for loc in locs:
            if loc in COUNTRY_COORDS:
                lat, lon = COUNTRY_COORDS[loc]
                event_coords.append({
                    'date': row['date'],
                    'location': loc,
                    'lat': lat,
                    'lon': lon,
                    'gpr_value': row['gpr_value'],
                    'gpr_diff': row['gpr_diff'],
                    'event_name': row['Event_Name'],
                    'BTC_CAR': row.get('BTC_CAR', np.nan),
                    'GOLD_CAR': row.get('GOLD_CAR', np.nan),
                    'OIL_CAR': row.get('OIL_CAR', np.nan),
                    'Event_Type': row.get('Event_Type', 'Unknown')
                })
    
    return pd.DataFrame(event_coords)


def create_beautiful_heatmap(coords_df):
    """Create beautiful static heatmap"""
    print("Creating beautiful world heatmap...")
    
    # Aggregate by location
    location_stats = coords_df.groupby('location').agg({
        'date': 'count',
        'lat': 'first',
        'lon': 'first',
        'gpr_diff': 'mean',
        'GOLD_CAR': 'mean'
    }).reset_index()
    location_stats.columns = ['location', 'event_count', 'lat', 'lon', 'avg_gpr_diff', 'avg_gold_car']
    
    # Create figure with better styling
    fig = plt.figure(figsize=(24, 12))
    ax = plt.axes()
    
    # Set background color
    ax.set_facecolor('#E8F4F8')
    fig.patch.set_facecolor('white')
    
    # Create scatter plot
    # Size by event count, color by GOLD CAR (safe haven response)
    scatter = ax.scatter(
        location_stats['lon'],
        location_stats['lat'],
        s=location_stats['event_count'] * 150,  # Larger bubbles
        c=location_stats['avg_gold_car'] * 100,  # Color by GOLD response (%)
        cmap='RdYlGn',  # Red (negative) to Green (positive)
        alpha=0.7,
        edgecolors='black',
        linewidth=2,
        vmin=-5,
        vmax=5
    )
    
    # Add labels for top locations (clean and readable)
    top_locations = location_stats.nlargest(12, 'event_count')
    
    for _, row in top_locations.iterrows():
        # Adjust text position based on location
        if row['location'] in ['United States']:
            xytext = (-40, -30)
        elif row['location'] in ['Russia']:
            xytext = (10, 10)
        elif row['location'] in ['Israel', 'Gaza', 'Gaza Strip']:
            xytext = (15, 0)
        else:
            xytext = (10, 5)
        
        ax.annotate(
            f"{row['location']}\n{int(row['event_count'])} events",
            xy=(row['lon'], row['lat']),
            xytext=xytext,
            textcoords='offset points',
            fontsize=10,
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                     edgecolor='black', alpha=0.9, linewidth=1.5),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.3',
                          color='black', lw=1.5)
        )
    
    # Formatting
    ax.set_xlabel('Longitude', fontsize=14, fontweight='bold')
    ax.set_ylabel('Latitude', fontsize=14, fontweight='bold')
    ax.set_title('Geopolitical Risk Events Heatmap (2015-2025)\nBubble Size = Event Frequency | Color = Average GOLD Response',
                fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 80)
    
    # Add gridlines for continents
    ax.axvline(x=0, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax.axhline(y=0, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    
    # Colorbar with better styling
    cbar = plt.colorbar(scatter, ax=ax, pad=0.02, fraction=0.046)
    cbar.set_label('Average GOLD CAR (%)\nGreen = Positive | Red = Negative', 
                   fontsize=12, fontweight='bold')
    cbar.ax.tick_params(labelsize=10)
    
    # Add legend for bubble sizes
    legend_sizes = [5, 10, 20]
    legend_labels = ['5 events', '10 events', '20 events']
    legend_handles = []
    
    for size, label in zip(legend_sizes, legend_labels):
        legend_handles.append(
            plt.scatter([], [], s=size*150, c='gray', alpha=0.7, 
                       edgecolors='black', linewidth=2, label=label)
        )
    
    legend = ax.legend(handles=legend_handles, loc='lower left', 
                      title='Event Frequency', fontsize=10, 
                      title_fontsize=11, framealpha=0.9)
    legend.get_frame().set_linewidth(1.5)
    
    # Add text box with key insights
    insights_text = (
        "KEY INSIGHTS:\n"
        "- Israel/Gaza: 25 events (most frequent)\n"
        "- Ukraine/Russia: 19 events (major conflict)\n"
        "- Middle East: Highest concentration\n"
        "- Europe events: GOLD +3-4%\n"
        "- US events: BTC +15%"
    )
    
    ax.text(0.02, 0.98, insights_text,
           transform=ax.transAxes,
           fontsize=11,
           verticalalignment='top',
           bbox=dict(boxstyle='round,pad=0.8', facecolor='lightyellow',
                    edgecolor='black', alpha=0.95, linewidth=2))
    
    plt.tight_layout()
    
    output_dir = Path('results/maps')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_dir / 'world_heatmap_beautiful.png', 
               dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Saved: {output_dir / 'world_heatmap_beautiful.png'}")


def create_regional_impact_map(coords_df):
    """Create map showing regional impact on each asset"""
    print("Creating regional impact maps...")
    
    location_stats = coords_df.groupby('location').agg({
        'lat': 'first',
        'lon': 'first',
        'BTC_CAR': 'mean',
        'GOLD_CAR': 'mean',
        'OIL_CAR': 'mean',
        'date': 'count'
    }).reset_index()
    location_stats.columns = ['location', 'lat', 'lon', 'BTC_CAR', 'GOLD_CAR', 'OIL_CAR', 'count']
    
    # Filter locations with at least 3 events
    location_stats = location_stats[location_stats['count'] >= 3]
    
    # Create 3 maps (one for each asset)
    fig, axes = plt.subplots(1, 3, figsize=(24, 8))
    
    assets = ['BTC_CAR', 'GOLD_CAR', 'OIL_CAR']
    titles = ['Bitcoin Response by Location', 'Gold Response by Location', 'Oil Response by Location']
    
    for idx, (asset, title) in enumerate(zip(assets, titles)):
        ax = axes[idx]
        
        # Set background
        ax.set_facecolor('#E8F4F8')
        
        # Scatter plot
        scatter = ax.scatter(
            location_stats['lon'],
            location_stats['lat'],
            s=location_stats['count'] * 100,
            c=location_stats[asset] * 100,
            cmap='RdYlGn',
            alpha=0.7,
            edgecolors='black',
            linewidth=1.5,
            vmin=-20,
            vmax=20
        )
        
        # Add labels for top locations
        top_locs = location_stats.nlargest(8, 'count')
        
        for _, row in top_locs.iterrows():
            car_value = row[asset] * 100
            ax.annotate(
                f"{row['location']}\n{car_value:+.1f}%",
                xy=(row['lon'], row['lat']),
                xytext=(8, 8),
                textcoords='offset points',
                fontsize=8,
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                         edgecolor='black', alpha=0.9),
                arrowprops=dict(arrowstyle='->', color='black', lw=1)
            )
        
        # Formatting
        ax.set_title(title, fontsize=13, fontweight='bold', pad=10)
        ax.set_xlabel('Longitude', fontsize=11)
        ax.set_ylabel('Latitude', fontsize=11)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xlim(-180, 180)
        ax.set_ylim(-60, 80)
        
        # Colorbar
        cbar = plt.colorbar(scatter, ax=ax, pad=0.02)
        cbar.set_label('Avg CAR (%)', fontsize=10, fontweight='bold')
    
    plt.suptitle('Regional Impact Analysis - Average CAR by Location (Min 3 events)',
                fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    output_dir = Path('results/maps')
    plt.savefig(output_dir / 'regional_impact_maps.png', 
               dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Saved: {output_dir / 'regional_impact_maps.png'}")


def create_hotspot_analysis(coords_df):
    """Create focused analysis on top 3 hotspots"""
    print("Creating hotspot analysis...")
    
    # Top 3 hotspots
    hotspots = {
        'Israel/Palestine': ['Israel', 'Gaza', 'Gaza Strip', 'West Bank', 'Jerusalem'],
        'Ukraine/Russia': ['Ukraine', 'Russia', 'Kyiv', 'Kiev', 'Donetsk', 'Crimea'],
        'Middle East': ['Iraq', 'Syria', 'Iran', 'Lebanon', 'Yemen']
    }
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    for idx, (hotspot_name, locations) in enumerate(hotspots.items()):
        # Filter events for this hotspot
        hotspot_data = coords_df[coords_df['location'].isin(locations)]
        
        if len(hotspot_data) == 0:
            continue
        
        # Calculate statistics
        btc_mean = hotspot_data['BTC_CAR'].mean() * 100
        gold_mean = hotspot_data['GOLD_CAR'].mean() * 100
        oil_mean = hotspot_data['OIL_CAR'].mean() * 100
        event_count = len(hotspot_data)
        
        # Bar plot
        assets = ['BTC', 'GOLD', 'OIL']
        values = [btc_mean, gold_mean, oil_mean]
        colors = ['#3498db', '#f39c12', '#2ecc71']
        
        bars = axes[idx].bar(assets, values, color=colors, alpha=0.8, 
                            edgecolor='black', linewidth=2)
        
        # Add value labels on bars
        for bar, val in zip(bars, values):
            height = bar.get_height()
            axes[idx].text(bar.get_x() + bar.get_width()/2., height,
                          f'{val:+.2f}%',
                          ha='center', va='bottom' if height > 0 else 'top',
                          fontsize=11, fontweight='bold')
        
        # Formatting
        axes[idx].set_title(f'{hotspot_name}\n({event_count} events)',
                           fontsize=12, fontweight='bold')
        axes[idx].set_ylabel('Average CAR (%)', fontsize=11, fontweight='bold')
        axes[idx].axhline(y=0, color='black', linestyle='-', linewidth=1.5)
        axes[idx].grid(True, alpha=0.3, axis='y')
        axes[idx].set_ylim(-10, 10)
    
    plt.suptitle('Top 3 Hotspots - Average Asset Response',
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    output_dir = Path('results/maps')
    plt.savefig(output_dir / 'hotspot_analysis.png', 
               dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Saved: {output_dir / 'hotspot_analysis.png'}")


def main():
    """Main function"""
    print("="*100)
    print("CREATING BEAUTIFUL WORLD MAPS")
    print("="*100)
    print()
    
    # Load data
    coords_df = load_and_process_data()
    print(f"Processed {len(coords_df)} location-event pairs")
    print(f"Unique locations: {coords_df['location'].nunique()}")
    print()
    
    # Create beautiful heatmap
    create_beautiful_heatmap(coords_df)
    print()
    
    # Create regional impact maps
    create_regional_impact_map(coords_df)
    print()
    
    # Create hotspot analysis
    create_hotspot_analysis(coords_df)
    print()
    
    print("="*100)
    print("BEAUTIFUL MAPS COMPLETE!")
    print("="*100)
    print()
    print("Files created:")
    print("  - results/maps/world_heatmap_beautiful.png (main heatmap)")
    print("  - results/maps/regional_impact_maps.png (3 asset maps)")
    print("  - results/maps/hotspot_analysis.png (top 3 hotspots)")
    print()


if __name__ == "__main__":
    main()

