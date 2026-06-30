from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QListWidget, QLineEdit, QPushButton, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt

from auth.password import change_password
from core.blocklist import (
    add_domain, remove_domain, get_all_blocked_domains,
    add_path_rule, remove_path_rule, get_all_path_rules,
)


class SettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('NetSentry — Settings')
        self.setMinimumSize(540, 420)

        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(self._domains_tab(), 'Blocked Domains')
        tabs.addTab(self._paths_tab(),   'Path Rules')
        tabs.addTab(self._password_tab(), 'Password')
        layout.addWidget(tabs)

    # ── Domains tab ───────────────────────────────────────────────────────────

    def _domains_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel('Domains blocked entirely (subdomains are also blocked):'))

        self._domain_list = QListWidget()
        self._refresh_domains()
        layout.addWidget(self._domain_list)

        row = QHBoxLayout()
        self._domain_input = QLineEdit()
        self._domain_input.setPlaceholderText('e.g. example.com')
        self._domain_input.returnPressed.connect(self._add_domain)
        row.addWidget(self._domain_input)

        btn_add = QPushButton('Block')
        btn_add.clicked.connect(self._add_domain)
        row.addWidget(btn_add)

        btn_remove = QPushButton('Remove')
        btn_remove.clicked.connect(self._remove_domain)
        row.addWidget(btn_remove)

        layout.addLayout(row)
        return w

    def _refresh_domains(self):
        self._domain_list.clear()
        self._domain_list.addItems(get_all_blocked_domains())

    def _add_domain(self):
        domain = self._domain_input.text().strip().lower()
        if not domain:
            return
        add_domain(domain)
        self._domain_input.clear()
        self._refresh_domains()

    def _remove_domain(self):
        item = self._domain_list.currentItem()
        if item:
            remove_domain(item.text())
            self._refresh_domains()

    # ── Path rules tab ────────────────────────────────────────────────────────

    def _paths_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel(
            'Block a specific path while leaving the rest of the domain accessible.\n'
            'Example: block tlgrm.eu/channels/adult but allow tlgrm.eu'
        ))

        row = QHBoxLayout()
        self._path_domain = QLineEdit()
        self._path_domain.setPlaceholderText('Domain (e.g. tlgrm.eu)')
        self._path_input = QLineEdit()
        self._path_input.setPlaceholderText('Path (e.g. /channels/adult)')
        row.addWidget(self._path_domain)
        row.addWidget(self._path_input)
        layout.addLayout(row)

        btn_add = QPushButton('Add Rule')
        btn_add.clicked.connect(self._add_path_rule)
        layout.addWidget(btn_add)

        self._path_list = QListWidget()
        self._refresh_paths()
        layout.addWidget(self._path_list)

        btn_remove = QPushButton('Remove Selected')
        btn_remove.clicked.connect(self._remove_path_rule)
        layout.addWidget(btn_remove)

        return w

    def _refresh_paths(self):
        self._path_list.clear()
        for domain, path in get_all_path_rules():
            self._path_list.addItem(f'{domain}{path}')

    def _add_path_rule(self):
        domain = self._path_domain.text().strip().lower()
        path   = self._path_input.text().strip()
        if not domain or not path:
            return
        if not path.startswith('/'):
            path = '/' + path
        add_path_rule(domain, path)
        self._path_domain.clear()
        self._path_input.clear()
        self._refresh_paths()

    def _remove_path_rule(self):
        item = self._path_list.currentItem()
        if not item:
            return
        # item text is "domain/path", e.g. "tlgrm.eu/channels/adult"
        domain, rest = item.text().split('/', 1)
        remove_path_rule(domain, '/' + rest)
        self._refresh_paths()

    # ── Password tab ──────────────────────────────────────────────────────────

    def _password_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.addWidget(QLabel('Change your NetSentry password:'))

        self._old_pw  = QLineEdit()
        self._new_pw  = QLineEdit()
        self._conf_pw = QLineEdit()
        for field, placeholder in (
            (self._old_pw,  'Current password'),
            (self._new_pw,  'New password (min. 6 characters)'),
            (self._conf_pw, 'Confirm new password'),
        ):
            field.setEchoMode(QLineEdit.EchoMode.Password)
            field.setPlaceholderText(placeholder)
            layout.addWidget(field)

        btn = QPushButton('Change Password')
        btn.clicked.connect(self._change_password)
        layout.addWidget(btn)
        layout.addStretch()
        return w

    def _change_password(self):
        old  = self._old_pw.text()
        new  = self._new_pw.text()
        conf = self._conf_pw.text()

        if len(new) < 6:
            QMessageBox.warning(self, 'NetSentry', 'New password must be at least 6 characters.')
            return
        if new != conf:
            QMessageBox.warning(self, 'NetSentry', 'New passwords do not match.')
            return
        if change_password(old, new):
            QMessageBox.information(self, 'NetSentry', 'Password changed successfully.')
            self._old_pw.clear()
            self._new_pw.clear()
            self._conf_pw.clear()
        else:
            QMessageBox.warning(self, 'NetSentry', 'Current password is incorrect.')
