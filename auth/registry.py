"""
Persists the password hash.
- Windows : HKEY_LOCAL_MACHINE\\SOFTWARE\\NetSentry  (requires admin)
- Linux   : data/.auth  (development fallback only)
"""
from __future__ import annotations

import platform
from pathlib import Path

_REG_PATH = r'SOFTWARE\NetSentry'
_REG_KEY  = 'PasswordHash'

_DEV_FILE = Path(__file__).parent.parent / 'data' / '.auth'


def save_hash(hashed: bytes) -> None:
    if platform.system() == 'Windows':
        _reg_write(hashed)
    else:
        _DEV_FILE.parent.mkdir(exist_ok=True)
        _DEV_FILE.write_bytes(hashed)


def load_hash() -> bytes | None:
    if platform.system() == 'Windows':
        return _reg_read()
    return _DEV_FILE.read_bytes() if _DEV_FILE.exists() else None


def delete_hash() -> None:
    """Called during uninstall after password is verified."""
    if platform.system() == 'Windows':
        _reg_delete()
    elif _DEV_FILE.exists():
        _DEV_FILE.unlink()


# ── Windows registry helpers ──────────────────────────────────────────────────

def _reg_write(hashed: bytes) -> None:
    import winreg
    key = winreg.CreateKeyEx(
        winreg.HKEY_LOCAL_MACHINE, _REG_PATH, 0, winreg.KEY_SET_VALUE
    )
    try:
        winreg.SetValueEx(key, _REG_KEY, 0, winreg.REG_BINARY, hashed)
    finally:
        winreg.CloseKey(key)


def _reg_read() -> bytes | None:
    import winreg
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, _REG_PATH, 0, winreg.KEY_READ
        )
        try:
            value, _ = winreg.QueryValueEx(key, _REG_KEY)
            return value
        finally:
            winreg.CloseKey(key)
    except OSError:
        return None


def _reg_delete() -> None:
    import winreg
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, _REG_PATH, 0, winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, _REG_KEY)
        finally:
            winreg.CloseKey(key)
    except OSError:
        pass
