import platform


def enable(host: str = '127.0.0.1', port: int = 8080) -> None:
    if platform.system() != 'Windows':
        return
    import winreg
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
        0, winreg.KEY_SET_VALUE
    )
    try:
        winreg.SetValueEx(key, 'ProxyServer', 0, winreg.REG_SZ, f'{host}:{port}')
        winreg.SetValueEx(key, 'ProxyEnable', 0, winreg.REG_DWORD, 1)
    finally:
        winreg.CloseKey(key)
    _refresh()


def disable() -> None:
    if platform.system() != 'Windows':
        return
    import winreg
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
        0, winreg.KEY_SET_VALUE
    )
    try:
        winreg.SetValueEx(key, 'ProxyEnable', 0, winreg.REG_DWORD, 0)
    finally:
        winreg.CloseKey(key)
    _refresh()


def _refresh() -> None:
    """Tell Windows to apply the proxy change immediately without a reboot."""
    try:
        import ctypes
        wininet = ctypes.windll.wininet
        wininet.InternetSetOptionW(0, 39, 0, 0)  # INTERNET_OPTION_SETTINGS_CHANGED
        wininet.InternetSetOptionW(0, 37, 0, 0)  # INTERNET_OPTION_REFRESH
    except Exception:
        pass
