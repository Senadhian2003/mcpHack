import boto3
import json
import csv
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def create_flights_table(dynamodb):
    """Create the flights table in DynamoDB"""
    try:
        table = dynamodb.create_table(
            TableName='DelayCompanion_Flights',
            KeySchema=[
                {
                    'AttributeName': 'flight_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'flight_id',
                    'AttributeType': 'S'
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"Creating table DelayCompanion_Flights...")
        table.meta.client.get_waiter('table_exists').wait(TableName='DelayCompanion_Flights')
        print(f"Table DelayCompanion_Flights created successfully!")
        return table
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print(f"Table DelayCompanion_Flights already exists.")
        return dynamodb.Table('DelayCompanion_Flights')

def create_passengers_table(dynamodb):
    """Create the passengers table in DynamoDB"""
    try:
        table = dynamodb.create_table(
            TableName='DelayCompanion_Passengers',
            KeySchema=[
                {
                    'AttributeName': 'passenger_id',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'passenger_id',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName': 'flight_id',
                    'AttributeType': 'S'
                }
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'FlightIndex',
                    'KeySchema': [
                        {
                            'AttributeName': 'flight_id',
                            'KeyType': 'HASH'
                        }
                    ],
                    'Projection': {
                        'ProjectionType': 'ALL'
                    }
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"Creating table DelayCompanion_Passengers...")
        table.meta.client.get_waiter('table_exists').wait(TableName='DelayCompanion_Passengers')
        print(f"Table DelayCompanion_Passengers created successfully!")
        return table
    except dynamodb.meta.client.exceptions.ResourceInUseException:
        print(f"Table DelayCompanion_Passengers already exists.")
        return dynamodb.Table('DelayCompanion_Passengers')

def load_flights_data(flights_table, csv_file):
    """Load flight data from CSV into DynamoDB"""
    with open(csv_file, mode='r', encoding='utf-8') as file:
        # Read the entire file content
        content = file.read()
        
        # Split by lines and skip header
        lines = content.strip().split('\n')
        header = lines[0].split(',')
        
        for i, line in enumerate(lines[1:], 1):
            # Create a clean item dictionary
            item = {}
            
            # Split the line by comma, but be careful with the JSON part
            parts = []
            in_quotes = False
            current_part = ""
            
            for char in line:
                if char == '"' and not in_quotes:
                    in_quotes = True
                    current_part += char
                elif char == '"' and in_quotes:
                    in_quotes = False
                    current_part += char
                elif char == ',' and not in_quotes:
                    parts.append(current_part)
                    current_part = ""
                else:
                    current_part += char
            
            # Add the last part
            if current_part:
                parts.append(current_part)
            
            # Map header to values
            for j, key in enumerate(header):
                if j < len(parts):
                    value = parts[j].strip()
                    
                    # Skip empty values
                    if not value:
                        continue
                    
                    # Handle special fields
                    if key == 'delay_minutes':
                        item[key] = int(value) if value else 0
                    elif key == 'rebooking_options':
                        if value.startswith('"') and value.endswith('"'):
                            # Remove the outer quotes
                            value = value[1:-1]
                        
                        if value:
                            try:
                                # Replace escaped quotes with regular quotes
                                value = value.replace('\\"', '"')
                                item[key] = json.loads(value)
                            except json.JSONDecodeError as e:
                                print(f"Error parsing JSON for row {i}: {e}")
                                print(f"JSON string: {value}")
                                item[key] = []
                        else:
                            item[key] = []
                    else:
                        item[key] = value
            
            # Debug print
            print(f"Row {i}: {item}")
            
            # Make sure flight_id is present
            if 'flight_id' not in item or not item['flight_id']:
                print(f"Skipping row {i} due to missing flight_id")
                continue
                
            # Add item to DynamoDB
            flights_table.put_item(Item=item)
    
    print(f"Loaded flight data into DelayCompanion_Flights table")

def load_passengers_data(passengers_table, csv_file):
    """Load passenger data from CSV into DynamoDB"""
    with open(csv_file, mode='r', encoding='utf-8') as file:
        # Read the entire file content
        content = file.read()
        
        # Split by lines and skip header
        lines = content.strip().split('\n')
        header = lines[0].split(',')
        
        for i, line in enumerate(lines[1:], 1):
            # Create a clean item dictionary
            item = {}
            
            # Split the line by comma, but be careful with quoted values
            parts = []
            in_quotes = False
            current_part = ""
            
            for char in line:
                if char == '"' and not in_quotes:
                    in_quotes = True
                    current_part += char
                elif char == '"' and in_quotes:
                    in_quotes = False
                    current_part += char
                elif char == ',' and not in_quotes:
                    parts.append(current_part)
                    current_part = ""
                else:
                    current_part += char
            
            # Add the last part
            if current_part:
                parts.append(current_part)
            
            # Map header to values
            for j, key in enumerate(header):
                if j < len(parts):
                    value = parts[j].strip()
                    
                    # Skip empty values
                    if not value:
                        continue
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    
                    item[key] = value
            
            # Debug print
            print(f"Passenger Row {i}: {item}")
            
            # Make sure passenger_id is present
            if 'passenger_id' not in item or not item['passenger_id']:
                print(f"Skipping passenger row {i} due to missing passenger_id")
                continue
                
            # Add item to DynamoDB
            passengers_table.put_item(Item=item)
    
    print(f"Loaded passenger data into DelayCompanion_Passengers table")

def main():
    """Main function to set up DynamoDB tables and load data"""
    # Initialize DynamoDB resource
    dynamodb = boto3.resource('dynamodb')
    
    # Create tables
    flights_table = create_flights_table(dynamodb)
    passengers_table = create_passengers_table(dynamodb)
    
    # Load data from CSV files
    flights_csv = os.path.join(project_root, 'data', 'flightdelays.csv')
    passengers_csv = os.path.join(project_root, 'data', 'passengers.csv')
    
    load_flights_data(flights_table, flights_csv)
    load_passengers_data(passengers_table, passengers_csv)
    
    print("DynamoDB setup complete!")

if __name__ == "__main__":
    main()
