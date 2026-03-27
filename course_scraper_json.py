import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin
import time

class CourseScraper:
    """
    Scraper to extract course details and save as JSON.
    Designed for semantic web conversion: JSON -> RDF -> OWL -> Ontology
    """
    
    def __init__(self, urls_file="course_urls.txt", output_file="course_data.json"):
        """
        Initialize the course scraper.
        
        Args:
            urls_file (str): Text file containing course URLs
            output_file (str): Output JSON file
        """
        self.urls_file = urls_file
        self.output_file = output_file
        self.course_data = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def extract_course_code(self, text):
        """Extract course code from text (e.g., CS101, ECE201)."""
        # Pattern for course codes like CS101, ECE-201, CS 101
        pattern = r'([A-Z]{2,4}[-\s]?\d{3,4})'
        matches = re.findall(pattern, text)
        return matches[0] if matches else None
    
    def extract_credits(self, text):
        """Extract course credits from text."""
        # Pattern for credits like "3 credits", "3-0-0", "4 credit hours"
        pattern = r'(\d+)\s*[-/]?\s*(\d+)?\s*[-/]?\s*(\d+)?\s*(?:credits?|hours?|units?)'
        matches = re.findall(pattern, text, re.IGNORECASE)
        return matches[0] if matches else None
    
    def extract_email(self, text, soup=None, raw_html=""):
        """Extract email from text and HTML elements using multiple methods."""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_pattern_at = r'[a-zA-Z0-9._%+-]+\[at\][a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        # Method 1: Look in mailto links
        if soup:
            mailto_links = soup.find_all('a', href=re.compile(r'mailto:', re.IGNORECASE))
            for link in mailto_links:
                href = link.get('href', '')
                email_match = re.search(email_pattern, href)
                if email_match:
                    return email_match.group()
        
        # Method 2: Look for [at] format in raw HTML
        if raw_html:
            at_matches = re.findall(email_pattern_at, raw_html, re.IGNORECASE)
            if at_matches:
                email = at_matches[0].replace('[at]', '@').replace('[AT]', '@').lower()
                return email
        
        # Method 3: Look in plain text
        at_matches = re.findall(email_pattern_at, text, re.IGNORECASE)
        if at_matches:
            email = at_matches[0].replace('[at]', '@').replace('[AT]', '@').lower()
            return email
        
        matches = re.findall(email_pattern, text)
        if matches:
            return matches[0]
        
        return None
    
    def remove_navigation_elements(self, soup):
        """Remove header, footer, and navigation elements from soup."""
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
    
    def extract_course_details(self, url):
        """
        Extract course details from a URL.
        
        Args:
            url (str): Course page URL
            
        Returns:
            dict: Course information structured for ontology conversion
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove navigation elements
            soup = self.remove_navigation_elements(soup)
            
            # Get text content
            page_text = soup.get_text()
            raw_html = response.text
            
            course = {
                "url": url,
                "course_name": "",
                "course_code": "",
                "department": "",
                "credits": "",
                "description": "",
                "prerequisites": [],
                "instructor": "",
                "instructor_email": "",
                "learning_outcomes": [],
                "topics_covered": [],
                "semester": "",
                "level": "",
                "textbooks": [],
                "course_type": "",
                "evaluation": {}
            }
            
            # Extract course name (usually in h1 or title)
            headings = soup.find_all(['h1', 'h2'])
            for heading in headings:
                text = heading.get_text().strip()
                if text and len(text) > 5 and len(text) < 200:
                    course["course_name"] = text
                    break
            
            # Extract course code
            code = self.extract_course_code(page_text)
            if code:
                course["course_code"] = code.replace(' ', '').replace('-', '')
            
            # Extract credits
            credits_match = self.extract_credits(page_text)
            if credits_match:
                course["credits"] = f"{credits_match[0]}-{credits_match[1] or '0'}-{credits_match[2] or '0'}"
            
            # Extract department
            dept_keywords = ['department', 'school', 'center', 'offered by']
            for keyword in dept_keywords:
                pattern = rf'{keyword}[:\s]+([^\n,]+)'
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                if matches:
                    course["department"] = matches[0].strip()[:150]
                    break
            
            # Extract course level
            level_keywords = {
                'undergraduate': r'(?:undergraduate|UG|intro|beginner)',
                'postgraduate': r'(?:postgraduate|PG|graduate|advanced)',
                'master': r'(?:M\.Tech|M\.Sc|master)',
                'phd': r'(?:Ph\.D|doctorate)'
            }
            for level, pattern in level_keywords.items():
                if re.search(pattern, page_text, re.IGNORECASE):
                    course["level"] = level
                    break
            
            # Extract course type
            type_keywords = {
                'core': r'(?:core|mandatory|required)',
                'elective': r'(?:elective|optional)',
                'lab': r'(?:lab|laboratory|practical)',
                'seminar': r'(?:seminar|workshop)',
                'project': r'(?:project|capstone)'
            }
            for ctype, pattern in type_keywords.items():
                if re.search(pattern, page_text, re.IGNORECASE):
                    course["course_type"] = ctype
                    break
            
            # Extract description (first meaningful paragraph)
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if text and len(text) > 50 and len(text) < 500:
                    course["description"] = text
                    break
            
            # Extract prerequisites
            prereq_pattern = r'(?:prerequisites?|requires?)[:\s]+([^\n]+)'
            prereq_matches = re.findall(prereq_pattern, page_text, re.IGNORECASE)
            if prereq_matches:
                prereqs = prereq_matches[0].split(',')
                course["prerequisites"] = [p.strip() for p in prereqs[:5]]
            
            # Extract learning outcomes
            outcomes_pattern = r'(?:learning outcomes?|course outcomes?|objectives?)[:\s]+([^\n]+(?:\n[^\n]+)*?)(?=\n\n|assessment|evaluation|$)'
            outcomes_matches = re.findall(outcomes_pattern, page_text, re.IGNORECASE | re.DOTALL)
            if outcomes_matches:
                outcomes_text = outcomes_matches[0]
                outcomes = [o.strip() for o in re.split('[•\-\*\n]', outcomes_text) if o.strip()]
                course["learning_outcomes"] = outcomes[:5]
            
            # Extract topics covered
            topics_pattern = r'(?:topics?|content|syllabus)[:\s]+([^\n]+(?:\n[^\n]+)*?)(?=\n\n|assessment|evaluation|$)'
            topics_matches = re.findall(topics_pattern, page_text, re.IGNORECASE | re.DOTALL)
            if topics_matches:
                topics_text = topics_matches[0]
                topics = [t.strip() for t in re.split('[•\-\*\n,]', topics_text) if t.strip()]
                course["topics_covered"] = topics[:8]
            
            # Extract instructor information
            instructor_pattern = r'(?:instructor|taught by|course taught by|faculty)[:\s]+([^,\n]+)'
            instructor_matches = re.findall(instructor_pattern, page_text, re.IGNORECASE)
            if instructor_matches:
                course["instructor"] = instructor_matches[0].strip()[:150]
            
            # Extract instructor email
            instructor_email = self.extract_email(page_text, soup, raw_html)
            if instructor_email:
                course["instructor_email"] = instructor_email
            
            # Extract semester information
            semester_pattern = r'(?:semester|offered in|schedule)[:\s]+([^\n]+)'
            semester_matches = re.findall(semester_pattern, page_text, re.IGNORECASE)
            if semester_matches:
                course["semester"] = semester_matches[0].strip()[:100]
            
            # Extract evaluation criteria
            eval_pattern = r'(?:evaluation|assessment|grading)[:\s]+([^\n]+(?:\n[^\n]+)*?)(?=\n\n|textbook|$)'
            eval_matches = re.findall(eval_pattern, page_text, re.IGNORECASE | re.DOTALL)
            if eval_matches:
                eval_text = eval_matches[0]
                # Try to parse grading components
                exam_pattern = r'(?:exam|quiz|midterm|final)[:\s]*(\d+)'
                project_pattern = r'(?:project|assignment)[:\s]*(\d+)'
                participation_pattern = r'(?:participation|attendance)[:\s]*(\d+)'
                
                exam_match = re.search(exam_pattern, eval_text, re.IGNORECASE)
                project_match = re.search(project_pattern, eval_text, re.IGNORECASE)
                participation_match = re.search(participation_pattern, eval_text, re.IGNORECASE)
                
                if exam_match:
                    course["evaluation"]["exam"] = exam_match.group(1) + "%"
                if project_match:
                    course["evaluation"]["project"] = project_match.group(1) + "%"
                if participation_match:
                    course["evaluation"]["participation"] = participation_match.group(1) + "%"
            
            # Extract textbooks
            textbook_pattern = r'(?:textbooks?|references?|books?)[:\s]+([^\n]+(?:\n[^\n]+)*?)(?=\n\n|$)'
            textbook_matches = re.findall(textbook_pattern, page_text, re.IGNORECASE | re.DOTALL)
            if textbook_matches:
                textbook_text = textbook_matches[0]
                textbooks = [t.strip() for t in re.split('[•\-\*\n]', textbook_text) if t.strip()]
                course["textbooks"] = textbooks[:5]
            
            print(f"✓ Extracted: {course.get('course_name', 'Unknown')} ({course.get('course_code', 'N/A')})")
            return course
            
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
            
            print(f"Found {len(urls)} course URLs to scrape.\n")
            print("Starting course details extraction...\n")
            
            # Scrape each URL
            for index, url in enumerate(urls, 1):
                print(f"[{index}/{len(urls)}] Processing: {url}")
                
                course_details = self.extract_course_details(url)
                
                if course_details:
                    self.course_data.append(course_details)
                
                # Be respectful to server
                time.sleep(0.5)
            
            # Save to JSON
            print(f"\n\nSaving {len(self.course_data)} course records to {self.output_file}...")
            
            output_data = {
                "metadata": {
                    "source": "IIITH Course Scraper",
                    "total_records": len(self.course_data),
                    "format": "JSON",
                    "description": "Course data structured for semantic web conversion (JSON -> RDF -> OWL -> Ontology)"
                },
                "courses": self.course_data
            }
            
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Successfully saved course data to {self.output_file}")
            print(f"\nSummary:")
            print(f"  - Total courses extracted: {len(self.course_data)}")
            print(f"  - Output file: {self.output_file}")
            print(f"  - Ready for RDF conversion")
            
            # Print sample data
            if self.course_data:
                print(f"\nSample record:")
                print(json.dumps(self.course_data[0], indent=2))
        
        except FileNotFoundError:
            print(f"✗ Error: Could not find {self.urls_file}")
            print(f"Make sure you have run web_scraper.py first to generate course URLs.")
        except Exception as e:
            print(f"✗ Error: {e}")

if __name__ == "__main__":
    # Get input file
    urls_file = input("Enter course URLs file [course_urls.txt]: ").strip() or "course_urls.txt"
    output_file = input("Enter output JSON file [course_data.json]: ").strip() or "course_data.json"
    
    scraper = CourseScraper(urls_file, output_file)
    scraper.run()
