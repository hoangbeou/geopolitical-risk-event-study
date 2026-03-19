"""
Test Wikipedia scraper với một vài events đầu tiên
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Now import
from scripts.scrape_wikipedia_regions import WikipediaRegionScraper
import pandas as pd

# Load events
events_df = pd.read_csv('results/event_study/detected_events_with_car.csv')
events_df['Date'] = pd.to_datetime(events_df['Date'])

# Test với 5 events đầu tiên
test_events = events_df.head(5).copy()
test_events.to_csv('results/test_events.csv', index=False)

print("Testing Wikipedia scraper with first 5 events...")
print("\nTest events:")
print(test_events[['Event_Number', 'Date']].to_string(index=False))

scraper = WikipediaRegionScraper(
    events_csv_path='results/test_events.csv',
    output_dir='results/region_analysis_test'
)

# Test scrape một event
print("\n" + "=" * 80)
print("TESTING SCRAPE FOR FIRST EVENT")
print("=" * 80)

test_date = test_events.iloc[0]['Date']
print(f"\nTesting date: {test_date}")

html_content = scraper.scrape_wikipedia_page(test_date)
if html_content:
    conflicts = scraper.parse_armed_conflicts_section(html_content)
    print(f"\nFound {len(conflicts)} conflict/attack entries:")
    for i, conflict in enumerate(conflicts[:5], 1):  # Show first 5
        print(f"  {i}. {conflict[:100]}...")
    
    if conflicts:
        regions = []
        for conflict_text in conflicts:
            region = scraper.identify_region_from_text(conflict_text)
            if region != 'Unknown':
                regions.append(region)
        
        if regions:
            from collections import Counter
            region_counts = Counter(regions)
            print(f"\nIdentified regions: {dict(region_counts)}")
            primary_region = region_counts.most_common(1)[0][0]
            print(f"Primary Region: {primary_region}")
else:
    print("Failed to scrape Wikipedia page")

print("\n" + "=" * 80)
print("TEST COMPLETED")
print("=" * 80)
print("\nIf test successful, run full scraper with:")
print("  python scripts/scrape_wikipedia_regions.py")


"""
import sys
import os
from pathlib import Path

# Add parent directory to path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Now import
from scripts.scrape_wikipedia_regions import WikipediaRegionScraper
import pandas as pd

# Load events
events_df = pd.read_csv('results/event_study/detected_events_with_car.csv')
events_df['Date'] = pd.to_datetime(events_df['Date'])

# Test với 5 events đầu tiên
test_events = events_df.head(5).copy()
test_events.to_csv('results/test_events.csv', index=False)

print("Testing Wikipedia scraper with first 5 events...")
print("\nTest events:")
print(test_events[['Event_Number', 'Date']].to_string(index=False))

scraper = WikipediaRegionScraper(
    events_csv_path='results/test_events.csv',
    output_dir='results/region_analysis_test'
)

# Test scrape một event
print("\n" + "=" * 80)
print("TESTING SCRAPE FOR FIRST EVENT")
print("=" * 80)

test_date = test_events.iloc[0]['Date']
print(f"\nTesting date: {test_date}")

html_content = scraper.scrape_wikipedia_page(test_date)
if html_content:
    conflicts = scraper.parse_armed_conflicts_section(html_content)
    print(f"\nFound {len(conflicts)} conflict/attack entries:")
    for i, conflict in enumerate(conflicts[:5], 1):  # Show first 5
        print(f"  {i}. {conflict[:100]}...")
    
    if conflicts:
        regions = []
        for conflict_text in conflicts:
            region = scraper.identify_region_from_text(conflict_text)
            if region != 'Unknown':
                regions.append(region)
        
        if regions:
            from collections import Counter
            region_counts = Counter(regions)
            print(f"\nIdentified regions: {dict(region_counts)}")
            primary_region = region_counts.most_common(1)[0][0]
            print(f"Primary Region: {primary_region}")
else:
    print("Failed to scrape Wikipedia page")

print("\n" + "=" * 80)
print("TEST COMPLETED")
print("=" * 80)
print("\nIf test successful, run full scraper with:")
print("  python scripts/scrape_wikipedia_regions.py")

