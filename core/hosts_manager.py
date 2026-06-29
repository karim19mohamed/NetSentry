import platform
import subprocess
from pathlib import Path
from core.blocklist import get_all_blocked_domains

HOSTS_PATH = (
    Path(r'C:\Windows\System32\drivers\etc\hosts')
    if platform.system() == 'Windows'
    else Path('/etc/hosts')
)

_MARKER_START = '# --- NetSentry START ---'
_MARKER_END   = '# --- NetSentry END ---'


def apply_blocklist():
    domains = get_all_blocked_domains()
    entries = '\n'.join(f'0.0.0.0 {d}' for d in domains)
    block = f'\n{_MARKER_START}\n{entries}\n{_MARKER_END}\n'

    content = HOSTS_PATH.read_text(encoding='utf-8')
    content = _strip_block(content) + block
    HOSTS_PATH.write_text(content, encoding='utf-8')
    _flush_dns()


def remove_blocklist():
    content = HOSTS_PATH.read_text(encoding='utf-8')
    HOSTS_PATH.write_text(_strip_block(content), encoding='utf-8')
    _flush_dns()


def _strip_block(content: str) -> str:
    lines, inside = [], False
    for line in content.splitlines(keepends=True):
        if _MARKER_START in line:
            inside = True
        elif _MARKER_END in line:
            inside = False
        elif not inside:
            lines.append(line)
    return ''.join(lines)


def _flush_dns():
    if platform.system() == 'Windows':
        subprocess.run(['ipconfig', '/flushdns'], capture_output=True)
