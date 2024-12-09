import streamlit as st
from utils.intent import identify_intent
from models.llm_streamlit import llm_prompt, llm_embedded
from utils.prompt_streamlit import generate_intent_prompt
from utils.context import check_followup
import os
import time 
import asyncio
import concurrent.futures


# Select Store
store_dir = './store'
folders = [f for f in os.listdir(store_dir) if os.path.isdir(os.path.join(store_dir, f))]
folder_options = {folder: os.path.normpath(os.path.join(store_dir, folder)) for folder in folders}
selected_folder_label = st.selectbox("Select a Store", options=folder_options.keys())
if selected_folder_label:
    st.session_state['store_dir'] = folder_options[selected_folder_label]
    print(f"option value: {st.session_state['store_dir']}")
    st.header(f"Store: {selected_folder_label}")


if 'bm250_status' not in st.session_state:  
    st.session_state['bm250_status'] = False 
bm250_status = st.checkbox("BM250 status", value=st.session_state['bm250_status'])  
st.session_state['bm250_status'] = bm250_status  
st.write(f"BM250 status is: {st.session_state['bm250_status']}")  

if 'llama_status' not in st.session_state:  
    st.session_state['llama_status'] = True
     
llama_status = st.checkbox("Llama status", value=st.session_state['llama_status'])  
st.session_state['llama_status'] = llama_status  
st.write(f"Llama status is: {st.session_state['llama_status']}")  


st.header("How can I help you?")

if "conversation_history" not in st.session_state:
    st.session_state["conversation_history"] = []

if "res_time" not in st.session_state:
    st.session_state["res_time"] = 0

# Display past conversation
for msg in st.session_state.conversation_history:
    st.chat_message(msg["role"]).write(msg["content"])

thread_result = {"intent": "", "followup_context": ""}

def call_identify_intent(query):
    print("Run call_identify_intent")
    start_time = time.time()
    intent = identify_intent(query)
    print(f"Intent: {intent}")
    res_time = (time.time() - start_time)
    print(f"Intent Response time: {res_time:.2f} seconds")
    return intent, res_time

def call_check_followup(query, last_message):
    print("Run call_check_followup")
    start_time = time.time()
    followup_context = check_followup(query, last_message)
    print(followup_context)
    res_time = (time.time() - start_time)
    print(f"Followup Response time: {res_time:.2f} seconds")
    return followup_context, res_time

# Chatbot function
async def chatbot(query):
    print("================")
    response_message.markdown("Processing your request...")

    st.session_state["res_time"] = 0
    st.session_state["res_time_async"] = 0
    print("before aysnc")
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start both function1 and function2 in parallel
        future1 = executor.submit(call_identify_intent, query)
        
        conversation_history = st.session_state.conversation_history
        last_message = conversation_history[-3:-1]
        st.session_state['last_message'] = last_message
        future2 = executor.submit(call_check_followup, query, last_message)

        # Wait for both futures to complete and get their results
        intent, res_time = future1.result()
        st.session_state["res_time"] += res_time
        response_message.markdown("Fetching the information...")

        followup_context, res_time = future2.result()
        st.session_state['context'] = followup_context
        st.session_state["res_time"] += res_time

    print("after aysnc")
    res_time_async = (time.time() - start_time)
    st.session_state["res_time_async"] += res_time_async

    start_time = time.time()
    prompt, query = generate_intent_prompt(intent, query)
    res_time = (time.time() - start_time)
    st.session_state["res_time"] += res_time
    st.session_state["res_time_async"] += res_time
    print(f"Prompt Response time: {res_time:.2f} seconds")
    response_message.markdown("Working on it...")

    start_time = time.time()
    response = llm_prompt(prompt, query)
    res_time = (time.time() - start_time)
    print(f"LLM Direct Response time: {res_time:.2f} seconds")


    st.session_state["res_time"] += res_time
    st.session_state["res_time_async"] += res_time
    print(f"Total Response time: {st.session_state['res_time']:.2f} seconds")
    print(f"Total Response time (Async): {st.session_state['res_time_async']:.2f} seconds")
    
    return response, st.session_state["res_time_async"]

# User Input and Bot Response Handling
if prompt := st.chat_input():  # When the user submits a query
    st.session_state.conversation_history.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    response_message = st.empty()

    response, response_time = asyncio.run(chatbot(prompt))  # Call the chatbot function with the user query
    st.session_state.conversation_history.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)
    response_message.markdown(f"Processed at {response_time:.2f} seconds")
