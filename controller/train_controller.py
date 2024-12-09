import os
import json
import chromadb
from flask import request, jsonify
from utils.intent import identify_intent
from models.llm import llm_prompt
from utils.prompt import generate_intent_prompt
from utils.context import check_followup
import os
import asyncio
import concurrent.futures
import traceback

# Define the directory for persistent storage
directory_path = './store/shopify'

# Create the directory if it doesn't exist
if not os.path.exists(directory_path):
    os.makedirs(directory_path)

# Initialize ChromaDB client
client = chromadb.PersistentClient(path=directory_path)

# Get or create the 'website' collection in ChromaDB
collection = client.get_or_create_collection(name="website")

# Function to get a document using dataset_id and store_id
def get_document():
    """
    Sample Payload
    {
        "store_id": "1",
        "dataset_id": "123"
    }
    """
    try:
        data = request.json
        store_id = data.get('store_id')
        dataset_id = data.get('dataset_id')

        if not store_id or not dataset_id:
            return jsonify({'status': False, 'message': 'Missing store_id or dataset_id'}), 400

        # Query the collection for the document using the dataset_id and store_id
        result = collection.get(ids=[str(dataset_id)], where={"store_id": store_id})
        print(result)
        if not result['documents']:
            return jsonify({'status': False, 'message': 'Document not found'}), 404

        # Return the document content
        document = result['documents'][0]  # Assuming only one document will match the query
        metadata = result['metadatas'][0]

        return jsonify({
            'status': True,
            'message': 'Document retrieved successfully',
            'data': {
                'document': json.loads(document),
                'metadata': metadata
            }
        }), 200

    except Exception as e:
        return jsonify({'status': False, 'message': f'Error occurred: {str(e)}'}), 500

# Function to create a document
def add_document():
    """
    sample payload
    {
        "data": [
            {
                "dataset_id": "123",
                "type": "pages",
                "content": {"title": "Sample", "description": "This is a sample dataset."}
            }
        ],
        "store_id": "1"
    }
    """
    try:
        # Extract the payload
        data = request.json
        if not data or 'data' not in data or 'store_id' not in data:
            return jsonify({'status': False, 'message': 'Invalid payload'}), 400

        # Process the dataset from the payload
        for item in data['data']:
            dataset_id = item.get('dataset_id')
            content = item.get('content')
            type = item.get('type')
            store_id = data.get('store_id')

            if not dataset_id or not content or not store_id:
                return jsonify({'status': False, 'message': 'Missing required fields'}), 400

            collection.delete(ids=[str(dataset_id)])
            result = collection.add(
                documents=[json.dumps(content)],
                metadatas=[{"store_id": store_id, "type": type, "is_active": True}],
                ids=[str(dataset_id)]
            )
            print(result)

        return jsonify({'status': True, 'message': 'Data stored successfully', 'data': data}), 200
    except Exception as e:
        return jsonify({'status': False, 'message': f'Error occurred: {str(e)}'}), 500


# Function to disable a document 
def disable_document():
    """
    Sample Payload
    {
        "store_id": "1",
        "dataset_ids": ["123", "456"]
    }
    """
    try:
        data = request.json
        store_id = data.get('store_id')
        dataset_ids = data.get('dataset_ids')

        # Validate store_id and dataset_ids
        if not store_id:
            return jsonify({'status': False, 'message': 'Missing store_id'}), 400

        if not dataset_ids or not isinstance(dataset_ids, list):
            return jsonify({'status': False, 'message': 'dataset_ids must be a non-empty array'}), 400

        # Convert all dataset_ids to strings (in case some are not)
        dataset_ids = [str(dataset_id) for dataset_id in dataset_ids]

        # Update metadata (is_active: False)
        collection.update(
            ids=dataset_ids,
            metadatas=[{"store_id": store_id, "is_active": False}]
        )

        return jsonify({'status': True, 'message': 'Document disabled successfully'}), 200
    except Exception as e:
        return jsonify({'status': False, 'message': f'Error occurred: {str(e)}'}), 500


# Function to remove a document from the collection
def remove_document():
    """
    Sample Payload
    {
        "dataset_ids": ["123", "456"]
    }
    """
    try:
        data = request.json
        dataset_ids = data.get('dataset_ids')

        if not dataset_ids or not isinstance(dataset_ids, list):
            return jsonify({'status': False, 'message': 'dataset_ids must be a non-empty array'}), 400

        # Convert all dataset_ids to strings (in case some are not)
        dataset_ids = [str(dataset_id) for dataset_id in dataset_ids]

        # Remove the documents
        collection.delete(ids=dataset_ids)

        return jsonify({'status': True, 'message': 'Documents removed successfully'}), 200
    except Exception as e:
        return jsonify({'status': False, 'message': f'Error occurred: {str(e)}'}), 500

def call_identify_intent(query):
    intent = identify_intent(query)
    return intent

def call_check_followup(query, last_message):
    followup_context = check_followup(query, last_message)
    return followup_context

async def generate_llm_response(store_id, query, chat_history):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future1 = executor.submit(call_identify_intent, query)
        future2 = executor.submit(call_check_followup, query, chat_history)

        intent = future1.result()
        context = future2.result()

    print(f"Intent: {intent}")
    print(f"Followup: {context}")
    system_prompt, modified_query, dataset = generate_intent_prompt(store_id, intent, context, query, chat_history)
    response, token = llm_prompt(system_prompt, modified_query, True)
    return response, dataset, token

def chat_with_llm():
    """
    Sample Payload
    {
        "store_id": "1",
        "query": "Tell me more about your product",
        "chat_history": [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Welcome to store! ..."}
        ]
    }
    """
    try:
        # Get data from the request
        data = request.json
        store_id = data.get('store_id')
        query = data.get('query')
        chat_history = data.get('chat_history', [])

        if not query:
            return jsonify({'status': False, 'message': 'Empty user query'}), 404
        
        # Check if store_id exists in the database
        store_check = collection.get(where={"store_id": store_id})
        if not store_check['documents']:
            return jsonify({'status': False, 'message': 'Store ID not found'}), 404

        # Simulate a response from an LLM based on the query and chat history
        response_content, dataset, token = asyncio.run(generate_llm_response(store_id, query, chat_history))

        # Prepare the response token
        # response_token = {
        #     "input": query,
        #     "output": response_content,
        #     "total": len(chat_history) + 1  # Total number of interactions
        # }

        return jsonify({
            'status': True,
            'message': 'Response generated successfully',
            'token': token,
            'response': response_content,
            'dataset': dataset
        }), 200

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({'status': False, 'message': f'Error occurred: {str(e)}'}), 500
