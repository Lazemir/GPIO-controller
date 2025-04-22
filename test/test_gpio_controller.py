import unittest
from unittest.mock import patch

from gpio_controller import ArduinoGPIOController

# A fake serial class to simulate the serial.Serial interface.
class FakeSerial:
    def __init__(self, port, baudrate, timeout):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.written = []
        self.open = True
        # Queue of responses that will be returned by readline().
        self._responses = []

    def write(self, data):
        self.written.append(data)

    def readline(self):
        # Return the next response if available, else a default.
        if self._responses:
            return self._responses.pop(0)
        return b"OK\n"

    def close(self):
        self.open = False

    @property
    def is_open(self):
        return self.open


# Unit test class for ArduinoGPIOController.
class TestArduinoGPIOController(unittest.TestCase):

    def setUp(self):
        # Patch the serial.Serial class so that our ArduinoGPIOController uses FakeSerial.
        patcher = patch("serial.Serial", new=FakeSerial)
        self.addCleanup(patcher.stop)
        self.fake_serial_class = patcher.start()
        # Create an instance of the controller with a dummy port.
        self.controller = ArduinoGPIOController("COM_TEST", baudrate=115200, timeout=1)
        # For testing, get the fake serial instance from the controller.
        self.fake_serial = self.controller.ser

    def test_set_pin_native(self):
        # Set a native Arduino pin without providing an address.
        # We'll simulate a response from the Arduino.
        expected_response = b"Arduino pin 13 set to HIGH\n"
        self.fake_serial._responses.append(expected_response)
        response = self.controller.set_pin(13, True)

        # Check that the command was formatted correctly.
        # The expected command is "13 HIGH\n" encoded as bytes.
        self.assertIn(b"13 HIGH\n", self.fake_serial.written)
        # And that the response is as simulated.
        self.assertEqual(response, expected_response.decode("utf-8").strip())

    def test_set_pin_with_address(self):
        # Set an MCP23017 pin (with address provided).
        expected_response = b"MCP23017 (addr 32) pin 7 set to LOW\n"
        self.fake_serial._responses.append(expected_response)
        response = self.controller.set_pin(7, False, address=32)

        # The expected command is "32 7 LOW\n"
        self.assertIn(b"32 7 LOW\n", self.fake_serial.written)
        self.assertEqual(response, expected_response.decode("utf-8").strip())

    def test_read_pin_native(self):
        # Read a native Arduino pin.
        expected_response = b"Arduino pin 13 state: 1\n"
        self.fake_serial._responses.append(expected_response)
        response = self.controller.read_pin(13)

        # Expected command is "13 read\n"
        self.assertIn(b"13 read\n", self.fake_serial.written)
        self.assertEqual(response, expected_response.decode("utf-8").strip())

    def test_read_pin_with_address(self):
        # Read an MCP23017 pin.
        expected_response = b"MCP 0x20 pin 7 state: 0\n"
        self.fake_serial._responses.append(expected_response)
        response = self.controller.read_pin(7, address=32)

        # Expected command is "32 7 read\n"
        self.assertIn(b"32 7 read\n", self.fake_serial.written)
        self.assertEqual(response, expected_response.decode("utf-8").strip())

    def test_context_manager(self):
        # Test that the context manager correctly closes the serial connection.
        with ArduinoGPIOController("COM_TEST") as controller:
            fake_serial = controller.ser
            self.assertTrue(fake_serial.is_open)
        # Once out of the context, the connection should be closed.
        self.assertFalse(fake_serial.is_open)


if __name__ == "__main__":
    unittest.main()
