import requests
import xml.etree.ElementTree as ET
import re
from collections import Counter
import requests
from bs4 import BeautifulSoup
import chromadb
import config, json, uuid, os
from nltk.tokenize import word_tokenize
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter


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

def extract_info(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None, None

    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract content from the main tag or fallback to general method
    main_tag = soup.find('main')
    if main_tag:
        content_elements = main_tag.find_all(['p', 'div'])
    else:
        content_elements = soup.find_all(['p', 'div'])
    
    cleaned_elements = []
    for element in content_elements:
        # Remove elements with classes that hide content
        hiding_classes = ['visually-hidden', 'hidden', 'sr-only', 'd-none']
        for class_name in hiding_classes:
            hidden_elements = element.find_all(class_=class_name)
            for hidden_element in hidden_elements:
                hidden_element.decompose()

        # Remove unwanted tags
        for unwanted_tag in element.find_all(['script', 'style', 'noscript']):
            unwanted_tag.decompose()
        
        cleaned_elements.append(element)
    
    # Clean content: combine text with a single space between elements
    content = ' '.join(element.get_text() for element in cleaned_elements if element.get_text())
    # Ensure at least one space between elements
    # clean_content = re.sub(r'\s*\n\s*+', '#', content).strip()
    # clean_content = re.sub(r'\s+', ' ', clean_content).strip()
    # clean_content = re.sub(r'\s*#\s*+', '\n\n', clean_content).strip()  
    clean_content = ' '.join(content.split())

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

            #Store into embedded form
            site_name = input("Site name: ")
            directory_path = create_check_dir(site_name)
            if not directory_path:
                continue
            
            url_link = [item['url'] for item in lists]
            # url_link = ["https://www.natureleafteas.com/", 
            #             "https://www.natureleafteas.com/products/green-rooibos-bonita-rooibos-herbal-tea",
            #             "https://www.natureleafteas.com/products/masala-chai-black-chai-tea?variant=40402327961698",
            #             "https://www.natureleafteas.com/products/earl-grey-moonlight?variant=40400737468514"
            #             ]
            loader = UnstructuredURLLoader(urls=url_link)
            data = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            docs = text_splitter.split_documents(data)
            vectorstore = Chroma.from_documents(
                documents=docs, 
                embedding=GoogleGenerativeAIEmbeddings(model="models/embedding-001"),
                persist_directory=directory_path
            )
            print(f"Embedding completed")       
            
        except Exception as e:  
                print(f"Error: {e}")  
                break
