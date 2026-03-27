import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time

def scrape_urls(start_url, output_file="urls.txt", max_pages=100):
    """
    Scrape all URLs accessible from a given URL and save to a text file.
    
    Args:
        start_url (str): The starting URL to scrape
        output_file (str): Name of the output text file
        max_pages (int): Maximum number of pages to crawl
    """
    
    # Set to store unique URLs
    visited_urls = set()
    all_urls = set()
    
    # Queue for BFS traversal
    to_visit = deque([start_url])
    
    # Parse the base domain to stay within the same website
    base_domain = urlparse(start_url).netloc
    
    # Headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    page_count = 0
    
    try:
        while to_visit and page_count < max_pages:
            current_url = to_visit.popleft()
            
            # Skip if already visited
            if current_url in visited_urls:
                continue
            
            visited_urls.add(current_url)
            page_count += 1
            
            try:
                print(f"Scraping ({page_count}): {current_url}")
                
                # Fetch the page
                response = requests.get(current_url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract all links
                for link in soup.find_all('a', href=True):
                    url = link['href']
                    
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(current_url, url)
                    
                    # Parse the URL
                    parsed_url = urlparse(absolute_url)
                    
                    # Remove fragments (hash)
                    clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                    if parsed_url.query:
                        clean_url += f"?{parsed_url.query}"
                    
                    # Only follow links from the same domain
                    if parsed_url.netloc == base_domain:
                        all_urls.add(clean_url)
                        
                        if clean_url not in visited_urls:
                            to_visit.append(clean_url)
                    else:
                        # Still save external URLs found on the site
                        all_urls.add(absolute_url)
                
                # Small delay to be respectful to the server
                time.sleep(0.5)
                
            except requests.RequestException as e:
                print(f"Error fetching {current_url}: {e}")
                continue
        
        # Write results to file
        print(f"\nFound {len(all_urls)} unique URLs. Writing to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for url in sorted(all_urls):
                f.write(url + '\n')
        
        print(f"✓ Successfully saved URLs to {output_file}")
        print(f"Total pages crawled: {page_count}")
        print(f"Total unique URLs found: {len(all_urls)}")
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Get URL from user
    url = input("Enter the URL to scrape (e.g., https://example.com): ").strip()
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Optional: customize output filename and max pages
    output_file = input("Enter output filename [urls.txt]: ").strip() or "urls.txt"
    max_pages_input = input("Enter maximum pages to crawl [100]: ").strip()
    max_pages = int(max_pages_input) if max_pages_input.isdigit() else 100
    
    print("\nStarting web scraper...\n")
    scrape_urls(url, output_file, max_pages)
