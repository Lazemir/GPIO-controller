from qcodes.parameters import Parameter
import qcodes.validators as vals

from qcodes.instrument import InstrumentBaseKWArgs

from gpio_controller import Bus
from .abstract_switch import AbstractSwitch


class SP8T_Switch(AbstractSwitch):
    """Concrete implementation of :class:`AbstractSwitch` for SP8T switches."""

    def __init__(self, name: str, bus: Bus, **kwargs: InstrumentBaseKWArgs):
        super().__init__(name, **kwargs)
        assert len(bus) == 3
        self._bus = bus
        self.add_parameter("state", Parameter, get_cmd=self._bus.state, set_cmd=self._bus.state, vals=vals.Ints(0,7), unit="")

