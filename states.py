from aiogram.fsm.state import StatesGroup, State

class ProjectOrder(StatesGroup):
    subject = State()
    tutor = State()
    deadline = State()
    details = State()
class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_price = State()
    waiting_for_delivery = State()
    waiting_for_notes_decision = State() # Do you want notes? (Yes/No)
    waiting_for_notes_text = State()     # Type the notes here.