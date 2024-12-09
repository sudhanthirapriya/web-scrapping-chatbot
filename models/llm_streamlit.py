import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from typing import List
import streamlit as st
from utils.token import token_count
import config

# Set your Google API key
os.environ["GOOGLE_API_KEY"] = config.API_KEY

# Initialize the Google Generative AI model
if 'llama_status' not in st.session_state:  
    st.session_state['llama_status'] = True
     
if st.session_state['llama_status']:
    model = "llama3-8b-8192"
    llm = ChatGroq(
        model=model,
        temperature=1,
        max_tokens=500,
        timeout=None,
        max_retries=2,
    )
else:
    model = "gemini-1.5-flash"
    llm = ChatGoogleGenerativeAI(
        model=model,
        temperature=0.5,
        max_tokens=150,
        timeout=10,
        max_retries=2,
    )


def llm_direct(query):
    # Generate the response using the language model
    response = llm.invoke(query)
    print(response.usage_metadata)
    response_text = response.content
    return response_text
    
def llm_prompt(system_prompt, query, token_status = False):
    # system_prompt = """
    # You are an AI assistant for an eCommerce website. 
    # Your job is to help users find products, answer questions, provide product recommendations, and assist with orders, payments, and returns. 
    # Be friendly, concise, and professional. 
    # Provide accurate details on product availability, pricing, shipping, and policies. 
    # If unsure, ask clarifying questions or direct the user to customer support."""
    
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template("{system_prompt}"),
            HumanMessagePromptTemplate.from_template("User query: {query}"),
        ]
    )
    query_input = {"query": query, "system_prompt": system_prompt}  

    response = llm.invoke(prompt.format(**query_input))

    # response = llm.invoke(query)
    print(f"Chat: {response.usage_metadata}")
    response_text = response.content
    if token_status:
        return response_text, response.usage_metadata
    else:
        return response_text

def llm_embedded(query):
    vectorstore = Chroma(
        persist_directory=st.session_state['store_dir'],
        embedding_function=GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    )
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    system_prompt = """
    You are an AI assistant for an eCommerce website. 
    Your job is to help users find products, answer questions, provide product recommendations, and assist with orders, payments, and returns. 
    Be friendly, concise, and professional. 
    Provide accurate details on product availability, pricing, shipping, and policies. 
    If unsure, ask clarifying questions or direct the user to customer support.

    {context}
    """
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    response = rag_chain.invoke({"input": query})
    print(response)
    response_text = response['answer']
    return response_text
