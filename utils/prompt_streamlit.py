import json, config
import chromadb
import streamlit as st
import traceback
from rank_bm25 import BM25Okapi
from utils.token import token_count
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.docstore.document import Document
import uuid, math
import spacy
import numpy as np

# Load the spaCy model for English (with word vectors)
nlp = spacy.load("en_core_web_md")

MAX_INPUT_TOKEN = 5000
n_results = 5

def split_text_into_chunks(text, chunk_size_in_tokens):
    words = text.split()  # Split the text into words
    return [' '.join(words[i:i + chunk_size_in_tokens]) for i in range(0, len(words), chunk_size_in_tokens)]

def store_into_temp_rag(data, reducing_factor):
    try:
        print("INITATE STORING....")
        client = chromadb.PersistentClient(path=st.session_state['store_dir'])
        collection = client.get_or_create_collection(name="temp")
        docs_to_add = []
        ids_to_add = []
        metadata_to_add = []

        for index, document in enumerate(data):
            content = document['content']
            doc_token = token_count(content)
            chunk_size = reducing_factor * doc_token
            chunk_size = math.floor(chunk_size / n_results)
            # print(f"acutal_size of doc({index}): {doc_token}")
            # print(f"chunk_size of doc({index}): {chunk_size}")
            chunks = split_text_into_chunks(content, chunk_size)

            for chunk in chunks:
                docs_to_add.append(chunk)
                ids_to_add.append(str(uuid.uuid4()))
                metadata_to_add.append({"index": index})
       
        result = collection.add(
            documents=docs_to_add,
            metadatas=metadata_to_add,
            ids=ids_to_add
        )

        filename = "sampleDataset.txt"  
        with open(filename, 'w', encoding='utf-8') as file:  
            file.write(json.dumps({"docs_to_add": docs_to_add, "metadata_to_add": metadata_to_add, "ids_to_add": ids_to_add}))
        return True
    except Exception as e:
        print(f"An unexpected error occurred (store_into_temp_rag): {e}")
        traceback.print_exc()
        return False

def extract_relevant_sentences_rag(query, doc_index):
    try:
        client = chromadb.PersistentClient(path=st.session_state['store_dir'])
        collection = client.get_or_create_collection(name="temp")

        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"index": doc_index}
        )
        merged_content = ""
        for index, doc in enumerate(results['documents'][0]):
            chunk_content = doc
            merged_content += chunk_content + "\n"
        
        return merged_content.strip()

    except Exception as e:
        print(f"An unexpected error occurred (extract_relevant_sentences_rag): {e}")
        traceback.print_exc()
        return ""

def search_documents(query, type=False):
    data = []
    try:
        if st.session_state['context']['followup'] and st.session_state['context']['followup_query']:
            query = st.session_state['context']['followup_query']

        #print(f"search_documents: {query}")
        client = chromadb.PersistentClient(path=st.session_state['store_dir'])
        collection = client.get_collection(name="website")
        query_where = {"is_active": True}
        if type:
            query_where = {
                "$and": [
                    {"is_active": {"$eq": True}},
                    {"type": {"$in": type}}
                ]
            }

        # Fetch documents matching the query
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=query_where
        )

        sum_of_tokens = 0  # To track the total token count of selected documents
        for index, doc in enumerate(results['documents'][0]):
            document = json.loads(doc)
            distance = results['distances'][0][index]
        
            if distance < 1.8:
                print("Selected")
                data.append(document)

            if 'title' in document:
                output = document['title'] 
            if 'content' in document:
                sum_of_tokens += token_count(document['content'])
            print(output, distance)

        if len(data) < 1:
            data = results['documents'][0][:1]

        context_token_size = token_count(json.dumps(st.session_state['last_message']))
        max_content_token = MAX_INPUT_TOKEN - context_token_size

        if sum_of_tokens >= max_content_token:
            # reducing factor
            reducing_factor = max_content_token / sum_of_tokens
            if store_into_temp_rag(data, reducing_factor):
                print("STOREDDDD")
                token_after_reduce = 0
                for index, document in enumerate(data):
                    content = extract_relevant_sentences_rag(query, index)
                    document['content'] = content
                    token_after_reduce += token_count(content)
                    print(f"Document {index} size:", token_count(content))

                client.delete_collection(name="temp")
                print(f"Sum of Init Token: {sum_of_tokens}")
                print(f"Sum of Reduced Doc Token: {token_after_reduce}")
            else:
                return []

        return data
    except Exception as e:
        print(f"An unexpected error occurred (search_documents): {e}")
        traceback.print_exc()
        return []
    
def generate_intent_prompt(intent, query):
    # Get prompt based on Intent
    context = f"Context from previous conversation: {st.session_state['last_message']}"
    data = search_documents(query)
    
    if intent == "greeting":
        prompt = f"""
        Identify and respond to user greetings in a friendly and engaging manner. Your response should acknowledge the user's greeting and invite further interaction with a warm and conversational tone.

        User input: {query}
        Available website data: {json.dumps(data)} or previously fetched website content
        Context: {context}

        Generate a response that includes:

        1. Acknowledgment of the greeting (e.g., "Hello!" or "Hi there!").
        2. A friendly follow-up to encourage continued conversation (e.g., "How can I assist you today?" or "What would you like to know?").

        Ensure the response:
        - Is friendly and approachable
        - Is brief and easy to read
        - Engages the user and prompts further interaction

        Provide the response directly as it should appear to the user, without any additional commentary or instructions.
        """

    else:
        prompt = f"""
        Generate a formal and concise response based on the available website content. Present information in a clear format, and provide URLs only if available from the website data. If the requested information is not available, apologize and ask clarifying questions instead of giving unrelated recommendations. Keep the response easy to read and engage the user in decision-making.

        Available website data: {json.dumps(data)} or previously fetched website content
        Context: {context}

        Ensure the response meets the following criteria:
        - Formal and professional tone
        - Short, easy-to-read structure
        - Present information clearly without using titles
        - If requested items are unavailable, apologize or ask further questions
        - Avoid any meta-statements or references to the data source, internal instructions, or context

        Structure the response as follows:
        1. Start with a brief introductory sentence relevant to the user query.
        2. For each relevant item, use the format:
        **Title 1**
        - Point 1
        - Point 2
        - Point 3
        3. Conclude with a polite closing note or recommendation if needed.
        """
            
    return prompt, query