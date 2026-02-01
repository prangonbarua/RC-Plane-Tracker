#!/usr/bin/env python3
"""
RC Plane Flight Tracker Server
Receives data from LoRa ground station, tracks flights, serves web dashboard
"""

import serial
import serial.tools.list_ports
import threading
import time
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, send_file
from flask_socketio import SocketIO
from flight_detector import FlightDetector
from data_logger import DataLogger
from exporter import FlightExporter

app = Flask(__name__)
app.config['SECRET_KEY'] = 'rc-plane-tracker-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
current_data = {
    'latitude': 0.0,
    'longitude': 0.0,
    'altitude': 0.0,
    'speed': 0.0,
    'satellites': 0,
    'rssi': 0,
    'snr': 0.0,
    'connected': False,
    'in_flight': False,
    'flight_id': None,
    'peak_speed': 0.0,
    'peak_altitude': 0.0,
    'flight_path': []
}

flight_detector = FlightDetector()
data_logger = DataLogger()
serial_port = None


def find_serial_port():
    """Find the LoRa receiver serial port"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Look for ESP32 or USB serial devices
        if 'USB' in port.description or 'CP210' in port.description or 'CH340' in port.description:
            return port.device
    return None


def parse_packet(line):
    """Parse incoming packet from ground receiver"""
    try:
        # Format: $FLT,lat,lon,alt,speed,sats,packet#*checksum|rssi,snr
        if not line.startswith('$FLT,'):
            return None

        # Split packet and signal info
        parts = line.split('|')
        packet = parts[0]

        # Get RSSI/SNR if available
        rssi, snr = 0, 0.0
        if len(parts) > 1:
            signal_parts = parts[1].split(',')
            rssi = int(signal_parts[0])
            snr = float(signal_parts[1]) if len(signal_parts) > 1 else 0.0

        # Remove checksum
        packet = packet.split('*')[0]

        # Parse data
        data_parts = packet[5:].split(',')  # Skip "$FLT,"
        if len(data_parts) >= 5:
            return {
                'latitude': float(data_parts[0]),
                'longitude': float(data_parts[1]),
                'altitude': float(data_parts[2]),
                'speed': float(data_parts[3]),
                'satellites': int(data_parts[4]),
                'rssi': rssi,
                'snr': snr,
                'timestamp': datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Parse error: {e}")

    return None


def serial_reader():
    """Background thread to read serial data"""
    global serial_port, current_data

    while True:
        try:
            # Find and connect to serial port
            if serial_port is None or not serial_port.is_open:
                port_name = find_serial_port()
                if port_name:
                    serial_port = serial.Serial(port_name, 115200, timeout=1)
                    print(f"Connected to {port_name}")
                    current_data['connected'] = True
                else:
                    time.sleep(2)
                    continue

            # Read line
            line = serial_port.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue

            # Handle signal lost
            if line == '$SIGNAL_LOST':
                current_data['connected'] = False
                socketio.emit('signal_lost', {})
                continue

            # Parse packet
            data = parse_packet(line)
            if data:
                current_data['connected'] = True
                current_data['latitude'] = data['latitude']
                current_data['longitude'] = data['longitude']
                current_data['altitude'] = data['altitude']
                current_data['speed'] = data['speed']
                current_data['satellites'] = data['satellites']
                current_data['rssi'] = data['rssi']
                current_data['snr'] = data['snr']

                # Update peaks
                if data['speed'] > current_data['peak_speed']:
                    current_data['peak_speed'] = data['speed']
                if data['altitude'] > current_data['peak_altitude']:
                    current_data['peak_altitude'] = data['altitude']

                # Check flight status
                flight_status = flight_detector.update(data['speed'])

                if flight_status == 'started':
                    # New flight started
                    current_data['in_flight'] = True
                    current_data['flight_id'] = data_logger.start_flight()
                    current_data['flight_path'] = []
                    current_data['peak_speed'] = data['speed']
                    current_data['peak_altitude'] = data['altitude']
                    print(f"Flight started: {current_data['flight_id']}")
                    socketio.emit('flight_started', {'flight_id': current_data['flight_id']})

                elif flight_status == 'ended':
                    # Flight ended
                    current_data['in_flight'] = False
                    data_logger.end_flight()
                    print(f"Flight ended: {current_data['flight_id']}")
                    socketio.emit('flight_ended', {'flight_id': current_data['flight_id']})
                    current_data['flight_id'] = None

                # Log data if in flight
                if current_data['in_flight']:
                    data_logger.log_point(data)
                    current_data['flight_path'].append({
                        'lat': data['latitude'],
                        'lng': data['longitude']
                    })

                # Emit to web clients
                socketio.emit('flight_data', {
                    'latitude': data['latitude'],
                    'longitude': data['longitude'],
                    'altitude': data['altitude'],
                    'speed': data['speed'],
                    'satellites': data['satellites'],
                    'rssi': data['rssi'],
                    'snr': data['snr'],
                    'in_flight': current_data['in_flight'],
                    'peak_speed': current_data['peak_speed'],
                    'peak_altitude': current_data['peak_altitude']
                })

        except serial.SerialException as e:
            print(f"Serial error: {e}")
            serial_port = None
            current_data['connected'] = False
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)


@app.route('/')
def index():
    return render_template('dashboard.html')


@app.route('/api/status')
def api_status():
    return jsonify(current_data)


@app.route('/api/flights')
def api_flights():
    flights = data_logger.get_all_flights()
    return jsonify(flights)


@app.route('/api/flight/<flight_id>')
def api_flight(flight_id):
    flight = data_logger.get_flight(flight_id)
    return jsonify(flight)


@app.route('/api/export/<flight_id>')
def api_export(flight_id):
    exporter = FlightExporter()
    filepath = exporter.export_flight(flight_id, data_logger)
    if filepath:
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'Flight not found'}), 404


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    socketio.emit('flight_data', {
        'latitude': current_data['latitude'],
        'longitude': current_data['longitude'],
        'altitude': current_data['altitude'],
        'speed': current_data['speed'],
        'satellites': current_data['satellites'],
        'rssi': current_data['rssi'],
        'snr': current_data['snr'],
        'in_flight': current_data['in_flight'],
        'peak_speed': current_data['peak_speed'],
        'peak_altitude': current_data['peak_altitude'],
        'flight_path': current_data['flight_path']
    })


if __name__ == '__main__':
    # Start serial reader thread
    serial_thread = threading.Thread(target=serial_reader, daemon=True)
    serial_thread.start()

    print("=" * 50)
    print("RC Plane Flight Tracker")
    print("Open http://localhost:5000 in your browser")
    print("=" * 50)

    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
