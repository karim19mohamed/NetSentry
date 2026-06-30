import sys

from PyQt6.QtWidgets import QApplication

from core.blocklist import init_db
from core.cert_manager import generate_ca, ca_exists, CERT_DIR
from core.hosts_manager import apply_blocklist, remove_blocklist
from core.proxy import start_proxy
from core.system_proxy import enable as enable_proxy, disable as disable_proxy
from ui.tray import TrayApp


def main():
    init_db()

    if not ca_exists():
        generate_ca()
        try:
            from core.cert_manager import install_ca_windows
            install_ca_windows()
        except Exception:
            pass

    # Apply domain blocks to the hosts file (requires admin — silently skipped if not)
    try:
        apply_blocklist()
    except PermissionError:
        pass

    # Point Windows system proxy to our local mitmproxy instance
    enable_proxy(host='127.0.0.1', port=8080)

    start_proxy(host='127.0.0.1', port=8080, confdir=str(CERT_DIR))

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray = TrayApp(app)  # must be kept alive for the duration of the app

    ret = app.exec()

    # Cleanup on exit
    disable_proxy()
    try:
        remove_blocklist()
    except PermissionError:
        pass

    sys.exit(ret)


if __name__ == '__main__':
    main()
