import unittest
from pathlib import Path

from switch.multi_switch import MultiSwitch
from switch.sp8t_switch import SP8T_Switch
from switch.abstract_switch import AbstractSwitch
from gpio_controller import Bus


class DummyPin:
    def __init__(self):
        self.val = 0
    def state(self, v=None):
        if v is None:
            return self.val
        self.val = v


class DummySwitch(SP8T_Switch):
    def __init__(self, name):
        bus = Bus((DummyPin(), DummyPin(), DummyPin()))
        super().__init__(name, bus)


class TestMultiSwitch(unittest.TestCase):
    def setUp(self):
        self.main = DummySwitch("main")
        self.s1 = DummySwitch("s1")
        self.s2 = DummySwitch("s2")
        self.leds = tuple(DummyPin() for _ in range(22))
        config_path = Path(__file__).resolve().parent.parent / "switch" / "switch_config.yaml"
        self.ms = MultiSwitch(
            "multi",
            self.main,
            self.s1,
            self.s2,
            self.leds,
            config_path,
        )

    def test_state_mapping(self):
        self.ms.state(3)
        self.assertEqual(self.main.state(), 1)
        self.assertEqual(self.s1.state(), 3)
        self.assertEqual(self.leds[3].val, 1)
        self.assertTrue(all(led.val == (1 if idx == 3 else 0) for idx, led in enumerate(self.leds)))

        self.ms.state(18)
        self.assertEqual(self.main.state(), 4)
        self.assertEqual(self.leds[18].val, 1)
        self.assertEqual(self.s1.state(), 3)  # unchanged
        self.assertEqual(self.s2.state(), 0)


if __name__ == "__main__":
    unittest.main()

