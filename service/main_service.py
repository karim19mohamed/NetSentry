"""
NetSentry main Windows service.
Run as Administrator:
  python service/main_service.py install
  python service/main_service.py start
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path regardless of working directory
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import win32event
import win32service
import win32serviceutil
import servicemanager


class NetSentryService(win32serviceutil.ServiceFramework):
    _svc_name_         = 'NetSentry'
    _svc_display_name_ = 'NetSentry Content Filter'
    _svc_description_  = 'Blocks unwanted websites at the network level.'

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
        self._run()

    def _run(self):
        from core.blocklist import init_db
        from core.cert_manager import generate_ca, ca_exists, install_ca_windows, CERT_DIR
        from core.hosts_manager import apply_blocklist, remove_blocklist
        from core.proxy import start_proxy, stop_proxy

        init_db()

        if not ca_exists():
            generate_ca()
            install_ca_windows()

        apply_blocklist()
        start_proxy(host='127.0.0.1', port=8080, confdir=str(CERT_DIR))

        # Block until stop is requested
        win32event.WaitForSingleObject(self._stop_event, win32event.INFINITE)

        stop_proxy()
        remove_blocklist()

        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, '')
        )


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(NetSentryService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(NetSentryService)
