from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from gmail_tools import (
    fetch_top_email,
    fetch_specific_email,
    reply_to_email,
    list_emails,
    get_email_id,
    send_email
)
from auth import authenticate_google, get_and_save_token
from dotenv import load_dotenv
load_dotenv()
import os

service = authenticate_google()

# Load LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
)

memory = MemorySaver()

# ReAct Agent
graph = create_react_agent(
    model=llm,
    tools=[fetch_top_email, fetch_specific_email, reply_to_email, list_emails, get_email_id, send_email],
    checkpointer=memory
)

get_and_save_token()
