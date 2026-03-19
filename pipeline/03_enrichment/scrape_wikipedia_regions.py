"""
Scrape Wikipedia Current Events để phân loại events theo region
Lấy thông tin từ phần "Armed conflicts and attacks" cho mỗi event date
"""
import pandas as pd
import requests
from requests.exceptions import Timeout, RequestException
from bs4 import BeautifulSoup
import time
import re
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class WikipediaRegionScraper:
    def __init__(self, events_csv_path: str, output_dir: str = 'results/region_analysis'):
        """
        Initialize Wikipedia scraper
        
        Parameters:
        -----------
        events_csv_path : str
            Path to CSV file with events and dates
        output_dir : str
            Output directory for results
        """
        self.events_df = pd.read_csv(events_csv_path)
        self.events_df['Date'] = pd.to_datetime(self.events_df['Date'])
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Region keywords mapping
        self.region_keywords = {
            'Middle East': ['yemen', 'saudi arabia', 'iran', 'iraq', 'syria', 'israel', 'palestine', 
                          'lebanon', 'jordan', 'uae', 'qatar', 'kuwait', 'bahrain', 'oman',
                          'gaza', 'west bank', 'hezbollah', 'houthi', 'israeli', 'palestinian'],
            'Europe': ['ukraine', 'russia', 'nato', 'eu', 'germany', 'france', 'uk', 'britain',
                      'poland', 'baltic', 'crimea', 'donbas', 'moscow', 'kiev', 'kyiv',
                      'wagner', 'putin', 'zelensky'],
            'Asia': ['china', 'north korea', 'south korea', 'japan', 'india', 'pakistan',
                    'afghanistan', 'myanmar', 'thailand', 'vietnam', 'philippines',
                    'taiwan', 'hong kong', 'xinjiang', 'tibet', 'kashmir'],
            'Africa': ['somalia', 'libya', 'sudan', 'ethiopia', 'nigeria', 'mali', 'niger',
                      'chad', 'congo', 'kenya', 'south africa', 'egypt', 'al-shabab',
                      'boko haram', 'mogadishu'],
            'Americas': ['united states', 'usa', 'us', 'mexico', 'brazil', 'venezuela',
                        'colombia', 'cuba', 'haiti', 'guatemala', 'honduras'],
            'Central Asia': ['kazakhstan', 'uzbekistan', 'tajikistan', 'kyrgyzstan', 'turkmenistan',
                            'afghanistan', 'uzbek'],
            'Southeast Asia': ['indonesia', 'malaysia', 'singapore', 'cambodia', 'laos',
                              'brunei', 'east timor', 'myanmar', 'thailand', 'vietnam', 'philippines']
        }
        
        print("=" * 80)
        print("WIKIPEDIA REGION SCRAPER")
        print("=" * 80)
        print(f"Loaded {len(self.events_df)} events")
    
    def scrape_wikipedia_page(self, date: pd.Timestamp, retry=3):
        """
        Scrape Wikipedia Current Events page for a specific date
        
        Parameters:
        -----------
        date : pd.Timestamp
            Date to scrape
        retry : int
            Number of retries if request fails
        """
        # Wikipedia format: YYYY_Month_DD (e.g., 2015_March_27)
        # Format: year_Month_day (no leading zero for day, month capitalized)
        day = date.day  # No leading zero
        month_name = date.strftime('%B')  # Full month name with capital first letter (March, not march)
        year = date.year
        
        # Primary format: YYYY_Month_DD (e.g., 2015_March_27)
        url_format = f"{year}_{month_name}_{day}"
        
        url = f"https://en.wikipedia.org/wiki/Portal:Current_events/{url_format}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for attempt in range(retry):
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    print(f"  Success: {url_format}")
                    return response.text
                else:
                    print(f"  Status code {response.status_code} for {url_format}")
                    if attempt < retry - 1:
                        time.sleep(2)
            except Timeout:
                print(f"  Timeout for {url_format}")
                if attempt < retry - 1:
                    time.sleep(2)
            except RequestException as e:
                print(f"  Request error: {e}")
                if attempt < retry - 1:
                    time.sleep(2)
            except Exception as e:
                print(f"  Error: {e}")
                if attempt < retry - 1:
                    time.sleep(2)
        
        print(f"  Failed to scrape for {date.strftime('%Y-%m-%d')}")
        return None
    
    def parse_armed_conflicts_section(self, html_content: str):
        """
        Parse "Armed conflicts and attacks" section from Wikipedia HTML
        
        Parameters:
        -----------
        html_content : str
            HTML content of Wikipedia page
        """
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        conflicts = []
        
        # Tìm theo nội dung chữ - cách tốt hơn
        # Tìm bất kỳ thẻ nào có chứa chính xác cụm từ "Armed conflicts and attacks"
        target_text = soup.find(lambda tag: tag.name in ['span', 'h3', 'h4', 'div'] 
                                and "Armed conflicts and attacks" in tag.get_text())
        
        if target_text:
            # Tìm thẻ danh sách (ul) ngay sau thẻ vừa tìm thấy
            content_list = target_text.find_next("ul")
            
            # Nếu thẻ vừa tìm thấy là con (ví dụ span), leo lên thẻ cha (h3/h4) để tìm ul kế tiếp
            if not content_list:
                parent = target_text.find_parent(['h2', 'h3', 'h4'])
                if parent:
                    content_list = parent.find_next("ul")
            
            if content_list:
                items = content_list.find_all("li")
                for item in items:
                    # Lấy text, loại bỏ các chú thích wiki [1], [2]...
                    text = item.get_text(separator=" ", strip=True)
                    # Clean text - remove citations and extra whitespace
                    text = re.sub(r'\[.*?\]', '', text)  # Remove [citation]
                    text = re.sub(r'\([^)]*\)', '', text)  # Remove (source)
                    text = ' '.join(text.split())  # Normalize whitespace
                    if text.strip():
                        conflicts.append(text.strip())
        
        return conflicts
    
    def identify_region_from_text(self, text: str):
        """
        Identify region from text using keyword matching
        
        Parameters:
        -----------
        text : str
            Text to analyze
        """
        text_lower = text.lower()
        region_scores = {}
        
        for region, keywords in self.region_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                region_scores[region] = score
        
        if region_scores:
            # Return region with highest score
            return max(region_scores.items(), key=lambda x: x[1])[0]
        
        return 'Unknown'
    
    def scrape_all_events(self, delay=1):
        """
        Scrape Wikipedia for all events
        
        Parameters:
        -----------
        delay : float
            Delay between requests (seconds)
        """
        print("\n" + "=" * 80)
        print("SCRAPING WIKIPEDIA FOR ALL EVENTS")
        print("=" * 80)
        
        results = []
        
        for idx, row in self.events_df.iterrows():
            event_num = row['Event_Number']
            date = row['Date']
            
            print(f"\n[{idx+1}/{len(self.events_df)}] Event {event_num} - {date.strftime('%Y-%m-%d')}")
            
            # Scrape Wikipedia
            html_content = self.scrape_wikipedia_page(date)
            
            if html_content:
                # Parse armed conflicts section
                conflicts = self.parse_armed_conflicts_section(html_content)
                
                if conflicts:
                    print(f"  Found {len(conflicts)} conflict/attack entries")
                    
                    # Identify regions from conflicts
                    regions = []
                    for conflict_text in conflicts:
                        region = self.identify_region_from_text(conflict_text)
                        if region != 'Unknown':
                            regions.append(region)
                    
                    # Get most common region
                    if regions:
                        from collections import Counter
                        region_counts = Counter(regions)
                        primary_region = region_counts.most_common(1)[0][0]
                        region_confidence = region_counts.most_common(1)[0][1] / len(regions)
                    else:
                        primary_region = 'Unknown'
                        region_confidence = 0.0
                    
                    print(f"  Primary Region: {primary_region} (confidence: {region_confidence:.2f})")
                    
                    results.append({
                        'Event_Number': event_num,
                        'Date': date,
                        'Conflicts_Found': len(conflicts),
                        'Primary_Region': primary_region,
                        'Region_Confidence': region_confidence,
                        'All_Regions': ', '.join(set(regions)) if regions else 'Unknown',
                        'Sample_Conflicts': ' | '.join(conflicts[:3])  # First 3 conflicts
                    })
                else:
                    print(f"  No conflicts/attacks section found")
                    results.append({
                        'Event_Number': event_num,
                        'Date': date,
                        'Conflicts_Found': 0,
                        'Primary_Region': 'Unknown',
                        'Region_Confidence': 0.0,
                        'All_Regions': 'Unknown',
                        'Sample_Conflicts': ''
                    })
            else:
                print(f"  Failed to scrape Wikipedia")
                results.append({
                    'Event_Number': event_num,
                    'Date': date,
                    'Conflicts_Found': 0,
                    'Primary_Region': 'Unknown',
                    'Region_Confidence': 0.0,
                    'All_Regions': 'Unknown',
                    'Sample_Conflicts': ''
                })
            
            # Delay to avoid rate limiting
            time.sleep(delay)
        
        # Create DataFrame
        region_df = pd.DataFrame(results)
        
        # Merge with events data
        self.events_df = self.events_df.merge(
            region_df[['Event_Number', 'Primary_Region', 'Region_Confidence', 'All_Regions', 'Conflicts_Found']],
            on='Event_Number',
            how='left'
        )
        
        # Save intermediate results
        region_df.to_csv(self.output_dir / 'wikipedia_scraping_results.csv', index=False, encoding='utf-8-sig')
        print(f"\nSaved scraping results to: {self.output_dir / 'wikipedia_scraping_results.csv'}")
        
        return self.events_df
    
    def analyze_car_by_region(self):
        """Phân tích CAR theo region"""
        print("\n" + "=" * 80)
        print("CAR ANALYSIS BY REGION")
        print("=" * 80)
        
        # Filter events with identified regions
        df_with_region = self.events_df[
            (self.events_df['Primary_Region'] != 'Unknown') & 
            (self.events_df['Region_Confidence'] > 0.3)
        ].copy()
        
        print(f"\nEvents with identified regions: {len(df_with_region)}/{len(self.events_df)}")
        
        # Statistics by region
        assets = ['BTC', 'GOLD', 'OIL']
        results = {}
        
        for asset in assets:
            car_col = f'CAR_{asset}'
            stats_by_region = df_with_region.groupby('Primary_Region')[car_col].agg(['mean', 'std', 'count'])
            results[asset] = stats_by_region
            
            print(f"\n{asset} CAR by Region:")
            print(stats_by_region.sort_values('mean', ascending=False))
        
        # Region distribution
        print("\nRegion Distribution:")
        print(df_with_region['Primary_Region'].value_counts())
        
        return results
    
    def visualize_region_impact(self):
        """Visualize CAR by region"""
        print("\n" + "=" * 80)
        print("CREATING VISUALIZATIONS")
        print("=" * 80)
        
        df_with_region = self.events_df[
            (self.events_df['Primary_Region'] != 'Unknown') & 
            (self.events_df['Region_Confidence'] > 0.3)
        ].copy()
        
        if len(df_with_region) == 0:
            print("No events with identified regions to visualize")
            return
        
        assets = ['BTC', 'GOLD', 'OIL']
        
        # Box plots
        fig, axes = plt.subplots(1, 3, figsize=(20, 6))
        for idx, asset in enumerate(assets):
            car_col = f'CAR_{asset}'
            # Sort regions by mean CAR
            region_order = df_with_region.groupby('Primary_Region')[car_col].mean().sort_values(ascending=False).index
            
            sns.boxplot(data=df_with_region, x='Primary_Region', y=car_col, 
                       order=region_order, ax=axes[idx])
            axes[idx].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[idx].set_title(f'{asset} CAR by Region')
            axes[idx].set_ylabel('CAR')
            axes[idx].tick_params(axis='x', rotation=45)
            axes[idx].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'car_by_region.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("Saved visualizations to", self.output_dir)
    
    def export_region_classified_events(self):
        """Export events with region classification"""
        output_path = self.output_dir / 'events_with_region_classification.csv'
        
        export_cols = [
            'Event_Number', 'Date', 'Detection_Method', 
            'GPR_Value', 'Primary_Region', 'Region_Confidence', 'All_Regions',
            'CAR_BTC', 'CAR_GOLD', 'CAR_OIL',
            'Tstat_BTC', 'Tstat_GOLD', 'Tstat_OIL'
        ]
        
        export_df = self.events_df[export_cols].copy()
        export_df['Date'] = export_df['Date'].dt.strftime('%Y-%m-%d')
        
        export_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\nExported region-classified events to: {output_path}")
        
        return export_df


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    scraper = WikipediaRegionScraper(
        events_csv_path='results/event_study/detected_events_with_car.csv',
        output_dir='results/region_analysis'
    )
    
    # Scrape Wikipedia (with delay to avoid rate limiting)
    scraper.scrape_all_events(delay=2)  # 2 second delay between requests
    
    # Analyze CAR by region
    scraper.analyze_car_by_region()
    
    # Visualize
    scraper.visualize_region_impact()
    
    # Export
    scraper.export_region_classified_events()
    
    print("\n" + "=" * 80)
    print("REGION ANALYSIS COMPLETED!")
    print("=" * 80)


Lấy thông tin từ phần "Armed conflicts and attacks" cho mỗi event date
"""
import pandas as pd
import requests
from requests.exceptions import Timeout, RequestException
from bs4 import BeautifulSoup
import time
import re
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class WikipediaRegionScraper:
    def __init__(self, events_csv_path: str, output_dir: str = 'results/region_analysis'):
        """
        Initialize Wikipedia scraper
        
        Parameters:
        -----------
        events_csv_path : str
            Path to CSV file with events and dates
        output_dir : str
            Output directory for results
        """
        self.events_df = pd.read_csv(events_csv_path)
        self.events_df['Date'] = pd.to_datetime(self.events_df['Date'])
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Region keywords mapping
        self.region_keywords = {
            'Middle East': ['yemen', 'saudi arabia', 'iran', 'iraq', 'syria', 'israel', 'palestine', 
                          'lebanon', 'jordan', 'uae', 'qatar', 'kuwait', 'bahrain', 'oman',
                          'gaza', 'west bank', 'hezbollah', 'houthi', 'israeli', 'palestinian'],
            'Europe': ['ukraine', 'russia', 'nato', 'eu', 'germany', 'france', 'uk', 'britain',
                      'poland', 'baltic', 'crimea', 'donbas', 'moscow', 'kiev', 'kyiv',
                      'wagner', 'putin', 'zelensky'],
            'Asia': ['china', 'north korea', 'south korea', 'japan', 'india', 'pakistan',
                    'afghanistan', 'myanmar', 'thailand', 'vietnam', 'philippines',
                    'taiwan', 'hong kong', 'xinjiang', 'tibet', 'kashmir'],
            'Africa': ['somalia', 'libya', 'sudan', 'ethiopia', 'nigeria', 'mali', 'niger',
                      'chad', 'congo', 'kenya', 'south africa', 'egypt', 'al-shabab',
                      'boko haram', 'mogadishu'],
            'Americas': ['united states', 'usa', 'us', 'mexico', 'brazil', 'venezuela',
                        'colombia', 'cuba', 'haiti', 'guatemala', 'honduras'],
            'Central Asia': ['kazakhstan', 'uzbekistan', 'tajikistan', 'kyrgyzstan', 'turkmenistan',
                            'afghanistan', 'uzbek'],
            'Southeast Asia': ['indonesia', 'malaysia', 'singapore', 'cambodia', 'laos',
                              'brunei', 'east timor', 'myanmar', 'thailand', 'vietnam', 'philippines']
        }
        
        print("=" * 80)
        print("WIKIPEDIA REGION SCRAPER")
        print("=" * 80)
        print(f"Loaded {len(self.events_df)} events")
    
    def scrape_wikipedia_page(self, date: pd.Timestamp, retry=3):
        """
        Scrape Wikipedia Current Events page for a specific date
        
        Parameters:
        -----------
        date : pd.Timestamp
            Date to scrape
        retry : int
            Number of retries if request fails
        """
        # Wikipedia format: YYYY_Month_DD (e.g., 2015_March_27)
        # Format: year_Month_day (no leading zero for day, month capitalized)
        day = date.day  # No leading zero
        month_name = date.strftime('%B')  # Full month name with capital first letter (March, not march)
        year = date.year
        
        # Primary format: YYYY_Month_DD (e.g., 2015_March_27)
        url_format = f"{year}_{month_name}_{day}"
        
        url = f"https://en.wikipedia.org/wiki/Portal:Current_events/{url_format}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for attempt in range(retry):
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code == 200:
                    print(f"  Success: {url_format}")
                    return response.text
                else:
                    print(f"  Status code {response.status_code} for {url_format}")
                    if attempt < retry - 1:
                        time.sleep(2)
            except Timeout:
                print(f"  Timeout for {url_format}")
                if attempt < retry - 1:
                    time.sleep(2)
            except RequestException as e:
                print(f"  Request error: {e}")
                if attempt < retry - 1:
                    time.sleep(2)
            except Exception as e:
                print(f"  Error: {e}")
                if attempt < retry - 1:
                    time.sleep(2)
        
        print(f"  Failed to scrape for {date.strftime('%Y-%m-%d')}")
        return None
    
    def parse_armed_conflicts_section(self, html_content: str):
        """
        Parse "Armed conflicts and attacks" section from Wikipedia HTML
        
        Parameters:
        -----------
        html_content : str
            HTML content of Wikipedia page
        """
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        conflicts = []
        
        # Tìm theo nội dung chữ - cách tốt hơn
        # Tìm bất kỳ thẻ nào có chứa chính xác cụm từ "Armed conflicts and attacks"
        target_text = soup.find(lambda tag: tag.name in ['span', 'h3', 'h4', 'div'] 
                                and "Armed conflicts and attacks" in tag.get_text())
        
        if target_text:
            # Tìm thẻ danh sách (ul) ngay sau thẻ vừa tìm thấy
            content_list = target_text.find_next("ul")
            
            # Nếu thẻ vừa tìm thấy là con (ví dụ span), leo lên thẻ cha (h3/h4) để tìm ul kế tiếp
            if not content_list:
                parent = target_text.find_parent(['h2', 'h3', 'h4'])
                if parent:
                    content_list = parent.find_next("ul")
            
            if content_list:
                items = content_list.find_all("li")
                for item in items:
                    # Lấy text, loại bỏ các chú thích wiki [1], [2]...
                    text = item.get_text(separator=" ", strip=True)
                    # Clean text - remove citations and extra whitespace
                    text = re.sub(r'\[.*?\]', '', text)  # Remove [citation]
                    text = re.sub(r'\([^)]*\)', '', text)  # Remove (source)
                    text = ' '.join(text.split())  # Normalize whitespace
                    if text.strip():
                        conflicts.append(text.strip())
        
        return conflicts
    
    def identify_region_from_text(self, text: str):
        """
        Identify region from text using keyword matching
        
        Parameters:
        -----------
        text : str
            Text to analyze
        """
        text_lower = text.lower()
        region_scores = {}
        
        for region, keywords in self.region_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                region_scores[region] = score
        
        if region_scores:
            # Return region with highest score
            return max(region_scores.items(), key=lambda x: x[1])[0]
        
        return 'Unknown'
    
    def scrape_all_events(self, delay=1):
        """
        Scrape Wikipedia for all events
        
        Parameters:
        -----------
        delay : float
            Delay between requests (seconds)
        """
        print("\n" + "=" * 80)
        print("SCRAPING WIKIPEDIA FOR ALL EVENTS")
        print("=" * 80)
        
        results = []
        
        for idx, row in self.events_df.iterrows():
            event_num = row['Event_Number']
            date = row['Date']
            
            print(f"\n[{idx+1}/{len(self.events_df)}] Event {event_num} - {date.strftime('%Y-%m-%d')}")
            
            # Scrape Wikipedia
            html_content = self.scrape_wikipedia_page(date)
            
            if html_content:
                # Parse armed conflicts section
                conflicts = self.parse_armed_conflicts_section(html_content)
                
                if conflicts:
                    print(f"  Found {len(conflicts)} conflict/attack entries")
                    
                    # Identify regions from conflicts
                    regions = []
                    for conflict_text in conflicts:
                        region = self.identify_region_from_text(conflict_text)
                        if region != 'Unknown':
                            regions.append(region)
                    
                    # Get most common region
                    if regions:
                        from collections import Counter
                        region_counts = Counter(regions)
                        primary_region = region_counts.most_common(1)[0][0]
                        region_confidence = region_counts.most_common(1)[0][1] / len(regions)
                    else:
                        primary_region = 'Unknown'
                        region_confidence = 0.0
                    
                    print(f"  Primary Region: {primary_region} (confidence: {region_confidence:.2f})")
                    
                    results.append({
                        'Event_Number': event_num,
                        'Date': date,
                        'Conflicts_Found': len(conflicts),
                        'Primary_Region': primary_region,
                        'Region_Confidence': region_confidence,
                        'All_Regions': ', '.join(set(regions)) if regions else 'Unknown',
                        'Sample_Conflicts': ' | '.join(conflicts[:3])  # First 3 conflicts
                    })
                else:
                    print(f"  No conflicts/attacks section found")
                    results.append({
                        'Event_Number': event_num,
                        'Date': date,
                        'Conflicts_Found': 0,
                        'Primary_Region': 'Unknown',
                        'Region_Confidence': 0.0,
                        'All_Regions': 'Unknown',
                        'Sample_Conflicts': ''
                    })
            else:
                print(f"  Failed to scrape Wikipedia")
                results.append({
                    'Event_Number': event_num,
                    'Date': date,
                    'Conflicts_Found': 0,
                    'Primary_Region': 'Unknown',
                    'Region_Confidence': 0.0,
                    'All_Regions': 'Unknown',
                    'Sample_Conflicts': ''
                })
            
            # Delay to avoid rate limiting
            time.sleep(delay)
        
        # Create DataFrame
        region_df = pd.DataFrame(results)
        
        # Merge with events data
        self.events_df = self.events_df.merge(
            region_df[['Event_Number', 'Primary_Region', 'Region_Confidence', 'All_Regions', 'Conflicts_Found']],
            on='Event_Number',
            how='left'
        )
        
        # Save intermediate results
        region_df.to_csv(self.output_dir / 'wikipedia_scraping_results.csv', index=False, encoding='utf-8-sig')
        print(f"\nSaved scraping results to: {self.output_dir / 'wikipedia_scraping_results.csv'}")
        
        return self.events_df
    
    def analyze_car_by_region(self):
        """Phân tích CAR theo region"""
        print("\n" + "=" * 80)
        print("CAR ANALYSIS BY REGION")
        print("=" * 80)
        
        # Filter events with identified regions
        df_with_region = self.events_df[
            (self.events_df['Primary_Region'] != 'Unknown') & 
            (self.events_df['Region_Confidence'] > 0.3)
        ].copy()
        
        print(f"\nEvents with identified regions: {len(df_with_region)}/{len(self.events_df)}")
        
        # Statistics by region
        assets = ['BTC', 'GOLD', 'OIL']
        results = {}
        
        for asset in assets:
            car_col = f'CAR_{asset}'
            stats_by_region = df_with_region.groupby('Primary_Region')[car_col].agg(['mean', 'std', 'count'])
            results[asset] = stats_by_region
            
            print(f"\n{asset} CAR by Region:")
            print(stats_by_region.sort_values('mean', ascending=False))
        
        # Region distribution
        print("\nRegion Distribution:")
        print(df_with_region['Primary_Region'].value_counts())
        
        return results
    
    def visualize_region_impact(self):
        """Visualize CAR by region"""
        print("\n" + "=" * 80)
        print("CREATING VISUALIZATIONS")
        print("=" * 80)
        
        df_with_region = self.events_df[
            (self.events_df['Primary_Region'] != 'Unknown') & 
            (self.events_df['Region_Confidence'] > 0.3)
        ].copy()
        
        if len(df_with_region) == 0:
            print("No events with identified regions to visualize")
            return
        
        assets = ['BTC', 'GOLD', 'OIL']
        
        # Box plots
        fig, axes = plt.subplots(1, 3, figsize=(20, 6))
        for idx, asset in enumerate(assets):
            car_col = f'CAR_{asset}'
            # Sort regions by mean CAR
            region_order = df_with_region.groupby('Primary_Region')[car_col].mean().sort_values(ascending=False).index
            
            sns.boxplot(data=df_with_region, x='Primary_Region', y=car_col, 
                       order=region_order, ax=axes[idx])
            axes[idx].axhline(y=0, color='r', linestyle='--', alpha=0.5)
            axes[idx].set_title(f'{asset} CAR by Region')
            axes[idx].set_ylabel('CAR')
            axes[idx].tick_params(axis='x', rotation=45)
            axes[idx].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'car_by_region.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("Saved visualizations to", self.output_dir)
    
    def export_region_classified_events(self):
        """Export events with region classification"""
        output_path = self.output_dir / 'events_with_region_classification.csv'
        
        export_cols = [
            'Event_Number', 'Date', 'Detection_Method', 
            'GPR_Value', 'Primary_Region', 'Region_Confidence', 'All_Regions',
            'CAR_BTC', 'CAR_GOLD', 'CAR_OIL',
            'Tstat_BTC', 'Tstat_GOLD', 'Tstat_OIL'
        ]
        
        export_df = self.events_df[export_cols].copy()
        export_df['Date'] = export_df['Date'].dt.strftime('%Y-%m-%d')
        
        export_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\nExported region-classified events to: {output_path}")
        
        return export_df


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    scraper = WikipediaRegionScraper(
        events_csv_path='results/event_study/detected_events_with_car.csv',
        output_dir='results/region_analysis'
    )
    
    # Scrape Wikipedia (with delay to avoid rate limiting)
    scraper.scrape_all_events(delay=2)  # 2 second delay between requests
    
    # Analyze CAR by region
    scraper.analyze_car_by_region()
    
    # Visualize
    scraper.visualize_region_impact()
    
    # Export
    scraper.export_region_classified_events()
    
    print("\n" + "=" * 80)
    print("REGION ANALYSIS COMPLETED!")
    print("=" * 80)

