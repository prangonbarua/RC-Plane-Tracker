/*
 * RC Plane Flight Transmitter
 * ESP32-C3 + BN-220 GPS + SX1278 LoRa
 *
 * Transmits GPS data via LoRa to ground station
 *
 * WIRING for ESP32-C3:
 * ESP32-C3    BN-220 GPS    SX1278 LoRa
 * ────────    ──────────    ───────────
 * 3.3V   -->  VCC           VCC
 * GND    -->  GND           GND
 * GPIO20 -->  TX (GPS out)
 * GPIO21 -->  RX (GPS in)
 * GPIO4  -->                SCK
 * GPIO5  -->                MISO
 * GPIO6  -->                MOSI
 * GPIO7  -->                NSS
 * GPIO8  -->                RST
 * GPIO10 -->                DIO0
 *
 * Note: ESP32-C3 uses different SPI pins than regular ESP32
 * BN-220 GPS default baud rate: 9600
 */

#include <SPI.h>
#include <LoRa.h>
#include <TinyGPS++.h>
#include <HardwareSerial.h>

// LoRa pins for ESP32-C3
#define LORA_SCK  4
#define LORA_MISO 5
#define LORA_MOSI 6
#define LORA_SS   7
#define LORA_RST  8
#define LORA_DIO0 10

// GPS Serial pins for ESP32-C3
#define GPS_RX 20  // Connect to GPS TX
#define GPS_TX 21  // Connect to GPS RX

// LoRa frequency (433MHz for most regions, check your local regulations)
#define LORA_FREQ 433E6

// Objects
TinyGPSPlus gps;
HardwareSerial gpsSerial(1);

// Data
float latitude = 0.0;
float longitude = 0.0;
float altitude = 0.0;
float speed_mph = 0.0;
int satellites = 0;
unsigned long lastTransmit = 0;
int packetNum = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("=== RC Plane Transmitter (ESP32-C3) ===");

  // Initialize GPS
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX, GPS_TX);
  Serial.println("GPS initialized");

  // Initialize LoRa
  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_SS);
  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);

  if (!LoRa.begin(LORA_FREQ)) {
    Serial.println("LoRa init FAILED!");
    while (1);
  }

  // Configure LoRa for better range
  LoRa.setSpreadingFactor(10);      // 7-12, higher = longer range, slower
  LoRa.setSignalBandwidth(125E3);   // 125kHz
  LoRa.setCodingRate4(5);           // 5-8
  LoRa.setTxPower(20);              // Max power for range

  Serial.println("LoRa initialized at 433MHz");
  Serial.println("Ready to transmit!");
}

void loop() {
  // Read GPS data
  while (gpsSerial.available() > 0) {
    gps.encode(gpsSerial.read());
  }

  // Update GPS values
  if (gps.location.isValid()) {
    latitude = gps.location.lat();
    longitude = gps.location.lng();
  }

  if (gps.altitude.isValid()) {
    altitude = gps.altitude.meters();
  }

  if (gps.speed.isValid()) {
    speed_mph = gps.speed.mph();
  }

  satellites = gps.satellites.value();

  // Transmit every 500ms
  if (millis() - lastTransmit >= 500) {
    lastTransmit = millis();
    transmitData();
  }
}

void transmitData() {
  // Create packet: $FLT,lat,lon,alt,speed,sats,packet#
  String packet = "$FLT,";
  packet += String(latitude, 6) + ",";
  packet += String(longitude, 6) + ",";
  packet += String(altitude, 1) + ",";
  packet += String(speed_mph, 1) + ",";
  packet += String(satellites) + ",";
  packet += String(packetNum);

  // Add checksum
  byte checksum = 0;
  for (int i = 1; i < packet.length(); i++) {
    checksum ^= packet[i];
  }
  packet += "*";
  packet += String(checksum, HEX);

  // Send via LoRa
  LoRa.beginPacket();
  LoRa.print(packet);
  LoRa.endPacket();

  // Debug output
  Serial.print("TX: ");
  Serial.println(packet);

  packetNum++;
}
