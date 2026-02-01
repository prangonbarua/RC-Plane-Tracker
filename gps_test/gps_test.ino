/*
 * GPS Test for ESP32-C3
 * Tests BN-220 GPS module without LoRa
 *
 * WIRING:
 * BN-220 GPS    ESP32-C3
 * ──────────    ────────
 * VCC (red)  -> 3.3V
 * GND (black)-> GND
 * TX (green) -> GPIO20
 * RX (white) -> GPIO21 (optional)
 */

#include <TinyGPS++.h>
#include <HardwareSerial.h>

// GPS Serial pins for ESP32-C3
#define GPS_RX 20  // Connect to GPS TX (green wire)
#define GPS_TX 21  // Connect to GPS RX (white wire) - optional

TinyGPSPlus gps;
HardwareSerial gpsSerial(1);

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("=================================");
  Serial.println("   GPS Test for ESP32-C3");
  Serial.println("=================================");
  Serial.println();

  // Initialize GPS
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX, GPS_TX);
  Serial.println("GPS initialized at 9600 baud");
  Serial.println("Waiting for GPS signal...");
  Serial.println("(Take GPS outside for best results)");
  Serial.println();
}

void loop() {
  // Read GPS data
  while (gpsSerial.available() > 0) {
    char c = gpsSerial.read();
    gps.encode(c);

    // Also print raw NMEA for debugging
    Serial.print(c);
  }

  // Print parsed data every 2 seconds
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint >= 2000) {
    lastPrint = millis();

    Serial.println();
    Serial.println("-------- GPS Status --------");

    Serial.print("Satellites: ");
    Serial.println(gps.satellites.value());

    if (gps.location.isValid()) {
      Serial.print("Latitude:  ");
      Serial.println(gps.location.lat(), 6);
      Serial.print("Longitude: ");
      Serial.println(gps.location.lng(), 6);
    } else {
      Serial.println("Location: NOT VALID (waiting for fix)");
    }

    if (gps.altitude.isValid()) {
      Serial.print("Altitude:  ");
      Serial.print(gps.altitude.meters());
      Serial.println(" m");
    }

    if (gps.speed.isValid()) {
      Serial.print("Speed:     ");
      Serial.print(gps.speed.mph());
      Serial.println(" mph");
    }

    Serial.println("----------------------------");
    Serial.println();
  }
}
