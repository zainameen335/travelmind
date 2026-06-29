from tools.calendar_tool import create_calendar_event
import sqlite3
from tools.flight_tool import search_flights as search_real_flights
from tools.hotel_tool import search_hotels as search_real_hotels
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from typing import TypedDict, Annotated
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("GITHUB_TOKEN")

llm = ChatOpenAI(
    api_key=token,
    base_url="https://models.inference.ai.azure.com",
    model="gpt-4.1-mini",
)

## STATE


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    departure_city: str
    destination: str
    budget: str
    dates: str
    travelers: str
    flights: list
    hotels: list
    approved: bool
    rejected: bool
    unclear_approval: bool
    package_ready: bool
    start_date: str
    end_date: str
    selected_package: int
    missing_info: list[str]
    
## PYDANTIC MODELS    


class TripDetails(BaseModel):
    departure_city: str = ""
    destination: str = ""
    budget: str = ""
    dates: str = ""
    start_date: str = ""
    end_date: str = ""
    travelers: str = ""


class ApprovalDecision(BaseModel):
    approved: bool = False
    rejected: bool = False
    unclear_approval: bool = False
    
class PackageSelection(BaseModel):
    selected_package: int = 0    


structured_llm = llm.with_structured_output(TripDetails)
structured_llm_2 = llm.with_structured_output(ApprovalDecision)
structured_llm_3 = llm.with_structured_output(PackageSelection)


## FUNCTIONS
def chatnode(state: AgentState):

    # 1. missing info check
    missing = state.get("missing_info", [])

    if missing:
        question = "I need a few more details: " + ", ".join(missing) + "."
        return {"messages": [AIMessage(content=question)]}

    # 2. approval checks 

    if state.get("approved"):
        return {
            "messages": [
                AIMessage(content="Great! Your travel package has been approved.")
            ]
        }

    if state.get("rejected"):
        return {
            "messages": [
                AIMessage(content="Okay, what would you like to change in the package?")
            ]
        }

    if state.get("unclear_approval"):
        return {
            "messages": [
                AIMessage(
                    content="Please reply with yes to approve or no to request changes."
                )
            ]
        }

    # 3. package summary
    flights = state.get("flights", [])
    hotels = state.get("hotels", [])

    if flights and hotels:
        budget = extract_number(state.get("budget"))

        package_summary = f"""
Great, I found 3 travel package options for you:

Trip Details:
- From: {state.get("departure_city")}
- To: {state.get("destination")}
- Dates: {state.get("dates")}
- Travelers: {state.get("travelers")}
- Budget: {state.get("budget")}
"""

        for i in range(min(3, len(flights), len(hotels))):
            flight = flights[i]
            hotel = hotels[i]

            flight_price = extract_number(flight["price"])
            hotel_price = extract_number(hotel["price"])
            total_price = round(flight_price + hotel_price, 2)

            package_summary += f"""

    Package {i + 1}

    Flight:
    - Airline: {flight["airline"]}
    - Route: {flight.get("origin")} to {flight.get("destination")}
    - Price: {flight["price"]}

    Hotel:
    - Hotel: {hotel["name"]}
    - Location: {hotel["location"]}
    - Price: {hotel["price"]}

    Total Estimated Price: {total_price}
    """

            if total_price > budget:
                package_summary += "⚠️ Over budget\n"
            else:
                package_summary += "✅ Within budget\n"

        package_summary += """

    Which package would you like to approve? Package 1, Package 2, or Package 3?
    """

        return {"messages": [AIMessage(content=package_summary)], "package_ready": True}


def extract_trip_details(state: AgentState):

    last_message = state["messages"][-1].content

    details = structured_llm.invoke(f"""
    Extract trip details from this message.

    Convert travel dates into ISO format.
    Current year is 2026.

    Example:
    "from 20 May to 30 May" =
    start_date: 2026-05-20
    end_date: 2026-05-30

    Message:
    {last_message}
    """)

    new_data = details.model_dump()

    updated_data = {}

    for key, value in new_data.items():
        updated_data[key] = value or state.get(key, "")

    return updated_data


def missing_info_checker(state: AgentState):
    missing = []

    if not state.get("departure_city"):
        missing.append("departure city")

    if not state.get("destination"):
        missing.append("destination")

    if not state.get("budget"):
        missing.append("budget")

    if not state.get("dates"):
        missing.append("travel dates")

    if not state.get("travelers"):
        missing.append("number of travelers")

    return {"missing_info": missing}


def approval_node(state: AgentState):
    last_message = state["messages"][-1].content

    selection = structured_llm_3.invoke(f"""
    Extract selected package number from user message.

    User may say:
    Package 1
    Package 2
    Package 3
    first package
    second package
    third package

    If no package is selected, return 0.

    User message:
    {last_message}
    """)

    if selection.selected_package in [1, 2, 3]:
        return {
            "approved": True,
            "rejected": False,
            "unclear_approval": False,
            "selected_package": selection.selected_package
        }

    decision = structured_llm_2.invoke(f"""
    The user is responding to package approval.

    User message: {last_message}

    Decide:
    - approved = True if user accepts, agrees, confirms, says go ahead
    - rejected = True if user says no, refuses, or wants changes
    - unclear_approval = True if the answer is unclear
    """)

    return {
        "approved": decision.approved,
        "rejected": decision.rejected,
        "unclear_approval": decision.unclear_approval,
    }


def search_flights(state: AgentState):
    flights = search_real_flights(
        departure_city=state.get("departure_city"),
        destination=state.get("destination"),
        departure_date=state.get("start_date"),
        travelers=state.get("travelers"),
    )

    if not flights:
        flights = [
            {
                "airline": "No flight found",
                "origin": state.get("departure_city"),
                "destination": state.get("destination"),
                "price": "N/A",
            }
        ]

    return {"flights": flights}


def search_hotels(state: AgentState):
    hotels = search_real_hotels(
        city=state.get("destination"),
        checkin_date=state.get("start_date"),
        checkout_date=state.get("end_date"),
        travelers=state.get("travelers"),
    )

    if not hotels:
        hotels = [
            {
                "name": f"No hotel found in {state.get('destination')}",
                "location": state.get("destination"),
                "price": "N/A",
            }
        ]

    return {"hotels": hotels}


def route_after_check(state: AgentState):
    if state.get("missing_info"):
        return "chatnode"
    return "search_flights"


def route_start(state: AgentState):
    if (
        state.get("package_ready")
        and not state.get("approved")
        and not state.get("rejected")
    ):
        return "approval_node"
    return "extract_trip_details"


def calendar_node(state: AgentState):
    selected_index = state.get("selected_package", 1) - 1

    flight = state.get("flights", [])[selected_index]
    hotel = state.get("hotels", [])[selected_index]
    
    flight_price = extract_number(flight.get("price"))
    hotel_price = extract_number(hotel.get("price"))
    total_price = flight_price + hotel_price

    event_link = create_calendar_event(
        destination=state.get("destination"),
        dates=state.get("dates"),
        travelers=state.get("travelers"),
        start_date=state.get("start_date"),
        end_date=state.get("end_date"),
    )

    message = f"""
Great! Package {state.get("selected_package")} has been approved and your calendar has been blocked.

Selected Package Details:

Flight:
- Airline: {flight.get("airline")}
- Route: {flight.get("origin")} to {flight.get("destination")}
- Price: {flight.get("price")}

Hotel:
- Hotel: {hotel.get("name")}
- Location: {hotel.get("location")}
- Price: {hotel.get("price")}

Total Estimated Price:
- {total_price}

⚠️ Note: Google Calendar integration is currently available only in the local development version. Public user calendar integration will be added in a future update.

"""

    return {"messages": [AIMessage(content=message)]}

def route_after_approval(state: AgentState):
    if state.get("approved"):
        return "calendar_node"
    return "chatnode"


def extract_number(value):
    if not value:
        return 0
    numbers = "".join(ch for ch in str(value) if ch.isdigit() or ch == ".")
    return float(numbers) if numbers else 0

## GRAPH SETUP

graph = StateGraph(AgentState)

graph.add_node("chatnode", chatnode)
graph.add_node("extract_trip_details", extract_trip_details)
graph.add_node("missing_info_checker", missing_info_checker)
graph.add_node("search_flights", search_flights)
graph.add_node("search_hotels", search_hotels)
graph.add_node("approval_node", approval_node)
graph.add_node("calendar_node", calendar_node)

graph.add_conditional_edges(
    START,
    route_start,
    {"approval_node": "approval_node", "extract_trip_details": "extract_trip_details"},
)
graph.add_edge("extract_trip_details", "missing_info_checker")
graph.add_conditional_edges(
    "missing_info_checker",
    route_after_check,
    {"chatnode": "chatnode", "search_flights": "search_flights"},
)
graph.add_edge("search_flights", "search_hotels")
graph.add_edge("search_hotels", "chatnode")
graph.add_conditional_edges(
    "approval_node",
    route_after_approval,
    {"calendar_node": "calendar_node", "chatnode": "chatnode"},
)

graph.add_edge("calendar_node", END)

conn = sqlite3.connect(database="chatbot.db", check_same_thread=False)
memory = SqliteSaver(conn=conn)

app = graph.compile(checkpointer=memory)
