import asyncio
import threading

from mitmproxy import http, options
from mitmproxy.tools.dump import DumpMaster

_BLOCK_PAGE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Blocked — NetSentry</title>
  <style>
    body {{ font-family: Arial, sans-serif; text-align: center;
            padding: 80px; background: #f5f5f5; }}
    h1   {{ color: #c0392b; font-size: 2rem; }}
    p    {{ color: #555; }}
    code {{ background: #eee; padding: 2px 8px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>Access Blocked</h1>
  <p>This website has been blocked by <strong>NetSentry</strong>.</p>
  <p><code>{url}</code></p>
</body>
</html>"""


class _NetSentryAddon:
    def request(self, flow: http.HTTPFlow) -> None:
        from core.blocklist import is_domain_blocked, is_path_blocked

        host = flow.request.pretty_host
        path = flow.request.path

        if is_domain_blocked(host) or is_path_blocked(host, path):
            flow.response = http.Response.make(
                403,
                _BLOCK_PAGE.format(url=flow.request.pretty_url),
                {'Content-Type': 'text/html; charset=utf-8'}
            )


_master: DumpMaster | None = None


def start_proxy(host: str = '127.0.0.1', port: int = 8080, confdir: str | None = None) -> threading.Thread:
    opts = options.Options(listen_host=host, listen_port=port)
    if confdir:
        opts.update(confdir=str(confdir))

    async def _run():
        global _master
        _master = DumpMaster(opts, with_termlog=False, with_dumper=False)
        _master.addons.add(_NetSentryAddon())
        await _master.run()

    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=lambda: loop.run_until_complete(_run()), daemon=True)
    thread.start()
    return thread


def stop_proxy():
    global _master
    if _master:
        _master.shutdown()
        _master = None
