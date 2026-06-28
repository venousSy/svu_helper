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


class ProfileStates(StatesGroup):
    choosing_specialization = State()

class TeamStates(StatesGroup):
    typing_course_name = State()     # Host types course name
    typing_doctor_name = State()     # Host types doctor name
    choosing_member_count = State()  # Host selects 1/2/3+

class ReferralStates(StatesGroup):
    waiting_shamcash_address = State()  # Step 1: bot asks for ShamCash address
    waiting_shamcash_name    = State()  # Step 2: bot asks for account name
    waiting_withdrawal_amount = State() # Step 3: bot asks for amount
