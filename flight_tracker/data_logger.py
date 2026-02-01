"""
Data Logger
Stores flight data in SQLite database
"""

import sqlite3
import os
from datetime import datetime


class DataLogger:
    def __init__(self, db_path='flights.db'):
        self.db_path = db_path
        self.current_flight_id = None
        self._init_db()

    def _init_db(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Flights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flights (
                id TEXT PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                duration_seconds INTEGER,
                peak_speed REAL,
                peak_altitude REAL,
                total_distance REAL,
                start_lat REAL,
                start_lon REAL,
                end_lat REAL,
                end_lon REAL
            )
        ''')

        # Flight data points
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flight_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flight_id TEXT,
                timestamp TEXT,
                latitude REAL,
                longitude REAL,
                altitude REAL,
                speed REAL,
                satellites INTEGER,
                rssi INTEGER,
                snr REAL,
                FOREIGN KEY (flight_id) REFERENCES flights(id)
            )
        ''')

        conn.commit()
        conn.close()

    def start_flight(self):
        """Start a new flight and return its ID"""
        self.current_flight_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        start_time = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO flights (id, start_time, peak_speed, peak_altitude, total_distance)
            VALUES (?, ?, 0, 0, 0)
        ''', (self.current_flight_id, start_time))
        conn.commit()
        conn.close()

        return self.current_flight_id

    def log_point(self, data):
        """Log a single data point"""
        if not self.current_flight_id:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert data point
        cursor.execute('''
            INSERT INTO flight_data
            (flight_id, timestamp, latitude, longitude, altitude, speed, satellites, rssi, snr)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.current_flight_id,
            data.get('timestamp', datetime.now().isoformat()),
            data['latitude'],
            data['longitude'],
            data['altitude'],
            data['speed'],
            data['satellites'],
            data.get('rssi', 0),
            data.get('snr', 0.0)
        ))

        # Update flight peaks
        cursor.execute('''
            UPDATE flights
            SET peak_speed = MAX(peak_speed, ?),
                peak_altitude = MAX(peak_altitude, ?)
            WHERE id = ?
        ''', (data['speed'], data['altitude'], self.current_flight_id))

        # Update start location if this is first point
        cursor.execute('''
            UPDATE flights
            SET start_lat = ?, start_lon = ?
            WHERE id = ? AND start_lat IS NULL
        ''', (data['latitude'], data['longitude'], self.current_flight_id))

        conn.commit()
        conn.close()

    def end_flight(self):
        """End the current flight"""
        if not self.current_flight_id:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        end_time = datetime.now().isoformat()

        # Get flight start time to calculate duration
        cursor.execute('SELECT start_time FROM flights WHERE id = ?', (self.current_flight_id,))
        row = cursor.fetchone()
        if row:
            start_time = datetime.fromisoformat(row[0])
            end_dt = datetime.now()
            duration = int((end_dt - start_time).total_seconds())

            # Get last data point for end location
            cursor.execute('''
                SELECT latitude, longitude FROM flight_data
                WHERE flight_id = ?
                ORDER BY id DESC LIMIT 1
            ''', (self.current_flight_id,))
            last_point = cursor.fetchone()

            # Update flight record
            if last_point:
                cursor.execute('''
                    UPDATE flights
                    SET end_time = ?, duration_seconds = ?, end_lat = ?, end_lon = ?
                    WHERE id = ?
                ''', (end_time, duration, last_point[0], last_point[1], self.current_flight_id))
            else:
                cursor.execute('''
                    UPDATE flights SET end_time = ?, duration_seconds = ? WHERE id = ?
                ''', (end_time, duration, self.current_flight_id))

        conn.commit()
        conn.close()

        self.current_flight_id = None

    def get_all_flights(self):
        """Get list of all flights"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM flights ORDER BY start_time DESC
        ''')

        flights = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return flights

    def get_flight(self, flight_id):
        """Get a specific flight with all data points"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get flight info
        cursor.execute('SELECT * FROM flights WHERE id = ?', (flight_id,))
        flight = cursor.fetchone()
        if not flight:
            conn.close()
            return None

        flight_data = dict(flight)

        # Get all data points
        cursor.execute('''
            SELECT * FROM flight_data WHERE flight_id = ? ORDER BY id
        ''', (flight_id,))
        flight_data['data_points'] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return flight_data
