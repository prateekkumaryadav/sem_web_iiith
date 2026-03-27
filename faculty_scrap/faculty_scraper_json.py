import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin
import time

class FacultyScraper:
    """
    Scraper to extract faculty details and save as JSON.
    Designed for semantic web conversion: JSON -> RDF -> OWL -> Ontology
    """
    
    def __init__(self, urls_file="iiith_fac.txt", output_file="faculty_data.json"):
        """
        Initialize the faculty scraper.
        
        Args:
            urls_file (str): Text file containing faculty URLs
            output_file (str): Output JSON file
        """
        self.urls_file = urls_file
        self.output_file = output_file
        self.faculty_data = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def extract_email(self, text, soup=None, raw_html=""):
        """Extract email from text and HTML elements using multiple methods."""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        # Pattern for emails with [at] format (anti-spam)
        email_pattern_at = r'[a-zA-Z0-9._%+-]+\[at\][a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        # Method 1: Look in mailto links
        if soup:
            mailto_links = soup.find_all('a', href=re.compile(r'mailto:', re.IGNORECASE))
            for link in mailto_links:
                href = link.get('href', '')
                email_match = re.search(email_pattern, href)
                if email_match:
                    return email_match.group()
        
        # Method 2: Look in elementor widget containers for [at] format emails
        if soup:
            elementor_widgets = soup.find_all(class_=re.compile(r'elementor-widget-container', re.IGNORECASE))
            for widget in elementor_widgets:
                text_content = widget.get_text()
                # Look for [at] format
                at_matches = re.findall(email_pattern_at, text_content, re.IGNORECASE)
                for match in at_matches:
                    # Convert [at] to @
                    email = match.replace('[at]', '@').replace('[AT]', '@').lower()
                    return email
                # Also look for regular @ format
                email_matches = re.findall(email_pattern, text_content)
                if email_matches:
                    return email_matches[0]
        
        # Method 3: Look in raw HTML (for Elementor and hidden elements)
        if raw_html:
            # First try [at] format
            at_matches = re.findall(email_pattern_at, raw_html, re.IGNORECASE)
            if at_matches:
                email = at_matches[0].replace('[at]', '@').replace('[AT]', '@').lower()
                return email
            
            # Then try regular @ format
            raw_matches = re.findall(email_pattern, raw_html)
            if raw_matches:
                # Filter to get only reasonable-looking emails
                for email in raw_matches:
                    if not email.endswith(('.jpg', '.png', '.gif')):
                        return email
        
        # Method 4: Look in plain text (with [at] format)
        at_matches = re.findall(email_pattern_at, text, re.IGNORECASE)
        if at_matches:
            email = at_matches[0].replace('[at]', '@').replace('[AT]', '@').lower()
            return email
        
        matches = re.findall(email_pattern, text)
        if matches:
            return matches[0]
        
        # Method 5: Look for email in specific classes
        if soup:
            email_elements = soup.find_all(['span', 'div', 'p'], 
                                          class_=re.compile(r'email|contact|mail|elementor', re.IGNORECASE))
            for elem in email_elements:
                text_content = elem.get_text()
                # Check [at] format first
                at_matches = re.findall(email_pattern_at, text_content, re.IGNORECASE)
                if at_matches:
                    email = at_matches[0].replace('[at]', '@').replace('[AT]', '@').lower()
                    return email
                # Then check regular format
                email_match = re.search(email_pattern, text_content)
                if email_match:
                    return email_match.group()
        
        # Method 6: Look in script tags (JSON-LD, etc.)
        if soup:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    script_emails = re.findall(email_pattern, script.string)
                    if script_emails:
                        return script_emails[0]
        
        return None
    
    def extract_phone(self, text):
        """Extract phone number from text."""
        phone_pattern = r'(\+?91[-.\s]?)?\d{10}|\d{4}[-.\s]\d{4}[-.\s]\d{4}'
        matches = re.findall(phone_pattern, text)
        return matches[0] if matches else None
    
    def remove_navigation_elements(self, soup):
        """Remove header, footer, and navigation elements from soup."""
        # Remove common navigation classes and ids
        nav_selectors = [
            'header', 'footer', 'nav', 'navigation',
            '[class*="menu"]', '[class*="navbar"]', '[class*="header"]',
            '[class*="footer"]', '[id*="menu"]', '[id*="nav"]',
            '.breadcrumb', '.pagination'
        ]
        
        for selector in nav_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        return soup
    
    def extract_from_structured_content(self, soup, page_text, raw_html=""):
        """Extract faculty info from structured HTML sections."""
        faculty_info = {
            "name": "",
            "title": "",
            "department": "",
            "email": "",
            "phone": "",
            "research_areas": [],
            "qualifications": [],
            "awards": [],
            "bio": ""
        }
        
        # Extract name - look for main heading on page
        headings = soup.find_all(['h1', 'h2'])
        for heading in headings:
            text = heading.get_text().strip()
            # Skip if it's a known menu item or too short
            if text and 10 < len(text) < 100 and not any(
                keyword in text.lower() for keyword in 
                ['menu', 'search', 'navigation', 'home', 'sitemap']
            ):
                faculty_info["name"] = text
                break
        
        # Extract email - Pass soup and raw_html for multi-method extraction
        email = self.extract_email(page_text, soup, raw_html)
        if email:
            faculty_info["email"] = email
        
        # Extract title/designation - look for specific patterns
        title_pattern = r'(Assistant Professor|Associate Professor|Professor|Lecturer|Instructor|Researcher|Fellow)[^.\n]*(?:Ph\.?D|M\.?[A-Z]+|B\.?[A-Z]+)?[^.\n]*'
        title_matches = re.findall(title_pattern, page_text, re.IGNORECASE)
        if title_matches:
            faculty_info["title"] = title_matches[0][:200]
        
        # Extract research areas - look for "Research areas" section
        areas_pattern = r'Research\s+areas?[:\s]+([^\n]+(?:\n[^\n]+)*?)(?=\n\n|Research|Awards|Center|Lab|$)'
        areas_matches = re.findall(areas_pattern, page_text, re.IGNORECASE | re.DOTALL)
        if areas_matches:
            areas_text = areas_matches[0]
            areas = [a.strip() for a in re.split('[,;]', areas_text) if a.strip()]
            faculty_info["research_areas"] = areas[:5]
        
        # Extract awards and achievements
        awards_pattern = r'(?:Awards?|Achievements?)[:\s]+([^\n]+(?:\n[^\n]+)*?)(?=\n\n|Research|$)'
        awards_matches = re.findall(awards_pattern, page_text, re.IGNORECASE | re.DOTALL)
        if awards_matches:
            awards_text = awards_matches[0]
            faculty_info["awards"] = awards_text.strip()[:300]
        
        # Extract research centers/labs
        center_pattern = r'(?:Research\s+Centers?|Labs?)[:\s]+([^\n]+(?:\n[^\n]+)*?)(?=\n\n|Awards|$)'
        center_matches = re.findall(center_pattern, page_text, re.IGNORECASE | re.DOTALL)
        if center_matches:
            faculty_info["department"] = center_matches[0].strip()[:200]
        
        # Extract qualifications
        degree_pattern = r'(B\.?(?:Tech|Sc|A)|M\.?(?:Tech|Sc|A)|Ph\.?D)[^,.\n]*'
        degrees = re.findall(degree_pattern, page_text, re.IGNORECASE)
        if degrees:
            faculty_info["qualifications"] = list(set(degrees[:5]))
        
        return faculty_info
    
    def extract_faculty_details(self, url):
        """
        Extract faculty details from a URL.
        
        Args:
            url (str): Faculty page URL
            
        Returns:
            dict: Faculty information structured for ontology conversion
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove navigation, header, footer elements
            soup = self.remove_navigation_elements(soup)
            
            # Get cleaned text content and raw HTML
            page_text = soup.get_text()
            raw_html = response.text
            
            # Extract structured data
            faculty_info = self.extract_from_structured_content(soup, page_text, raw_html)
            
            # Build final faculty record
            faculty = {
                "url": url,
                "name": faculty_info.get("name", ""),
                "title": faculty_info.get("title", ""),
                "department": faculty_info.get("department", ""),
                "email": faculty_info.get("email", ""),
                "phone": faculty_info.get("phone", ""),
                "research_areas": faculty_info.get("research_areas", []),
                "qualifications": faculty_info.get("qualifications", []),
                "awards": faculty_info.get("awards", ""),
                "bio": faculty_info.get("bio", ""),
                "office_location": "",
                "office_phone": ""
            }
            
            print(f"✓ Extracted: {faculty.get('name', 'Unknown')} - Email: {faculty.get('email', 'N/A')}")
            return faculty
            
        except requests.RequestException as e:
            print(f"✗ Error fetching {url}: {e}")
            return None
        except Exception as e:
            print(f"✗ Error processing {url}: {e}")
            return None
    
    def run(self):
        """Run the scraper and save results to JSON."""
        print(f"Reading URLs from {self.urls_file}...\n")
        
        try:
            # Read URLs from file
            with open(self.urls_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            print(f"Found {len(urls)} faculty URLs to scrape.\n")
            print("Starting faculty details extraction...\n")
            
            # Scrape each URL
            for index, url in enumerate(urls, 1):
                print(f"[{index}/{len(urls)}] Processing: {url}")
                
                faculty_details = self.extract_faculty_details(url)
                
                if faculty_details:
                    self.faculty_data.append(faculty_details)
                
                # Be respectful to server
                time.sleep(0.5)
            
            # Save to JSON
            print(f"\n\nSaving {len(self.faculty_data)} records to {self.output_file}...")
            
            output_data = {
                "metadata": {
                    "source": "IIITH Faculty Scraper",
                    "total_records": len(self.faculty_data),
                    "format": "JSON",
                    "description": "Faculty data structured for semantic web conversion (JSON -> RDF -> OWL -> Ontology)"
                },
                "faculty": self.faculty_data
            }
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Successfully saved faculty data to {self.output_file}")
            print(f"\nSummary:")
            print(f"  - Total faculty extracted: {len(self.faculty_data)}")
            print(f"  - Output file: {self.output_file}")
            print(f"  - Ready for RDF conversion")
            
            # Print sample data
            if self.faculty_data:
                print(f"\nSample record:")
                print(json.dumps(self.faculty_data[0], indent=2))
        
        except FileNotFoundError:
            print(f"✗ Error: Could not find {self.urls_file}")
            print(f"Make sure you have run web_scraper.py first to generate faculty URLs.")
        except Exception as e:
            print(f"✗ Error: {e}")

if __name__ == "__main__":
    # Get input file
    urls_file = input("Enter faculty URLs file [iiith_fac.txt]: ").strip() or "iiith_fac.txt"
    output_file = input("Enter output JSON file [faculty_data.json]: ").strip() or "faculty_data.json"
    
    scraper = FacultyScraper(urls_file, output_file)
    scraper.run()
