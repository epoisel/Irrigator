#!/usr/bin/env python3
"""
Test script for the irrigation control system API.
This script tests the basic functionality of the API endpoints.
"""

import unittest
import json
import os
import tempfile
import time
from app import app, init_db

class IrrigationAPITestCase(unittest.TestCase):
    """Test case for the irrigation API."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary database
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        self.client = app.test_client()
        
        # Initialize the database
        with app.app_context():
            init_db()
    
    def tearDown(self):
        """Clean up test environment."""
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])
    
    def test_sensor_data_endpoint(self):
        """Test the sensor data endpoint."""
        # Test with valid data
        response = self.client.post(
            '/api/sensor-data',
            data=json.dumps({'device_id': 'test_device', 'moisture': 45.5}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        
        # Test with invalid data
        response = self.client.post(
            '/api/sensor-data',
            data=json.dumps({'device_id': 'test_device'}),  # Missing moisture
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_commands_endpoint(self):
        """Test the commands endpoint."""
        response = self.client.get('/api/commands/test_device')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('command', data)
    
    def test_valve_control_endpoint(self):
        """Test the valve control endpoint."""
        # Test turning valve ON
        response = self.client.post(
            '/api/valve/control',
            data=json.dumps({'device_id': 'test_device', 'state': 1}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Test turning valve OFF
        response = self.client.post(
            '/api/valve/control',
            data=json.dumps({'device_id': 'test_device', 'state': 0}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Test with invalid data
        response = self.client.post(
            '/api/valve/control',
            data=json.dumps({'device_id': 'test_device'}),  # Missing state
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_analytics_endpoints(self):
        """Test the analytics endpoints."""
        # Add some test data
        self.client.post(
            '/api/sensor-data',
            data=json.dumps({'device_id': 'test_device', 'moisture': 45.5}),
            content_type='application/json'
        )
        
        self.client.post(
            '/api/valve/control',
            data=json.dumps({'device_id': 'test_device', 'state': 1}),
            content_type='application/json'
        )
        
        # Test moisture analytics
        response = self.client.get('/api/analytics/moisture?device_id=test_device&days=1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        
        # Test valve history
        response = self.client.get('/api/analytics/valve?device_id=test_device&days=1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
    
    def test_automation_endpoints(self):
        """Test the automation endpoints."""
        # Test getting default automation rules
        response = self.client.get('/api/automation?device_id=test_device')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('device_id', data)
        self.assertIn('enabled', data)
        self.assertIn('low_threshold', data)
        self.assertIn('high_threshold', data)
        
        # Test setting automation rules
        response = self.client.post(
            '/api/automation',
            data=json.dumps({
                'device_id': 'test_device',
                'enabled': 1,
                'low_threshold': 20.0,
                'high_threshold': 80.0
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify the rules were set
        response = self.client.get('/api/automation?device_id=test_device')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['low_threshold'], 20.0)
        self.assertEqual(data['high_threshold'], 80.0)

if __name__ == '__main__':
    unittest.main() 