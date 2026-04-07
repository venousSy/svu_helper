"""
Common Keyboard Module
======================
Thin delegation layer – all keyboards are built by KeyboardFactory.
Import from keyboards.factory directly in new code.
"""
from keyboards.factory import KeyboardFactory


def get_student_main_kb():
    return KeyboardFactory.student_main()
