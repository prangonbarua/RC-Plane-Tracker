# RC Plane Flight Tracker

Real-time GPS tracking system for RC planes with automatic flight detection, web dashboard, and data logging.

## Hardware Required

### On the Plane
| Component | Notes |
|-----------|-------|
| ESP32-C3 | Main microcontroller |
| BN-220 GPS | 9600 baud default |
| SX1278 LoRa 433MHz | For long-range transmission |
| 3.7V LiPo battery | Power source |

### Ground Station
| Component | Notes |
|-----------|-------|
| ESP32 DevKit | Any ESP32 board works |
| SX1278 LoRa 433MHz | Must match plane frequency |
| USB cable | Connects to computer |

## Wiring

### Plane (ESP32-C3 + BN-220 GPS + SX1278 LoRa)

| ESP32-C3 | BN-220 GPS | SX1278 LoRa |
|----------|------------|-------------|
| 3.3V | VCC | VCC |
| GND | GND | GND |
| GPIO20 | TX | - |
| GPIO21 | RX | - |
| GPIO4 | - | SCK |
| GPIO5 | - | MISO |
| GPIO6 | - | MOSI |
| GPIO7 | - | NSS |
| GPIO8 | - | RST |
| GPIO10 | - | DIO0 |

### Ground Station (ESP32 + SX1278 LoRa)

| ESP32 | SX1278 LoRa |
|-------|-------------|
| 3.3V | VCC |
| GND | GND |
| GPIO18 | SCK |
| GPIO19 | MISO |
| GPIO23 | MOSI |
| GPIO5 | NSS |
| GPIO2 | RST |
| GPIO4 | DIO0 |

## Setup Instructions

### 1. Install Arduino Libraries
In Arduino IDE, install:
- `LoRa` by Sandeep Mistry
- `TinyGPS++` by Mikal Hart

### 2. Upload Arduino Code
- Flash `plane_transmitter/plane_transmitter.ino` to ESP32-C3 (plane)
- Flash `ground_receiver/ground_receiver.ino` to ESP32 (ground)

### 3. Install Python Dependencies
```bash
cd flight_tracker
pip install -r requirements.txt
```

### 4. Run the Server
```bash
python server.py
```

### 5. Open Dashboard
Open http://localhost:5000 in your browser

## Features
- Real-time map tracking (OpenStreetMap)
- Automatic flight detection (starts when speed > 5mph for 5s)
- Flight logging to SQLite database
- Excel export with bold peak values
- Signal strength monitoring (RSSI/SNR)
- Flight history with replay

## Shopping List
- SX1278 LoRa 433MHz (2-pack) - search Amazon
- ESP32 DevKit (for ground station)
- You have: ESP32-C3, BN-220 GPS, 3.7V battery

## Project Structure
```
RC-Plane-Tracker/
├── plane_transmitter/
│   └── plane_transmitter.ino
├── ground_receiver/
│   └── ground_receiver.ino
└── flight_tracker/
    ├── server.py
    ├── flight_detector.py
    ├── data_logger.py
    ├── exporter.py
    ├── requirements.txt
    ├── templates/
    └── static/
```
