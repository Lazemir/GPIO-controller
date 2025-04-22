import serial
import time
import re


ARDUINO_PIN_COUNT = 14
MCP23017_PIN_COUNT = 16


class SerialCommunicator:
    def __init__(self, serial_interface):
        self.serial_interface = serial_interface

    def send(self, command: str) -> str:
        full_command = command.strip() + "\n"
        self.serial_interface.write(full_command.encode('utf-8'))
        time.sleep(0.1)
        # Read one line from the serial interface
        response = self.serial_interface.readline().decode('utf-8').strip()
        return response


class Pin:
    """
    A class representing a GPIO pin used by both Arduino and MCP modules.
    """

    def __init__(self, module, pin_number: int):
        self.module = module
        self.pin_number = pin_number

    def set(self, value: bool) -> None:
        state = "HIGH" if value else "LOW"
        cmd = f"{self.pin_number} {state}"
        self.module.send_command(cmd)

    def read(self) -> bool:
        cmd = f"{self.pin_number} read"
        response = self.module.send_command(cmd)
        # Assume the response contains "state: 1" for HIGH.
        return '1' in response


class GPIOModule():
    def __init__(self, communicator: SerialCommunicator, pin_count: int, module_index: int):
        self.communicator = communicator
        self.module_index = module_index  # This value prefixes each command.
        self.pins = [Pin(self, i) for i in range(pin_count)]

    def send_command(self, command: str) -> str:
        # Prefix command with the module index assigned by the controller.
        full_command = f"{self.module_index} {command.strip()}"
        return self.communicator.send(full_command)


# class ArduinoModule(GPIOModule):
#     def __init__(self, communicator: SerialCommunicator, pin_count: int, module_index: int = 0):
#         super().__init__(communicator, module_index)
#         self.pin_count = pin_count
#         self.pins = [Pin(self, i) for i in range(pin_count)]
#
#     def send_command(self, command: str) -> str:
#         # Prefix command with module index (0 for Arduino native pins).
#         full_command = f"{self.module_index} {command.strip()}"
#         return self.communicator.send(full_command)
#
#
# class MCPModule(GPIOModule):
#     def __init__(self, communicator: SerialCommunicator, address: int, pin_count: int = 16, module_index: int = 1):
#         super().__init__(communicator, module_index)
#         self.address = address  # Informational only; Arduino uses module index.
#         self.pin_count = pin_count
#         self.pins = [Pin(self, i) for i in range(pin_count)]
#
#     def send_command(self, command: str) -> str:
#         # Prefix command with the module index assigned by the controller.
#         full_command = f"{self.module_index} {command.strip()}"
#         return self.communicator.send(full_command)


class ArduinoGPIOController:
    """
    Controller class to manage GPIO on Arduino and connected MCP23017 modules.
    During initialization, it establishes the serial connection and reads the startup
    messages output by the Arduino (which now include discovery and device information).
    It then parses these messages to initialize the modules list:
      - Index 0: Arduino native pins.
      - Indices 1..n: MCP23017 modules discovered during setup.
    """

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self._serial_interface = None
        try:
            self._serial_interface = serial.Serial(port, baudrate, timeout=timeout)
        except serial.SerialException as e:
            raise Exception(f"Could not open serial port {port}: {e}")

        self.communicator = SerialCommunicator(self._serial_interface)

        # Read all output from the Arduino's setup (including discovery and device info)
        startup_lines = self._read_all_lines(timeout=2.0)
        print("Startup messages from Arduino:")
        for line in startup_lines:
            print(line)

        # Parse discovered MCP23017 module addresses from the startup messages
        addresses = []
        for line in startup_lines:
            # Look for lines like: "MCP23017 initialized at 0x20"
            m = re.search(r"MCP23017 initialized at 0x([0-9A-Fa-f]+)", line)
            if m:
                addr = int(m.group(1), 16)
                addresses.append(addr)

        # Initialize modules list: index 0 for Arduino native pins
        self.modules = [GPIOModule(self.communicator, ARDUINO_PIN_COUNT, module_index=0)]
        for _ in addresses:
            module_index = len(self.modules)
            self.modules.append(GPIOModule(self.communicator, MCP23017_PIN_COUNT, module_index=module_index))

    def _read_all_lines(self, timeout=1.0):
        """
        Helper method to read all available lines from the serial interface within a timeout.
        """
        lines = []
        start_time = time.time()
        while time.time() - start_time < timeout:
            while self._serial_interface.in_waiting:
                line = self._serial_interface.readline().decode('utf-8').strip()
                if line:
                    lines.append(line)
            time.sleep(0.1)
        return lines

    def module_count(self) -> int:
        return len(self.modules)

    def _close(self):
        if self._serial_interface is not None and self._serial_interface.is_open:
            self._serial_interface.close()

    def __del__(self):
        self._close()


# -----------------------------------------------------------------------------
# Example Usage
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Replace 'COM3' with the correct serial port for your setup.
    controller = ArduinoGPIOController("/dev/cu.wchusbserial1420")
    print("Total modules detected:", controller.module_count())

    # Example: Set Arduino native pin 13 to HIGH and read its state.
    controller.modules[0].pins[13].set(True)
    print("Arduino pin 13 state:", controller.modules[0].pins[13].read())

    # If an MCP module was discovered (module index 1), control one of its pins.
    if controller.module_count() > 1:
        controller.modules[1].pins[7].set(False)
        print("MCP pin 7 state:", controller.modules[1].pins[7].read())
