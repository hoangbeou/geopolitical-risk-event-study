"""
Run scraper with logging to file
"""
import sys
from pathlib import Path
import datetime

sys.path.insert(0, str(Path(__file__).parent))

from scripts.scrape_wikipedia_regions import WikipediaRegionScraper
import pandas as pd

# Redirect output to file
log_file = f'results/scraper_log_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'

class TeeOutput:
    def __init__(self, *files):
        self.files = files
    
    def write(self, text):
        for f in self.files:
            f.write(text)
            f.flush()
        sys.stdout.write(text)
        sys.stdout.flush()
    
    def flush(self):
        for f in self.files:
            f.flush()
        sys.stdout.flush()

with open(log_file, 'w', encoding='utf-8') as f:
    sys.stdout = TeeOutput(sys.stdout, f)
    
    print("=" * 80)
    print("WIKIPEDIA REGION SCRAPER - WITH LOGGING")
    print("=" * 80)
    print(f"Log file: {log_file}")
    
    # Load first 3 events for quick test
    events_df = pd.read_csv('results/event_study/detected_events_with_car.csv')
    events_df['Date'] = pd.to_datetime(events_df['Date'])
    
    test_events = events_df.head(3).copy()
    test_events.to_csv('results/test_events.csv', index=False)
    
    print(f"\nTesting with {len(test_events)} events:")
    print(test_events[['Event_Number', 'Date']].to_string(index=False))
    
    scraper = WikipediaRegionScraper(
        events_csv_path='results/test_events.csv',
        output_dir='results/region_test'
    )
    
    # Test scrape
    print("\nStarting scrape...")
    scraper.scrape_all_events(delay=1)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETED!")
    print("=" * 80)
    print(f"\nCheck log file: {log_file}")
    print(f"Check results in: results/region_test/")

