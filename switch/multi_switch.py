from __future__ import annotations

import yaml
from qcodes.parameters import Parameter
import qcodes.validators as vals

from gpio_controller import Pin
from .abstract_switch import AbstractSwitch
from .sp8t_switch import SP8T_Switch


class MultiSwitch(AbstractSwitch):
    """Switch composed of multiple SP8T switches with LED indication."""

    def __init__(
        self,
        name: str,
        main_switch: SP8T_Switch,
        switch1: SP8T_Switch,
        switch2: SP8T_Switch,
        leds: tuple[Pin, ...],
        config_path: str,
        **kwargs: InstrumentBaseKWArgs,
    ) -> None:
        super().__init__(name, **kwargs)
        self._main = main_switch
        self._sw1 = switch1
        self._sw2 = switch2
        self._leds = leds
        self._active_led = None

        with open(config_path, "r", encoding="utf-8") as f:
            self._state_map: list[dict[str, int]] = yaml.safe_load(f)["states"]

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


