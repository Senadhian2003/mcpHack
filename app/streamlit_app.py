import streamlit as st
import sys
import os
from pathlib import Path
import json
import pandas as pd
from datetime import datetime
import re
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from app.agent import DelayCompanionAgent
    from models.dynamodb import DynamoDBService
    
    # Initialize the agent and DB service
    agent = DelayCompanionAgent()
    db_service = DynamoDBService()
    DB_AVAILABLE = True
except Exception as e:
    print(f"Database services unavailable: {e}")
    DB_AVAILABLE = False
    # Create mock data for demo purposes
    MOCK_PASSENGERS = [
        {
            'passenger_id': 'P001',
            'name': 'John Smith',
            'loyalty_tier': 'Gold',
            'flight_id': 'F001'
        },
        {
            'passenger_id': 'P002', 
            'name': 'Sarah Johnson',
            'loyalty_tier': 'Platinum',
            'flight_id': 'F002'
        },
        {
            'passenger_id': 'P003',
            'name': 'Mike Chen',
            'loyalty_tier': 'Silver',
            'flight_id': 'F003'
        }
    ]
    
    MOCK_FLIGHTS = {
        'F001': {
            'flight_id': 'F001',
            'flight_number': 'UA456',
            'origin': 'JFK',
            'destination': 'LAX',
            'airline': 'United Airlines',
            'status': 'Delayed',
            'gate': 'A12',
            'terminal': '4',
            'scheduled_departure': '2025-06-18 14:30',
            'actual_departure': '2025-06-18 16:45',
            'delay_minutes': 135,
            'delay_reason': 'Weather',
            'rebooking_options': [
                {
                    'flight_id': 'F004',
                    'flight_number': 'UA789',
                    'departure': '2025-06-18 18:30',
                    'arrival': '2025-06-18 21:45',
                    'original_departure': '2025-06-18 14:30'
                },
                {
                    'flight_id': 'F005',
                    'flight_number': 'UA234',
                    'departure': '2025-06-19 08:15',
                    'arrival': '2025-06-19 11:30',
                    'original_departure': '2025-06-18 14:30'
                }
            ]
        },
        'F002': {
            'flight_id': 'F002',
            'flight_number': 'DL123',
            'origin': 'ATL',
            'destination': 'ORD',
            'airline': 'Delta Airlines',
            'status': 'On Time',
            'gate': 'B8',
            'terminal': '2',
            'scheduled_departure': '2025-06-18 15:45',
            'rebooking_options': []
        },
        'F003': {
            'flight_id': 'F003',
            'flight_number': 'AA987',
            'origin': 'DFW',
            'destination': 'MIA',
            'airline': 'American Airlines',
            'status': 'Delayed',
            'gate': 'C15',
            'terminal': '3',
            'scheduled_departure': '2025-06-18 16:20',
            'actual_departure': '2025-06-18 17:50',
            'delay_minutes': 90,
            'delay_reason': 'Mechanical',
            'rebooking_options': [
                {
                    'flight_id': 'F006',
                    'flight_number': 'AA654',
                    'departure': '2025-06-18 20:30',
                    'arrival': '2025-06-18 23:15',
                    'original_departure': '2025-06-18 16:20'
                }
            ]
        }
    }

# Set page configuration
st.set_page_config(
    page_title="WingHelp",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS with dark gray/black minimal color scheme
# Enhanced CSS with dark gray/black minimal color scheme
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #ffffff;
        margin-bottom: 1rem;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    .sub-header {
        font-size: 1.5rem;
        color: #ffffff;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    .status-delayed {
        color: #ffffff;
        font-weight: bold;
        background-color: #dc2626;
        padding: 4px 8px;
        border-radius: 4px;
        border: 1px solid #fecaca;
    }
    .status-ontime {
        color: #ffffff;
        font-weight: bold;
        background-color: #059669;
        padding: 4px 8px;
        border-radius: 4px;
        border: 1px solid #a7f3d0;
    }
    .info-box {
        background: #1f1f1f;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #404040;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.5);
        color: #ffffff;
    }
    .info-box h3 {
        color: #ffffff;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .info-box p {
        color: #ffffff;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    .alert-box {
        background: #2d2d2d;
        border: 2px solid #525252;
        color: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        font-weight: 500;
    }
    .success-box {
        background: #1a1a1a;
        border: 2px solid #404040;
        color: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        font-weight: 500;
    }
    .error-box {
        background: #262626;
        border: 2px solid #525252;
        color: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        font-weight: 500;
    }
    
    /* Main app background - Dark minimal */
    .stApp {
        background: #0d0d0d;
        color: #ffffff;
    }
    
    /* Main content area */
    .main .block-container {
        background: transparent;
        padding-top: 2rem;
    }
    
    /* Sidebar styling - Dark gray */
    .css-1d391kg {
        background: #1a1a1a;
        border-right: 2px solid #404040;
    }
    
    /* Chat area - Very dark background */
    .stChatMessage {
        background-color: #0f0f0f !important;
        color: #ffffff !important;
        border-radius: 0px !important;
        margin-bottom: 1rem !important;
        padding: 1rem !important;
        border: 1px solid #2d2d2d !important;
    }
    
    /* Chat input - Dark background */
    .stChatInput > div > div > div {
        background-color: #0d0d0d !important;
        color: #ffffff !important;
        border: 1px solid #2d2d2d !important;
        border-radius: 0px !important;
    }
    
    /* Chat input text */
    .stChatInput input {
        background-color: #0d0d0d !important;
        color: #ffffff !important;
    }
    
    /* Chat container background */
    section[data-testid="stChatInputContainer"] {
        background-color: #0d0d0d !important;
        padding: 1rem !important;
        border-radius: 0px !important;
        margin: 1rem 0 !important;
        border: none !important;
    }
    
    /* Chat input wrapper */
    .stChatInput {
        background-color: #0d0d0d !important;
    }
    
    /* Additional chat input styling */
    .stChatInput > div {
        background-color: #0d0d0d !important;
    }
    
    /* Chat input placeholder */
    .stChatInput input::placeholder {
        color: #666666 !important;
    }
    
    /* All chat related elements */
    [data-testid="stChatMessageContainer"] {
        background-color: #0f0f0f !important;
        border-radius: 0px !important;
        margin-bottom: 1rem !important;
    }
    
    .stButton > button {
        background: #2d2d2d;
        color: #ffffff;
        border: 2px solid #404040;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .stButton > button:hover {
        background: #404040;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.5);
        border-color: #525252;
    }
    
    /* White text for better visibility */
    .stMarkdown {
        color: #ffffff;
    }
    
    /* Global text color override */
    * {
        color: #ffffff !important;
    }
    
    .stSelectbox > div > div {
        background-color: #1a1a1a;
        color: #ffffff;
        border: 2px solid #404040;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background-color: #525252;
    }
    
    /* Selectbox text */
    .stSelectbox label {
        color: #ffffff !important;
    }
    
    /* Input labels */
    .stSelectbox > label, .stTextInput > label, .stButton > label {
        color: #ffffff !important;
    }
    
    /* Paragraph text override */
    p, div, span, h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
    }
    
    /* Streamlit markdown headings */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #ffffff !important;
        font-weight: bold !important;
    }
    
    /* Specific heading overrides */
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMarkdownContainer"] h5,
    [data-testid="stMarkdownContainer"] h6 {
        color: #ffffff !important;
        font-weight: bold !important;
    }
    
    /* All text elements in markdown containers */
    [data-testid="stMarkdownContainer"] * {
        color: #ffffff !important;
    }
    
    /* Bold text visibility */
    strong, b {
        color: #ffffff !important;
        font-weight: bold !important;
    }
    
    /* Footer styling */
    div[style*="text-align: center"] {
        color: #ffffff !important;
    }
    
    /* Spinner styling */
    .stSpinner > div {
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

def format_agent_response(response):
    """Format the agent response for better display in Streamlit"""
    if isinstance(response, dict):
        if 'content' in response:
            if isinstance(response['content'], list):
                content_text = ""
                for item in response['content']:
                    if isinstance(item, dict) and 'text' in item:
                        content_text += item['text']
                response = content_text
            else:
                response = response['content']
    
    if isinstance(response, str) and "'role':" in response:
        try:
            text_match = re.search(r"'text': \"(.*?)\"", response, re.DOTALL)
            if text_match:
                response = text_match.group(1)
                response = response.replace('\\n', '\n').replace('\\"', '"')
        except:
            pass
    
    response = apply_delaycompanion_formatting(response)
    return response

def apply_delaycompanion_formatting(text):
    """Apply DelayCompanion-specific formatting to the response text"""
    text = text.replace("Delayed", "🔴 **Delayed**")
    text = text.replace("On Time", "🟢 **On Time**")
    text = re.sub(r'\b([A-Z]{2}\d{3,4})\b', r'**\1**', text)
    
    if "Would you like me to:" in text:
        text = text.replace("Would you like me to:", "\n---\n### 🤝 How Can I Help You Next?\n\nWould you like me to:")
    
    text = text.replace("- Help you explore", "- ✈️ Help you explore")
    text = text.replace("- Connect you with", "- 📞 Connect you with")
    text = text.replace("- Provide general", "- 📋 Provide general")
    text = text.replace("Flight Delay Information", "✈️ Flight Delay Information")
    text = text.replace("Available Options", "🔄 Available Options")
    text = text.replace("Rebooking Options", "✈️ Rebooking Options")
    text = text.replace("Delay Compensation", "💰 Delay Compensation")
    text = text.replace("Connect with an Agent", "📞 Connect with an Agent")
    
    return text

def display_flight_card(flight, passenger=None):
    """Display a formatted flight information card"""
    status_class = "status-delayed" if flight['status'] == "Delayed" else "status-ontime"
    status_emoji = "🔴" if flight['status'] == "Delayed" else "🟢"
    
    st.markdown(f"""
    <div class='info-box'>
        <h3>✈️ Flight Information</h3>
        <p><strong>Flight:</strong> {flight['flight_number']}</p>
        <p><strong>Route:</strong> {flight['origin']} → {flight['destination']}</p>
        <p><strong>Airline:</strong> {flight['airline']}</p>
        <p><strong>Status:</strong> <span class='{status_class}'>{status_emoji} {flight['status']}</span></p>
        <p><strong>Gate:</strong> {flight['gate']}, Terminal {flight['terminal']}</p>
        <p><strong>Scheduled Departure:</strong> {flight['scheduled_departure']}</p>
        {f"<p><strong>New Departure:</strong> {flight['actual_departure']}</p>" if flight.get('actual_departure') else ""}
        {f"<p><strong>Delay Duration:</strong> {format_delay_duration(flight['delay_minutes'])}</p>" if flight.get('delay_minutes') else ""}
        {f"<p><strong>Delay Reason:</strong> {get_delay_emoji(flight['delay_reason'])} {flight['delay_reason']}</p>" if flight.get('delay_reason') else ""}
    </div>
    """, unsafe_allow_html=True)

def display_rebooking_options_info(rebooking_options):
    """Display rebooking options information without selection buttons"""
    if not rebooking_options:
        st.markdown("""
        <div class='alert-box'>
            <h4>❌ No rebooking options currently available</h4>
            <p>Please ask me in the chat below for assistance with rebooking alternatives.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    for i, option in enumerate(rebooking_options, 1):
        # Calculate time difference
        time_diff_text = ""
        try:
            original_time = datetime.strptime(option.get('original_departure', ''), '%Y-%m-%d %H:%M')
            new_time = datetime.strptime(option['departure'], '%Y-%m-%d %H:%M')
            time_diff = new_time - original_time
            hours_diff = time_diff.total_seconds() / 3600
            
            if hours_diff > 0:
                time_diff_text = f"<p style='color: #fbbf24;'>⏰ <strong>{hours_diff:.1f} hours later than original</strong></p>"
            elif hours_diff < 0:
                time_diff_text = f"<p style='color: #34d399;'>⏰ <strong>{abs(hours_diff):.1f} hours earlier than original</strong></p>"
        except:
            pass
        
        st.markdown(f"""
        <div class='info-box'>
            <h4>✈️ Option {i}: Flight {option['flight_number']}</h4>
            <p><strong>🛫 Departure:</strong> {option['departure']}</p>
            <p><strong>🛬 Arrival:</strong> {option['arrival']}</p>
            {time_diff_text}
        </div>
        """, unsafe_allow_html=True)

def format_delay_duration(delay_minutes):
    """Format delay duration in a readable format"""
    delay_minutes = int(delay_minutes)
    hours = delay_minutes // 60
    mins = delay_minutes % 60
    return f"{hours}h {mins}m" if hours > 0 else f"{mins}m"

def get_delay_emoji(delay_reason):
    """Get appropriate emoji for delay reason"""
    reason_emojis = {
        "Weather": "🌧️",
        "Mechanical": "🔧",
        "Crew": "👨‍✈️",
        "Air Traffic Control": "🗼",
        "Aircraft Late Arrival": "⏱️",
        "Security": "🔒",
        "Other": "ℹ️"
    }
    return reason_emojis.get(delay_reason, "ℹ️")

def get_passenger_data(passenger_id):
    """Get passenger data from DB or mock data"""
    if DB_AVAILABLE:
        try:
            return db_service.get_passenger(passenger_id)
        except:
            pass
    
    # Return mock data
    for passenger in MOCK_PASSENGERS:
        if passenger['passenger_id'] == passenger_id:
            return passenger
    return None

def get_flight_data(flight_id):
    """Get flight data from DB or mock data"""
    if DB_AVAILABLE:
        try:
            return db_service.get_flight(flight_id)
        except:
            pass
    
    # Return mock data
    return MOCK_FLIGHTS.get(flight_id)

def get_all_passengers():
    """Get all passengers from DB or mock data"""
    if DB_AVAILABLE:
        try:
            response = db_service.passengers_table.scan()
            return response.get('Items', [])
        except:
            pass
    
    # Return mock data
    return MOCK_PASSENGERS

def generate_mock_response(prompt, flight, rebooking_options, passenger):
    """Generate mock AI responses with rebooking functionality"""
    prompt_lower = prompt.lower()
    
    # Check if user is asking about rebooking
    if any(word in prompt_lower for word in ['book', 'rebook', 'select', 'choose', 'flight', 'ua789', 'ua234', 'aa654']):
        # Check which flight they want to book
        for option in rebooking_options:
            if option['flight_number'].lower() in prompt_lower:
                return f"""
                ✅ **Perfect! I'll help you book flight {option['flight_number']}.**
                
                ### ✈️ Your Selected Flight:
                - **Flight:** {option['flight_number']}
                - **🛫 Departure:** {option['departure']}
                - **🛬 Arrival:** {option['arrival']}
                
                ### 🎯 Booking Process:
                I'm processing your rebooking request for **{option['flight_number']}**...
                
                **✅ Rebooking Confirmed!**
                
                ### 📋 Next Steps:
                - 📧 Confirmation email sent to your registered address
                - 💺 Seat assignment: You'll be contacted for preferences
                - 🍽️ Meal selection: Available during online check-in
                - 🎫 New boarding pass: Available 24 hours before departure
                
                ### 🤝 Anything else I can help you with?
                - 💰 Delay compensation information
                - 🚗 Ground transportation options
                - 🏨 Hotel accommodations (if needed)
                - 📞 Connect with customer service
                """
        
        # Generic rebooking response if no specific flight mentioned
        return f"""
        I'd be happy to help you rebook your flight! Here are your available options:
        
        ### ✈️ Available Flights:
        {chr(10).join([f"**{i+1}. Flight {opt['flight_number']}** - Departs {opt['departure']}" for i, opt in enumerate(rebooking_options)])}
        
        ### 🎯 To Book:
        Just tell me which flight number you'd like (e.g., "I want to book flight UA789") and I'll process your rebooking immediately!
        
        ### 🤝 What would you like to do?
        - Tell me which flight to book
        - Ask about seat preferences
        - Get more details about any option
        """
    
    # Check for compensation questions
    elif any(word in prompt_lower for word in ['compensation', 'refund', 'money', 'reimburse']):
        return f"""
        ### 💰 Delay Compensation Information
        
        Based on your flight **{flight['flight_number']}** delay of **{format_delay_duration(flight['delay_minutes'])}**, you may be eligible for compensation.
        
        ### 🎯 Your Eligibility:
        - **Delay Duration:** {format_delay_duration(flight['delay_minutes'])} ✅
        - **Reason:** {flight['delay_reason']} 
        - **Loyalty Status:** {passenger['loyalty_tier']} Member 🏆
        
        ### 💵 Potential Compensation:
        - **Meal Vouchers:** $25 for delays over 2 hours ✅
        - **Flight Credit:** Up to $200 for delays over 3 hours ✅
        - **Hotel Accommodation:** If overnight delay (if applicable)
        
        ### 🤝 How to Claim:
        Would you like me to:
        - 📧 Email you the compensation claim form
        - 📞 Connect you with customer service
        - 🎫 Apply credits to your loyalty account
        """
    
    # General help response
    else:
        return f"""
        I understand you're asking about **{prompt}** regarding your flight **{flight['flight_number']}**.
        
        ### ✈️ Current Flight Status:
        Your flight is delayed by **{format_delay_duration(flight['delay_minutes'])}** due to **{flight['delay_reason']}**.
        
        ### 🔄 I Can Help You With:
        - ✈️ **Rebooking:** Choose from {len(rebooking_options)} available alternative flights
        - 💰 **Compensation:** Information about delay compensation
        - 📞 **Customer Service:** Connect with a live agent
        - 🏨 **Accommodations:** Hotel and meal arrangements
        - 🚗 **Transportation:** Ground transport options
        
        ### 🤝 How Can I Help You Next?
        - Tell me which rebooking option you'd like
        - Ask about compensation details
        - Connect with customer service
        - Get general travel assistance
        
        What would you like to do?
        """

def generate_ontime_response(prompt, flight, passenger):
    """Generate mock AI responses for on-time flights"""
    prompt_lower = prompt.lower()
    
    # Check for gate/terminal questions
    if any(word in prompt_lower for word in ['gate', 'terminal', 'location', 'where']):
        return f"""
        ### 🗺️ Gate & Terminal Information
        
        **Your flight {flight['flight_number']} details:**
        - **Gate:** {flight['gate']} 
        - **Terminal:** {flight['terminal']}
        - **Status:** 🟢 On Time
        - **Departure:** {flight['scheduled_departure']}
        
        ### 🚶‍♂️ Navigation Tips:
        - Gate {flight['gate']} is typically a 5-7 minute walk from security
        - Look for Terminal {flight['terminal']} signs after security
        - Boarding typically begins 30 minutes before departure
        
        ### 🤝 Need more help?
        - Airport map and directions
        - Nearby dining options
        - Shopping recommendations
        """
    
    # Check for dining questions
    elif any(word in prompt_lower for word in ['food', 'dining', 'restaurant', 'eat', 'meal']):
        return f"""
        ### 🍽️ Dining Options Near Gate {flight['gate']}
        
        **Recommended restaurants within 5 minutes of your gate:**
        
        ### 🍕 Quick Bites:
        - **Terminal Café** - Sandwiches, salads (2 min walk)
        - **Express Grill** - Burgers, fries (3 min walk)
        - **Fresh Market** - Healthy options, smoothies (4 min walk)
        
        ### 🍴 Sit-Down Options:
        - **Sky Bistro** - Full menu, bar service (5 min walk)
        - **International Kitchen** - Various cuisines (6 min walk)
        
        ### ⏰ Timing Recommendation:
        With your flight departing at {flight['scheduled_departure']}, you have plenty of time to enjoy a meal!
        
        ### 🤝 Would you like:
        - Specific menu recommendations
        - Airport shopping options
        - Entertainment areas
        """
    
    # Check for boarding/timing questions
    elif any(word in prompt_lower for word in ['board', 'time', 'when', 'departure']):
        return f"""
        ### ⏰ Boarding Information
        
        **Flight {flight['flight_number']} Timeline:**
        - **Scheduled Departure:** {flight['scheduled_departure']}
        - **Boarding Begins:** Approximately 30 minutes before departure
        - **Gate Closes:** 15 minutes before departure
        - **Current Status:** 🟢 On Time
        
        ### 🎯 Boarding Groups (Estimated):
        - **First Class & {passenger['loyalty_tier']}:** First to board
        - **Main Cabin:** By seat rows (back to front)
        
        ### 💡 Pro Tips:
        - Arrive at gate 15 minutes before boarding
        - Have boarding pass and ID ready
        - Check flight status monitors for updates
        
        ### 🤝 Anything else?
        - Gate directions
        - Airport amenities
        - Travel tips
        """
    
    # General on-time flight response
    else:
        return f"""
        I understand you're asking about **{prompt}** for your flight **{flight['flight_number']}**.
        
        ### ✅ Flight Status: On Time
        - **Flight:** {flight['flight_number']} 
        - **Gate:** {flight['gate']}, Terminal {flight['terminal']}
        - **Departure:** {flight['scheduled_departure']}
        - **Status:** 🟢 Right on schedule!
        
        ### 🎯 I Can Help With:
        - 🗺️ **Gate Directions:** Navigate to your departure gate
        - 🍽️ **Dining:** Restaurant recommendations near your gate  
        - 🛍️ **Shopping:** Duty-free and retail options
        - ⏰ **Timing:** Boarding times and airport procedures
        - 📋 **Travel Info:** General travel assistance
        
        ### 🤝 What would you like to know?
        - Airport navigation help
        - Dining and shopping options
        - Boarding procedures
        - General travel assistance
        
        How can I make your travel experience better today?
        """

# App header
st.markdown("<h1 class='main-header'>✈️ WingHelp !</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.2rem; color: #ffffff; font-weight: 600;'>Your AI-powered assistant for flight delays and rebooking</p>", unsafe_allow_html=True)

# Database status indicator
if not DB_AVAILABLE:
    st.markdown("""
    <div class='alert-box'>
        <strong>🔧 Demo Mode:</strong> Running with sample data. Connect to DynamoDB for live flight information.
    </div>
    """, unsafe_allow_html=True)

# Sidebar for login
st.sidebar.markdown("## 👤 Passenger Login")

# Get all passengers for the dropdown
try:
    all_passengers = get_all_passengers()
    
    if all_passengers:
        passenger_options = ["Select a passenger..."] + [f"{p['name']} ({p['passenger_id']})" for p in all_passengers]
        selected_passenger = st.sidebar.selectbox("", passenger_options)
        
        if selected_passenger != "Select a passenger...":
            passenger_id = selected_passenger.split("(")[1].split(")")[0]
            passenger = get_passenger_data(passenger_id)
            
            if passenger:
                st.sidebar.success(f"✅ **Logged in as {passenger['name']}**")
                st.sidebar.markdown(f"🏆 **Loyalty Tier:** {passenger['loyalty_tier']}")
                
                # Get flight information
                flight_id = passenger['flight_id']
                flight = get_flight_data(flight_id)
                
                if flight:
                    # Display flight information in sidebar
                    st.sidebar.markdown("### ✈️ Your Flight")
                    
                    status_class = "status-delayed" if flight['status'] == "Delayed" else "status-ontime"
                    status_emoji = "🔴" if flight['status'] == "Delayed" else "🟢"
                    
                    st.sidebar.markdown(f"**Flight:** {flight['flight_number']}")
                    st.sidebar.markdown(f"**Route:** {flight['origin']} → {flight['destination']}")
                    st.sidebar.markdown(f"**Status:** <span class='{status_class}'>{status_emoji} {flight['status']}</span>", unsafe_allow_html=True)
                    
                    # Main content area
                    if flight['status'] == "Delayed":
                        # Display delay information
                        st.markdown("<h2 class='sub-header'>🚨 Flight Delay Alert</h2>", unsafe_allow_html=True)
                        
                        # Flight details card
                        display_flight_card(flight, passenger)
                        
                    
                        
                        # Call center option
                        st.markdown("---")
                        st.markdown("<h2 class='sub-header'>📞 Quick Actions</h2>", unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("Connect with Customer Service", help="Get connected with a live agent"):
                                st.session_state.call_center = True
                        
                        # Chat with DelayCompanion
                        st.markdown("---")
                        st.markdown("<h2 class='sub-header'>💬 Chat with WingHelp AI</h2>", unsafe_allow_html=True)
                        st.markdown("**Ask me anything about your delayed flight, rebooking options, or travel policies. To book a rebooking option, just tell me which flight you'd like!**")
                        
                        # Initialize chat history
                        if "messages" not in st.session_state:
                            st.session_state.messages = []
                        
                        # Display chat history
                        for message in st.session_state.messages:
                            with st.chat_message(message["role"]):
                                st.markdown(message["content"])
                        
                        # Chat input
                        if prompt := st.chat_input("💭 How can I help you with your delayed flight? Ask me to book any rebooking option!"):
                            # Add user message to chat history
                            st.session_state.messages.append({"role": "user", "content": prompt})
                            
                            # Display user message
                            with st.chat_message("user"):
                                st.markdown(prompt)
                            
                            # Get response from agent
                            with st.chat_message("assistant"):
                                with st.spinner("🤔 Thinking..."):
                                    try:
                                        if DB_AVAILABLE:
                                            response, context = agent.process_query(prompt, passenger_id)
                                            formatted_response = format_agent_response(response)
                                        else:
                                            # Enhanced mock AI response with rebooking capabilities
                                            formatted_response = generate_mock_response(prompt, flight, rebooking_options, passenger)
                                        
                                        st.markdown(formatted_response)
                                    except Exception as e:
                                        error_message = f"""
                                        🚨 **System Notice**
                                        
                                        I'm experiencing some technical difficulties at the moment. 
                                        However, I can still assist you with general information about your flight **{flight['flight_number']}**.
                                        
                                        ### 🔄 What I can help with:
                                        - ✈️ Book any of the rebooking options shown above
                                        - 💰 Information about delay compensation policies
                                        - 📞 Connect you with a customer service representative
                                        - 📋 General travel assistance and policies
                                        
                                        ---
                                        ### 🤝 How would you like to proceed?
                                        Just tell me which flight option you'd like to book, or ask me any other questions!
                                        """
                                        st.markdown(error_message)
                                        formatted_response = error_message
                            
                            # Add assistant response to chat history
                            st.session_state.messages.append({"role": "assistant", "content": formatted_response})
                        
                        # Handle call center handoff
                        if "call_center" in st.session_state and st.session_state.call_center:
                            st.markdown("---")
                            st.markdown("<h2 class='sub-header'>📞 Customer Service Connection</h2>", unsafe_allow_html=True)
                            
                            st.markdown("""
                            <div class='info-box'>
                                <h4>🎯 Connecting you with a live agent...</h4>
                                <p><strong>Please hold while we gather your information for our customer service team.</strong></p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.markdown("### 📋 Information Shared with Agent")
                            st.markdown("**The following details will be provided to help expedite your call:**")
                            
                            st.markdown(f"""
                            **👤 Passenger:** {passenger['name']} ({passenger['loyalty_tier']} Member)
                            
                            **✈️ Flight:** {flight['flight_number']} from {flight['origin']} to {flight['destination']}
                            
                            **⏰ Delay:** {flight['delay_minutes']} minutes due to {flight['delay_reason']}
                            
                            **📞 Estimated wait time:** 3-5 minutes
                            """)
                            
                            # Simulated call progress
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            for i in range(100):
                                progress_bar.progress(i + 1)
                                if i < 30:
                                    status_text.text("🔍 Gathering your flight information...")
                                elif i < 60:
                                    status_text.text("📞 Connecting to next available agent...")
                                elif i < 90:
                                    status_text.text("🎧 Agent found! Preparing connection...")
                                else:
                                    status_text.text("✅ Connected! Please check your phone.")
                                time.sleep(0.05)
                            
                            st.success("📞 **Call Connected!** A customer service representative will be with you shortly.")
                            
                            if st.button("🔙 Return to Main Screen"):
                                st.session_state.call_center = False
                                st.rerun()
                    
                    else:
                        # Flight is on time
                        st.markdown("<h2 class='sub-header'>✅ Flight Status: On Time</h2>", unsafe_allow_html=True)
                        
                        display_flight_card(flight, passenger)
                        
                        st.markdown("""
                        <div class='success-box'>
                            <h4>🎉 Great News!</h4>
                            <p><strong>Your flight is currently on time. Please proceed to the gate at the scheduled boarding time.</strong></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Additional on-time flight options
                        st.markdown("### 🎯 Quick Actions")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("🗺️ Airport Map"):
                                st.info("📍 Opening interactive airport map...")
                        
                        with col2:
                            if st.button("🍽️ Dining Options"):
                                st.info("🍴 Showing nearby restaurants and cafes...")
                        
                        with col3:
                            if st.button("🛍️ Shopping"):
                                st.info("🛒 Browse duty-free and retail options...")
                        
                        # Chat for on-time flights too
                        st.markdown("---")
                        st.markdown("<h2 class='sub-header'>💬 Chat with WingHelp AI</h2>", unsafe_allow_html=True)
                        st.markdown("**Ask me anything about your flight, airport services, or travel assistance.**")
                        
                        # Initialize chat history
                        if "messages" not in st.session_state:
                            st.session_state.messages = []
                        
                        # Display chat history
                        for message in st.session_state.messages:
                            with st.chat_message(message["role"]):
                                st.markdown(message["content"])
                        
                        # Chat input
                        if prompt := st.chat_input("💭 How can I assist you with your travel today?"):
                            # Add user message to chat history
                            st.session_state.messages.append({"role": "user", "content": prompt})
                            
                            # Display user message
                            with st.chat_message("user"):
                                st.markdown(prompt)
                            
                            # Get response from agent
                            with st.chat_message("assistant"):
                                with st.spinner("🤔 Thinking..."):
                                    try:
                                        if DB_AVAILABLE:
                                            response, context = agent.process_query(prompt, passenger_id)
                                            formatted_response = format_agent_response(response)
                                        else:
                                            # Mock AI response for on-time flights
                                            formatted_response = generate_ontime_response(prompt, flight, passenger)
                                        
                                        st.markdown(formatted_response)
                                    except Exception as e:
                                        error_message = """
                                        🚨 **System Notice**
                                        
                                        I'm experiencing some technical difficulties, but I'm here to help with general travel assistance.
                                        
                                        ### 🎯 I can still help with:
                                        - 🗺️ Airport information and navigation
                                        - 📋 General travel policies
                                        - 🍽️ Airport dining and shopping
                                        - ⏰ Flight status updates
                                        
                                        What would you like to know?
                                        """
                                        st.markdown(error_message)
                                        formatted_response = error_message
                            
                            # Add assistant response to chat history
                            st.session_state.messages.append({"role": "assistant", "content": formatted_response})
                else:
                    st.sidebar.error("❌ Flight information not found.")
        else:
            # No passenger selected, show demo information
            st.markdown("""
            <div class='alert-box'>
                <h3>👈 Welcome to WingHelp!</h3>
                <p><strong>Please select a passenger from the sidebar to experience our AI-powered flight assistance.</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Demo information with better formatting
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                ## 🚀 About WingHelp
                
                **WingHelp is your intelligent travel companion that transforms the stress of flight delays into a seamless experience.**
                
                ### ✨ Key Features:
                - 🚨 **Real-time Notifications** - Instant delay alerts
                - 🤖 **AI-Powered Assistance** - Smart rebooking through chat  
                - ✈️ **Personalized Options** - Tailored to your preferences
                - 📞 **Seamless Handoffs** - Smooth transition to human agents
                - 💎 **Loyalty Integration** - Priority treatment for elite members
                """)
            
            with col2:
                st.markdown("""
                ## 🔧 How it Works:
                
                ### 1. 🔍 **Detection**
                **Our system monitors flights in real-time and detects delays immediately.**
                
                ### 2. 📱 **Notification**  
                **Affected passengers receive personalized delay notifications with options.**
                
                ### 3. 🎯 **Chat-Based Resolution**
                **Use our AI chatbot to rebook flights, get assistance, or connect with live agents.**
                
                ### 4. ✅ **Confirmation**
                **Seamless rebooking through conversation with seat and meal preferences.**
                """)
  

except Exception as e:
    st.markdown(f"""
    <div class='error-box'>
        <h3>🚨 System Error</h3>
        <p><strong>Error:</strong> {str(e)}</p>
        <p><strong>The application is running in demo mode with sample data. For full functionality, please ensure DynamoDB is properly configured.</strong></p>
    </div>
    """, unsafe_allow_html=True)

