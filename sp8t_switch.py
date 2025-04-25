from dataclasses import dataclass
from typing import Unpack

import numpy as np

from qcodes.instrument import Instrument, InstrumentBaseKWArgs
from qcodes.parameters import Parameter
import qcodes.validators as vals

from gpio_controller import Bus


class SP8T_Switch(Instrument):
    def __init__(self, name: str, bus: Bus, **kwargs):
        super().__init__(name, **kwargs)
        assert len(bus) == 3
        self._bus = bus

        self.state = self.add_parameter('state',
                                        Parameter,
                                        get_cmd=self._bus.state,
                                        set_cmd=self._bus.state,
                                        vals=vals.Ints(0, 7))


class Switch_23_to_1(Instrument):
    def __init__(self, name: str, **kwargs: Unpack[InstrumentBaseKWArgs]):
        super().__init__(name, **kwargs)

