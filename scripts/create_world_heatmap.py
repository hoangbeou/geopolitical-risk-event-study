"""
Create world heatmap showing GPR events by location
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import json

try:
    import folium
    from folium.plugins import HeatMap
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    print("Warning: folium not installed. Will create static map only.")

# Country coordinates (major countries)
COUNTRY_COORDS = {
    'Afghanistan': (33.9391, 67.7100),
    'Algeria': (28.0339, 1.6596),
    'Argentina': (-38.4161, -63.6167),
    'Australia': (-25.2744, 133.7751),
    'Austria': (47.5162, 14.5501),
    'Azerbaijan': (40.1431, 47.5769),
    'Belgium': (50.5039, 4.4699),
    'Brazil': (-14.2350, -51.9253),
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
    'Mexico': (23.6345, -102.5528),
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
    
    # Extract coordinates for each event
    event_coords = []
    
    for idx, row in df.iterrows():
        locations = str(row['Detected_Locations'])
        
        if locations == 'nan' or locations == '':
            continue
        
        # Split locations
        locs = [l.strip() for l in locations.split(',')]
        
        # Get coordinates
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


def create_static_heatmap(coords_df):
    """Create static matplotlib heatmap"""
    print("Creating static world heatmap...")
    
    # Count events by location
    location_counts = coords_df.groupby('location').agg({
        'date': 'count',
        'lat': 'first',
        'lon': 'first',
        'gpr_diff': 'mean'
    }).reset_index()
    location_counts.columns = ['location', 'event_count', 'lat', 'lon', 'avg_gpr_diff']
    
    # Create figure
    fig, ax = plt.subplots(figsize=(20, 10))
    
    # Plot world map (simple scatter)
    scatter = ax.scatter(
        location_counts['lon'],
        location_counts['lat'],
        s=location_counts['event_count'] * 100,  # Size by event count
        c=location_counts['avg_gpr_diff'],  # Color by GPR magnitude
        cmap='Reds',
        alpha=0.6,
        edgecolors='black',
        linewidth=1
    )
    
    # Add labels for major locations
    for _, row in location_counts.nlargest(15, 'event_count').iterrows():
        ax.annotate(
            f"{row['location']}\n({row['event_count']})",
            xy=(row['lon'], row['lat']),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=8,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7)
        )
    
    # Formatting
    ax.set_xlabel('Longitude', fontsize=12, fontweight='bold')
    ax.set_ylabel('Latitude', fontsize=12, fontweight='bold')
    ax.set_title('GPR Events Heatmap (2015-2025)\nSize = Event Count, Color = Avg GPR Magnitude',
                fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 80)
    
    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Average GPR Diff (Magnitude)', fontsize=11)
    
    plt.tight_layout()
    
    output_dir = Path('results/maps')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_dir / 'world_heatmap_static.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Saved: {output_dir / 'world_heatmap_static.png'}")
    
    return location_counts


def create_interactive_heatmap(coords_df):
    """Create interactive folium heatmap"""
    if not FOLIUM_AVAILABLE:
        print("Folium not available. Skipping interactive map.")
        return
    
    print("Creating interactive world heatmap...")
    
    # Create base map
    world_map = folium.Map(
        location=[20, 0],
        zoom_start=2,
        tiles='OpenStreetMap'
    )
    
    # Prepare heatmap data
    heat_data = [[row['lat'], row['lon'], row['gpr_diff']/50] 
                 for _, row in coords_df.iterrows()]
    
    # Add heatmap layer
    HeatMap(heat_data, radius=15, blur=20, max_zoom=13).add_to(world_map)
    
    # Add markers for major events
    location_counts = coords_df.groupby('location').size().reset_index(name='count')
    major_locations = location_counts.nlargest(20, 'count')
    
    for _, row in coords_df.iterrows():
        if row['location'] in major_locations['location'].values:
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=5,
                popup=f"{row['location']}<br>{row['event_name'][:50]}<br>GPR: {row['gpr_diff']:.0f}",
                color='red',
                fill=True,
                fillColor='red',
                fillOpacity=0.6
            ).add_to(world_map)
    
    # Save
    output_dir = Path('results/maps')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    world_map.save(str(output_dir / 'world_heatmap_interactive.html'))
    print(f"Saved: {output_dir / 'world_heatmap_interactive.html'}")


def create_regional_summary(coords_df):
    """Create regional summary statistics"""
    print("\nCreating regional summary...")
    
    # Count by location
    location_stats = coords_df.groupby('location').agg({
        'date': 'count',
        'gpr_diff': 'mean',
        'BTC_CAR': 'mean',
        'GOLD_CAR': 'mean',
        'OIL_CAR': 'mean'
    }).round(4)
    location_stats.columns = ['Event_Count', 'Avg_GPR_Diff', 'Avg_BTC_CAR', 'Avg_GOLD_CAR', 'Avg_OIL_CAR']
    location_stats = location_stats.sort_values('Event_Count', ascending=False)
    
    # Save
    output_path = Path('results/maps/location_summary.csv')
    location_stats.to_csv(output_path, encoding='utf-8-sig')
    
    print(f"Saved: {output_path}")
    
    # Print top locations
    print("\nTop 15 Locations by Event Count:")
    print(location_stats.head(15).to_string())
    print()
    
    return location_stats


def main():
    """Main function"""
    print("="*100)
    print("CREATING WORLD HEATMAP - GPR EVENTS")
    print("="*100)
    print()
    
    # Load and process
    coords_df = load_and_process_data()
    print(f"Processed {len(coords_df)} location-event pairs")
    print(f"Unique locations: {coords_df['location'].nunique()}")
    print()
    
    # Create static heatmap
    location_counts = create_static_heatmap(coords_df)
    
    # Create interactive heatmap
    create_interactive_heatmap(coords_df)
    
    # Create summary
    location_stats = create_regional_summary(coords_df)
    
    print("="*100)
    print("WORLD HEATMAP COMPLETE!")
    print("="*100)
    print()
    print("Files created:")
    print("  - results/maps/world_heatmap_static.png")
    if FOLIUM_AVAILABLE:
        print("  - results/maps/world_heatmap_interactive.html")
    print("  - results/maps/location_summary.csv")
    print()


if __name__ == "__main__":
    main()

