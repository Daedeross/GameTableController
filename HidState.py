from BluetoothService import BleBtnState
from HidService import ModifierKey

_default_map = {
    BleBtnState.ENC_UP: 0x52,       # Up Arrow
    BleBtnState.ENC_LEFT: 0x50,     # Left Arrow
    BleBtnState.ENC_DOWN: 0x51,     # Down Arrow
    BleBtnState.ENC_RIGHT: 0x4F,    # Right Arrow
    BleBtnState.ENC_SELECT: 0x2C,   # Spacebar
}

class BleToHidMapping:
    def __init__(self) -> None:
        self.mouse0 = BleBtnState.BTN_0
        self.mouse1 = BleBtnState.BTN_1
        self.mouse2 = BleBtnState.NONE  # no pointer button maps to Mouse2 (aka middle-click) by default
        self.key_map = _default_map

class HidState:
    def __init__(self, mapping: BleToHidMapping = BleToHidMapping()) -> None:
        self._mapping = mapping
        self._main_callback = None
        self._callbacks = dict()
        # mouse
        self.mouse0 = False
        self.mouse1 = False
        self.mouse2 = False
        # pen
        self.last_x = 0
        self.last_y = 0
        self.x = 0
        self.y = 0
        self.in_range = False
        self.wheel_delta = 0
        # kb
        self.modifiers : ModifierKey = 0
        self.keys = set()

    def set_callback(self, mask: BleBtnState | None, callback: function):
        if (mask):
            self._callbacks[mask] = callback
        else:
            self._main_callback = callback

    def remove_callback(self, mask: BleBtnState | None = None):
        if (mask):
            self._callbacks.pop(mask)
        else:
            self._main_callback = None

    def apply_buttons(self, state: BleBtnState):
        if (self._main_callback):
            self._main_callback(state)
        elif state in self._callbacks:
            self._callbacks[state](state)
        else:
            self.mouse0 = (bool)(state & self._mapping.mouse0)
            self.mouse1 = (bool)(state & self._mapping.mouse1)
            self.mouse2 = (bool)(state & self._mapping.mouse2)
            self.keys.clear()
            for k, v in self._mapping.key_map.items():
                if (k & state):
                    self.keys.add(v)
