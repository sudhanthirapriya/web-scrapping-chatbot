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

model = "llama3-8b-8192"
llm = ChatGroq(
    model=model,
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

def llm_direct(query):
    # Generate the response using the language model
    response = llm.invoke(query)
    print(f"Direct: {response.usage_metadata}")
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

# from langchain_core.output_parsers import PydanticOutputParser
# from langchain_core.prompts import PromptTemplate
# from pydantic import BaseModel, Field, model_validator

# def llm_strutured_output(query):
#     class ProductResponse(BaseModel):
#         title: str = Field(description="Product title or name")
#         price: str = Field(description="Price of the product")
#         url: str = Field(description="URL of the product")
#         image_url: str = Field(description="URL of the product image")
#         description: str = Field(description="Product information tailored to answer user query")
#         accuracy: float = Field(description="Check Output accuracy from searched data in 0 to 1, where 1 is highly accurate")

#     parser = PydanticOutputParser(pydantic_object=ProductResponse)
#     prompt = PromptTemplate(
#         template=(
#             "{query}\n"
#             "{format_instructions}"
#         ),
#         input_variables=["query"],
#         partial_variables={"format_instructions": parser.get_format_instructions()},
#     )

#     prompt_and_model = prompt | llm
#     output = prompt_and_model.invoke({"query": query})
#     print(output)
#     print("\n=================\n")
#     parsed_output = parser.invoke(output)
#     print("parsed_output:", parsed_output)