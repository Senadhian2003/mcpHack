import sys
import os
from pathlib import Path
import json
import emoji
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from strands import Agent, tool
from strands.models import BedrockModel
from models.dynamodb import DynamoDBService
from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp import MCPClient

class DelayCompanionAgent:
    """DelayCompanion airline assistant agent using Strands Agent SDK"""
    def __init__(self):
   
        """Initialize the DelayCompanion agent"""
        # Initialize DynamoDB service
        self.stdio_mcp_client = MCPClient(lambda: stdio_client(
        StdioServerParameters(
        command="uvx", 
        args=["awslabs.dynamodb-mcp-server@latest"],
        env = {
        
        "AWS_PROFILE": "default",
        "AWS_REGION": "us-west-2",
        "FASTMCP_LOG_LEVEL": "DEBUG"
        }
    )
))
        self.mailMCP_client = MCPClient(lambda: stdio_client(StdioServerParameters(
            command="npx",
            args=["@gongrzhe/server-gmail-autoauth-mcp"]
        )))
        self.db_service = DynamoDBService()
       
    
    def _get_system_prompt(self):
        """Get the system prompt for the agent"""
        return """You are DelayCompanion, an airline assistant that helps passengers with flight delays.

Your primary responsibilities are:
1. Detect delayed flights and identify affected passengers
2. Send personalized delay notifications with rebooking options
3. Help passengers select new flights or request assistance
4. Generate handoff context for call center agents when needed
5. Send email to user regarding new bookings or confirmations of passenger to stay on current flight.

Communication style:
- Use clear, concise language with a helpful and empathetic tone
- Include relevant emojis to make messages engaging
- Format information with clear sections and labels
- Prioritize the most important information first
- Provide specific times, flight numbers, and gate information

When interacting with passengers:
1. Acknowledge the inconvenience of the delay
2. Clearly explain the delay reason and expected duration
3. Present rebooking options with key details (departure time, arrival time)
4. Offer to connect with a live agent if needed
5. Ask for passenger preferences (window/aisle seat, time preferences)

Always maintain a professional, helpful tone while being concise and informative.

NOTE:
- You have access to the following dynamo db databases:[DelayCompanion_Flights, DelayCompanion_Passengers]
- Use the following database to get information about flights and passengers
"""
    
    @tool
    def get_delayed_flights(self):
        """Get a list of all currently delayed flights"""
        delayed_flights = self.db_service.get_delayed_flights()
        return delayed_flights
    
    @tool
    def get_flight_details(self, flight_id: str):
        """
        Get detailed information about a specific flight
        
        Args:
            flight_id: The unique identifier for the flight
        """
        flight = self.db_service.get_flight(flight_id)
        return flight
    
    @tool
    def get_passenger_details(self, passenger_id: str):
        """
        Get detailed information about a specific passenger
        
        Args:
            passenger_id: The unique identifier for the passenger
        """
        passenger = self.db_service.get_passenger(passenger_id)
        return passenger
    
    @tool
    def get_rebooking_options(self, flight_id: str):
        """
        Get available rebooking options for a delayed flight
        
        Args:
            flight_id: The unique identifier for the delayed flight
        """
        options = self.db_service.get_rebooking_options(flight_id)
        return options
    
    @tool
    def rebook_passenger(self, passenger_id: str, new_flight_id: str, seat_preference: str = None):
        """
        Rebook a passenger on a new flight
        
        Args:
            passenger_id: The unique identifier for the passenger
            new_flight_id: The flight ID for the new booking
            seat_preference: Optional seat preference (window, aisle, etc.)
        """
        success = self.db_service.update_passenger_rebooking(
            passenger_id, 
            new_flight_id, 
            seat_preference
        )
        
        if success:
            # Get updated passenger and flight details
            passenger = self.db_service.get_passenger(passenger_id)
            flight = self.db_service.get_flight(new_flight_id)
            
            return {
                "success": True,
                "message": f"Successfully rebooked passenger {passenger['name']} on flight {flight['flight_number']}",
                "passenger": passenger,
                "flight": flight
            }
        else:
            return {
                "success": False,
                "message": "Failed to rebook passenger. Please try again or contact customer service."
            }
    
    @tool
    def generate_handoff_context(self, passenger_id: str):
        """
        Generate handoff context for call center agents
        
        Args:
            passenger_id: The unique identifier for the passenger
        """
        handoff_context = self.db_service.generate_handoff_context(passenger_id)
        return handoff_context
    
    @tool
    def format_delay_message(self, 
                           passenger_name: str, 
                           flight_number: str,
                           origin: str,
                           destination: str, 
                           delay_minutes: int,
                           delay_reason: str,
                           scheduled_departure: str,
                           new_departure: str,
                           gate: str,
                           terminal: str,
                           rebooking_options: list):
        """
        Format a delay notification message with emojis and clear sections
        
        Args:
            passenger_name: Name of the passenger
            flight_number: Flight number
            origin: Origin airport code
            destination: Destination airport code
            delay_minutes: Delay duration in minutes
            delay_reason: Reason for the delay
            scheduled_departure: Original scheduled departure time
            new_departure: New expected departure time
            gate: Gate information
            terminal: Terminal information
            rebooking_options: List of available rebooking options
        """
        # Convert delay minutes to hours and minutes
        hours = delay_minutes // 60
        mins = delay_minutes % 60
        delay_text = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
        
        # Map delay reasons to appropriate emojis
        reason_emojis = {
            "Weather": "🌧️",
            "Mechanical": "🔧",
            "Crew": "👨‍✈️",
            "Air Traffic Control": "🗼",
            "Aircraft Late Arrival": "⏱️",
            "Security": "🔒",
            "Other": "ℹ️"
        }
        
        reason_emoji = reason_emojis.get(delay_reason, "ℹ️")
        
        # Format the message with emojis and clear sections
        message = f"""
Hello {passenger_name},

❗ **FLIGHT DELAY ALERT** ❗

Your flight {flight_number} from {origin} to {destination} has been delayed by {delay_text}.

📋 **DELAY DETAILS**
• Reason: {reason_emoji} {delay_reason}
• Original departure: {scheduled_departure}
• New departure: {new_departure}
• Gate: {gate}
• Terminal: {terminal}

✈️ **REBOOKING OPTIONS**
"""
        
        # Add rebooking options
        if rebooking_options:
            for i, option in enumerate(rebooking_options, 1):
                message += f"{i}. Flight {option['flight_number']} - Departs: {option['departure']} - Arrives: {option['arrival']}\n"
        else:
            message += "No rebooking options are currently available.\n"
        
        # Add assistance information
        message += """
📱 **NEED HELP?**
• Select a rebooking option
• Request a call with an agent
• Update your preferences

We apologize for the inconvenience and are working to get you to your destination as soon as possible.
"""
        
        return message
    
    def process_query(self, query, passenger_id=None):
        """Process a user query with the agent"""
        context = {}
        
        # If passenger ID is provided, add passenger context
        if passenger_id:
            passenger = self.db_service.get_passenger(passenger_id)
            if passenger:
                flight_id = passenger.get('flight_id')
                flight = self.db_service.get_flight(flight_id)
                
                context = {
                    "passenger": passenger,
                    "flight": flight
                }
                
                # Add context to the query
                query = f"[CONTEXT: Passenger ID: {passenger_id}, Name: {passenger.get('name')}, " \
                       f"Flight: {flight.get('flight_number')}, Status: {flight.get('status')}]\n\n{query}"
        with self.stdio_mcp_client, self.mailMCP_client:
            # Get the tools from the MCP server
            tools = self.stdio_mcp_client.list_tools_sync() + self.mailMCP_client.list_tools_sync()
            print(f"Available tools: {tools}")
        # Create the agent with Claude Sonnet model
            self.agent = Agent(
            model=BedrockModel(
                model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                region_name="us-west-2",
                temperature=0.2
            ),
            tools=tools,
            system_prompt=self._get_system_prompt()
        )
        # Process the query with the agent
            response = self.agent(query)
        
        return response.message, context
