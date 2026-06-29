"""
Public password API used by the UI and the uninstall checker.

Typical flow
------------
First run  : is_password_set() → False → set_password("chosen")
Settings   : verify_password("input") → True/False
Change     : change_password("old", "new") → True/False
Uninstall  : verify_password("input") → True → proceed
"""

import bcrypt
from auth.registry import save_hash, load_hash, delete_hash


def is_password_set() -> bool:
    return load_hash() is not None


def set_password(password: str) -> None:
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    save_hash(hashed)


def verify_password(password: str) -> bool:
    hashed = load_hash()
    if hashed is None:
        return False
    return bcrypt.checkpw(password.encode('utf-8'), hashed)


def change_password(old_password: str, new_password: str) -> bool:
    """Returns True and updates the hash only if old_password is correct."""
    if not verify_password(old_password):
        return False
    set_password(new_password)
    return True


def remove_password() -> None:
    """Clears the stored hash — only called after a successful verify during uninstall."""
    delete_hash()
