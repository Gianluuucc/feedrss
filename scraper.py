import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

def get_news(url):
    print(f"Scraping URL: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        news_items = []
        
        # Strategy 1: Look for specific Halley CMS patterns
        date_pattern = re.compile(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})')
        
        possible_dates = soup.find_all(string=date_pattern)
        
        print(f"Found {len(possible_dates)} potential dates")
        
        seen_links = set()
        
        for date_str in possible_dates:
            date_text = date_str.strip()
            match = date_pattern.search(date_text)
            if not match:
                continue
                
            try:
                day, month, year = map(int, match.groups())
                date_obj = datetime(year, month, day)
            except ValueError:
                continue
                
            container = date_str.parent
            
            found_link = False
            current_element = container
            
            for _ in range(4):
                if current_element is None:
                    break
                
                if current_element.name in ['tr', 'div', 'li', 'p']:
                    link_tag = current_element.find('a', href=True)
                    if link_tag:
                        link = urljoin(url, link_tag['href'])
                        
                        if 'javascript:' in link or link.endswith('#'):
                            continue

                        if link in seen_links:
                            found_link = True
                            break
                            
                        title = link_tag.get_text(strip=True)
                        if not title:
                            title = link_tag.get('title') or ''
                            
                        if not title:
                            continue
                            
                        title = re.sub(r'\s+', ' ', title)
                        # Remove control characters that are invalid in XML
                        title = "".join(ch for ch in title if (0x20 <= ord(ch) <= 0xD7FF) or (0xE000 <= ord(ch) <= 0xFFFD) or (0x10000 <= ord(ch) <= 0x10FFFF) or ch in '\t\n\r')
                        
                        news_items.append({
                            'title': title,
                            'link': link,
                            'pubDate': date_obj,
                            'description': title
                        })
                        seen_links.add(link)
                        found_link = True
                        break
                
                current_element = current_element.parent
            
            if not found_link:
                pass 

        # Strategy 2: Fallback
        if len(news_items) < 1:
            print("Strategy 1 yielded few results, trying generic extraction")
            for selector in ['.news-item', '.article', '.post', '.entry', '.avviso', '.comunicato', 'table.news tr']:
                for container in soup.select(selector):
                    link_tag = container.find('a', href=True)
                    if link_tag:
                        link = urljoin(url, link_tag['href'])
                        if link in seen_links: continue
                        
                        title = link_tag.get_text(strip=True)
                        if title:
                            news_items.append({
                                'title': title,
                                'link': link,
                                'pubDate': datetime.now(),
                                'description': ''
                            })
                            seen_links.add(link)

        print(f"Total news items found: {len(news_items)}")
        return news_items

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []
