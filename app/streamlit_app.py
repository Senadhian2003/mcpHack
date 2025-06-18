import streamlit as st
import sys
import os
from pathlib import Path
import json
import pandas as pd
from datetime import datetime
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.agent import DelayCompanionAgent
from models.dynamodb import DynamoDBService

# Initialize the agent and DB service
agent = DelayCompanionAgent()
db_service = DynamoDBService()

# Set page configuration
st.set_page_config(
    page_title="DelayCompanion",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #003366;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0066cc;
        margin-bottom: 1rem;
    }
    .status-delayed {
        color: #cc0000;
        font-weight: bold;
    }
    .status-ontime {
        color: #009900;
        font-weight: bold;
    }
    .info-box {
        background-color: #f0f7ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #cce0ff;
        margin-bottom: 1rem;
    }
    .option-box {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
        transition: all 0.3s ease;
    }
    .option-box:hover {
        background-color: #e6f2ff;
        border: 1px solid #99ccff;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .emoji-large {
        font-size: 1.5rem;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
    }
    .alert-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def format_agent_response(response):
    """
    Format the agent response for better display in Streamlit
    """
    # If response is a dict with role/content structure, extract the content
    if isinstance(response, dict):
        if 'content' in response:
            if isinstance(response['content'], list):
                # Extract text from content list
                content_text = ""
                for item in response['content']:
                    if isinstance(item, dict) and 'text' in item:
                        content_text += item['text']
                response = content_text
            else:
                response = response['content']
    
    # If response is still a string representation of a dict, try to parse it
    if isinstance(response, str) and "'role':" in response:
        # This handles the raw format you showed
        try:
            # Extract the text content from the string representation
            text_match = re.search(r"'text': \"(.*?)\"", response, re.DOTALL)
            if text_match:
                response = text_match.group(1)
                # Clean up escaped characters
                response = response.replace('\\n', '\n').replace('\\"', '"')
        except:
            pass
    
    # Apply additional formatting for better display
    response = apply_delaycompanion_formatting(response)
    
    return response

def apply_delaycompanion_formatting(text):
    """
    Apply DelayCompanion-specific formatting to the response text
    """
    # Add status indicators with colored text
    text = text.replace("Delayed", "🔴 **Delayed**")
    text = text.replace("On Time", "🟢 **On Time**")
    
    # Format flight numbers
    text = re.sub(r'\b([A-Z]{2}\d{3,4})\b', r'**\1**', text)
    
    # Add section dividers
    if "Would you like me to:" in text:
        text = text.replace("Would you like me to:", "\n---\n### 🤝 How Can I Help You Next?\n\nWould you like me to:")
    
    # Format bullet points with emojis
    text = text.replace("- Help you explore", "- ✈️ Help you explore")
    text = text.replace("- Connect you with", "- 📞 Connect you with")
    text = text.replace("- Provide general", "- 📋 Provide general")
    
    # Add emojis to common phrases
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

def display_rebooking_options(rebooking_options, flight_id):
    """Display rebooking options with enhanced formatting"""
    if not rebooking_options:
        st.warning("❌ No rebooking options are currently available.")
        return None
    
    st.markdown("### ✈️ Available Rebooking Options")
    st.markdown("Select an alternative flight below:")
    
    selected_option = None
    
    for i, option in enumerate(rebooking_options):
        with st.container():
            st.markdown(f"""
            <div class='option-box' id='option_{i}'>
            """, unsafe_allow_html=True)
            
            cols = st.columns([1, 4, 2])
            
            with cols[0]:
                st.markdown("<span class='emoji-large'>✈️</span>", unsafe_allow_html=True)
            
            with cols[1]:
                st.markdown(f"**Flight {option['flight_number']}**")
                st.markdown(f"🛫 Departs: **{option['departure']}**")
                st.markdown(f"🛬 Arrives: **{option['arrival']}**")
                
                # Calculate time difference if available
                try:
                    original_time = datetime.strptime(option.get('original_departure', ''), '%Y-%m-%d %H:%M')
                    new_time = datetime.strptime(option['departure'], '%Y-%m-%d %H:%M')
                    time_diff = new_time - original_time
                    hours_diff = time_diff.total_seconds() / 3600
                    
                    if hours_diff > 0:
                        st.markdown(f"⏰ **{hours_diff:.1f} hours later than original**")
                    elif hours_diff < 0:
                        st.markdown(f"⏰ **{abs(hours_diff):.1f} hours earlier than original**")
                except:
                    pass
            
            with cols[2]:
                if st.button(f"✅ Select Flight", key=f"select_{i}", help=f"Select flight {option['flight_number']}"):
                    selected_option = option
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("")  # Add spacing
    
    return selected_option

# App header
st.markdown("<h1 class='main-header'>✈️ DelayCompanion</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.2rem; color: #666;'>Your AI-powered assistant for flight delays and rebooking</p>", unsafe_allow_html=True)

# Sidebar for login
st.sidebar.markdown("## 👤 Passenger Login")

# Get all passengers for the dropdown
try:
    # In a real app, we would authenticate users
    # For this demo, we'll just list all passengers
    all_passengers = []
    response = db_service.passengers_table.scan()
    all_passengers = response.get('Items', [])
    
    passenger_options = ["Select a passenger..."] + [f"{p['name']} ({p['passenger_id']})" for p in all_passengers]
    selected_passenger = st.sidebar.selectbox("🔍 Select your name:", passenger_options)
    
    if selected_passenger != "Select a passenger...":
        passenger_id = selected_passenger.split("(")[1].split(")")[0]
        passenger = db_service.get_passenger(passenger_id)
        
        if passenger:
            st.sidebar.success(f"✅ Logged in as **{passenger['name']}**")
            st.sidebar.markdown(f"🏆 **Loyalty Tier:** {passenger['loyalty_tier']}")
            
            # Get flight information
            flight_id = passenger['flight_id']
            flight = db_service.get_flight(flight_id)
            
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
                    
                    # Display rebooking options
                    st.markdown("<h2 class='sub-header'>✈️ Rebooking Options</h2>", unsafe_allow_html=True)
                    
                    rebooking_options = flight.get('rebooking_options', [])
                    selected_option = display_rebooking_options(rebooking_options, flight_id)
                    
                    # Handle rebooking selection
                    if selected_option:
                        st.session_state.rebooking = True
                        st.session_state.selected_option = selected_option
                    
                    # Call center option
                    st.markdown("---")
                    st.markdown("<h2 class='sub-header'>📞 Need Personal Assistance?</h2>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📞 Connect with Customer Service", help="Get connected with a live agent"):
                            st.session_state.call_center = True
                    
                    with col2:
                        if st.button("📧 Send Email Updates", help="Get email notifications about your flight"):
                            st.success("✅ Email notifications enabled!")
                    
                    # Chat with DelayCompanion
                    st.markdown("---")
                    st.markdown("<h2 class='sub-header'>💬 Chat with DelayCompanion AI</h2>", unsafe_allow_html=True)
                    st.markdown("Ask me anything about your delayed flight, rebooking options, or travel policies.")
                    
                    # Initialize chat history
                    if "messages" not in st.session_state:
                        st.session_state.messages = []
                    
                    # Display chat history
                    for message in st.session_state.messages:
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])
                    
                    # Chat input
                    if prompt := st.chat_input("💭 How can I help you with your delayed flight?"):
                        # Add user message to chat history
                        st.session_state.messages.append({"role": "user", "content": prompt})
                        
                        # Display user message
                        with st.chat_message("user"):
                            st.markdown(prompt)
                        
                        # Get response from agent
                        with st.chat_message("assistant"):
                            with st.spinner("🤔 Thinking..."):
                                try:
                                    response, context = agent.process_query(prompt, passenger_id)
                                    formatted_response = format_agent_response(response)
                                    st.markdown(formatted_response)
                                except Exception as e:
                                    error_message = f"""
                                    🚨 **System Notice**
                                    
                                    I'm experiencing some technical difficulties accessing the flight database at the moment. 
                                    However, I can still assist you with general information about your flight **{flight['flight_number']}**.
                                    
                                    ### 🔄 What I can help with:
                                    - ✈️ Explore rebooking options from the list above
                                    - 💰 Information about delay compensation policies
                                    - 📞 Connect you with a customer service representative
                                    - 📋 General travel assistance and policies
                                    
                                    ---
                                    ### 🤝 How would you like to proceed?
                                    Please let me know how I can best assist you during this delay.
                                    """
                                    st.markdown(error_message)
                                    formatted_response = error_message
                        
                        # Add assistant response to chat history
                        st.session_state.messages.append({"role": "assistant", "content": formatted_response})
                    
                    # Handle rebooking confirmation
                    if "rebooking" in st.session_state and st.session_state.rebooking:
                        option = st.session_state.selected_option
                        
                        st.markdown("---")
                        st.markdown("<h2 class='sub-header'>✅ Confirm Your Rebooking</h2>", unsafe_allow_html=True)
                        
                        st.markdown(f"""
                        <div class='success-box'>
                            <h4>🎯 Selected Flight Details</h4>
                            <p><strong>Flight:</strong> {option['flight_number']}</p>
                            <p><strong>Departure:</strong> {option['departure']}</p>
                            <p><strong>Arrival:</strong> {option['arrival']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Get seat preference
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            seat_preference = st.selectbox(
                                "💺 Seat Preference:",
                                ["Window", "Aisle", "Middle", "No Preference"],
                                help="Select your preferred seat type"
                            )
                        
                        with col2:
                            meal_preference = st.selectbox(
                                "🍽️ Meal Preference:",
                                ["Standard", "Vegetarian", "Vegan", "Kosher", "No Meal"],
                                help="Select your meal preference"
                            )
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if st.button("✅ Confirm Rebooking", type="primary"):
                                # Process rebooking
                                with st.spinner("Processing your rebooking..."):
                                    try:
                                        result = agent.rebook_passenger(
                                            passenger_id=passenger_id,
                                            new_flight_id=option['flight_id'],
                                            seat_preference=seat_preference
                                        )
                                        
                                        if result['success']:
                                            st.success("🎉 **Rebooking Successful!**")
                                            st.markdown(f"✅ You have been rebooked on flight **{option['flight_number']}**")
                                            st.markdown(f"🛫 Departure: **{option['departure']}**")
                                            st.markdown(f"🛬 Arrival: **{option['arrival']}**")
                                            st.markdown(f"💺 Seat Preference: **{seat_preference}**")
                                            st.markdown(f"🍽️ Meal Preference: **{meal_preference}**")
                                            
                                            # Clear rebooking state
                                            st.session_state.rebooking = False
                                            st.session_state.selected_option = None
                                            
                                            # Auto-refresh after 3 seconds
                                            st.balloons()
                                            time.sleep(2)
                                            st.experimental_rerun()
                                        else:
                                            st.error("❌ **Rebooking Failed**")
                                            st.markdown(result['message'])
                                    except Exception as e:
                                        st.error("❌ **Technical Error**")
                                        st.markdown("Please try again or contact customer service.")
                        
                        with col2:
                            if st.button("🔙 Go Back"):
                                st.session_state.rebooking = False
                                st.session_state.selected_option = None
                                st.experimental_rerun()
                        
                        with col3:
                            if st.button("📞 Call Instead"):
                                st.session_state.call_center = True
                                st.session_state.rebooking = False
                                st.experimental_rerun()
                    
                    # Handle call center handoff
                    if "call_center" in st.session_state and st.session_state.call_center:
                        st.markdown("---")
                        st.markdown("<h2 class='sub-header'>📞 Customer Service Connection</h2>", unsafe_allow_html=True)
                        
                        st.markdown("""
                        <div class='info-box'>
                            <h4>🎯 Connecting you with a live agent...</h4>
                            <p>Please hold while we gather your information for our customer service team.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Generate handoff context
                        try:
                            handoff_context = agent.generate_handoff_context(passenger_id)
                            
                            st.markdown("### 📋 Information Shared with Agent")
                            st.markdown("The following details will be provided to help expedite your call:")
                            
                            # Display handoff context in a formatted way
                            st.markdown(f"""
                            **👤 Passenger:** {handoff_context['passenger']['name']} ({handoff_context['passenger']['loyalty_tier']} Member)
                            
                            **✈️ Flight:** {handoff_context['flight']['number']} from {handoff_context['flight']['origin']} to {handoff_context['flight']['destination']}
                            
                            **⏰ Delay:** {handoff_context['flight']['delay_minutes']} minutes due to {handoff_context['flight']['delay_reason']}
                            
                            **📞 Estimated wait time:** 3-5 minutes
                            """)
                            
                            # Display rebooking history if any
                            if handoff_context.get('rebooking_history'):
                                st.markdown("**🔄 Recent Activity:**")
                                for rebooking in handoff_context['rebooking_history']:
                                    st.markdown(f"- Attempted rebooking from {rebooking['old_flight_id']} to {rebooking['new_flight_id']} at {rebooking['timestamp']}")
                        
                        except Exception as e:
                            st.markdown("**📋 Basic Information Available:**")
                            st.markdown(f"- Passenger: {passenger['name']}")
                            st.markdown(f"- Flight: {flight['flight_number']}")
                            st.markdown(f"- Status: Delayed")
                        
                        # Simulated call progress
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        import time
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
                            st.experimental_rerun()
                
                else:
                    # Flight is on time
                    st.markdown("<h2 class='sub-header'>✅ Flight Status: On Time</h2>", unsafe_allow_html=True)
                    
                    display_flight_card(flight, passenger)
                    
                    st.markdown("""
                    <div class='success-box'>
                        <h4>🎉 Great News!</h4>
                        <p>Your flight is currently on time. Please proceed to the gate at the scheduled boarding time.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Additional on-time flight options
                    st.markdown("### 🎯 Quick Actions")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("🗺️ Airport Map"):
                            st.info("Opening interactive airport map...")
                    
                    with col2:
                        if st.button("🍽️ Dining Options"):
                            st.info("Showing nearby restaurants and cafes...")
                    
                    with col3:
                        if st.button("🛍️ Shopping"):
                            st.info("Browse duty-free and retail options...")
        else:
            st.sidebar.error("❌ Passenger not found.")
    else:
        # No passenger selected, show demo information
        st.markdown("""
        <div class='alert-box'>
            <h3>👈 Welcome to DelayCompanion!</h3>
            <p>Please select a passenger from the sidebar to experience our AI-powered flight assistance.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Demo information with better formatting
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ## 🚀 About DelayCompanion
            
            DelayCompanion is your intelligent travel companion that transforms the stress of flight delays into a seamless experience.
            
            ### ✨ Key Features:
            - 🚨 **Real-time Notifications** - Instant delay alerts
            - 🤖 **AI-Powered Assistance** - Smart rebooking suggestions
            - ✈️ **Personalized Options** - Tailored to your preferences
            - 📞 **Seamless Handoffs** - Smooth transition to human agents
            - 💎 **Loyalty Integration** - Priority treatment for elite members
            """)
        
        with col2:
            st.markdown("""
            ## 🔧 How it Works:
            
            ### 1. 🔍 **Detection**
            Our system monitors flights in real-time and detects delays immediately.
            
            ### 2. 📱 **Notification**
            Affected passengers receive personalized delay notifications with options.
            
            ### 3. 🎯 **Resolution**
            Choose from AI-curated rebooking options or connect with live agents.
            
            ### 4. ✅ **Confirmation**
            Seamless rebooking with seat preferences and meal options.
            """)
        
        st.markdown("---")
        st.markdown("### 🎭 Demo Passengers Available:")
        
        # Show available demo passengers
        if all_passengers:
            for passenger in all_passengers[:3]:  # Show first 3 passengers
                flight = db_service.get_flight(passenger['flight_id'])
                status_emoji = "🔴" if flight['status'] == "Delayed" else "🟢"
                
                st.markdown(f"""
                **{passenger['name']}** ({passenger['loyalty_tier']}) - Flight {flight['flight_number']} {status_emoji}
                """)

except Exception as e:
    st.markdown(f"""
    <div class='error-box'>
        <h3>🚨 System Error</h3>
        <p><strong>Error:</strong> {str(e)}</p>
        <p>Please ensure you've set up the DynamoDB tables and loaded the sample data.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.code("python utils/setup_dynamodb.py", language="bash")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>© 2025 DelayCompanion | Built with ❤️ using AWS Strands Agent SDK and Claude Sonnet on Bedrock</p>
    <p>🔒 Secure • 🚀 Fast • 🎯 Intelligent</p>
</div>
""", unsafe_allow_html=True)