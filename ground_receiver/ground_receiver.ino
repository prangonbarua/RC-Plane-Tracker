/*
 * RC Plane Ground Receiver
 * ESP32 + SX1278 LoRa
 *
 * Receives GPS data via LoRa and forwards to computer via USB Serial
 *
 * WIRING:
 * ESP32       SX1278 LoRa
 * ─────       ───────────
 * 3.3V   -->  VCC
 * GND    -->  GND
 * GPIO18 -->  SCK
 * GPIO19 -->  MISO
 * GPIO23 -->  MOSI
 * GPIO5  -->  NSS
 * GPIO2  -->  RST
 * GPIO4  -->  DIO0
 */

#include <SPI.h>
#include <LoRa.h>

// LoRa pins for ESP32
#define LORA_SCK  18
#define LORA_MISO 19
#define LORA_MOSI 23
#define LORA_SS   5
#define LORA_RST  2
#define LORA_DIO0 4

// LoRa frequency (must match transmitter)
#define LORA_FREQ 433E6

// Stats
int packetsReceived = 0;
unsigned long lastPacketTime = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("=== RC Plane Ground Receiver ===");

  // Initialize LoRa
  SPI.begin(LORA_SCK, LORA_MISO, LORA_MOSI, LORA_SS);
  LoRa.setPins(LORA_SS, LORA_RST, LORA_DIO0);

  if (!LoRa.begin(LORA_FREQ)) {
    Serial.println("LoRa init FAILED!");
    while (1);
  }

  // Configure LoRa (must match transmitter settings)
  LoRa.setSpreadingFactor(10);
  LoRa.setSignalBandwidth(125E3);
  LoRa.setCodingRate4(5);

  Serial.println("LoRa initialized at 433MHz");
  Serial.println("Waiting for packets...");
  Serial.println("---");
}

void loop() {
  // Check for incoming packets
  int packetSize = LoRa.parsePacket();

  if (packetSize) {
    // Read packet
    String packet = "";
    while (LoRa.available()) {
      packet += (char)LoRa.read();
    }

    // Get signal strength
    int rssi = LoRa.packetRssi();
    float snr = LoRa.packetSnr();

    packetsReceived++;
    lastPacketTime = millis();

    // Forward to computer with RSSI info
    // Format: $FLT,lat,lon,alt,speed,sats,packet#*checksum|rssi,snr
    Serial.print(packet);
    Serial.print("|");
    Serial.print(rssi);
    Serial.print(",");
    Serial.println(snr);
  }

  // Check for signal loss (no packet in 5 seconds)
  if (lastPacketTime > 0 && millis() - lastPacketTime > 5000) {
    Serial.println("$SIGNAL_LOST");
    lastPacketTime = 0;
  }
}
