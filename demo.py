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
    # print(visible_text)
    # Clean the extracted text
    cleaned_content = clean_text(visible_text)
    

    # Extract title or fallback to h1, then h2
    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag and title_tag.text else None

    if not title:  # If title is empty, try to find the first h1, then h2
        h1_tag = soup.find('h1')
        h2_tag = soup.find('h2')
        title = h1_tag.text.strip() if h1_tag else (h2_tag.text.strip() if h2_tag else None)

    return title, cleaned_content

    
# Main loop
if __name__ == "__main__":
    title, content = extract_info("https://www.steppingedge.com/cyber/devsecops-and-secure-development", True)
    filename = "page2.txt"  
    with open(filename, 'w', encoding='utf-8') as file:  
        file.write(content) 
    exit()