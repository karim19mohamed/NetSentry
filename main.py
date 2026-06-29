import time

from core.blocklist import init_db
from core.cert_manager import generate_ca, ca_exists, CERT_DIR
from core.proxy import start_proxy, stop_proxy


def main():
    print("NetSentry starting...")

    init_db()
    print("Database ready.")

    if not ca_exists():
        print("Generating CA certificate...")
        generate_ca()
        print(f"CA saved to: {CERT_DIR}")
        print("Install certs/mitmproxy-ca-cert.pem into your trusted store to enable HTTPS inspection.")
    else:
        print("CA certificate found.")

    proxy_thread = start_proxy(host='127.0.0.1', port=8080, confdir=str(CERT_DIR))
    print("Proxy listening on 127.0.0.1:8080 — press Ctrl+C to stop.")

    try:
        while proxy_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        stop_proxy()


if __name__ == '__main__':
    main()
