#!/usr/bin/env python3
"""
DelayCompanion - Airline Assistant for Flight Delays
Built with AWS Strands Agent SDK and Claude Sonnet on Bedrock
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("delaycompanion")

def setup_database():
    """Set up the DynamoDB tables and load sample data"""
    from utils.setup_dynamodb import main as setup_db
    logger.info("Setting up DynamoDB tables and loading sample data...")
    setup_db()
    logger.info("Database setup complete!")

def run_streamlit():
    """Run the Streamlit web interface"""
    import subprocess
    logger.info("Starting Streamlit web interface...")
    subprocess.run(["streamlit", "run", "app/streamlit_app.py"])

def run_cli(passenger_id=None):
    """Run the CLI interface for testing the agent"""
    from app.agent import DelayCompanionAgent
    
    agent = DelayCompanionAgent()
    logger.info("DelayCompanion CLI started. Type 'exit' to quit.")
    
    if passenger_id:
        logger.info(f"Using passenger ID: {passenger_id}")
    
    while True:
        try:
            query = input("\nYou: ")
            if query.lower() in ["exit", "quit", "q"]:
                break
            
            response, _ = agent.process_query(query, passenger_id)
            print(f"\nDelayCompanion: {response}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
    
    logger.info("DelayCompanion CLI exited.")

def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description="DelayCompanion - Airline Assistant for Flight Delays")
    parser.add_argument("--setup", action="store_true", help="Set up DynamoDB tables and load sample data")
    parser.add_argument("--web", action="store_true", help="Run the Streamlit web interface")
    parser.add_argument("--cli", action="store_true", help="Run the CLI interface")
    parser.add_argument("--passenger", type=str, help="Passenger ID for CLI testing")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("strands").setLevel(logging.DEBUG)
    
    # Run the requested action
    if args.setup:
        setup_database()
    elif args.web:
        run_streamlit()
    elif args.cli:
        run_cli(args.passenger)
    else:
        # Default to web interface
        run_streamlit()

if __name__ == "__main__":
    main()
