"""
Service lifecycle management — install, uninstall, start, stop, status.
All functions require Administrator privileges on Windows.
"""

import subprocess
import sys
from pathlib import Path

try:
    import win32service
    import win32serviceutil
    _WIN32 = True
except ImportError:
    _WIN32 = False

_SVC_DIR  = Path(__file__).resolve().parent
_MAIN_SVC = 'NetSentry'
_WATCH_SVC = 'NetSentryWatchdog'


def install():
    _require_windows()

    # Register both services
    for script, name in (
        (_SVC_DIR / 'main_service.py', _MAIN_SVC),
        (_SVC_DIR / 'watchdog.py',     _WATCH_SVC),
    ):
        subprocess.run([sys.executable, str(script), '--startup', 'auto', 'install'], check=True)
        _set_recovery(name)

    # Watchdog starts first so it's ready before the main service
    win32serviceutil.StartService(_WATCH_SVC)
    win32serviceutil.StartService(_MAIN_SVC)


def uninstall():
    _require_windows()

    for svc, script in (
        (_MAIN_SVC,  'main_service.py'),
        (_WATCH_SVC, 'watchdog.py'),
    ):
        try:
            win32serviceutil.StopService(svc)
        except Exception:
            pass
        subprocess.run(
            [sys.executable, str(_SVC_DIR / script), 'remove'],
            capture_output=True
        )


def start():
    _require_windows()
    win32serviceutil.StartService(_MAIN_SVC)


def stop():
    _require_windows()
    win32serviceutil.StopService(_MAIN_SVC)


def is_running() -> bool:
    if not _WIN32:
        return False
    try:
        state = win32serviceutil.QueryServiceStatus(_MAIN_SVC)[1]
        return state == win32service.SERVICE_RUNNING
    except Exception:
        return False


def status() -> str:
    if not _WIN32:
        return 'unavailable (not Windows)'
    try:
        state = win32serviceutil.QueryServiceStatus(_MAIN_SVC)[1]
        return {
            win32service.SERVICE_RUNNING:       'running',
            win32service.SERVICE_STOPPED:       'stopped',
            win32service.SERVICE_START_PENDING: 'starting',
            win32service.SERVICE_STOP_PENDING:  'stopping',
            win32service.SERVICE_PAUSED:        'paused',
        }.get(state, f'unknown ({state})')
    except Exception:
        return 'not installed'


def _set_recovery(service_name: str):
    """Auto-restart on failure: 3 attempts with 5 s delay, reset count after 24 h."""
    subprocess.run([
        'sc', 'failure', service_name,
        'reset=', '86400',
        'actions=', 'restart/5000/restart/5000/restart/10000'
    ], check=True, capture_output=True)


def _require_windows():
    if not _WIN32:
        raise RuntimeError('Service management is only available on Windows.')
