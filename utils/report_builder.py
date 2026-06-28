"""
Report Builder — Withdrawal Audit Reports
==========================================
Produces two formats for admin consumption:
  1. telegram_summary  — compact, formatted Telegram message (Markdown)
  2. txt_report        — full plain-text audit file sent as a .txt attachment
"""
from typing import List, Tuple
from domain.entities import CommissionLog, WithdrawalRequest


def build_withdrawal_report(
    user_id: int,
    req: WithdrawalRequest,
    referral_ids: List[int],
    commission_logs: List[CommissionLog],
    remaining_balance: float,
) -> Tuple[str, str]:
    """
    Args:
        user_id:            The referrer's Telegram user_id.
        req:                The WithdrawalRequest domain object.
        referral_ids:       All user_ids who registered via this user's link.
        commission_logs:    All CommissionLog records for this referrer.
        remaining_balance:  Balance after deduction (for display only).

    Returns:
        (telegram_summary, txt_report)
    """
    total_earned = sum(log.commission_amount for log in commission_logs)

    # ── Telegram Summary ────────────────────────────────────────────────────
    telegram_summary = (
        f"💸 *طلب سحب رصيد جديد*\n\n"
        f"👤 معرّف المستخدم: `{user_id}`\n"
        f"💰 المبلغ المطلوب: *{req.amount:.0f} ل.س*\n"
        f"📱 اسم ShamCash: {req.shamcash_name}\n"
        f"🔑 عنوان ShamCash: `{req.shamcash_address}`\n"
        f"📅 وقت الطلب: {req.requested_at.strftime('%Y-%m-%d %H:%M')} UTC\n\n"
        f"📎 التقرير التفصيلي مرفق في الملف أدناه."
    )

    # ── Plain-text Audit File ───────────────────────────────────────────────
    lines = [
        "═══════════════════════════════════════════════════",
        "         طلب سحب رصيد — تقرير تفصيلي             ",
        "═══════════════════════════════════════════════════",
        f"معرّف المستخدم    : {user_id}",
        f"تاريخ الطلب      : {req.requested_at.strftime('%Y-%m-%d %H:%M')} UTC",
        f"رقم الطلب        : {req.request_id}",
        "",
        "بيانات ShamCash:",
        f"  الاسم           : {req.shamcash_name}",
        f"  العنوان         : {req.shamcash_address}",
        f"  المبلغ المطلوب  : {req.amount:.0f} ل.س",
        "",
        "───────────────────────────────────────────────────",
        "الحسابات المُحالة (المسجّلة عبر رابط هذا المستخدم):",
        "───────────────────────────────────────────────────",
    ]

    if not referral_ids:
        lines.append("  (لا توجد حسابات مُحالة)")
    else:
        for rid in referral_ids:
            lines.append(f"  • حساب: {rid}")
            # Filter commission logs for this specific referral
            logs_for_referral = [l for l in commission_logs if l.referred_user_id == rid]
            if not logs_for_referral:
                lines.append("      لا توجد مشاريع مدفوعة مرتبطة بهذا الحساب.")
            for log in logs_for_referral:
                lines.append(
                    f"      - مشروع #{log.project_id} ({log.project_subject})"
                    f" | السعر: {log.project_price:.0f} ل.س"
                    f" | العمولة المضافة: {log.commission_amount:.0f} ل.س"
                    f" | بتاريخ: {log.earned_at.strftime('%Y-%m-%d')}"
                )

    lines += [
        "",
        "───────────────────────────────────────────────────",
        f"إجمالي العمولات المكتسبة : {total_earned:.0f} ل.س",
        f"الرصيد المتبقي بعد السحب : {remaining_balance:.0f} ل.س",
        "═══════════════════════════════════════════════════",
    ]

    txt_report = "\n".join(lines)
    return telegram_summary, txt_report
