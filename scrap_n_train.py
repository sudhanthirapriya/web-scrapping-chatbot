import requests
import xml.etree.ElementTree as ET
import re
from collections import Counter
import requests
from bs4 import BeautifulSoup
import chromadb
import config, json, uuid, os
from nltk.tokenize import word_tokenize
from playwright.sync_api import sync_playwright
import time

def parse_sitemap(sitemap_content, nested=False):
    root = ET.fromstring(sitemap_content)
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    
    urls = []
    if nested:
        sitemap_urls = [sitemap.find('ns:loc', namespace).text for sitemap in root.findall('ns:sitemap', namespace)]
        for url in sitemap_urls:
            response = requests.get(url)
            response.raise_for_status()
            urls.extend(parse_sitemap(response.content, nested=False))
    else:
        for url_element in root.findall('ns:url', namespace):
            loc = url_element.find('ns:loc', namespace).text
            if loc and validate_url(loc):
                url_type = determine_url_type(loc)
                urls.append({"url": loc, "type": url_type})
    return urls

def determine_url_type(url):
    if '/collections/' in url:
        return 'collections'
    elif '/products/' in url:
        return 'products'
    elif '/articles/' in url:
        return 'articles'
    elif '/blogs/' in url:
        return 'blogs'
    else:
        return 'pages'
    
def validate_url(url):
    # Regex for basic URL validation
    url_pattern = re.compile(r'^(https?|ftp):\/\/[^\s/$.?#].[^\s]*$')
    status = re.match(url_pattern, url)
    return status

def get_sitemap_urls(sitemap_url):
    try:
        # Fetch and parse the initial sitemap
        response = requests.get(sitemap_url)
        response.raise_for_status()
        sitemap_content = response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return False
    
    # Determine if the sitemap is an index or a direct sitemap
    root = ET.fromstring(sitemap_content)
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    
    if root.find('ns:url', namespace) is not None:
        # It’s a direct sitemap
        return parse_sitemap(sitemap_content, nested=False)
    elif root.find('ns:sitemap', namespace) is not None:
        # It’s a sitemap index
        return parse_sitemap(sitemap_content, nested=True)
    else:
        raise ValueError("Unsupported sitemap format")


def validate_url(url):
    # Regex for basic URL validation
    url_pattern = re.compile(r'^(https?|ftp):\/\/[^\s/$.?#].[^\s]*$')
    return re.match(url_pattern, url)


def clean_text(text):
    # Step 1: Split the text by newlines
    lines = text.split('\n')
    
    # Step 2: Clean each line by removing extra spaces, tabs, and trailing spaces
    cleaned_lines = []
    for line in lines:
        # Remove leading/trailing spaces and reduce multiple spaces/tabs within the line
        cleaned_line = re.sub(r'[ \t]+', ' ', line).strip()
        # Append only non-empty cleaned lines
        if cleaned_line:
            cleaned_lines.append(cleaned_line)
    
    # Step 3: Join the cleaned lines with single newlines
    result = '\n'.join(cleaned_lines)
    # Step 4: Split by ". " (period followed by space) and rejoin with newlines
    result = '\n'.join(result.split(". "))
    return result

def extract_info(url, use_js_rendering = False):
    try:
        if use_js_rendering:
            with sync_playwright() as p:
                browser = p.firefox.launch(headless=True)  # Use Firefox instead of Chromium
                page = browser.new_page()
                page.goto(url)
                time.sleep(5)
                content = page.content()  # Get the fully rendered HTML content
                browser.close()
                html_content = content
        else:
            # Use standard requests for static content
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
            html_content = response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None, None
    
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove unwanted tags like <script>, <style>, etc.
    for tag in soup(['script', 'style', 'head', 'footer', 'header']):
        tag.extract()
    
    # Get the visible text from the remaining content
    visible_text = soup.get_text(separator=' ')
    # Clean the extracted text
    clean_content = clean_text(visible_text)

    # Extract title or fallback to h1, then h2
    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag and title_tag.text else None

    if not title:  # If title is empty, try to find the first h1, then h2
        h1_tag = soup.find('h1')
        h2_tag = soup.find('h2')
        title = h1_tag.text.strip() if h1_tag else (h2_tag.text.strip() if h2_tag else None)

    return title, clean_content


def create_check_dir(site_name):
    try:  
        directory_path = f"./store/{site_name}"  
        os.makedirs(directory_path)  
        print(f"Directory '{directory_path}' created successfully.") 
        return directory_path
    except FileExistsError:  
        print(f"Error: The directory '{directory_path}' already exists.")  
        return False
    
# Main loop
if __name__ == "__main__":
    while True:
        try:  
            sitemap_url = input("Enter your Sitemap URL (https://sitename.com/sitemap.xml) or exit: ")
            if sitemap_url.lower() == "exit":
                print("Goodbye!")
                break

            
            sitemap_url = f"{sitemap_url}"
            lists = get_sitemap_urls(sitemap_url)
            type_counts = Counter(item['type'] for item in lists)
            print(type_counts)

            site_name = input("Site name: ")
            directory_path = create_check_dir(site_name)
            if not directory_path:
                continue
            
            js_framework = input("Site build on JS framework (y/n): ")
            use_js_rendering = False
            if js_framework.lower() == 'y': use_js_rendering = True
            
            client = chromadb.PersistentClient(path=directory_path)
            collection = client.get_or_create_collection(name="website")

            for index, list in enumerate(lists):
                url = list['url']
                type = list['type']
                if not validate_url(url):
                    print("Invalid Scrap URL:", url)
                    continue

                title, content = extract_info(url, use_js_rendering)
                print(f"title: {title}")
                print(f"content: {content[:20]}")
                if title is None or content is None:
                    print("Failed to retrieve content from the URL:", url)
                    continue

                collection.add(
                        documents=[json.dumps({"title": title, "content": content, "url": url})],
                        metadatas=[{"type": type, "is_active": True}],
                        ids=[str(uuid.uuid4())]
                    )
                print(f"Loaded: {index+1}/{len(lists)}.")       
            
        except Exception as e:  
                print(f"Error: {e}")  
                break
