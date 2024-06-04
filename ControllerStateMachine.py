from statemachine import StateMachine, State

class ControllerStateMachine(StateMachine):
    "Game Table Controller State Machine"

    __callbacks = {
        "initialize": lambda: None,
        "scanning": lambda: None,
        "connecting": lambda: None,
        "calibrating": lambda: None,
        "running": lambda: None,
    }

    # States
    initialize = State(initial=True)
    scanning = State()
    connecting = State()
    calibrating = State()
    running = State()

    # Transitions
    scan = initialize.to(scanning)
    connect = scanning.to(connecting)
    scan = initialize.to(scanning) | connecting.to(scanning)
    calibrate = connecting.to(calibrating) | running.to(calibrating)
    loop = calibrating.to(running) | running.to.itself(internal = True)

    def set_enter_callback(self, name, callback):
        if name in self.__callbacks:
            self.__callbacks[name] = callback

    # def on_transition(self, event, state):
    #     print(f"On '{event}', on the '{state.id}' state.")

    def on_enter_state(self, event, state):
        self.__callbacks[state.id]()

if __name__ == '__main__':
    def make_print(text):
        return lambda : print(text)

    sm = ControllerStateMachine()
    sm.set_enter_callback("scanning", make_print("SCANNING"))
    sm.set_enter_callback("connecting", make_print("CONNECTING"))

    def calibrate():
        print("CALIBRATE")
        sm.loop()

    sm.set_enter_callback("calibrating", calibrate)
    sm.set_enter_callback("running", make_print("RUNNING"))

    sm.scan()
    sm.connect()
    sm.calibrate()
