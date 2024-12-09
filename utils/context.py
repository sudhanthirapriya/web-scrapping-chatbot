from models.llm import llm_direct
from langchain_core.messages import AIMessage
import json, re

def check_followup(query, history):
    try:
        prompt = f"""Determine if the current user query is a follow-up question from the conversation history 
        and whether it requires checking the database for new documents or information.
        
        user query: {query}

        conversation history: {json.dumps(history)}

        Give only response in below JSON with any additional information.
        - followup: boolean
        - followup_reason: string, why the query is a follow-up question or not
        - followup_query: string, if followup is true, prepare followup user query.
        """
        followup = llm_direct(prompt)
        pattern = r'```(.*?)```'
        # Using re.DOTALL to match across multiple lines
        matches = re.findall(pattern, followup, re.DOTALL)
        cleaned_response = matches[0].strip().strip('```json').strip('```')
        # Parse the cleaned response as JSON
        response_data = json.loads(cleaned_response)
        return response_data
    except Exception as e:
        print(f"Error: {e}")
        return {"followup": False, "followup_reason": "", "followup_query": ""}