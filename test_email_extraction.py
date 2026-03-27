import requests
from bs4 import BeautifulSoup
import re
import json

def test_email_extraction(url):
    """Test email extraction on a single URL (handles Elementor pages)."""
    print(f"\n{'='*60}")
    print(f"Testing URL: {url}")
    print(f"{'='*60}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text()
        raw_html = response.text
        
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        print("\n1. Looking for MAILTO links...")
        mailto_links = soup.find_all('a', href=re.compile(r'mailto:', re.IGNORECASE))
        if mailto_links:
            for link in mailto_links:
                href = link.get('href', '')
                print(f"   Found: {href}")
                email_match = re.search(email_pattern, href)
                if email_match:
                    print(f"   ✓ Extracted email: {email_match.group()}")
        else:
            print("   No mailto links found")
        
        print("\n2. Looking in page text with regex...")
        text_matches = re.findall(email_pattern, page_text)
        if text_matches:
            print(f"   ✓ Found {len(text_matches)} email(s):")
            for email in text_matches[:3]:
                print(f"     - {email}")
        else:
            print("   No emails found in page text")
        
        print("\n3. Looking in email-specific HTML elements...")
        email_elements = soup.find_all(['span', 'div', 'p'], 
                                      class_=re.compile(r'email|contact|mail', re.IGNORECASE))
        if email_elements:
            print(f"   Found {len(email_elements)} email-related elements:")
            for elem in email_elements[:3]:
                text_content = elem.get_text().strip()
                print(f"     - {text_content[:80]}")
        else:
            print("   No email-specific elements found")
        
        print("\n4. Looking in raw HTML for emails (Elementor widgets)...")
        raw_emails = re.findall(email_pattern, raw_html)
        if raw_emails:
            print(f"   ✓ Found {len(set(raw_emails))} unique email(s) in raw HTML:")
            for email in set(raw_emails)[:5]:
                print(f"     - {email}")
        else:
            print("   No emails found in raw HTML")
        
        print("\n5. Looking for script tags with JSON data...")
        scripts = soup.find_all('script')
        for idx, script in enumerate(scripts):
            if script.string:
                if 'email' in script.string.lower() or '@' in script.string:
                    print(f"   Script {idx}: Found email-related content")
                    # Try to find emails in this script
                    script_emails = re.findall(email_pattern, script.string)
                    if script_emails:
                        print(f"     Emails: {script_emails[:3]}")
        
        print("\n6. Looking for microdata/schema.org...")
        schema_elements = soup.find_all(['div', 'span'], 
                                       attrs={'itemtype': re.compile(r'schema.org|Person', re.IGNORECASE)})
        if schema_elements:
            print(f"   Found {len(schema_elements)} schema.org elements")
            for elem in schema_elements[:2]:
                text = elem.get_text()[:200]
                print(f"     - {text}...")
        
        print("\n8. Looking specifically in Elementor widget containers for [at] format emails...")
        elementor_widgets = soup.find_all(class_=re.compile(r'elementor-widget-container', re.IGNORECASE))
        if elementor_widgets:
            print(f"   Found {len(elementor_widgets)} elementor widgets")
            email_pattern_at = r'[a-zA-Z0-9._%+-]+\[at\][a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            for widget in elementor_widgets:
                text_content = widget.get_text().strip()
                if text_content and '@' not in text_content:  # Only show non-empty that might have emails
                    at_matches = re.findall(email_pattern_at, text_content, re.IGNORECASE)
                    if at_matches:
                        print(f"   ✓ Found [at] format email: {text_content[:100]}")
                        for match in at_matches:
                            converted = match.replace('[at]', '@').replace('[AT]', '@').lower()
                            print(f"     - Original: {match}")
                            print(f"     - Converted: {converted}")
        else:
            print("   No elementor widget containers found")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test with a few faculty URLs
    test_urls = [
        "https://www.iiit.ac.in/faculty/aakansha-natani/",
        "https://www.iiit.ac.in/faculty/abhishek-deshpande/",
        "https://www.iiit.ac.in/faculty/jayanthi-sivaswamy/"
    ]
    
    for url in test_urls:
        test_email_extraction(url)
