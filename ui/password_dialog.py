from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QDialogButtonBox, QMessageBox
)


class PasswordDialog(QDialog):
    """Single password input — used to gate sensitive actions."""

    def __init__(self, prompt: str = 'Enter password:', parent=None):
        super().__init__(parent)
        self.setWindowTitle('NetSentry')
        self.setFixedWidth(320)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(prompt))

        self._input = QLineEdit()
        self._input.setEchoMode(QLineEdit.EchoMode.Password)
        self._input.returnPressed.connect(self.accept)
        layout.addWidget(self._input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def password(self) -> str:
        return self._input.text()


class SetPasswordDialog(QDialog):
    """First-run dialog: choose and confirm a new password."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('NetSentry — Set Password')
        self.setFixedWidth(340)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Choose a password to protect NetSentry.\nYou will need it to change settings or uninstall.'))

        self._pw = QLineEdit()
        self._pw.setEchoMode(QLineEdit.EchoMode.Password)
        self._pw.setPlaceholderText('Password (min. 6 characters)')
        layout.addWidget(self._pw)

        self._confirm = QLineEdit()
        self._confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm.setPlaceholderText('Confirm password')
        self._confirm.returnPressed.connect(self._validate)
        layout.addWidget(self._confirm)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self._validate)
        layout.addWidget(buttons)

    def _validate(self):
        if len(self._pw.text()) < 6:
            QMessageBox.warning(self, 'NetSentry', 'Password must be at least 6 characters.')
            return
        if self._pw.text() != self._confirm.text():
            QMessageBox.warning(self, 'NetSentry', 'Passwords do not match.')
            return
        self.accept()

    def password(self) -> str:
        return self._pw.text()
