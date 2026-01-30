from aiogram.fsm.state import State, StatesGroup


class ProjectOrder(StatesGroup):
    subject = State()
    tutor = State()
    deadline = State()
    details = State()
    waiting_for_payment_proof = State()


class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_price = State()
    waiting_for_delivery = State()
    waiting_for_notes_decision = State()  # Do you want notes? (Yes/No)
    waiting_for_notes_text = State()  # Type the notes here.
    waiting_for_finished_work = State()
