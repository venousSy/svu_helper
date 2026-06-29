"""
Referral Handlers
=================
Handles: /referral command, withdrawal FSM (3 steps + confirm/cancel).
All business logic is in WithdrawalService — this file is thin.
"""
import structlog
from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from domain.exceptions import (
    InsufficientBalanceError, WithdrawalAmountInvalidError,
    WithdrawalLimitError, WithdrawalTooLargeError, WithdrawalTooSmallError,
)
from keyboards.callbacks import WithdrawalAction, WithdrawalCallback
from keyboards.factory import KeyboardFactory
from states import ReferralStates
from utils.constants import (
    MSG_CANCELLED,
    MSG_REFERRAL_INFO, MSG_REWARD_RECEIVED,
    MSG_WITHDRAWAL_ASK_ADDRESS, MSG_WITHDRAWAL_ASK_NAME,
    MSG_WITHDRAWAL_ASK_AMOUNT, MSG_WITHDRAWAL_CONFIRM_PROMPT,
    MSG_WITHDRAWAL_SUCCESS, MSG_WITHDRAWAL_TOO_SMALL,
    MSG_WITHDRAWAL_TOO_LARGE, MSG_WITHDRAWAL_AMOUNT_INVALID,
    MSG_WITHDRAWAL_LIMIT_REACHED, MSG_WITHDRAWAL_INSUFFICIENT,
)
from utils.helpers import notify_admins_with_document

logger = structlog.get_logger(__name__)
router = Router()


# ── /referral ────────────────────────────────────────────────────────────────

@router.message(Command("referral"))
async def cmd_referral(
    message: types.Message,
    user_referral_repo,   # injected by DbInjectionMiddleware
    bot,
):
    user = await user_referral_repo.get_or_create_user(message.from_user.id)
    bot_info = await bot.me()
    link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    await message.answer(
        MSG_REFERRAL_INFO.format(link=link, balance=user.balance),
        reply_markup=KeyboardFactory.referral_menu(has_balance=user.balance > 0),
        parse_mode="Markdown",
    )


# ── Withdrawal FSM — Step 1 ───────────────────────────────────────────────────

@router.callback_query(WithdrawalCallback.filter(F.action == WithdrawalAction.request))
async def cb_start_withdrawal(
    query: types.CallbackQuery,
    state: FSMContext,
):
    await query.answer()
    await query.message.answer(MSG_WITHDRAWAL_ASK_ADDRESS)
    await state.set_state(ReferralStates.waiting_shamcash_address)


# ── Withdrawal FSM — Step 2 ───────────────────────────────────────────────────

@router.message(ReferralStates.waiting_shamcash_address)
async def fsm_got_address(message: types.Message, state: FSMContext):
    await state.update_data(shamcash_address=message.text.strip())
    await message.answer(MSG_WITHDRAWAL_ASK_NAME)
    await state.set_state(ReferralStates.waiting_shamcash_name)


# ── Withdrawal FSM — Step 3 ───────────────────────────────────────────────────

@router.message(ReferralStates.waiting_shamcash_name)
async def fsm_got_name(message: types.Message, state: FSMContext):
    await state.update_data(shamcash_name=message.text.strip())
    await message.answer(MSG_WITHDRAWAL_ASK_AMOUNT)
    await state.set_state(ReferralStates.waiting_withdrawal_amount)


# ── Withdrawal FSM — Amount + Confirmation ────────────────────────────────────

@router.message(ReferralStates.waiting_withdrawal_amount)
async def fsm_got_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer(MSG_WITHDRAWAL_ASK_AMOUNT)   # re-prompt on bad input
        return

    data = await state.get_data()
    await state.update_data(amount=amount)
    await message.answer(
        MSG_WITHDRAWAL_CONFIRM_PROMPT.format(
            amount=amount,
            name=data["shamcash_name"],
            address=data["shamcash_address"],
        ),
        reply_markup=KeyboardFactory.withdrawal_confirm(),
        parse_mode="Markdown",
    )


# ── Confirm ────────────────────────────────────────────────────────────────────

@router.callback_query(WithdrawalCallback.filter(F.action == WithdrawalAction.confirm))
async def cb_confirm_withdrawal(
    query: types.CallbackQuery,
    state: FSMContext,
    user_referral_repo,       # injected
    withdrawal_service,       # injected
    bot,
):
    await query.answer()
    data = await state.get_data()
    user_id = query.from_user.id

    try:
        req, tg_summary, txt_report = await withdrawal_service.request_withdrawal(
            user_id=user_id,
            amount=data["amount"],
            shamcash_address=data["shamcash_address"],
            shamcash_name=data["shamcash_name"],
        )
    except WithdrawalAmountInvalidError:
        await query.message.answer(MSG_WITHDRAWAL_AMOUNT_INVALID)
        await state.clear()
        return
    except WithdrawalTooSmallError:
        await query.message.answer(MSG_WITHDRAWAL_TOO_SMALL)
        await state.clear()
        return
    except WithdrawalTooLargeError:
        await query.message.answer(MSG_WITHDRAWAL_TOO_LARGE.format(
            max_amount=1_000_000
        ))
        await state.clear()
        return
    except WithdrawalLimitError:
        await query.message.answer(MSG_WITHDRAWAL_LIMIT_REACHED)
        await state.clear()
        return
    except InsufficientBalanceError:
        await query.message.answer(MSG_WITHDRAWAL_INSUFFICIENT)
        await state.clear()
        return

    await state.clear()
    await query.message.answer(MSG_WITHDRAWAL_SUCCESS)
    await notify_admins_with_document(
        bot=bot,
        text=tg_summary,
        filename=f"withdrawal_{req.request_id}.txt",
        file_content=txt_report,
    )
    logger.info("Withdrawal submitted and admins notified", user_id=user_id,
                request_id=req.request_id)


# ── Cancel ─────────────────────────────────────────────────────────────────────

@router.callback_query(WithdrawalCallback.filter(F.action == WithdrawalAction.cancel))
async def cb_cancel_withdrawal(query: types.CallbackQuery, state: FSMContext):
    await query.answer()
    await state.clear()
    await query.message.answer(MSG_CANCELLED)
