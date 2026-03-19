"""
Tạo các visualizations nâng cao cho khóa luận:
1. Annotated Time Series với Wiki events
2. Word Cloud từ Wiki_Content
3. Geospatial Heatmap từ Region data
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from wordcloud import WordCloud
try:
    import folium
    from folium.plugins import HeatMap
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
from pathlib import Path
import re
import random
import json
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Set style
try:
    plt.style.use('seaborn-v0_8-darkgrid')
except:
    plt.style.use('seaborn-darkgrid')

class AdvancedVisualizations:
    def __init__(self, output_dir='results/advanced_visualizations'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if not FOLIUM_AVAILABLE:
            print("Warning: folium not installed. Interactive heatmap will be skipped.")
        
    def create_annotated_timeseries(self, data_path='data/data.csv', 
                                    events_path='ket_qua_wiki_with_regions.csv'):
        """
        1. Annotated Time Series với Wiki events
        Vẽ giá tài sản và đánh dấu các events từ Wiki
        """
        print("="*70)
        print("1. TẠO ANNOTATED TIME SERIES")
        print("="*70)
        
        # Load data
        print("\nLoading data...")
        data = pd.read_csv(data_path, index_col=0)
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index, dayfirst=True, errors='coerce')
        
        # Load events
        events_df = pd.read_csv(events_path)
        events_df['Date'] = pd.to_datetime(events_df['Date'], dayfirst=True, errors='coerce')
        
        # Filter out invalid dates
        events_df = events_df.dropna(subset=['Date'])
        
        if len(events_df) == 0:
            print("  Warning: No valid events found")
            return
        
        # Filter data range
        start_date = events_df['Date'].min()
        end_date = events_df['Date'].max()
        
        if pd.isna(start_date) or pd.isna(end_date):
            print("  Warning: Invalid date range")
            return
        
        data = data[(data.index >= start_date) & (data.index <= end_date)]
        
        print(f"  Data range: {start_date.date()} to {end_date.date()}")
        print(f"  Number of events: {len(events_df)}")
        
        # Create figure với 3 subplots cho 3 assets
        fig, axes = plt.subplots(3, 1, figsize=(18, 12))
        assets = ['BTC', 'GOLD', 'OIL']
        colors = ['#f39c12', '#f1c40f', '#e74c3c']
        
        for idx, asset in enumerate(assets):
            ax = axes[idx]
            
            if asset not in data.columns:
                ax.text(0.5, 0.5, f'No data for {asset}', 
                       ha='center', va='center', transform=ax.transAxes)
                continue
            
            # Normalize prices để dễ so sánh (base = 100 tại ngày đầu)
            prices = data[asset].dropna()
            if len(prices) == 0:
                continue
            
            normalized_prices = (prices / prices.iloc[0]) * 100
            
            # Plot price line
            ax.plot(normalized_prices.index, normalized_prices.values,
                   linewidth=1.5, color=colors[idx], alpha=0.7, label=f'{asset} Price')
            
            # Add vertical lines for events
            for _, event in events_df.iterrows():
                event_date = event['Date']
                if pd.isna(event_date):
                    continue
                # Check if event_date is within the data range
                if normalized_prices.index.min() <= event_date <= normalized_prices.index.max():
                    # Color based on region
                    region = event.get('Region', 'UNKNOWN')
                    if region == 'Middle East':
                        color = '#e74c3c'  # Red
                        alpha = 0.6
                    elif region == 'Russia/CIS':
                        color = '#3498db'  # Blue
                        alpha = 0.6
                    elif region == 'Europe':
                        color = '#9b59b6'  # Purple
                        alpha = 0.6
                    else:
                        color = '#95a5a6'  # Gray
                        alpha = 0.3
                    
                    ax.axvline(x=event_date, color=color, linestyle='--', 
                             linewidth=1, alpha=alpha)
            
            # Formatting
            ax.set_title(f'{asset} Price với GPR Events (Annotated)', 
                        fontsize=14, fontweight='bold')
            ax.set_ylabel('Normalized Price (Base=100)', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper left')
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            ax.xaxis.set_major_locator(mdates.YearLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Add legend for event types
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color='#e74c3c', linestyle='--', linewidth=2, label='Middle East Events'),
            Line2D([0], [0], color='#3498db', linestyle='--', linewidth=2, label='Russia/CIS Events'),
            Line2D([0], [0], color='#9b59b6', linestyle='--', linewidth=2, label='Europe Events'),
            Line2D([0], [0], color='#95a5a6', linestyle='--', linewidth=2, label='Other Events')
        ]
        fig.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98))
        
        plt.suptitle('Annotated Time Series: Asset Prices với GPR Events', 
                    fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        
        output_path = self.output_dir / 'annotated_timeseries.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"\n✓ Saved: {output_path}")
        plt.close()
        
        # Create zoomed version for key periods
        self._create_zoomed_timeseries(data, events_df, assets, colors)
    
    def _create_zoomed_timeseries(self, data, events_df, assets, colors):
        """Tạo zoomed version cho các giai đoạn quan trọng"""
        print("\nCreating zoomed versions for key periods...")
        
        key_periods = [
            ('2022-02-01', '2022-04-30', 'Ukraine War Period'),
            ('2023-10-01', '2023-12-31', 'Israel-Palestine Escalation'),
            ('2020-01-01', '2020-06-30', 'COVID-19 Early Period')
        ]
        
        for start, end, title in key_periods:
            fig, axes = plt.subplots(3, 1, figsize=(16, 10))
            period_data = data[(data.index >= start) & (data.index <= end)]
            period_events = events_df[(events_df['Date'] >= start) & (events_df['Date'] <= end)]
            
            for idx, asset in enumerate(assets):
                ax = axes[idx]
                if asset not in period_data.columns:
                    continue
                
                prices = period_data[asset].dropna()
                if len(prices) == 0:
                    continue
        
                normalized_prices = (prices / prices.iloc[0]) * 100
                ax.plot(normalized_prices.index, normalized_prices.values,
                       linewidth=2, color=colors[idx], label=f'{asset}')
                
                # Add events
                for _, event in period_events.iterrows():
                    event_date = event['Date']
                    if pd.isna(event_date):
                        continue
                    # Check if event_date is within the data range
                    if normalized_prices.index.min() <= event_date <= normalized_prices.index.max():
                        region = event.get('Region', 'UNKNOWN')
                        if region == 'Middle East':
                            color = '#e74c3c'
                        elif region == 'Russia/CIS':
                            color = '#3498db'
                        else:
                            color = '#95a5a6'
                        ax.axvline(x=event_date, color=color, linestyle='--', 
                                 linewidth=2, alpha=0.7)
                        # Add annotation
                        ax.annotate(f"Event {event['Event_Number']}", 
                                  xy=(event_date, normalized_prices.loc[event_date]),
                                  xytext=(5, 5), textcoords='offset points',
                                  fontsize=8, alpha=0.7)
                
                ax.set_title(f'{asset} - {title}', fontsize=12, fontweight='bold')
                ax.set_ylabel('Normalized Price', fontsize=10)
                ax.grid(True, alpha=0.3)
                ax.legend()
            
            plt.suptitle(f'Zoomed View: {title}', fontsize=14, fontweight='bold')
            plt.tight_layout()
            
            filename = f'annotated_timeseries_{title.replace(" ", "_").lower()}.png'
            output_path = self.output_dir / filename
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"  ✓ Saved: {filename}")
            plt.close()
    
    def create_wordcloud(self, events_path='ket_qua_wiki_with_regions.csv'):
        """
        2. Word Cloud từ Wiki_Content
        Phân loại loại hình xung đột phổ biến nhất
        """
        print("\n" + "="*70)
        print("2. TẠO WORD CLOUD")
        print("="*70)
        
        # Load events
        print("\nLoading Wiki content...")
        events_df = pd.read_csv(events_path)
        
        # Check if Wiki_Content column exists
        if 'Wiki_Content' not in events_df.columns:
            print("  Warning: 'Wiki_Content' column not found")
            return
        
        # Combine all Wiki_Content
        all_text = ' '.join(events_df['Wiki_Content'].dropna().astype(str))
        
        if len(all_text.strip()) == 0:
            print("  Warning: No Wiki content found")
            return
        
        # Clean text: remove citations [x], parentheses, special chars
        all_text = re.sub(r'\[.*?\]', '', all_text)  # Remove citations
        all_text = re.sub(r'\(.*?\)', '', all_text)  # Remove parentheses
        all_text = re.sub(r'[^\w\s]', ' ', all_text)  # Keep only words and spaces
        all_text = re.sub(r'\s+', ' ', all_text)  # Multiple spaces to single
        
        print(f"  Total words: {len(all_text.split())}")
        
        # Create word cloud
        wordcloud = WordCloud(
            width=1600,
            height=800,
            background_color='white',
            max_words=200,
            colormap='Reds',
            relative_scaling=0.5,
            random_state=42
        ).generate(all_text)
        
        # Plot
        fig, ax = plt.subplots(figsize=(20, 10))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title('Word Cloud: Loại hình Xung đột Địa chính trị (2015-2025)', 
                    fontsize=18, fontweight='bold', pad=20)
        
        plt.tight_layout()
        output_path = self.output_dir / 'wordcloud_wiki_content.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"\n✓ Saved: {output_path}")
        plt.close()
        
        # Create word cloud by region
        self._create_wordcloud_by_region(events_df)
        
        # Analyze top keywords
        self._analyze_keywords(all_text)
    
    def _create_wordcloud_by_region(self, events_df):
        """Tạo word cloud riêng cho từng region"""
        print("\nCreating word clouds by region...")
        
        regions = ['Middle East', 'Russia/CIS', 'Europe', 'Asia', 'Africa']
        
        for region in regions:
            region_events = events_df[events_df['Region'] == region]
            if len(region_events) == 0:
                continue
        
            all_text = ' '.join(region_events['Wiki_Content'].dropna().astype(str))
            all_text = re.sub(r'\[.*?\]', '', all_text)
            all_text = re.sub(r'\(.*?\)', '', all_text)
            all_text = re.sub(r'[^\w\s]', ' ', all_text)
            all_text = re.sub(r'\s+', ' ', all_text)
            
            wordcloud = WordCloud(
                width=1200,
                height=600,
                background_color='white',
                max_words=100,
                colormap='Reds',
                relative_scaling=0.5
            ).generate(all_text)
            
            fig, ax = plt.subplots(figsize=(14, 7))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            ax.set_title(f'Word Cloud: {region} Events', 
                        fontsize=16, fontweight='bold')
            
            plt.tight_layout()
            filename = f'wordcloud_{region.replace("/", "_").replace(" ", "_").lower()}.png'
            output_path = self.output_dir / filename
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"  ✓ Saved: {filename}")
            plt.close()
    
    def _analyze_keywords(self, text):
        """Phân tích top keywords"""
        words = text.lower().split()
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                     'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'are',
                     'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do',
                     'does', 'did', 'will', 'would', 'could', 'should', 'may',
                     'might', 'can', 'this', 'that', 'these', 'those', 'it',
                     'its', 'they', 'them', 'their', 'there', 'then', 'than'}
        
        words = [w for w in words if w not in stop_words and len(w) > 3]
        
        word_freq = Counter(words)
        top_words = word_freq.most_common(30)
        
        # Save to file
        with open(self.output_dir / 'top_keywords.txt', 'w', encoding='utf-8') as f:
            f.write("TOP 30 KEYWORDS TỪ WIKI CONTENT\n")
            f.write("="*50 + "\n\n")
            for word, count in top_words:
                f.write(f"{word:20s}: {count:4d}\n")
        
        print(f"  ✓ Saved: top_keywords.txt")
    
    def create_geospatial_heatmap(self, events_path='ket_qua_wiki_with_regions.csv'):
        """
        3. Geospatial Heatmap từ Region data
        Chấm các điểm nóng lên bản đồ thế giới
        """
        print("\n" + "="*70)
        print("3. TẠO GEOSPATIAL HEATMAP")
        print("="*70)
        
        # Load events
        print("\nLoading events with regions...")
        events_df = pd.read_csv(events_path)
        events_df['Date'] = pd.to_datetime(events_df['Date'], dayfirst=True, errors='coerce')
        
        # Region to coordinates mapping
        region_coords = {
            'Middle East': {'lat': 25.0, 'lon': 45.0, 'name': 'Middle East'},
            'Russia/CIS': {'lat': 55.0, 'lon': 37.6, 'name': 'Russia/CIS'},
            'Europe': {'lat': 50.0, 'lon': 10.0, 'name': 'Europe'},
            'Asia': {'lat': 35.0, 'lon': 105.0, 'name': 'Asia'},
            'Africa': {'lat': 0.0, 'lon': 20.0, 'name': 'Africa'},
            'Americas': {'lat': 40.0, 'lon': -100.0, 'name': 'Americas'}
        }
        
        # Prepare heatmap data
        heat_data = []
        region_counts = {}
        
        for _, event in events_df.iterrows():
            region = event.get('Region', 'UNKNOWN')
            if region in region_coords:
                coords = region_coords[region]
                heat_data.append([coords['lat'], coords['lon']])
                region_counts[region] = region_counts.get(region, 0) + 1
        
        if len(heat_data) == 0:
            print("  Warning: No valid region data for heatmap")
            return
        
        print(f"  Total events mapped: {len(heat_data)}")
        print(f"  Region distribution:")
        for region, count in sorted(region_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"    {region:20s}: {count:3d} events")
        
        # Create interactive map if folium available
        if FOLIUM_AVAILABLE:
            # Create base map with world map tiles
            world_map = folium.Map(
                location=[20, 0],
                zoom_start=2,
                tiles='CartoDB positron'  # Clean world map style
            )
            
            # Add heatmap layer
            HeatMap(heat_data, radius=20, blur=15, max_zoom=1, 
                   gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1: 'red'}).add_to(world_map)
            
            # Add markers for each region with size based on count
            for region, coords in region_coords.items():
                if region in region_counts:
                    count = region_counts[region]
                    # Calculate marker size (min 10, max 50)
                    marker_size = max(10, min(50, count * 3))
                    
                    folium.CircleMarker(
                        location=[coords['lat'], coords['lon']],
                        radius=marker_size,
                        popup=folium.Popup(
                            f"<b>{region}</b><br>Events: {count}",
                            max_width=200
                        ),
                        tooltip=f"{region}: {count} events",
                        color='darkred',
                        fill=True,
                        fillColor='red',
                        fillOpacity=0.7,
                        weight=2
                    ).add_to(world_map)
                    
                    # Add text label
                    folium.Marker(
                        location=[coords['lat'], coords['lon']],
                        icon=folium.DivIcon(
                            html=f'<div style="font-size: 12px; font-weight: bold; color: black; text-shadow: 1px 1px 2px white;">{region}<br>{count}</div>',
                            icon_size=(100, 30),
                            icon_anchor=(50, 15)
                        )
                    ).add_to(world_map)
            
            # Save interactive map
            output_path = self.output_dir / 'geospatial_heatmap.html'
            world_map.save(str(output_path))
            print(f"\n✓ Saved interactive map: {output_path}")
            
            # Also create a static version using folium screenshot (if possible)
            # For now, we'll use the improved matplotlib version
        
        # Create static version using matplotlib
        self._create_static_heatmap(region_counts, region_coords)
    
    def _create_static_heatmap(self, region_counts, region_coords):
        """Tạo static heatmap bằng matplotlib với bản đồ thế giới"""
        print("\nCreating static heatmap with world map...")
        
        fig, ax = plt.subplots(figsize=(18, 9))
        
        # Set world map bounds
        ax.set_xlim(-180, 180)
        ax.set_ylim(-90, 90)
        ax.set_aspect('equal')
        
        # Draw simple world map background
        # Draw continents as simple rectangles/regions
        # This is a simplified representation
        ax.add_patch(plt.Rectangle((-180, -90), 360, 180, 
                                   facecolor='#e8f4f8', edgecolor='none', zorder=0))
        
        # Draw major landmasses (simplified)
        # North America
        ax.add_patch(plt.Rectangle((-170, 15), 60, 50, 
                                   facecolor='#f0f0f0', edgecolor='#999', linewidth=0.5, zorder=1))
        # South America
        ax.add_patch(plt.Rectangle((-85, -55), 35, 70, 
                                   facecolor='#f0f0f0', edgecolor='#999', linewidth=0.5, zorder=1))
        # Europe
        ax.add_patch(plt.Rectangle((-10, 35), 40, 30, 
                                   facecolor='#f0f0f0', edgecolor='#999', linewidth=0.5, zorder=1))
        # Africa
        ax.add_patch(plt.Rectangle((-20, -35), 50, 70, 
                                   facecolor='#f0f0f0', edgecolor='#999', linewidth=0.5, zorder=1))
        # Asia
        ax.add_patch(plt.Rectangle((30, 10), 90, 50, 
                                   facecolor='#f0f0f0', edgecolor='#999', linewidth=0.5, zorder=1))
        # Australia
        ax.add_patch(plt.Rectangle((110, -45), 40, 30, 
                                   facecolor='#f0f0f0', edgecolor='#999', linewidth=0.5, zorder=1))
        
        # Draw grid lines
        ax.grid(True, linestyle='--', alpha=0.3, color='gray', linewidth=0.5)
        ax.set_xticks(range(-180, 181, 30))
        ax.set_yticks(range(-90, 91, 30))
        
        # Plot regions with size based on event count
        max_count = max(region_counts.values()) if region_counts else 1
        
        for region, coords in region_coords.items():
            if region in region_counts:
                count = region_counts[region]
                # Normalize size (min 200, max 2000)
                size = 200 + (count / max_count) * 1800
                
                # Color intensity based on count
                intensity = count / max_count
                color = plt.cm.Reds(0.3 + intensity * 0.5)
                
                # Plot marker
                ax.scatter(coords['lon'], coords['lat'], 
                          s=size, alpha=0.7, c=[color], 
                          edgecolors='darkred', linewidth=2.5, zorder=3)
                
                # Add label with count
                ax.annotate(f"{region}\n{count} events", 
                          xy=(coords['lon'], coords['lat']),
                          xytext=(10, 10), textcoords='offset points',
                          fontsize=11, fontweight='bold',
                          bbox=dict(boxstyle='round,pad=0.5', 
                                   facecolor='white', alpha=0.9,
                                   edgecolor='darkred', linewidth=2),
                          zorder=4)
        
        ax.set_title('Geospatial Heatmap: GPR Events by Region (2015-2025)', 
                    fontsize=18, fontweight='bold', pad=20)
        ax.set_xlabel('Longitude', fontsize=14, fontweight='bold')
        ax.set_ylabel('Latitude', fontsize=14, fontweight='bold')
        
        # Add legend
        legend_elements = [
            plt.scatter([], [], s=200, c='red', alpha=0.7, edgecolors='darkred', 
                       label='Low events (1-5)'),
            plt.scatter([], [], s=1000, c='red', alpha=0.7, edgecolors='darkred', 
                       label='Medium events (6-15)'),
            plt.scatter([], [], s=2000, c='red', alpha=0.7, edgecolors='darkred', 
                       label='High events (16+)')
        ]
        ax.legend(handles=legend_elements, loc='lower left', fontsize=10, framealpha=0.9)
        
        plt.tight_layout()
        output_path = self.output_dir / 'geospatial_heatmap_static.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"  ✓ Saved: geospatial_heatmap_static.png")
        plt.close()
        
        # Create bar chart by region
        fig, ax = plt.subplots(figsize=(12, 6))
        regions = list(region_counts.keys())
        counts = list(region_counts.values())
        colors_map = plt.cm.Reds(np.linspace(0.4, 0.9, len(regions)))
        
        bars = ax.bar(regions, counts, color=colors_map, edgecolor='black', linewidth=1.5)
        ax.set_title('Số lượng GPR Events theo Region', fontsize=14, fontweight='bold')
        ax.set_ylabel('Số lượng Events', fontsize=12)
        ax.set_xlabel('Region', fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{count}',
                   ha='center', va='bottom', fontweight='bold')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        output_path = self.output_dir / 'region_event_counts.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: region_event_counts.png")
        plt.close()

    def create_country_level_heatmap(self, events_path='du_lieu_phan_tich_region.csv'):
        """
        Tạo bản đồ chi tiết theo từng quốc gia từ Detected_Locations
        Sử dụng heatmap thay vì markers chồng chéo
        """
        print("\n" + "="*70)
        print("4. TẠO COUNTRY-LEVEL HEATMAP")
        print("="*70)
        
        # Dictionary với tên quốc gia và tọa độ (capital city)
        # Mở rộng để map các locations khác nhau
        location_to_country = {
            # Cities/States to Countries
            'Borno State': 'Nigeria', 'north-east Nigeria': 'Nigeria', 'northeastern Nigeria': 'Nigeria',
            'Charleville-Mézières': 'France', 'Mogadishu': 'Somalia',
            'Saada Governorate': 'Yemen', 'Youssifiyah': 'Iraq',
            'Aden': 'Yemen', 'Tel Aviv': 'Israel',
            'Brussels': 'Belgium', 'Paris': 'France',
            'Ouagadougou': 'Burkina Faso', 'Baga': 'Nigeria',
            'Grenoble': 'France', 'Toulouse': 'France', 'Bobigny': 'France',
            'Ibb Governorate': 'Yemen', 'Sinai': 'Egypt',
            'Borno': 'Nigeria', 'Borno State': 'Nigeria',
        }
        
        country_coords = {
            # Middle East
            'Iraq': (33.3152, 44.3661), 'Syria': (33.5138, 36.2765), 
            'Yemen': (15.3694, 44.1910), 'Saudi Arabia': (24.7136, 46.6753),
            'Israel': (31.7683, 35.2137), 'Palestine': (31.9522, 35.2332),
            'Lebanon': (33.8547, 35.8623), 'Jordan': (31.9539, 35.9106),
            'Iran': (35.6892, 51.3890), 'Turkey': (39.9334, 32.8597),
            'Afghanistan': (34.5553, 69.2075), 'Pakistan': (33.6844, 73.0479),
            'United Arab Emirates': (24.4539, 54.3773), 'Kuwait': (29.3759, 47.9774),
            'Qatar': (25.2854, 51.5310), 'Bahrain': (26.0667, 50.5577),
            'Oman': (23.5859, 58.4059), 'Egypt': (30.0444, 31.2357),
            
            # Europe
            'France': (48.8566, 2.3522), 'Belgium': (50.8503, 4.3517),
            'Germany': (52.5200, 13.4050), 'United Kingdom': (51.5074, -0.1278),
            'Spain': (40.4168, -3.7038), 'Italy': (41.9028, 12.4964),
            'Greece': (37.9838, 23.7275), 'Poland': (52.2297, 21.0122),
            'Ukraine': (50.4501, 30.5234), 'Russia': (55.7558, 37.6173),
            
            # Asia
            'China': (39.9042, 116.4074), 'Japan': (35.6762, 139.6503),
            'South Korea': (37.5665, 126.9780), 'North Korea': (39.0392, 125.7625),
            'India': (28.6139, 77.2090), 'Philippines': (14.5995, 120.9842),
            'Thailand': (13.7563, 100.5018), 'Myanmar': (16.8661, 96.1951),
            'Bangladesh': (23.8103, 90.4125), 'Sri Lanka': (6.9271, 79.8612),
            'Indonesia': (-6.2088, 106.8456), 'Malaysia': (3.1390, 101.6869),
            'Singapore': (1.3521, 103.8198), 'Vietnam': (21.0285, 105.8542),
            
            # Africa
            'Nigeria': (9.0765, 7.3986), 'Somalia': (2.0469, 45.3182),
            'Libya': (32.8872, 13.1913), 'Tunisia': (36.8065, 10.1815),
            'Algeria': (36.7538, 3.0588), 'Mali': (12.6392, -8.0029),
            'Niger': (13.5127, 2.1124), 'Burkina Faso': (12.3714, -1.5197),
            'Chad': (12.1348, 15.0557), 'Sudan': (15.5007, 32.5599),
            'South Sudan': (4.8594, 31.5713), 'Ethiopia': (9.1450, 38.7667),
            'Kenya': (-1.2921, 36.8219), 'Democratic Republic of the Congo': (-4.4419, 15.2663),
            'Central African Republic': (4.3947, 18.5582), 'Cameroon': (3.8480, 11.5021),
            
            # Americas
            'United States': (38.9072, -77.0369), 'Canada': (45.4215, -75.6972),
            'Mexico': (19.4326, -99.1332), 'Brazil': (-15.7975, -47.8919),
            'Colombia': (4.7110, -74.0721), 'Venezuela': (10.4806, -66.9036),
            'Argentina': (-34.6037, -58.3816), 'Chile': (-33.4489, -70.6693),
            'Peru': (-12.0464, -77.0428), 'Ecuador': (-0.1807, -78.4678),
            
            # Others
            'Australia': (-35.2809, 149.1300), 'New Zealand': (-41.2865, 174.7762),
        }
        
        # Load events
        print("\nLoading events from Detected_Locations...")
        events_df = pd.read_csv(events_path)
        events_df['Date'] = pd.to_datetime(events_df['Date'], dayfirst=True, errors='coerce')
        
        # Extract countries from Detected_Locations
        country_counts = {}
        country_event_map = {}  # Map country to list of events
        
        print("Extracting countries from Detected_Locations...")
        for idx, row in events_df.iterrows():
            detected_locations = str(row.get('Detected_Locations', ''))
            event_num = row.get('Event_Number', idx + 1)
            date = row.get('Date', '')
            
            if pd.isna(detected_locations) or detected_locations == 'nan':
                continue
            
            # Parse locations (comma-separated)
            locations = [loc.strip() for loc in detected_locations.split(',')]
            found_countries = set()
            
            # Map locations to countries
            for location in locations:
                location_clean = location.strip()
                if not location_clean:
                    continue
                
                # Check if location is directly a country
                if location_clean in country_coords:
                    found_countries.add(location_clean)
                # Check location_to_country mapping
                elif location_clean in location_to_country:
                    country = location_to_country[location_clean]
                    if country in country_coords:
                        found_countries.add(country)
                # Try fuzzy matching with country names
                else:
                    for country in country_coords.keys():
                        # Check if location contains country name or vice versa
                        if country.lower() in location_clean.lower() or location_clean.lower() in country.lower():
                            found_countries.add(country)
                            break
            
            # Update counts
            for country in found_countries:
                country_counts[country] = country_counts.get(country, 0) + 1
                if country not in country_event_map:
                    country_event_map[country] = []
                country_event_map[country].append({
                    'event_num': event_num,
                    'date': date,
                    'locations': detected_locations
                })
        
        if len(country_counts) == 0:
            print("  Warning: No countries found in Detected_Locations")
            return
    
        print(f"  Found {len(country_counts)} countries with events")
        print(f"  Top 10 countries:")
        for country, count in sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    {country:30s}: {count:3d} events")
        
        # Function để get color based on count
        max_count = max(country_counts.values()) if country_counts else 1
        
        def get_color_for_count(count, max_count):
            if count == 0:
                return '#ffffff'  # White for no events
            ratio = count / max_count
            if ratio > 0.7:
                return '#8B0000'  # Dark red
            elif ratio > 0.4:
                return '#DC143C'  # Crimson
            elif ratio > 0.2:
                return '#FF6347'  # Tomato
            else:
                return '#FFA500'  # Orange
        
        # Create interactive map with folium - TÔ MÀU CẢ QUỐC GIA
        if FOLIUM_AVAILABLE:
            print("\nCreating interactive country-level map (coloring entire countries)...")
            world_map = folium.Map(
                location=[20, 0],
                zoom_start=2,
                tiles='CartoDB positron',
                min_zoom=2,
                max_bounds=True
            )
            
            # Mapping này không được sử dụng - đã xóa để tránh nhầm lẫn
            # Mapping thực sự được dùng là name_mapping ở dưới
            
            # Sử dụng folium.Choropleth để tô màu toàn bộ quốc gia (theo cách đơn giản)
            print("  Preparing country data for choropleth...")
            
            # Tạo DataFrame từ country_counts với mapping tên nước
            # Chuẩn hóa tên nước theo mapping để match với GeoJSON
            # GeoJSON dùng tên đầy đủ, không dùng tên viết tắt
            name_mapping = {
                "United States": "United States of America",  # GeoJSON dùng "United States of America"
                "USA": "United States of America",
                "UK": "United Kingdom",
                "United Kingdom": "United Kingdom",  # GeoJSON dùng "United Kingdom"
                # Russia, South Korea, North Korea, Syria, Vietnam đều match trực tiếp
                # "Democratic Republic of the Congo" match trực tiếp với GeoJSON (không cần map)
                # Lưu ý: Bahrain, Palestine, Singapore không có trong GeoJSON này
            }
            
            # Tạo list countries với mapping
            all_countries_mapped = []
            for country, count in country_counts.items():
                standard_name = name_mapping.get(country, country)
                # Thêm count lần để tạo frequency
                for _ in range(count):
                    all_countries_mapped.append(standard_name)
            
            # Tạo DataFrame thống kê
            data_counts = pd.Series(all_countries_mapped).value_counts().reset_index()
            data_counts.columns = ['Country', 'Count']
            
            print(f"  Top 5 countries with most events:")
            print(data_counts.head())
            
            # GeoJSON URL (sử dụng trực tiếp, không cần download)
            GEOJSON_URL = "https://raw.githubusercontent.com/python-visualization/folium/master/examples/data/world-countries.json"
            
            # Kiểm tra xem có file local không
            geojson_path = Path('data/world-countries.json')
            geo_data = None
            
            if geojson_path.exists():
                print("  Using local GeoJSON file...")
                geo_data = str(geojson_path)
            else:
                # Thử download về local nếu có requests
                if REQUESTS_AVAILABLE:
                    try:
                        print("  Downloading GeoJSON to local...")
                        response = requests.get(GEOJSON_URL, timeout=15)
                        if response.status_code == 200:
                            # Tạo thư mục data nếu chưa có
                            geojson_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(geojson_path, 'wb') as f:
                                f.write(response.content)
                            print("  ✓ GeoJSON downloaded successfully")
                            geo_data = str(geojson_path)
                        else:
                            print("  ⚠ Could not download, using URL directly...")
                            geo_data = GEOJSON_URL
                    except Exception as e:
                        print(f"  ⚠ Download failed: {e}, using URL directly...")
                        geo_data = GEOJSON_URL
                else:
                    print("  Using GeoJSON from URL...")
                    geo_data = GEOJSON_URL
            
            # Kiểm tra data_counts có dữ liệu không
            if len(data_counts) == 0:
                print("  ⚠ Warning: No country data to display")
                return
            
            print(f"  Data ready: {len(data_counts)} countries with events")
            
            # Tạo Choropleth layer
            try:
                folium.Choropleth(
                    geo_data=geo_data,
                    name="choropleth",
                    data=data_counts,
                    columns=["Country", "Count"],
                    key_on="feature.properties.name",
                    fill_color="YlOrRd",  # Yellow-Orange-Red colormap
                    fill_opacity=0.7,
                    line_opacity=0.2,
                    legend_name="GPR Events Count",
                    nan_fill_color="white",
                    nan_fill_opacity=0.1
                ).add_to(world_map)
                print("  ✓ Choropleth layer added successfully")
            except Exception as e:
                print(f"  ⚠ Error creating Choropleth: {e}")
                print("  Trying alternative method...")
                # Fallback: thử với GeoJSON đã load
                if REQUESTS_AVAILABLE and geojson_path.exists():
                    try:
                        import json
                        with open(geojson_path, 'r', encoding='utf-8') as f:
                            world_geojson = json.load(f)
                        folium.Choropleth(
                            geo_data=world_geojson,
                            name="choropleth",
                            data=data_counts,
                            columns=["Country", "Count"],
                            key_on="feature.properties.name",
                            fill_color="YlOrRd",
                            fill_opacity=0.7,
                            line_opacity=0.2,
                            legend_name="GPR Events Count",
                            nan_fill_color="white",
                            nan_fill_opacity=0.1
                        ).add_to(world_map)
                        print("  ✓ Choropleth created with local GeoJSON")
                    except Exception as e2:
                        print(f"  ⚠ Alternative method also failed: {e2}")
                        raise
            
            print("  ✓ Countries colored successfully with Choropleth")
            
            # Thêm layer control
            folium.LayerControl().add_to(world_map)
            
            # Add legend
            # Add legend as HTML
            try:
                from branca.element import MacroElement, Template
                
                legend_html = '''
                <div style="position: fixed; 
                            bottom: 50px; right: 50px; width: 200px; height: auto;
                            background-color: white; border: 2px solid #34495e;
                            border-radius: 8px; padding: 15px; z-index:9999;
                            font-family: Arial, sans-serif; box-shadow: 0 4px 8px rgba(0,0,0,0.3);">
                    <h4 style="margin: 0 0 10px 0; color: #2c3e50; font-size: 14px;">
                        Event Intensity
                    </h4>
                    <div style="font-size: 11px; line-height: 1.8;">
                        <div><span style="display: inline-block; width: 20px; height: 20px; background: #8B0000; border-radius: 50%; margin-right: 8px; vertical-align: middle;"></span>High (15+)</div>
                        <div><span style="display: inline-block; width: 18px; height: 18px; background: #DC143C; border-radius: 50%; margin-right: 8px; vertical-align: middle;"></span>Medium (8-14)</div>
                        <div><span style="display: inline-block; width: 16px; height: 16px; background: #FF6347; border-radius: 50%; margin-right: 8px; vertical-align: middle;"></span>Low (4-7)</div>
                        <div><span style="display: inline-block; width: 14px; height: 14px; background: #FFA500; border-radius: 50%; margin-right: 8px; vertical-align: middle;"></span>Minimal (1-3)</div>
                    </div>
                </div>
                '''
                
                class LegendElement(MacroElement):
                    def __init__(self, html):
                        super().__init__()
                        self._template = Template(html)
                
                legend_element = LegendElement(legend_html)
                world_map.get_root().add_child(legend_element)
            except:
                pass  # Skip legend if branca not available
            
            # Save map
            output_path = self.output_dir / 'country_level_heatmap.html'
            world_map.save(str(output_path))
            print(f"  ✓ Saved: {output_path}")
        
        # Create static version
        self._create_country_static_map(country_counts, country_coords, country_event_map)
    
    def _create_country_static_map(self, country_counts, country_coords, country_event_map):
        """Tạo static map với các quốc gia - phiên bản đẹp hơn"""
        print("\nCreating static country-level map...")
        
        # Create figure with better styling
        fig = plt.figure(figsize=(22, 11), facecolor='white')
        ax = fig.add_subplot(111, facecolor='#f5f6fa')
        
        # Set world map bounds
        ax.set_xlim(-180, 180)
        ax.set_ylim(-90, 90)
        ax.set_aspect('equal')
        
        # Draw ocean background with gradient effect
        ocean_gradient = plt.Rectangle((-180, -90), 360, 180, 
                                      facecolor='#e3f2fd', edgecolor='none', zorder=0)
        ax.add_patch(ocean_gradient)
        
        # Draw major landmasses with better colors
        landmasses = [
            ((-170, 15), 60, 50, 'North America'),
            ((-85, -55), 35, 70, 'South America'),
            ((-10, 35), 40, 30, 'Europe'),
            ((-20, -35), 50, 70, 'Africa'),
            ((30, 10), 90, 50, 'Asia'),
            ((110, -45), 40, 30, 'Australia')
        ]
        
        for (x, y), w, h, name in landmasses:
            # Light grey landmass with subtle border
            land = plt.Rectangle((x, y), w, h, 
                                facecolor='#f8f9fa', edgecolor='#dee2e6', 
                                linewidth=0.8, zorder=1, alpha=0.9)
            ax.add_patch(land)
        
        # Draw subtle grid
        ax.grid(True, linestyle='--', alpha=0.2, color='#6c757d', linewidth=0.4, zorder=2)
        ax.set_xticks(range(-180, 181, 30))
        ax.set_yticks(range(-90, 91, 30))
        ax.tick_params(labelsize=9, colors='#495057')
        
        # Tạo heatmap density data
        max_count = max(country_counts.values()) if country_counts else 1
        
        # Tạo grid cho heatmap
        lon_grid = np.linspace(-180, 180, 360)
        lat_grid = np.linspace(-90, 90, 180)
        lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)
        
        # Tạo density map từ country data
        density = np.zeros_like(lon_mesh)
        
        for country, count in country_counts.items():
            if country in country_coords:
                lat, lon = country_coords[country]
                # Tìm grid cell gần nhất
                lon_idx = np.argmin(np.abs(lon_grid - lon))
                lat_idx = np.argmin(np.abs(lat_grid - lat))
                
                # Tăng density tại vị trí này (tỷ lệ với số events)
                # Spread ra một chút để tạo heat effect
                spread = 3  # pixels
                for i in range(max(0, lat_idx - spread), min(len(lat_grid), lat_idx + spread + 1)):
                    for j in range(max(0, lon_idx - spread), min(len(lon_grid), lon_idx + spread + 1)):
                        dist = np.sqrt((lat_grid[i] - lat)**2 + (lon_grid[j] - lon)**2)
                        if dist < 2:  # Within 2 degrees
                            weight = count * np.exp(-dist**2 / 0.5)  # Gaussian weight
                            density[i, j] += weight
        
        # Normalize density
        if density.max() > 0:
            density = density / density.max()
        
        # Plot heatmap với màu gradient: càng đậm = càng nhiều events
        im = ax.contourf(lon_mesh, lat_mesh, density, 
                        levels=20,
                        cmap='YlOrRd',  # Yellow-Orange-Red colormap
                        alpha=0.7,
                        zorder=2,
                        vmin=0, vmax=1)
        
        # Thêm contour lines để rõ hơn
        ax.contour(lon_mesh, lat_mesh, density,
                 levels=10,
                 colors='white',
                 linewidths=0.5,
                 alpha=0.3,
                 zorder=3)
        
        # Thêm text labels cho top countries (không chồng chéo)
        sorted_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
        top_countries = sorted_countries[:15]  # Chỉ hiển thị top 15 để tránh chồng chéo
        
        for country, count in top_countries:
            if country in country_coords:
                lat, lon = country_coords[country]
                
                # Chỉ hiển thị label nếu count đủ lớn
                if count >= 3:
                    # Màu text dựa trên intensity
                    intensity = count / max_count
                    if intensity > 0.5:
                        text_color = 'white'
                    else:
                        text_color = '#2c3e50'
                    
                    fontsize = 8 if count < 10 else 9
                    ax.annotate(f"{country}\n{count}", 
                              xy=(lon, lat),
                              xytext=(8, 8), 
                              textcoords='offset points',
                              fontsize=fontsize, 
                              fontweight='bold',
                              color=text_color,
                              bbox=dict(
                                  boxstyle='round,pad=0.4', 
                                  facecolor='white', 
                                  alpha=0.85,
                                  edgecolor='#e74c3c', 
                                  linewidth=1.5
                              ),
                              zorder=5,
                              family='sans-serif')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, fraction=0.02, pad=0.04)
        cbar.set_label('Event Density (Màu càng đậm = Càng nhiều events)', 
                       fontsize=11, fontweight='bold', color='#495057')
        cbar.ax.tick_params(labelsize=9, colors='#495057')
        
        # Beautiful title
        title = ax.set_title('Geopolitical Risk Events by Country (2015-2025)', 
                            fontsize=22, fontweight='bold', pad=25,
                            color='#2c3e50', family='sans-serif')
        title.set_position([0.5, 1.02])
        
        # Subtle subtitle
        subtitle = ax.text(0.5, 0.98, 'Heatmap Density: Màu càng đậm = Càng nhiều GPR events',
                          transform=ax.transAxes, ha='center', va='top',
                          fontsize=12, style='italic', color='#6c757d',
                          family='sans-serif')
        
        # Axis labels
        ax.set_xlabel('Longitude', fontsize=13, fontweight='bold', 
                     color='#495057', family='sans-serif', labelpad=10)
        ax.set_ylabel('Latitude', fontsize=13, fontweight='bold', 
                     color='#495057', family='sans-serif', labelpad=10)
        
        # Remove top and right spines for cleaner look
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#dee2e6')
        ax.spines['bottom'].set_color('#dee2e6')
        
        plt.tight_layout()
        output_path = self.output_dir / 'country_level_heatmap_static.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none', pad_inches=0.2)
        print(f"  ✓ Saved: country_level_heatmap_static.png")
        plt.close()

        # Create summary table
        print("\nCreating country summary...")
        top_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        summary_path = self.output_dir / 'country_event_summary.txt'
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("TOP 20 COUNTRIES BY GPR EVENTS\n")
            f.write("=" * 50 + "\n\n")
            for i, (country, count) in enumerate(top_countries, 1):
                f.write(f"{i:2d}. {country:30s}: {count:3d} events\n")
        print(f"  ✓ Saved: country_event_summary.txt")

def main():
    """Main function"""
    visualizer = AdvancedVisualizations()
    
    # 1. Annotated Time Series
    visualizer.create_annotated_timeseries()
    
    # 2. Word Cloud
    visualizer.create_wordcloud()
    
    # 3. Geospatial Heatmap (by region)
    visualizer.create_geospatial_heatmap()
    
    # 4. Country-level Heatmap (by country)
    visualizer.create_country_level_heatmap()
    
    print("\n" + "="*70)
    print("✓ HOÀN THÀNH TẤT CẢ VISUALIZATIONS")
    print("="*70)
    print(f"\nTất cả files đã được lưu trong: {visualizer.output_dir}")

if __name__ == '__main__':
    import sys
    import io
    # Set UTF-8 encoding for stdout
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    main()
