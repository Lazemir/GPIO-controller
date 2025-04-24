#include <Wire.h>
#include <Adafruit_MCP23X17.h>

#define MAX_MCP 8  // Maximum number of supported MCP23017 modules
#define ARDUINO_PORTS 14 // The amount of Arduino ports
#define MCP_PORTS 16 // The amount of MCP23017 ports

// Array of MCP23017 objects
Adafruit_MCP23X17 mcp[MAX_MCP];
// Array to store discovered MCP23017 addresses
uint8_t discovered_mcp_addresses[MAX_MCP];
// Actual number of discovered modules
uint8_t num_mcp_discovered = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial) { delay(10); }
  Serial.println("GPIO Controller Starting...");
  Wire.begin();

  // Automatically run discovery and device information functions in setup
  discovery();
  deviceInfo();
}

void loop() {
  // Optionally, process additional commands received via serial after setup.
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input.length() > 0) {
      processCommand(input);
    }
  }
}

void reset_arduino_ports() {
  for (int pin = 0; pin < ARDUINO_PORTS; ++pin) {
    pinMode(pin, OUTPUT);
    digitalWrite(pin, LOW);
  }
}

void reset_mcp_ports(const Adafruit_MCP23X17& module) {
  for (int pin = 0; pin < ARDUINO_PORTS; ++pin) {
    module.pinMode(pin, OUTPUT);
    module.digitalWrite(pin, LOW);
  }
}

void reset() {
  reset_arduino_ports();
  for (const Adafruit_MCP23X17& module: mcp) {
    reset_mcp_ports(module);
  }
}

// Function to scan the I2C bus and initialize MCP23017 modules dynamically
void discovery() {
  Serial.println("Scanning I2C bus for MCP23017 devices...");
  byte error, address;
  int nDevices = 0;
  num_mcp_discovered = 0;  // Reset discovered modules count

  // Scan addresses from 8 to 126
  for (address = 8; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    if (error == 0) {
      Serial.print("I2C device found at address 0x");
      if (address < 16) Serial.print("0");
      Serial.print(address, HEX);
      Serial.println("!");

      // Attempt to initialize the device as MCP23017 if space is available
      if (num_mcp_discovered < MAX_MCP) {
        if (mcp[num_mcp_discovered].begin_I2C(address)) {
          discovered_mcp_addresses[num_mcp_discovered] = address;
          Serial.print("MCP23017 initialized at 0x");
          if (address < 16) Serial.print("0");
          Serial.print(address, HEX);
          Serial.println();
          // Set all 16 pins to OUTPUT mode and initialize them to LOW
          for (uint8_t pin = 0; pin < 16; pin++) {
            mcp[num_mcp_discovered].pinMode(pin, OUTPUT);
            mcp[num_mcp_discovered].digitalWrite(pin, LOW);
          }
          num_mcp_discovered++;
        } else {
          Serial.print("Device at 0x");
          Serial.print(address, HEX);
          Serial.println(" is not MCP23017");
        }
      }
      nDevices++;
    } else if (error == 4) {
      Serial.print("Unknown error at address 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
    }
  }
  if (nDevices == 0)
    Serial.println("No I2C devices found");
  else
    Serial.println("I2C scan completed");
}

// Function to output device information
void deviceInfo() {
  Serial.println("Device Info:");
  Serial.println("Firmware: GPIO Controller v1.0");
  Serial.print("Number of MCP23017 modules discovered: ");
  Serial.println(num_mcp_discovered);
}

// Function to process additional commands (if needed)
// Expected command format: <moduleIndex> <pin> <action>
// moduleIndex 0: Arduino native pins
// moduleIndex >= 1: MCP23017 modules (index = moduleIndex - 1)
void processCommand(String command) {
  const int maxTokens = 3;
  String tokens[maxTokens];
  int tokenCount = 0;
  int start = 0;
  command += " "; // Append space to capture the last token.
  for (int i = 0; i < command.length(); i++) {
    if (command.charAt(i) == ' ') {
      if (i > start) {
        tokens[tokenCount++] = command.substring(start, i);
        if (tokenCount >= maxTokens) break;
      }
      start = i + 1;
    }
  }
  if (tokenCount != 3) {
    Serial.println("Invalid command. Format: <moduleIndex> <pin> <action>");
    return;
  }

  int moduleIndex = tokens[0].toInt();
  int pin = tokens[1].toInt();
  String action = tokens[2];

  if (moduleIndex == 0) {
    // Process Arduino native pin
    if (action.equalsIgnoreCase("read")) {
      int state = digitalRead(pin);
      Serial.print("Arduino pin ");
      Serial.print(pin);
      Serial.print(" state: ");
      Serial.println(state);
    } else {
      int value = (action.equalsIgnoreCase("HIGH") || tokens[2].toInt() == 1) ? HIGH : LOW;
      digitalWrite(pin, value);
      Serial.print("Arduino pin ");
      Serial.print(pin);
      Serial.print(" set to ");
      Serial.println(value == HIGH ? "HIGH" : "LOW");
    }
  } else {
    // Process MCP23017 module
    int mcpIndex = moduleIndex - 1;
    if (mcpIndex < 0 || mcpIndex >= num_mcp_discovered) {
      Serial.println("Invalid MCP module index");
      return;
    }
    uint8_t address = discovered_mcp_addresses[mcpIndex];
    if (action.equalsIgnoreCase("read")) {
      uint8_t state = mcp[mcpIndex].digitalRead(pin);
      Serial.print("MCP 0x");
      Serial.print(address, HEX);
      Serial.print(" pin ");
      Serial.print(pin);
      Serial.print(" state: ");
      Serial.println(state);
    } else {
      int value = (action.equalsIgnoreCase("HIGH") || tokens[2].toInt() == 1) ? HIGH : LOW;
      mcp[mcpIndex].digitalWrite(pin, value);
      Serial.print("MCP 0x");
      Serial.print(address, HEX);
      Serial.print(" pin ");
      Serial.print(pin);
      Serial.print(" set to ");
      Serial.println(value == HIGH ? "HIGH" : "LOW");
    }
  }
}
