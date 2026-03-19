"""
Quick test Wikipedia scraper với URL cụ thể
"""
import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/Portal:Current_events/2015_March_27"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print("Testing Wikipedia scraper...")
print(f"URL: {url}")

try:
    response = requests.get(url, headers=headers, timeout=15)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find "Armed conflicts and attacks" section
        spans = soup.find_all('span', class_='mw-headline')
        armed_section = None
        
        for span in spans:
            text = span.get_text().strip()
            print(f"Found span: {text}")
            if 'Armed conflicts' in text or ('Attacks' in text and 'conflict' in text.lower()):
                armed_section = span.find_parent(['h2', 'h3', 'h4'])
                print(f"Found armed conflicts section: {armed_section.name if armed_section else 'None'}")
                break
        
        if armed_section:
            conflicts = []
            current = armed_section.find_next_sibling()
            section_level = int(armed_section.name[1])
            
            while current:
                if current.name in ['h2', 'h3', 'h4']:
                    current_level = int(current.name[1])
                    if current_level <= section_level:
                        break
                
                if current.name == 'ul':
                    items = current.find_all('li', recursive=False)
                    for item in items:
                        text = item.get_text()
                        text = re.sub(r'\[.*?\]', '', text)
                        text = re.sub(r'\([^)]*\)', '', text)
                        text = ' '.join(text.split())
                        if text.strip():
                            conflicts.append(text.strip())
                
                current = current.find_next_sibling()
            
            print(f"\nFound {len(conflicts)} conflicts:")
            for i, conflict in enumerate(conflicts, 1):
                print(f"  {i}. {conflict}")
        else:
            print("Could not find 'Armed conflicts and attacks' section")
            # Try to find all headings
            headings = soup.find_all(['h2', 'h3', 'h4'])
            print("\nAll headings found:")
            for h in headings[:10]:
                print(f"  {h.name}: {h.get_text().strip()[:50]}")
    else:
        print(f"Failed to fetch page: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()


Quick test Wikipedia scraper với URL cụ thể
"""
import requests
from bs4 import BeautifulSoup
import re

url = "https://en.wikipedia.org/wiki/Portal:Current_events/2015_March_27"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print("Testing Wikipedia scraper...")
print(f"URL: {url}")

try:
    response = requests.get(url, headers=headers, timeout=15)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find "Armed conflicts and attacks" section
        spans = soup.find_all('span', class_='mw-headline')
        armed_section = None
        
        for span in spans:
            text = span.get_text().strip()
            print(f"Found span: {text}")
            if 'Armed conflicts' in text or ('Attacks' in text and 'conflict' in text.lower()):
                armed_section = span.find_parent(['h2', 'h3', 'h4'])
                print(f"Found armed conflicts section: {armed_section.name if armed_section else 'None'}")
                break
        
        if armed_section:
            conflicts = []
            current = armed_section.find_next_sibling()
            section_level = int(armed_section.name[1])
            
            while current:
                if current.name in ['h2', 'h3', 'h4']:
                    current_level = int(current.name[1])
                    if current_level <= section_level:
                        break
                
                if current.name == 'ul':
                    items = current.find_all('li', recursive=False)
                    for item in items:
                        text = item.get_text()
                        text = re.sub(r'\[.*?\]', '', text)
                        text = re.sub(r'\([^)]*\)', '', text)
                        text = ' '.join(text.split())
                        if text.strip():
                            conflicts.append(text.strip())
                
                current = current.find_next_sibling()
            
            print(f"\nFound {len(conflicts)} conflicts:")
            for i, conflict in enumerate(conflicts, 1):
                print(f"  {i}. {conflict}")
        else:
            print("Could not find 'Armed conflicts and attacks' section")
            # Try to find all headings
            headings = soup.find_all(['h2', 'h3', 'h4'])
            print("\nAll headings found:")
            for h in headings[:10]:
                print(f"  {h.name}: {h.get_text().strip()[:50]}")
    else:
        print(f"Failed to fetch page: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

