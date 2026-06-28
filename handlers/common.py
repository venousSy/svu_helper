"""
Common Handlers Module
======================
Manages universal bot commands like /start, /help, and /cancel,
as well as basic main menu navigation logic.
"""

from aiogram import Router, types, F
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext

from utils.constants import (
    BTN_MY_OFFERS,
    BTN_MY_PROJECTS,
    BTN_NEW_PROJECT,
    MSG_ASK_DETAILS,
    MSG_ASK_NOTES,
    MSG_CANCELLED,
    MSG_DATE_SELECTED_DEADLINE,
    MSG_DATE_SELECTED_DELIVERY,
    MSG_HELP,
    MSG_NO_ACTIVE_PROCESS,
    MSG_WELCOME,
)
from keyboards.factory import KeyboardFactory
from keyboards.callbacks import MenuCallback, MenuAction
from keyboards.calendar_kb import build_calendar, CalendarCallback
from states import ProjectOrder, AdminStates

# --- ROUTER INITIALIZATION ---
router = Router()


@router.message(Command("start"))
async def welcome(
    message: types.Message,
    command: CommandObject,
    user_referral_repo,  # injected
):
    """Greets the user and processes referral links if present."""
    referred_by = None
    if command.args and command.args.isdigit():
        referred_by = int(command.args)

    # Upsert user and record referral if applicable
    await user_referral_repo.get_or_create_user(message.from_user.id, referred_by)

    await message.answer(MSG_WELCOME, reply_markup=KeyboardFactory.student_main())


@router.message(Command("help"))
async def help_command(message: types.Message):
    """Provides help information to the user."""
    await message.answer(MSG_HELP, reply_markup=types.ReplyKeyboardRemove())

@router.callback_query(MenuCallback.filter(F.action == MenuAction.help))
async def cb_help(callback: types.CallbackQuery):
    await callback.message.answer(MSG_HELP)
    await callback.answer()

@router.callback_query(MenuCallback.filter(F.action == MenuAction.referral))
async def cb_referral(
    callback: types.CallbackQuery,
    user_referral_repo,  # injected
    bot,
):
    user = await user_referral_repo.get_or_create_user(callback.from_user.id)
    bot_info = await bot.me()
    link = f"https://t.me/{bot_info.username}?start={callback.from_user.id}"
    
    from utils.constants import MSG_REFERRAL_INFO
    from keyboards.factory import KeyboardFactory
    await callback.message.answer(
        MSG_REFERRAL_INFO.format(link=link, balance=user.balance),
        reply_markup=KeyboardFactory.referral_menu(has_balance=user.balance > 0),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(Command("cancel"), StateFilter("*"))
async def global_cancel(message: types.Message, state: FSMContext):
    """Universal cancel command to reset any active FSM state."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            MSG_NO_ACTIVE_PROCESS, reply_markup=types.ReplyKeyboardRemove()
        )
        return
    await state.clear()
    await message.answer(MSG_CANCELLED, reply_markup=types.ReplyKeyboardRemove())

@router.callback_query(MenuCallback.filter(F.action == MenuAction.cancel_flow))
async def cb_global_cancel(callback: types.CallbackQuery, state: FSMContext):
    """Inline cancel button handler to reset FSM state."""
    await state.clear()
    # Try to edit the message to remove the inline keyboard, if possible
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer(MSG_CANCELLED, reply_markup=types.ReplyKeyboardRemove())
    await callback.answer()

@router.callback_query(CalendarCallback.filter())
async def process_calendar(callback: types.CallbackQuery, callback_data: CalendarCallback, state: FSMContext):
    action = callback_data.action
    year = callback_data.year
    month = callback_data.month
    day = callback_data.day

    if action == "ignore":
        return await callback.answer()

    if action == "nav":
        await callback.message.edit_reply_markup(reply_markup=build_calendar(year, month))
        return await callback.answer()

    if action == "day":
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        current_state = await state.get_state()
        
        if current_state == ProjectOrder.deadline.state:
            await state.update_data(deadline=date_str)
            try:
                await callback.message.edit_text(
                    text=MSG_DATE_SELECTED_DEADLINE.format(date_str),
                    parse_mode="Markdown"
                )
            except Exception:
                pass
            await state.set_state(ProjectOrder.details)
            await callback.message.answer(
                MSG_ASK_DETAILS, 
                parse_mode="Markdown",
                reply_markup=KeyboardFactory.inline_cancel()
            )
        elif current_state == AdminStates.waiting_for_delivery.state:
            await state.update_data(delivery=date_str)
            try:
                await callback.message.edit_text(
                    text=MSG_DATE_SELECTED_DELIVERY.format(date_str),
                    parse_mode="Markdown"
                )
            except Exception:
                pass
            await state.set_state(AdminStates.waiting_for_notes_decision)
            await callback.message.answer(MSG_ASK_NOTES, reply_markup=KeyboardFactory.notes_decision())
        else:
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass

    # Always answer the callback to dismiss the spinner, regardless of state
    await callback.answer()
