# DelayCompanion

An airline assistant for flight delays built with AWS Strands Agent SDK and Claude Sonnet on Bedrock.

## Overview

DelayCompanion is an AI-powered airline assistant that helps passengers manage flight delays and rebooking options. It provides:

- 🚨 Real-time flight delay notifications
- ✈️ Personalized rebooking options
- 💬 Interactive chat assistance
- ☎️ Seamless handoff to human agents

## Project Structure

```
DelayCompanion/
├── app/                    # Application code
│   ├── __init__.py
│   ├── agent.py            # Strands Agent implementation
│   └── streamlit_app.py    # Streamlit web interface
├── data/                   # Sample data files
│   ├── flightdelays.csv    # Sample flight delay data
│   └── passengers.csv      # Sample passenger data
├── models/                 # Data models
│   ├── __init__.py
│   └── dynamodb.py         # DynamoDB data access layer
├── utils/                  # Utility scripts
│   ├── __init__.py
│   └── setup_dynamodb.py   # Script to set up DynamoDB tables
├── main.py                 # Main entry point
├── README.md               # Project documentation
└── requirements.txt        # Python dependencies
```

## Prerequisites

- Python 3.9+
- AWS account with DynamoDB access
- AWS CLI configured with appropriate credentials
- Access to Claude Sonnet model in Amazon Bedrock

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/DelayCompanion.git
   cd DelayCompanion
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up DynamoDB tables and load sample data:
   ```
   python main.py --setup
   ```

## Usage

### Web Interface

Run the Streamlit web interface:
```
python main.py --web
```

Or simply:
```
python main.py
```

This will start a local web server at http://localhost:8501 where you can interact with the DelayCompanion assistant.

### CLI Interface

For testing purposes, you can also use the CLI interface:
```
python main.py --cli
```

To test with a specific passenger:
```
python main.py --cli --passenger P001
```

## Development

Enable debug logging for development:
```
python main.py --web --debug
```

## Architecture

DelayCompanion uses the following AWS services:

- **AWS Strands Agent SDK**: Core agent framework
- **Amazon Bedrock**: Claude Sonnet model for natural language understanding
- **Amazon DynamoDB**: Storage for flight and passenger data
- **Streamlit**: Web interface for demonstration

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- AWS Strands Agent SDK team
- Anthropic for Claude Sonnet model
- Streamlit for the web interface framework
