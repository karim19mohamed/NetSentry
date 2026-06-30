from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QMessageBox, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt

from auth.password import is_password_set, set_password, verify_password
from ui.password_dialog import PasswordDialog, SetPasswordDialog
from ui.settings_window import SettingsWindow


def _make_icon(color: str) -> QIcon:
    """Programmatic colored shield icon — no image file required."""
    px = QPixmap(32, 32)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    # Shield: rounded rect for body, triangle for bottom point
    p.drawRoundedRect(4, 2, 24, 20, 4, 4)
    from PyQt6.QtGui import QPolygon
    from PyQt6.QtCore import QPoint
    p.drawPolygon(QPolygon([QPoint(4, 16), QPoint(28, 16), QPoint(16, 30)]))
    p.end()
    return QIcon(px)


class TrayApp:
    def __init__(self, app: QApplication):
        self._app = app
        self._settings_win = None

        # Icons must be created after QApplication exists
        self._icon_active = _make_icon('#27ae60')
        self._icon_error  = _make_icon('#c0392b')

        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, 'NetSentry', 'System tray is not available on this system.')
            app.quit()
            return

        self._tray = QSystemTrayIcon()
        self._tray.setIcon(self._icon_active)
        self._tray.setToolTip('NetSentry — Active')
        self._tray.setContextMenu(self._build_menu())
        self._tray.show()
        self._tray.showMessage(
            'NetSentry',
            'Content filter is active. Right-click this icon to open settings.',
            QSystemTrayIcon.MessageIcon.Information,
            4000
        )

        self._first_run_setup()

    # ── Menu ──────────────────────────────────────────────────────────────────

    def _build_menu(self) -> QMenu:
        menu = QMenu()

        title = menu.addAction('NetSentry — Active')
        title.setEnabled(False)
        menu.addSeparator()

        menu.addAction('Open Settings', self._open_settings)
        menu.addSeparator()
        menu.addAction('Exit', self._exit)

        return menu

    # ── Actions ───────────────────────────────────────────────────────────────

    def _first_run_setup(self):
        if not is_password_set():
            dlg = SetPasswordDialog()
            if dlg.exec():
                set_password(dlg.password())
            else:
                # User cancelled — quit without setting a password
                self._app.quit()

    def _open_settings(self):
        if not self._ask_password('Enter password to open settings:'):
            return
        if self._settings_win is None or not self._settings_win.isVisible():
            self._settings_win = SettingsWindow()
        self._settings_win.show()
        self._settings_win.raise_()
        self._settings_win.activateWindow()

    def _exit(self):
        if not self._ask_password('Enter password to close NetSentry:'):
            return
        self._stop_service()
        self._app.quit()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _ask_password(self, prompt: str) -> bool:
        dlg = PasswordDialog(prompt=prompt)
        if dlg.exec() and verify_password(dlg.password()):
            return True
        QMessageBox.warning(None, 'NetSentry', 'Incorrect password.')
        return False

    def _stop_service(self):
        try:
            from service.manager import stop
            stop()
        except Exception:
            pass
