from aiogram.fsm.state import StatesGroup, State

class ProjectOrder(StatesGroup):
    subject = State()
    tutor = State()
    deadline = State()
    details = State()

class AdminStates(StatesGroup):
    waiting_for_broadcast = State()