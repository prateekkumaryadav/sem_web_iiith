import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time

def is_relevant_url(url, page_text=""):
    # Keywords to filter relevant URLs
    # relevant_keywords = [
    #     'faculty', 'professor', 'staff',
    #     'academic', 'department', 'school',
    #     'course', 'curriculum', 'program', 'subject', 'placement', 'internship', 'recruitment', 'career',
    #     'people', 'team'
    # ]

    # manually tailored tags for IIITH
    # relevant_keywords = [
    #     'faculty'
    # ]

    # 
    relevant_keywords = [
        'degree'
    ]
    
    url_lower = url.lower()
    
    # Check if URL contains any relevant keywords
    for keyword in relevant_keywords:
        if keyword in url_lower:
            return True
    
    # Also check page content if provided
    if page_text:
        page_text_lower = page_text.lower()
        for keyword in relevant_keywords:
            if keyword in page_text_lower:
                return True
    
    return False

def scrape_urls(start_url, output_file="urls.txt", max_pages=100):
    
    # Set to store unique URLs
    visited_urls = set()
    relevant_urls = set()
    
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
                
                # Get page text for content-based filtering
                page_text = soup.get_text()
                
                # Extract all links
                for link in soup.find_all('a', href=True):
                    url = link['href']
                    link_text = link.get_text() if link.get_text() else ""
                    
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(current_url, url)
                    
                    # Parse the URL
                    parsed_url = urlparse(absolute_url)
                    
                    # Remove fragments (hash)
                    clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                    if parsed_url.query:
                        clean_url += f"?{parsed_url.query}"
                    
                    # Check if URL is relevant
                    is_relevant = is_relevant_url(clean_url, link_text)
                    
                    # Only follow links from the same domain
                    if parsed_url.netloc == base_domain:
                        # Add to relevant URLs only if it matches our criteria
                        if is_relevant:
                            relevant_urls.add(clean_url)
                        
                        # Always add to to_visit queue to explore all pages
                        if clean_url not in visited_urls:
                            to_visit.append(clean_url)
                    else:
                        # Save external relevant URLs found on the site
                        if is_relevant:
                            relevant_urls.add(absolute_url)
                
                # Small delay to be respectful to the server (not getting temporarily blocked)
                time.sleep(0.5)
                # time.sleep(4)
                
            except requests.RequestException as e:
                print(f"Error fetching {current_url}: {e}")
                continue
        
        # Write results to file
        print(f"\nFound {len(relevant_urls)} relevant URLs. Writing to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for url in sorted(relevant_urls):
                f.write(url + '\n')
        
        print(f"✓ Successfully saved URLs to {output_file}")
        print(f"Total pages crawled: {page_count}")
        print(f"Total relevant URLs found: {len(relevant_urls)}")
        
    except KeyboardInterrupt:
        print("\nManual Scraping interruption.")
    except Exception as e:
        print(f"error occurred: {e}")

if __name__ == "__main__":
    # url = input("Enter the URL to scrape (e.g., https://example.com): ").strip()
    
    url = "https://www.iiit.ac.in"

    # Validate URL
    # setted as only interested for the paths inside the webpage (especially for IIITH website)
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # customize output filename and max pages for managing the outputs
    output_file = input("Enter output filename [urls.txt]: ").strip() or "urls.txt"
    max_pages_input = input("Enter maximum pages to crawl [100]: ").strip()
    max_pages = int(max_pages_input) if max_pages_input.isdigit() else 100
    
    # web scraper started
    scrape_urls(url, output_file, max_pages)
