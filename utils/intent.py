from models.llm import llm_direct
from langchain_core.messages import AIMessage
import re

intents = {
    "greeting": ["hi", "hello"],
    "product_search": ["find", "search", "look for", "discover"],
    "product_recommendations": ["recommend", "suggest", "interested in", "suggestions"],
    "product_details": ["details", "information", "more info", "specifications"],
    "product_comparison": ["compare", "versus", "vs", "comparison"],
    "product_reviews": ["reviews", "opinions", "feedback", "ratings"],
    "price_inquiry": ["price", "cost", "how much", "pricing"],
    "availability_check": ["availability", "in stock", "available", "stock"],
    "order_tracking": ["track", "tracking", "order status", "where is my order"],
    "shipping_information": ["shipping", "delivery", "send", "dispatch"],
    "return_policy_inquiry": ["return policy", "returns", "refund", "exchange"],
    "promotions_and_discounts": ["discount", "promotion", "deal", "offer"],
    "customer_support": ["support", "help", "assistance", "issue"],
    "account_information": ["account", "login", "profile", "sign in"],
    "store_location": ["store", "location", "near me", "branch"],
    "cart_management": ["cart", "add to cart", "remove from cart", "checkout"],
    "store_information": [],
    "about_store": [],
}

def strip_special_chars(s):  
    s = str(s).strip()
    # Remove special characters from the beginning  
    s = re.sub(r'^[^a-zA-Z0-9\s]+', '', s)  # Remove from the start  
    # Remove special characters from the end  
    s = re.sub(r'[^a-zA-Z0-9\s]+$', '', s)  # Remove from the end  
    return s  

def identify_intent(user_input):
    prompt = f"""Identify the intent of the following customer query from the list of intents: {list(intents.keys())}. 
    Query: '{user_input}'. 
    Respond with the intent keyword only, or 'null' if it doesn't match any intent.
    
    Return: String, the intent keyword or 'null' 
    """
    intent = llm_direct(prompt)
    return strip_special_chars(intent)  