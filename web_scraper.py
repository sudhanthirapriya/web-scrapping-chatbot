import requests
from bs4 import BeautifulSoup
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

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
    clean_content = ' '.join(content.split())

    # Extract title or fallback to h1, then h2
    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag and title_tag.text else None

    if not title:  # If title is empty, try to find the first h1, then h2
        h1_tag = soup.find('h1')
        h2_tag = soup.find('h2')
        title = h1_tag.text.strip() if h1_tag else (h2_tag.text.strip() if h2_tag else None)

    return title, clean_content

# Main loop
if __name__ == "__main__":
    while True:
        url = input("Enter your URL: ")

        if url.lower() == "exit":
            print("Goodbye!")
            break

        if not validate_url(url):
            print("Invalid URL. Please enter a valid URL.")
            continue

        title, clean_content = extract_info(url)

        if title is None or clean_content is None:
            print("Failed to retrieve content from the URL.")
            continue

        # print(f"Title: {title}")
        # print(f"Content: {clean_content}")
        print(f"Size: {len(clean_content)}")

        # clean_content = preprocess_text(clean_content)

        filename = "sampleDataset.txt"  
        with open(filename, 'w', encoding='utf-8') as file:  
            # Write the text content to the file  
            file.write(clean_content)  

        