import boto3
from boto3.dynamodb.conditions import Key
import json
from datetime import datetime

class DynamoDBService:
    """Service class for interacting with DynamoDB tables"""
    
    def __init__(self):
        """Initialize the DynamoDB service"""
        self.dynamodb = boto3.resource('dynamodb')
        self.flights_table = self.dynamodb.Table('DelayCompanion_Flights')
        self.passengers_table = self.dynamodb.Table('DelayCompanion_Passengers')
    
    def get_flight(self, flight_id):
        """Get flight details by flight ID"""
        response = self.flights_table.get_item(
            Key={'flight_id': flight_id}
        )
        return response.get('Item')
    
    def get_delayed_flights(self):
        """Get all delayed flights"""
        response = self.flights_table.scan(
            FilterExpression=Key('status').eq('Delayed')
        )
        return response.get('Items', [])
    
    def get_passengers_for_flight(self, flight_id):
        """Get all passengers for a specific flight"""
        response = self.passengers_table.query(
            IndexName='FlightIndex',
            KeyConditionExpression=Key('flight_id').eq(flight_id)
        )
        return response.get('Items', [])
    
    def get_passenger(self, passenger_id):
        """Get passenger details by passenger ID"""
        response = self.passengers_table.get_item(
            Key={'passenger_id': passenger_id}
        )
        return response.get('Item')
    
    def update_passenger_rebooking(self, passenger_id, new_flight_id, new_seat=None):
        """Update passenger's flight after rebooking"""
        # Get current flight info to keep history
        passenger = self.get_passenger(passenger_id)
        if not passenger:
            return False
        
        old_flight_id = passenger.get('flight_id')
        
        # Update passenger record
        update_expression = "SET flight_id = :new_flight_id"
        expression_values = {
            ':new_flight_id': new_flight_id
        }
        
        if new_seat:
            update_expression += ", seat = :new_seat"
            expression_values[':new_seat'] = new_seat
        
        # Add rebooking history
        if 'rebooking_history' not in passenger:
            update_expression += ", rebooking_history = :history"
            expression_values[':history'] = [{
                'timestamp': datetime.now().isoformat(),
                'old_flight_id': old_flight_id,
                'new_flight_id': new_flight_id
            }]
        else:
            update_expression += ", rebooking_history = list_append(rebooking_history, :history)"
            expression_values[':history'] = [{
                'timestamp': datetime.now().isoformat(),
                'old_flight_id': old_flight_id,
                'new_flight_id': new_flight_id
            }]
        
        self.passengers_table.update_item(
            Key={'passenger_id': passenger_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        
        return True
    
    def get_rebooking_options(self, flight_id):
        """Get rebooking options for a delayed flight"""
        flight = self.get_flight(flight_id)
        if not flight:
            return []
        
        return flight.get('rebooking_options', [])
    
    def generate_handoff_context(self, passenger_id):
        """Generate handoff context for call center agents"""
        passenger = self.get_passenger(passenger_id)
        if not passenger:
            return {}
        
        flight_id = passenger.get('flight_id')
        flight = self.get_flight(flight_id)
        if not flight:
            return {}
        
        # Create handoff context with all relevant information
        handoff_context = {
            'passenger': {
                'id': passenger.get('passenger_id'),
                'name': passenger.get('name'),
                'loyalty_tier': passenger.get('loyalty_tier'),
                'seat': passenger.get('seat')
            },
            'flight': {
                'id': flight.get('flight_id'),
                'number': flight.get('flight_number'),
                'airline': flight.get('airline'),
                'origin': flight.get('origin'),
                'destination': flight.get('destination'),
                'scheduled_departure': flight.get('scheduled_departure'),
                'scheduled_arrival': flight.get('scheduled_arrival'),
                'status': flight.get('status'),
                'delay_minutes': flight.get('delay_minutes'),
                'delay_reason': flight.get('delay_reason'),
                'gate': flight.get('gate'),
                'terminal': flight.get('terminal')
            },
            'rebooking_history': passenger.get('rebooking_history', []),
            'timestamp': datetime.now().isoformat()
        }
        
        return handoff_context
