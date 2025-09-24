import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import json
import time
from typing import Set, List, Dict

class DeltaruneScraper:
    def __init__(self):
        self.base_url = "https://deltarune.fandom.com/wiki/"  # Changed to Fandom wiki
        self.visited_urls: Set[str] = set()
        self.keywords = {
            'ralsei'
        }
        self.min_content_length = 50  # Reduced minimum length for content
        self.session = requests.Session()
        self.collected_data: List[Dict] = []
        
        # Set up session with proper headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })

    def is_valid_url(self, url: str) -> bool:
        """Check if URL belongs to the wiki domain and hasn't been visited."""
        parsed = urlparse(url)
        return (
            'deltarune.fandom.com' in parsed.netloc and
            '/wiki/' in url and  # Only process wiki article pages
            not any(x in url for x in ['Special:', 'File:', 'User:', 'Talk:', 'Category:', 'Help:', 'Blog:', 'Template:']) and
            not url.endswith(('.jpg', '.png', '.gif', '.css', '.js')) and
            not '#' in url and  # Skip section anchors
            url not in self.visited_urls
        )

    def contains_keywords(self, text: str) -> bool:
        """Check if text contains any of the keywords."""
        return any(keyword.lower() in text.lower() for keyword in self.keywords)

    def clean_text(self, text: str) -> str:
        """Clean extracted text by removing extra whitespace and special characters."""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\[edit\]', '', text)
        return text.strip()

    def save_data(self):
        """Save the collected data to a JSON file."""
        with open('deltarune_wiki_data.json', 'w', encoding='utf-8') as f:
            json.dump(self.collected_data, f, ensure_ascii=False, indent=2)

    def extract_content(self, soup: BeautifulSoup, url: str) -> None:
        """Extract relevant content from the page."""
        main_content = soup.find('div', {'id': 'mw-content-text'})  # Changed to correct content div
        if not main_content:
            print(f"No main content found for {url}")
            return

        # Extract title
        title = soup.find('h1', {'id': 'firstHeading'})
        title_text = title.get_text().strip() if title else "No Title"

        # Extract paragraphs and headers
        content_elements = main_content.find_all(['p', 'h2', 'h3', 'h4', 'li'])
        
        page_content = []
        for element in content_elements:
            text = self.clean_text(element.get_text())
            if len(text) >= self.min_content_length:
                has_keywords = self.contains_keywords(text)
                if has_keywords:
                    page_content.append({
                        'type': element.name,
                        'content': text
                    })
                print(f"Found content [{len(text)} chars] {'✓' if has_keywords else '✗'} Keywords: {text[:100]}...")

        if page_content:  # Only save if we found relevant content
            self.collected_data.append({
                'title': title_text,
                'url': url,
                'content': page_content
            })
            # Save immediately after finding content
            self.save_data()

    def scrape_page(self, url: str) -> Set[str]:
        """Scrape a single page and return all found links."""
        if not self.is_valid_url(url):
            return set()

        self.visited_urls.add(url)
        print(f"Scraping: {url}")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = self.session.get(url, timeout=10, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract content from the current page
            print(f"\nProcessing page: {url}")
            self.extract_content(soup, url)

            # Save data after each page
            if len(self.collected_data) > 0:
                self.save_data()

            # Find all links on the page
            links = set()
            main_content = soup.find('div', {'id': 'mw-content-text'})
            if main_content:
                for a_tag in main_content.find_all('a', href=True):
                    new_url = urljoin(url, a_tag['href'])
                    if self.is_valid_url(new_url):
                        links.add(new_url)

            time.sleep(1)  # Be nice to the server
            return links

        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return set()

    def start_scraping(self, max_pages: int = 1000):
        """Start the scraping process from the base URL."""
        to_visit = {self.base_url}
        
        while to_visit and len(self.visited_urls) < max_pages:
            current_url = to_visit.pop()
            new_links = self.scrape_page(current_url)
            to_visit.update(new_links - self.visited_urls)

        # Save the collected data
        with open('deltarune_wiki_data.json', 'w', encoding='utf-8') as f:
            json.dump(self.collected_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    scraper = DeltaruneScraper()
    scraper.start_scraping()
    print(f"Scraping completed. Visited {len(scraper.visited_urls)} pages.")
    print(f"Collected data saved to 'deltarune_wiki_data.json'")
