"""
Create true choropleth map - color countries by event frequency
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

try:
    import folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    print("ERROR: folium not installed!")
    print("Install: pip install folium")
    exit(1)

# Country name mapping to match GeoJSON
COUNTRY_MAPPING = {
    'United States': 'United States of America',
    'USA': 'United States of America',
    'UK': 'United Kingdom',
    'United Kingdom': 'United Kingdom',
    'Russia': 'Russia',
    'Ukraine': 'Ukraine',
    'Syria': 'Syria',
    'Iraq': 'Iraq',
    'Iran': 'Iran',
    'Israel': 'Israel',
    'Palestine': 'Palestine',
    'Gaza': 'Palestine',
    'Gaza Strip': 'Palestine',
    'West Bank': 'Palestine',
    'Lebanon': 'Lebanon',
    'Afghanistan': 'Afghanistan',
    'Pakistan': 'Pakistan',
    'India': 'India',
    'China': 'China',
    'France': 'France',
    'Germany': 'Germany',
    'Turkey': 'Turkey',
    'Yemen': 'Yemen',
    'Saudi Arabia': 'Saudi Arabia',
    'Libya': 'Libya',
    'Egypt': 'Egypt',
    'Nigeria': 'Nigeria',
    'Somalia': 'Somalia',
    'Congo': 'Democratic Republic of the Congo',
    'Myanmar': 'Myanmar',
    'Thailand': 'Thailand',
    'Philippines': 'Philippines',
    'Indonesia': 'Indonesia',
    'Australia': 'Australia',
    'Poland': 'Poland',
    'Belgium': 'Belgium',
    'Austria': 'Austria',
    'Colombia': 'Colombia',
    'Mexico': 'Mexico',
    'Canada': 'Canada',
    'Brazil': 'Brazil',
    # Cities map to countries
    'Kyiv': 'Ukraine',
    'Kiev': 'Ukraine',
    'Donetsk': 'Ukraine',
    'Crimea': 'Ukraine',
    'Kashmir': 'India',
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
    
    country_data = []
    
    for idx, row in df.iterrows():
        locations = str(row['Detected_Locations'])
        
        if locations == 'nan' or locations == '':
            continue
        
        locs = [l.strip() for l in locations.split(',')]
        
        for loc in locs:
            # Map to standard country name
            country = COUNTRY_MAPPING.get(loc, loc)
            
            country_data.append({
                'country': country,
                'date': row['date'],
                'event_name': row['Event_Name'],
                'gpr_diff': row['gpr_diff'],
                'BTC_CAR': row.get('BTC_CAR', np.nan),
                'GOLD_CAR': row.get('GOLD_CAR', np.nan),
                'OIL_CAR': row.get('OIL_CAR', np.nan),
            })
    
    country_df = pd.DataFrame(country_data)
    
    # Aggregate
    country_stats = country_df.groupby('country').agg({
        'date': 'count',
        'gpr_diff': 'mean',
        'BTC_CAR': 'mean',
        'GOLD_CAR': 'mean',
        'OIL_CAR': 'mean'
    }).round(4)
    
    country_stats.columns = ['Event_Count', 'Avg_GPR_Diff', 'Avg_BTC_CAR', 'Avg_GOLD_CAR', 'Avg_OIL_CAR']
    
    return country_stats


def create_choropleth_map(country_stats):
    """Create interactive choropleth map"""
    print("Creating interactive choropleth map...")
    
    # Load world GeoJSON (use built-in or download)
    # For simplicity, use folium's built-in world data
    
    # Create base map
    m = folium.Map(
        location=[30, 20],
        zoom_start=2,
        tiles='CartoDB positron',
        width='100%',
        height='100%'
    )
    
    # Prepare data for choropleth
    # Convert to dict for folium
    country_dict = country_stats['Event_Count'].to_dict()
    
    # Download world geojson if not exists
    geojson_path = Path('data/raw/world-countries.json')
    
    if not geojson_path.exists():
        print("Downloading world countries GeoJSON...")
        import requests
        url = 'https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson'
        response = requests.get(url)
        geojson_path.parent.mkdir(parents=True, exist_ok=True)
        with open(geojson_path, 'w') as f:
            f.write(response.text)
        print(f"Downloaded to {geojson_path}")
    
    # Load GeoJSON
    with open(geojson_path, 'r', encoding='utf-8') as f:
        world_geo = json.load(f)
    
    # Prepare data as DataFrame with country name as column
    choropleth_data = country_stats.reset_index()
    choropleth_data.columns = ['country', 'Event_Count', 'Avg_GPR_Diff', 'Avg_BTC_CAR', 'Avg_GOLD_CAR', 'Avg_OIL_CAR']
    
    # Create choropleth
    folium.Choropleth(
        geo_data=world_geo,
        name='GPR Events',
        data=choropleth_data,
        columns=['country', 'Event_Count'],
        key_on='feature.properties.name',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.3,
        legend_name='Number of GPR Events (2015-2025)',
        nan_fill_color='lightgray',
        nan_fill_opacity=0.3
    ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add title
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 500px; height: 90px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:16px; padding: 10px">
    <b>GPR Events Choropleth Map (2015-2025)</b><br>
    Color intensity = Event frequency<br>
    Darker = More events
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Save
    output_dir = Path('results/maps')
    output_path = output_dir / 'choropleth_interactive.html'
    m.save(str(output_path))
    
    print(f"Saved: {output_path}")
    print(f"Open in browser to view interactive map!")


def create_multiple_choropleths():
    """Create separate choropleth for each asset"""
    print("Creating asset-specific choropleth maps...")
    
    country_stats = load_and_aggregate_by_country()
    geojson_path = Path('data/raw/world-countries.json')
    
    if not geojson_path.exists():
        print("GeoJSON not found. Run main choropleth first.")
        return
    
    with open(geojson_path, 'r', encoding='utf-8') as f:
        world_geo = json.load(f)
    
    assets = ['Avg_BTC_CAR', 'Avg_GOLD_CAR', 'Avg_OIL_CAR']
    names = ['Bitcoin', 'Gold', 'Oil']
    
    for asset, name in zip(assets, names):
        # Create map
        m = folium.Map(
            location=[30, 20],
            zoom_start=2,
            tiles='CartoDB positron'
        )
        
        # Prepare data (convert to percentage)
        asset_data = country_stats.reset_index()
        asset_data.columns = ['country', 'Event_Count', 'Avg_GPR_Diff', 'Avg_BTC_CAR', 'Avg_GOLD_CAR', 'Avg_OIL_CAR']
        asset_data[asset] = asset_data[asset] * 100  # To percentage
        
        # Create choropleth
        folium.Choropleth(
            geo_data=world_geo,
            name=f'{name} Response',
            data=asset_data,
            columns=['country', asset],
            key_on='feature.properties.name',
            fill_color='RdYlGn',  # Red-Yellow-Green
            fill_opacity=0.7,
            line_opacity=0.3,
            legend_name=f'{name} Average CAR (%)',
            nan_fill_color='lightgray',
            nan_fill_opacity=0.3
        ).add_to(m)
        
        # Add title
        title_html = f'''
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 400px; height: 80px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:16px; padding: 10px">
        <b>{name} Response to GPR Events</b><br>
        Green = Positive CAR | Red = Negative CAR
        </div>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # Save
        output_dir = Path('results/maps')
        output_path = output_dir / f'choropleth_{name.lower()}.html'
        m.save(str(output_path))
        
        print(f"Saved: {output_path}")


def main():
    """Main function"""
    print("="*100)
    print("CREATING TRUE CHOROPLETH MAPS")
    print("="*100)
    print()
    
    if not FOLIUM_AVAILABLE:
        return
    
    # Aggregate data
    country_stats = load_and_aggregate_by_country()
    print(f"Aggregated {len(country_stats)} countries")
    print()
    
    # Create main choropleth (event frequency)
    create_choropleth_map(country_stats)
    print()
    
    # Create asset-specific choropleths
    create_multiple_choropleths()
    print()
    
    print("="*100)
    print("CHOROPLETH MAPS COMPLETE!")
    print("="*100)
    print()
    print("Files created:")
    print("  - results/maps/choropleth_interactive.html (event frequency)")
    print("  - results/maps/choropleth_bitcoin.html (BTC response)")
    print("  - results/maps/choropleth_gold.html (GOLD response)")
    print("  - results/maps/choropleth_oil.html (OIL response)")
    print()
    print("Open HTML files in browser to view interactive maps!")
    print()


if __name__ == "__main__":
    main()

