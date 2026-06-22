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


class TicketStates(StatesGroup):
    waiting_for_message = State()    # User composing initial ticket message
    waiting_for_reply = State()      # User replying to existing ticket


class PeerProfileStates(StatesGroup):
    waiting_for_program = State()
    waiting_for_semester = State()
    waiting_for_courses = State()


class PeerAdStates(StatesGroup):
    waiting_for_course_code = State()
    waiting_for_requirements = State()
    waiting_for_duration = State()

class PeerSearchStates(StatesGroup):
    waiting_for_search_course = State()

