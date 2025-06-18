import streamlit as st
import sys
import os
from pathlib import Path
import json
import pandas as pd
from datetime import datetime

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
    }
    .option-box:hover {
        background-color: #e6f2ff;
        border: 1px solid #99ccff;
    }
    .emoji-large {
        font-size: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown("<h1 class='main-header'>✈️ DelayCompanion</h1>", unsafe_allow_html=True)
st.markdown("<p>Your AI assistant for flight delays and rebooking</p>", unsafe_allow_html=True)

# Sidebar for login
st.sidebar.markdown("<h2>Passenger Login</h2>", unsafe_allow_html=True)

# Get all passengers for the dropdown
try:
    # In a real app, we would authenticate users
    # For this demo, we'll just list all passengers
    all_passengers = []
    response = db_service.passengers_table.scan()
    all_passengers = response.get('Items', [])
    
    passenger_options = ["Select a passenger..."] + [f"{p['name']} ({p['passenger_id']})" for p in all_passengers]
    selected_passenger = st.sidebar.selectbox("Select your name:", passenger_options)
    
    if selected_passenger != "Select a passenger...":
        passenger_id = selected_passenger.split("(")[1].split(")")[0]
        passenger = db_service.get_passenger(passenger_id)
        
        if passenger:
            st.sidebar.success(f"Logged in as {passenger['name']}")
            st.sidebar.markdown(f"**Loyalty Tier:** {passenger['loyalty_tier']}")
            
            # Get flight information
            flight_id = passenger['flight_id']
            flight = db_service.get_flight(flight_id)
            
            if flight:
                # Display flight information in sidebar
                st.sidebar.markdown("### Your Flight")
                
                status_class = "status-delayed" if flight['status'] == "Delayed" else "status-ontime"
                st.sidebar.markdown(f"**Flight:** {flight['flight_number']}")
                st.sidebar.markdown(f"**Route:** {flight['origin']} → {flight['destination']}")
                st.sidebar.markdown(f"**Status:** <span class='{status_class}'>{flight['status']}</span>", unsafe_allow_html=True)
                
                # Main content area
                if flight['status'] == "Delayed":
                    # Display delay information
                    st.markdown("<h2 class='sub-header'>🚨 Flight Delay Alert</h2>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
                        st.markdown(f"### Flight Details")
                        st.markdown(f"**Airline:** {flight['airline']}")
                        st.markdown(f"**Flight:** {flight['flight_number']}")
                        st.markdown(f"**From:** {flight['origin']} to {flight['destination']}")
                        st.markdown(f"**Gate:** {flight['gate']}, Terminal {flight['terminal']}")
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
                        st.markdown(f"### Delay Information")
                        
                        # Calculate delay in hours and minutes
                        delay_minutes = int(flight['delay_minutes'])
                        hours = delay_minutes // 60
                        mins = delay_minutes % 60
                        delay_text = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
                        
                        st.markdown(f"**Delay Duration:** {delay_text}")
                        st.markdown(f"**Reason:** {flight['delay_reason']}")
                        st.markdown(f"**Original Departure:** {flight['scheduled_departure']}")
                        st.markdown(f"**New Departure:** {flight['actual_departure']}")
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Display rebooking options
                    st.markdown("<h2 class='sub-header'>✈️ Rebooking Options</h2>", unsafe_allow_html=True)
                    
                    rebooking_options = flight.get('rebooking_options', [])
                    if rebooking_options:
                        selected_option = None
                        
                        for i, option in enumerate(rebooking_options):
                            option_id = f"option_{i}"
                            
                            st.markdown(f"<div class='option-box' id='{option_id}'>", unsafe_allow_html=True)
                            cols = st.columns([1, 3, 2])
                            
                            with cols[0]:
                                st.markdown(f"<span class='emoji-large'>✈️</span>", unsafe_allow_html=True)
                            
                            with cols[1]:
                                st.markdown(f"**Flight {option['flight_number']}**")
                                st.markdown(f"Departs: {option['departure']}")
                                st.markdown(f"Arrives: {option['arrival']}")
                            
                            with cols[2]:
                                if st.button(f"Select This Flight", key=f"select_{i}"):
                                    selected_option = option
                            
                            st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Handle rebooking
                        if selected_option:
                            st.session_state.rebooking = True
                            st.session_state.selected_option = selected_option
                    else:
                        st.info("No rebooking options are currently available.")
                    
                    # Call center option
                    st.markdown("<h2 class='sub-header'>☎️ Need More Help?</h2>", unsafe_allow_html=True)
                    
                    if st.button("Connect with a Customer Service Agent"):
                        st.session_state.call_center = True
                    
                    # Chat with DelayCompanion
                    st.markdown("<h2 class='sub-header'>💬 Chat with DelayCompanion</h2>", unsafe_allow_html=True)
                    
                    # Initialize chat history
                    if "messages" not in st.session_state:
                        st.session_state.messages = []
                    
                    # Display chat history
                    for message in st.session_state.messages:
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])
                    
                    # Chat input
                    if prompt := st.chat_input("How can I help you with your delayed flight?"):
                        # Add user message to chat history
                        st.session_state.messages.append({"role": "user", "content": prompt})
                        
                        # Display user message
                        with st.chat_message("user"):
                            st.markdown(prompt)
                        
                        # Get response from agent
                        with st.chat_message("assistant"):
                            with st.spinner("Thinking..."):
                                response, context = agent.process_query(prompt, passenger_id)
                                st.markdown(response)
                        
                        # Add assistant response to chat history
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    # Handle rebooking confirmation
                    if "rebooking" in st.session_state and st.session_state.rebooking:
                        option = st.session_state.selected_option
                        
                        st.markdown("<h2 class='sub-header'>✅ Rebooking Confirmation</h2>", unsafe_allow_html=True)
                        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
                        
                        # Get seat preference
                        seat_preference = st.selectbox(
                            "Seat Preference:",
                            ["Window", "Aisle", "Middle", "No Preference"]
                        )
                        
                        if st.button("Confirm Rebooking"):
                            # Process rebooking
                            result = agent.rebook_passenger(
                                passenger_id=passenger_id,
                                new_flight_id=option['flight_id'],
                                seat_preference=seat_preference
                            )
                            
                            if result['success']:
                                st.success("✅ Rebooking Successful!")
                                st.markdown(f"You have been rebooked on flight {option['flight_number']}")
                                st.markdown(f"Departure: {option['departure']}")
                                st.markdown(f"Arrival: {option['arrival']}")
                                st.markdown(f"Seat Preference: {seat_preference}")
                                
                                # Clear rebooking state
                                st.session_state.rebooking = False
                                st.session_state.selected_option = None
                                
                                # Refresh the page
                                st.experimental_rerun()
                            else:
                                st.error("❌ Rebooking Failed")
                                st.markdown(result['message'])
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Handle call center handoff
                    if "call_center" in st.session_state and st.session_state.call_center:
                        st.markdown("<h2 class='sub-header'>☎️ Call Center Handoff</h2>", unsafe_allow_html=True)
                        st.markdown("<div class='info-box'>", unsafe_allow_html=True)
                        
                        # Generate handoff context
                        handoff_context = agent.generate_handoff_context(passenger_id)
                        
                        st.markdown("### Handoff Context for Call Center Agent")
                        st.markdown("The following information will be provided to the call center agent:")
                        
                        # Display handoff context in a formatted way
                        st.markdown(f"**Passenger:** {handoff_context['passenger']['name']} ({handoff_context['passenger']['loyalty_tier']})")
                        st.markdown(f"**Flight:** {handoff_context['flight']['number']} from {handoff_context['flight']['origin']} to {handoff_context['flight']['destination']}")
                        st.markdown(f"**Delay:** {handoff_context['flight']['delay_minutes']} minutes due to {handoff_context['flight']['delay_reason']}")
                        
                        # Display rebooking history if any
                        if handoff_context['rebooking_history']:
                            st.markdown("**Rebooking History:**")
                            for rebooking in handoff_context['rebooking_history']:
                                st.markdown(f"- Changed from {rebooking['old_flight_id']} to {rebooking['new_flight_id']} at {rebooking['timestamp']}")
                        
                        st.markdown("A customer service agent will call you shortly.")
                        
                        if st.button("Close"):
                            st.session_state.call_center = False
                            st.experimental_rerun()
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    # Flight is on time
                    st.markdown("<h2 class='sub-header'>✅ Flight Status: On Time</h2>", unsafe_allow_html=True)
                    st.markdown("<div class='info-box'>", unsafe_allow_html=True)
                    st.markdown(f"### Flight Details")
                    st.markdown(f"**Airline:** {flight['airline']}")
                    st.markdown(f"**Flight:** {flight['flight_number']}")
                    st.markdown(f"**From:** {flight['origin']} to {flight['destination']}")
                    st.markdown(f"**Departure:** {flight['scheduled_departure']}")
                    st.markdown(f"**Arrival:** {flight['scheduled_arrival']}")
                    st.markdown(f"**Gate:** {flight['gate']}, Terminal {flight['terminal']}")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.success("Your flight is currently on time. Please proceed to the gate at the scheduled time.")
        else:
            st.sidebar.error("Passenger not found.")
    else:
        # No passenger selected, show demo information
        st.info("👈 Please select a passenger from the sidebar to simulate the DelayCompanion experience.")
        
        st.markdown("""
        ## About DelayCompanion
        
        DelayCompanion is an AI-powered airline assistant that helps passengers manage flight delays and rebooking options.
        
        ### Key Features:
        - 🚨 Real-time flight delay notifications
        - ✈️ Personalized rebooking options
        - 💬 Interactive chat assistance
        - ☎️ Seamless handoff to human agents
        
        ### How it Works:
        1. The system detects flight delays from airline systems
        2. Affected passengers receive personalized notifications
        3. Passengers can view and select rebooking options
        4. All context is preserved when transferring to human agents
        
        Select a passenger from the sidebar to see a demonstration of the DelayCompanion experience.
        """)
except Exception as e:
    st.error(f"Error loading passenger data: {str(e)}")
    st.info("Make sure you've set up the DynamoDB tables and loaded the sample data.")
    st.code("python utils/setup_dynamodb.py")

# Footer
st.markdown("---")
st.markdown("© 2025 DelayCompanion | Built with AWS Strands Agent SDK and Claude Sonnet on Bedrock")
