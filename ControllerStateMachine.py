from statemachine import StateMachine, State

class ControllerStateMachine(StateMachine):
    "Game Table Controller State Machine"

    # States
    initialize = State(initial=True)
    scanning = State()
    connecting = State()
    calibrating = State()
    loop = State()

    # Transitions
    connect = scanning.to(connecting)
    scan = initialize.to(scanning) | connecting.to(scanning)
    calibrate = connect.to(calibrating) | loop.to(calibrating)

    def on_transition(self, event, state):
        print(f"On '{event}', on the '{state.id}' state.")
        return "on_transition_return"