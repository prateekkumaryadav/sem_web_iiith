import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time

def is_course_url(url, page_text=""):
    """
    Check if a URL is relevant to courses/academics.
    
    Args:
        url (str): The URL to check
        page_text (str): Optional page text content for additional filtering
    
    Returns:
        bool: True if URL is course-related
    """
    # Keywords to filter course-related URLs
    course_keywords = [
        'course', 'curriculum', 'syllabus', 'program',
        'subject', 'module', 'academic', 'discipline',
        'class', 'lectures', 'schedule', 'timetable'
    ]
    
    url_lower = url.lower()
    
    # Check if URL contains any course-related keywords
    for keyword in course_keywords:
        if keyword in url_lower:
            return True
    
    # Also check page content if provided
    if page_text:
        page_text_lower = page_text.lower()
        for keyword in course_keywords:
            if keyword in page_text_lower:
                return True
    
    return False

def scrape_course_urls(start_url, output_file="course_urls.txt", max_pages=100):
    """
    Scrape course URLs from a website and save to a text file.
    
    Args:
        start_url (str): The starting URL to scrape
        output_file (str): Name of the output text file
        max_pages (int): Maximum number of pages to crawl
    """
    
    # Set to store unique URLs
    visited_urls = set()
    course_urls = set()
    
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
                print(f"Crawling ({page_count}): {current_url}")
                
                # Fetch the page
                response = requests.get(current_url, headers=headers, timeout=10)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
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
                    
                    # Check if URL is course-related
                    is_course = is_course_url(clean_url, link_text)
                    
                    # Only follow links from the same domain
                    if parsed_url.netloc == base_domain:
                        # Add to course URLs only if it matches our criteria
                        if is_course:
                            course_urls.add(clean_url)
                        
                        # Always add to to_visit queue to explore all pages
                        if clean_url not in visited_urls:
                            to_visit.append(clean_url)
                    else:
                        # Save external course-related URLs found on the site
                        if is_course:
                            course_urls.add(absolute_url)
                
                # Small delay to be respectful to the server
                time.sleep(0.5)
                
            except requests.RequestException as e:
                print(f"Error fetching {current_url}: {e}")
                continue
        
        # Write results to file
        print(f"\nFound {len(course_urls)} course URLs. Writing to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for url in sorted(course_urls):
                f.write(url + '\n')
        
        print(f"✓ Successfully saved course URLs to {output_file}")
        print(f"Total pages crawled: {page_count}")
        print(f"Total unique course URLs found: {len(course_urls)}")
        
    except KeyboardInterrupt:
        print("\nCrawling interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Get URL from user
    url = input("Enter the URL to scrape for courses (e.g., https://iiit.ac.in): ").strip()
    
    # Validate URL
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Optional: customize output filename and max pages
    output_file = input("Enter output filename [course_urls.txt]: ").strip() or "course_urls.txt"
    max_pages_input = input("Enter maximum pages to crawl [100]: ").strip()
    max_pages = int(max_pages_input) if max_pages_input.isdigit() else 100
    
    print("\nStarting course URL scraper...\n")
    scrape_course_urls(url, output_file, max_pages)
