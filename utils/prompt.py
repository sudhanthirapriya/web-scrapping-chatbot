import json, config
import chromadb
import streamlit as st
from utils.token import token_count


def search_documents(store_id, query):
    data = []
    try:
        print(f"\nsearch_documents: {query}\n")
        client = chromadb.PersistentClient(path="./store/shopify")
        collection = client.get_collection(name="website")

        query_where = {
            "$and": [
                {"is_active": True},
                {"store_id": store_id}
            ]
        }
        results = collection.query(
            query_texts=[query],
            n_results=10,
            where=query_where
        )

        for index, doc in enumerate(results['documents'][0]):
            document = json.loads(doc)
            distance = results['distances'][0][index]

            if distance < 1.8:
                print("Selected")
                data.append(document)

            if 'title' in document:
                output = document['title'] 
            if 'question' in document: 
                output = document['question'] 
            print(output, distance)
            

        if len(data) < 3:
            data = results['documents'][0][:3]
        return data
    except Exception as e:
        print(f"An unexpected error occurred (search_documents): {e}")
        return []

def generate_intent_prompt(store_id, intent, context, query, chat_history):
    if context['followup'] and context['followup_query']:
            query = context['followup_query']

    context = f"Context from previous conversation: {chat_history}"
    data = search_documents(store_id, query)

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
    return prompt, query, data