from qcodes.instrument import Instrument, InstrumentBaseKWArgs
from qcodes.parameters import Parameter


class AbstractSwitch(Instrument):
    """Base class for switch instruments with an abstract ``state`` parameter."""

    def __init__(self, name: str, **kwargs: InstrumentBaseKWArgs):
        super().__init__(name, **kwargs)
        # ``state`` is left abstract to be overridden by concrete subclasses
        self.add_parameter("state", Parameter, abstract=True)
