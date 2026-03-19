"""
Run Wikipedia region scraper
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.scrape_wikipedia_regions import WikipediaRegionScraper
import pandas as pd

print("=" * 80)
print("WIKIPEDIA REGION SCRAPER")
print("=" * 80)

# Load events
events_df = pd.read_csv('results/event_study/detected_events_with_car.csv')
events_df['Date'] = pd.to_datetime(events_df['Date'])

print(f"\nTotal events: {len(events_df)}")
print(f"Date range: {events_df['Date'].min()} to {events_df['Date'].max()}")

# Ask user: full scrape or test?
print("\nOptions:")
print("1. Test with first 5 events (recommended)")
print("2. Scrape all events (will take ~2-3 minutes)")
choice = input("\nEnter choice (1 or 2): ").strip()

if choice == '1':
    test_events = events_df.head(5).copy()
    test_events.to_csv('results/test_events.csv', index=False)
    print(f"\nTesting with {len(test_events)} events...")
    scraper = WikipediaRegionScraper(
        events_csv_path='results/test_events.csv',
        output_dir='results/region_analysis_test'
    )
    scraper.scrape_all_events(delay=1)
    scraper.analyze_car_by_region()
    scraper.visualize_region_impact()
    scraper.export_region_classified_events()
else:
    print(f"\nScraping all {len(events_df)} events...")
    print("This will take approximately 2-3 minutes...")
    scraper = WikipediaRegionScraper(
        events_csv_path='results/event_study/detected_events_with_car.csv',
        output_dir='results/region_analysis'
    )
    scraper.scrape_all_events(delay=2)  # 2 second delay to avoid rate limit
    scraper.analyze_car_by_region()
    scraper.visualize_region_impact()
    scraper.export_region_classified_events()

print("\n" + "=" * 80)
print("SCRAPING COMPLETED!")
print("=" * 80)
print("\nResults saved to:")
print(f"  - {scraper.output_dir}/wikipedia_scraping_results.csv")
print(f"  - {scraper.output_dir}/events_with_region_classification.csv")


Run Wikipedia region scraper
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.scrape_wikipedia_regions import WikipediaRegionScraper
import pandas as pd

print("=" * 80)
print("WIKIPEDIA REGION SCRAPER")
print("=" * 80)

# Load events
events_df = pd.read_csv('results/event_study/detected_events_with_car.csv')
events_df['Date'] = pd.to_datetime(events_df['Date'])

print(f"\nTotal events: {len(events_df)}")
print(f"Date range: {events_df['Date'].min()} to {events_df['Date'].max()}")

# Ask user: full scrape or test?
print("\nOptions:")
print("1. Test with first 5 events (recommended)")
print("2. Scrape all events (will take ~2-3 minutes)")
choice = input("\nEnter choice (1 or 2): ").strip()

if choice == '1':
    test_events = events_df.head(5).copy()
    test_events.to_csv('results/test_events.csv', index=False)
    print(f"\nTesting with {len(test_events)} events...")
    scraper = WikipediaRegionScraper(
        events_csv_path='results/test_events.csv',
        output_dir='results/region_analysis_test'
    )
    scraper.scrape_all_events(delay=1)
    scraper.analyze_car_by_region()
    scraper.visualize_region_impact()
    scraper.export_region_classified_events()
else:
    print(f"\nScraping all {len(events_df)} events...")
    print("This will take approximately 2-3 minutes...")
    scraper = WikipediaRegionScraper(
        events_csv_path='results/event_study/detected_events_with_car.csv',
        output_dir='results/region_analysis'
    )
    scraper.scrape_all_events(delay=2)  # 2 second delay to avoid rate limit
    scraper.analyze_car_by_region()
    scraper.visualize_region_impact()
    scraper.export_region_classified_events()

print("\n" + "=" * 80)
print("SCRAPING COMPLETED!")
print("=" * 80)
print("\nResults saved to:")
print(f"  - {scraper.output_dir}/wikipedia_scraping_results.csv")
print(f"  - {scraper.output_dir}/events_with_region_classification.csv")

