#define ARDUINO_PINS_COUNT 14
#define MAX_MCP_COUNT 8
#define MCP_PINS_COUNT 16

#include "Arduino.h"
#include "Vrekrer_scpi_parser.h"
#include <Adafruit_MCP23X17.h>

int arduino_pin_modes[ARDUINO_PINS_COUNT];
int mcp_pin_modes[MAX_MCP_COUNT][MCP_PINS_COUNT];
int num_mcp_discovered = 0;
uint8_t discovered_mcp_addresses[MAX_MCP_COUNT];

Adafruit_MCP23X17 mcp[MAX_MCP_COUNT];

SCPI_Parser scpi_parser;

void setup() {
  scpi_parser.RegisterCommand("*IDN?", &Identify);

  scpi_parser.SetCommandTreeBase(F("INFO"));
    scpi_parser.RegisterCommand(F("MODules:COUNt?"), &QueryModulesCount);

  //Use "#" at the end of a token to accept numeric suffixes.
  scpi_parser.SetCommandTreeBase(F("MODule#:PIN#"));
    scpi_parser.RegisterCommand(F("MODE?"), &QueryPinMode);
    scpi_parser.RegisterCommand(F("MODE"), &WritePinMode);
    scpi_parser.RegisterCommand(F("STATe?"), &QueryPinState);
    scpi_parser.RegisterCommand(F("STATe"), &WritePinState);

  discovery();

  Serial.begin(9600);
}

void loop() {
  scpi_parser.ProcessInput(Serial, "\r");
}

int get_pin_number(SCPI_C commands) {
  String pin_cmd = String(commands[1]);
  pin_cmd.toUpperCase();

  int suffix = -1;
  sscanf(pin_cmd.c_str(),"%*[PIN]%u", &suffix);

  return suffix;
}

int get_module_number(SCPI_C commands) {
  String module_cmd = String(commands[0]);
  module_cmd.toUpperCase();

  int suffix = -1;
  sscanf(module_cmd.c_str(),"%*[MODULE]%u", &suffix);

  return suffix;
}

bool check_constraints(const int& module_number, const int& pin_number) {
  if (module_number < 0 || module_number > num_mcp_discovered) return false;
  if (module_number == 0) return pin_number < ARDUINO_PINS_COUNT;
  return pin_number < MCP_PINS_COUNT;
}

int get_pin_mode(const int& module_number, const int& pin_number) {
  if (!check_constraints(module_number, pin_number)) return -1;
  if (module_number == 0) {
    return arduino_pin_modes[pin_number];
  }
  int mcp_number = module_number - 1;
  return mcp_pin_modes[mcp_number][pin_number];
}

void set_pin_mode(const int& module_number, const int& pin_number, const int& pin_mode) {
  if (!check_constraints(module_number, pin_number)) return;
  if (pin_mode < 0 || pin_mode > 2) return;
  if (module_number == 0) {
    arduino_pin_modes[pin_number] = pin_mode;
    pinMode(pin_number, pin_mode);
    return;
  }
  int mcp_number = module_number - 1;
  mcp_pin_modes[mcp_number][pin_number] = pin_mode;
  mcp[mcp_number].pinMode(pin_number, pin_mode);
}

void Identify(SCPI_C commands, SCPI_P parameters, Stream& interface) {
    interface.println(F("Vrekrer,SCPI Numeric suffixes example,#00," 
                        VREKRER_SCPI_VERSION));
}

void QueryModulesCount(SCPI_C commands, SCPI_P parameters, Stream& interface) {
  interface.println(num_mcp_discovered + 1);
}

void QueryPinMode(SCPI_C commands, SCPI_P parameters, Stream& interface) {
  int module_number = get_module_number(commands);
  int pin_number = get_pin_number(commands);
  interface.println(get_pin_mode(module_number, pin_number));
}

void WritePinMode(SCPI_C commands, SCPI_P parameters, Stream& interface) {
  int module_number = get_module_number(commands);
  int pin_number = get_pin_number(commands);
  String parameter_str = String(parameters.First());
  int pin_mode = parameter_str.toInt();
  set_pin_mode(module_number, pin_number, pin_mode);
}

void QueryPinState(SCPI_C commands, SCPI_P parameters, Stream& interface) {
  int module_number = get_module_number(commands);
  int pin_number = get_pin_number(commands);
  if (!check_constraints(module_number, pin_number)) return;
  int pin_state;
  if (module_number == 0) {
    pin_state = digitalRead(pin_number);
  } else {
    int mcp_number = module_number - 1;
    pin_state = mcp[mcp_number].digitalRead(pin_number);
  }
  interface.println(pin_state);
}

void WritePinState(SCPI_C commands, SCPI_P parameters, Stream& interface) {
  int module_number = get_module_number(commands);
  int pin_number = get_pin_number(commands);
  if (!check_constraints(module_number, pin_number)) return;
  String parameter_str = String(parameters.First());
  int pin_state = parameter_str.toInt();
  if (module_number == 0) {
    digitalWrite(pin_number, pin_state);
  } else {
    int mcp_number = module_number - 1;
    mcp[mcp_number].digitalWrite(pin_number, pin_state);
  }
}

// Function to scan the I2C bus and initialize MCP23017 modules dynamically
void discovery() {
  byte error, address;
  num_mcp_discovered = 0;  // Reset discovered modules count

  // Scan addresses from 8 to 126
  for (address = 8; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();
    if (error == 0) {
      // Attempt to initialize the device as MCP23017 if space is available
      if (num_mcp_discovered < MAX_MCP_COUNT) {
        if (mcp[num_mcp_discovered].begin_I2C(address)) {
          discovered_mcp_addresses[num_mcp_discovered] = address;         
          num_mcp_discovered++;
        }
      }
    } else if (error == 4) {
      Serial.print("Unknown error at address 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
    }
  }
}
  
