import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data' / 'blocklist.db'


def _connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with _connect() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS domains (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT    UNIQUE NOT NULL,
                source TEXT    NOT NULL DEFAULT 'user'
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS path_rules (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                path   TEXT NOT NULL,
                UNIQUE(domain, path)
            )
        ''')


def add_domain(domain: str, source: str = 'user'):
    with _connect() as conn:
        conn.execute(
            'INSERT OR IGNORE INTO domains (domain, source) VALUES (?, ?)',
            (domain.lower(), source)
        )


def remove_domain(domain: str):
    with _connect() as conn:
        conn.execute('DELETE FROM domains WHERE domain = ?', (domain.lower(),))


def add_path_rule(domain: str, path: str):
    with _connect() as conn:
        conn.execute(
            'INSERT OR IGNORE INTO path_rules (domain, path) VALUES (?, ?)',
            (domain.lower(), path)
        )


def remove_path_rule(domain: str, path: str):
    with _connect() as conn:
        conn.execute(
            'DELETE FROM path_rules WHERE domain = ? AND path = ?',
            (domain.lower(), path)
        )


def is_domain_blocked(domain: str) -> bool:
    domain = domain.lower()
    with _connect() as conn:
        if conn.execute('SELECT 1 FROM domains WHERE domain = ?', (domain,)).fetchone():
            return True
        # also match parent domains (sub.evil.com -> evil.com)
        parts = domain.split('.')
        for i in range(1, len(parts) - 1):
            parent = '.'.join(parts[i:])
            if conn.execute('SELECT 1 FROM domains WHERE domain = ?', (parent,)).fetchone():
                return True
    return False


def is_path_blocked(domain: str, path: str) -> bool:
    domain = domain.lower()
    with _connect() as conn:
        rows = conn.execute(
            'SELECT path FROM path_rules WHERE domain = ?', (domain,)
        ).fetchall()
    return any(path.startswith(rule) for (rule,) in rows)


def get_all_blocked_domains() -> list[str]:
    with _connect() as conn:
        return [r[0] for r in conn.execute('SELECT domain FROM domains').fetchall()]


def load_stevenblack_list(filepath: str) -> int:
    """Load domains from a StevenBlack-format hosts file. Returns count added."""
    count = 0
    with _connect() as conn:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) >= 2 and parts[0] in ('0.0.0.0', '127.0.0.1'):
                    domain = parts[1].lower()
                    if domain not in ('0.0.0.0', 'localhost', 'local', 'broadcasthost'):
                        conn.execute(
                            "INSERT OR IGNORE INTO domains (domain, source) VALUES (?, 'stevenblack')",
                            (domain,)
                        )
                        count += 1
    return count
