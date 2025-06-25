from typing import Unpack, overload

import numpy as np
import qcodes
import time

from qcodes import Parameter, InstrumentChannel, ChannelList, VisaInstrument
from qcodes.instrument import InstrumentModule, InstrumentBaseKWArgs, InstrumentBase

ARDUINO_PIN_COUNT = 14
MCP23017_PIN_COUNT = 16


class Pin(InstrumentChannel):
    """
    Controller class to manage GPIO on Arduino and connected MCP23017 modules.
    During initialization, it establishes the serial connection and reads the startup
    messages output by the Arduino (which now include discovery and device information).
    It then parses these messages to initialize the modules list:
      - Index 0: Arduino native pins.
      - Indices 1..n: MCP23017 modules discovered during setup.
    """
    def __init__(self, parent: 'GPIOModule', name: str, pin_number: int, **kwargs: Unpack[InstrumentBaseKWArgs]):

        super().__init__(parent, name, **kwargs)
        self.add_parameter('state', qcodes.Parameter,
                           get_cmd=f'PIN{pin_number}:STATe?',
                           set_cmd=f'PIN{pin_number}:STATe {{:d}}',
                           get_parser=int)

        self.add_parameter('mode', qcodes.Parameter,
                           get_cmd=f'PIN{pin_number}:MODE?',
                           set_cmd=f'PIN{pin_number}:MODE {{:d}}',
                           get_parser=int)


class GPIOModule(InstrumentChannel):
    def __init__(self, pin_count: int, module_index: int, parent: InstrumentBase,
                 name: str, **kwargs: Unpack[InstrumentBaseKWArgs]):
        super().__init__(parent, name, **kwargs)
        self.module_index = module_index  # This value prefixes each command.
        self.pins = [Pin(self, f'pin_{i}', i) for i in range(pin_count)]

    def ask(self, cmd: str) -> str:
        return super().ask(f'MODule{self.module_index}:{cmd}')

    def write(self, cmd: str) -> None:
        super().write(f'MODule{self.module_index}:{cmd}')


class GPIOController(VisaInstrument):
    def __init__(self, name: str, address: str, **kwargs: Unpack[InstrumentBaseKWArgs]):
        super().__init__(name, address, **kwargs)
        modules = ChannelList(
            self, "gpio_modules", GPIOModule
        )

        self._modules_count = self.add_parameter('_modules_count', Parameter,
                                                 get_cmd='INFO:MODules:COUNt?',
                                                 get_parser=int)

        modules.append(GPIOModule(ARDUINO_PIN_COUNT, 0, self, 'arduino_module'))

        time.sleep(2)

        for module_id in range(1, self._modules_count()):
            modules.append(GPIOModule(MCP23017_PIN_COUNT, module_id, self, f'mcp23017_module_{module_id}'))

        self.add_submodule('modules', modules.to_channel_tuple())

        for module in self.modules:
            for pin in module.pins:
                pin.mode(1)
                pin.state(0)


def _int_to_bool_tuple(value: int, n_bits: int):
    binary_array = np.array(list(np.binary_repr(value, width=n_bits)), dtype=int)
    bool_tuple = tuple(binary_array.astype(bool))
    return bool_tuple


def _bool_tuple_to_int(bool_tuple):
    binary_string = ''.join(['1' if x else '0' for x in bool_tuple])
    return int(binary_string, 2)


class Bus(tuple[Pin]):
    @overload
    def state(self) -> int:
        pass

    @overload
    def state(self, val: int) -> None:
        pass

    def state(self, val=None):
        if val is None:
            return _bool_tuple_to_int(pin.state() for pin in self)

        bool_tuple = _int_to_bool_tuple(val, len(self))
        for pin, state in zip(self, bool_tuple):
            pin.state(state)


# -----------------------------------------------------------------------------
# Example Usage
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Replace 'COM3' with the correct serial port for your setup.
    controller = GPIOController('test', "COM5")

    # print("Total modules detected:", controller.module_count())

    # Example: Set Arduino native pin 13 to HIGH and read its state.
    controller.modules[0].pins[13].mode(1)
    controller.modules[0].pins[13].state(1)
    try:
        print("Arduino pin 13 state:", controller.modules[0].pins[13].state())
    except Exception as e:
        print(e)

    # # If an MCP module was discovered (module index 1), control one of its pins.
    # if controller.module_count() > 1:
    controller.modules[1].pins[0].mode(1)
    controller.modules[1].pins[0].state(1)
    print("MCP pin 7 state:", controller.modules[1].pins[0].state())
