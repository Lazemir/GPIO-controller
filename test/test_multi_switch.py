import unittest
from pathlib import Path

from switch.multi_switch import MultiSwitch


class DummyPin:
    def __init__(self):
        self.val = 0

    def state(self, v=None):
        if v is None:
            return self.val
        self.val = v


class DummyModule:
    def __init__(self, count: int):
        self.pins = [DummyPin() for _ in range(count)]


class DummyController:
    def __init__(self):
        self.modules = (
            DummyModule(11),
            DummyModule(16),
            DummyModule(16),
        )


class TestMultiSwitch(unittest.TestCase):
    def setUp(self):
        self.ctrl = DummyController()
        config_path = Path(__file__).resolve().parent.parent / "switch" / "switch_config.yaml"
        self.ms = MultiSwitch(
            "multi",
            self.ctrl,
            config_path,
        )
        self.led_pins = list(self.ms._leds)

    def test_state_mapping(self):
        self.ms.state(3)
        self.assertEqual(self.ms._main.state(), 1)
        self.assertEqual(self.ms._sw1.state(), 3)
        self.assertEqual(self.ctrl.modules[1].pins[3].val, 1)
        self.assertTrue(
            all(led.val == (1 if idx == 3 else 0) for idx, led in enumerate(self.led_pins))
        )

        self.ms.state(18)
        self.assertEqual(self.ms._main.state(), 4)
        self.assertEqual(self.ctrl.modules[2].pins[2].val, 1)
        self.assertEqual(self.ms._sw1.state(), 3)  # unchanged
        self.assertEqual(self.ms._sw2.state(), 0)
        self.assertTrue(
            all(led.val == (1 if idx == 18 else 0) for idx, led in enumerate(self.led_pins))
        )


if __name__ == "__main__":
    unittest.main()

