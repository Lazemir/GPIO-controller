from __future__ import annotations

import yaml
from qcodes.instrument import InstrumentBaseKWArgs
from qcodes.parameters import Parameter
import qcodes.validators as vals

from gpio_controller import GPIOController, Bus
from .abstract_switch import AbstractSwitch
from .sp8t_switch import SP8T_Switch


class MultiSwitch(AbstractSwitch):
    """Switch composed of multiple SP8T switches with LED indication."""

    def __init__(
        self,
        name: str,
        controller: GPIOController,
        config_path: str,
        **kwargs: InstrumentBaseKWArgs,
    ) -> None:
        super().__init__(name, **kwargs)

        cfg = self._load_config(config_path)

        pins = cfg["switches"]
        self._main = SP8T_Switch(
            f"{name}_main",
            Bus(tuple(controller.modules[0].pins[p] for p in pins["main"])),
        )
        self._sw1 = SP8T_Switch(
            f"{name}_sw1",
            Bus(tuple(controller.modules[0].pins[p] for p in pins["sw1"])),
        )
        self._sw2 = SP8T_Switch(
            f"{name}_sw2",
            Bus(tuple(controller.modules[0].pins[p] for p in pins["sw2"])),
        )

        self._leds = tuple(
            controller.modules[item["module"]].pins[item["pin"]]
            for item in cfg["leds"]
        )
        self._active_led = None

        self._state_map: list[dict[str, int]] = cfg["states"]

        self._current_state = 0
        self.add_parameter("state", Parameter, get_cmd=self._get_state, set_cmd=self._set_state, vals=vals.Ints(0, len(self._state_map) - 1), unit="")


        self._update_leds(0)

    # ------------------------------------------------------------------
    def _get_state(self) -> int:
        return self._current_state

    def _set_state(self, val: int) -> None:
        cfg = self._state_map[val]
        self._main.state(cfg["main"])
        if "sw1" in cfg:
            self._sw1.state(cfg["sw1"])
        if "sw2" in cfg:
            self._sw2.state(cfg["sw2"])
        self._update_leds(val)
        self._current_state = val

    def _update_leds(self, active: int) -> None:
        if self._active_led is not None and self._active_led != active:
            self._leds[self._active_led].state(0)
        self._leds[active].state(1)
        self._active_led = active

    def _load_config(self, path: str) -> dict:
        """Load YAML configuration."""
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)


