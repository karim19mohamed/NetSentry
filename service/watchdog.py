"""
NetSentry watchdog Windows service.
Monitors the main NetSentry service every 30 seconds and restarts it if down.
Run as Administrator:
  python service/watchdog.py install
  python service/watchdog.py start
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import win32event
import win32service
import win32serviceutil
import servicemanager


_WATCHED_SERVICE  = 'NetSentry'
_CHECK_INTERVAL_MS = 30_000  # 30 seconds


class NetSentryWatchdog(win32serviceutil.ServiceFramework):
    _svc_name_         = 'NetSentryWatchdog'
    _svc_display_name_ = 'NetSentry Watchdog'
    _svc_description_  = 'Monitors and restarts the NetSentry service if it stops.'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self._stop_event = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self._stop_event)

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self._watch()

    def _watch(self):
        while True:
            result = win32event.WaitForSingleObject(self._stop_event, _CHECK_INTERVAL_MS)

            if result == win32event.WAIT_OBJECT_0:
                break  # stop requested

            self._ensure_main_running()

    def _ensure_main_running(self):
        try:
            state = win32serviceutil.QueryServiceStatus(_WATCHED_SERVICE)[1]
            if state not in (win32service.SERVICE_RUNNING, win32service.SERVICE_START_PENDING):
                servicemanager.LogInfoMsg(f'NetSentry stopped (state={state}), restarting...')
                win32serviceutil.StartService(_WATCHED_SERVICE)
        except Exception as e:
            servicemanager.LogErrorMsg(f'Watchdog check failed: {e}')


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(NetSentryWatchdog)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(NetSentryWatchdog)
