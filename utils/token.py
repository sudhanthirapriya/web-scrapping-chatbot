from nltk.tokenize import word_tokenize

def token_count(query):
    tokenized = word_tokenize(query)
    return len(tokenized)

def crop_query(query, max_tokens=5000):
    # Tokenize the query
    tokenized = word_tokenize(query)
    
    # Crop to the maximum number of tokens if necessary
    if len(tokenized) > max_tokens:
        tokenized = tokenized[:max_tokens]
    
    # Join tokens back into a string (optional)
    cropped_query = ' '.join(tokenized)
    
    return cropped_query, len(tokenized)