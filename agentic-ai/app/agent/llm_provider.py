from langchain_google_genai import ChatGoogleGenerativeAI
from ..config import settings

def get_llm():
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set")
        
    return ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0
    )

