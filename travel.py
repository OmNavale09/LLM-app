import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_tavily import TavilySearch
import serpapi

# Load environment variables from .env file
load_dotenv()

# Step 1: Initialize the Model
google_api_key = os.getenv('GEMINI_API_KEY')
model = init_chat_model(
    "google_genai:gemini-2.5-flash",
    api_key=google_api_key
)
# Step 2: Create Destination Research Tool (Tavily)
tavily_api_key = os.getenv('TAVILY_API_KEY')
destination_research_tool = TavilySearch(
    max_results=5,
    search_depth="advanced",
    tavily_api_key=tavily_api_key
)
# Step 3: Create Flight Search Tool
@tool
def search_flights(origin: str, destination: str, date: str) -> list:
    """Search for flights using SerpAPI Google Flights. Date should be in YYYY-MM-DD format like '2026-12-15'."""
    print(f"\nCalling search_flights tool")
    print(f"Searching flights from {origin} to {destination} on {date}")
    serpapi_key = os.getenv('SERPAPI_KEY')
    
    params = {
        "api_key": serpapi_key,
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": date,
        "currency": "INR",
        "type": "2"
    }

    client = serpapi.Client(api_key=serpapi_key)

    search = client.search(params)

    best_flights = search["best_flights"]
    return best_flights

# Step 4: Define System Prompt
system_prompt = """You are a TravelBuddy assistant that helps travelers plan trips.
You have access to these tools:
- destination_research_tool: Research attractions, culture, and travel tips
- search_flights: Find flight options (use IATA codes: HYD=Hyderabad, GOI=Goa, BOM=Mumbai, DEL=Delhi, BLR=Bangalore)
Help the traveler by researching destinations and finding flights.
Present results in a clean, readable format with clear sections.
Don't use markdown format."""

# Step 5: Create and Run the Agent
agent = create_agent(
    model=model,
    tools=[destination_research_tool, search_flights],
    system_prompt=system_prompt
)
user_query = "I want to visit Goa from Mumbai on 2026-12-15. Show me top attractions and flight options"
response = agent.invoke({
    "messages": [{"role": "user", "content": user_query}]
})
print(response["messages"][-1].content)