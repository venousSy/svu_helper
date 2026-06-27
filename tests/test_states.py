import pytest
from states import ProjectOrder, AdminStates, TicketStates, ProfileStates, TeamStates

def test_project_order_states():
    assert ProjectOrder.subject.state == "ProjectOrder:subject"
    assert ProjectOrder.tutor.state == "ProjectOrder:tutor"
    assert ProjectOrder.deadline.state == "ProjectOrder:deadline"
    assert ProjectOrder.details.state == "ProjectOrder:details"
    assert ProjectOrder.waiting_for_payment_proof.state == "ProjectOrder:waiting_for_payment_proof"

def test_admin_states():
    assert AdminStates.waiting_for_broadcast.state == "AdminStates:waiting_for_broadcast"
    assert AdminStates.waiting_for_price.state == "AdminStates:waiting_for_price"
    assert AdminStates.waiting_for_delivery.state == "AdminStates:waiting_for_delivery"
    assert AdminStates.waiting_for_notes_decision.state == "AdminStates:waiting_for_notes_decision"
    assert AdminStates.waiting_for_notes_text.state == "AdminStates:waiting_for_notes_text"
    assert AdminStates.waiting_for_finished_work.state == "AdminStates:waiting_for_finished_work"

def test_ticket_states():
    assert TicketStates.waiting_for_message.state == "TicketStates:waiting_for_message"
    assert TicketStates.waiting_for_reply.state == "TicketStates:waiting_for_reply"

def test_profile_states():
    assert ProfileStates.choosing_specialization.state == "ProfileStates:choosing_specialization"

def test_team_states():
    assert TeamStates.typing_course_name.state == "TeamStates:typing_course_name"
    assert TeamStates.typing_doctor_name.state == "TeamStates:typing_doctor_name"
    assert TeamStates.choosing_member_count.state == "TeamStates:choosing_member_count"
