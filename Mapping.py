from BluetoothService import BluetoothService, BleEvent, BleBtnState
from HidService import HidService, ModifierKeys

class HidState:

    def __init__(self) -> None:
        # mouse
        self.mouse0 = False
        self.mouse1 = False
        self.mouse2 = False
        # pen
        self.last_x = 0
        self.last_y = 0
        self.in_range = False
        # kb
        self.modifiers = 0
        self.keys = []

foo = lambda state, pressed : (state.mouse0 := pressed)[-1]

button_map: dict[BleBtnState, function] = {
    BleBtnState.BTN_0 : ,
    BleBtnState.BTN_1 : "bar"

}
