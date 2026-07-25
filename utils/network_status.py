"""
Network connectivity status for the art_panel notif bar wifi icon.

Push-based, in-memory only — same split as api/github.py, but with no SQLite cache
since this state is transient runtime status, not worth persisting across restarts.
check_and_update() does the actual carrier-file read + TCP probe and is only ever
called from main.py (startup + a dedicated background poll loop). get_status() is a
cache-only read — safe to call from the render path (components/art_panel.py calls it
every render), since it never touches the filesystem or network.

States:
  'ok'          — wifi associated with an AP and internet reachable
  'no_internet' — wifi associated, but the TCP probe failed
  'no_network'  — wifi not associated (no carrier)
"""
import socket
from pathlib import Path

import config

_CHECK_HOST = ('1.1.1.1', 53)
_CHECK_TIMEOUT = 2

_status = 'no_network'


def get_status() -> str:
    """Cache-only read of the last known status. No I/O."""
    return _status


def check_and_update() -> str:
    """Probe the interface + internet reachability and update the cached status.
    Never called from the render path — main.py runs this at startup and on a
    background poll loop. Returns the new status."""
    global _status
    try:
        has_link = Path(f'/sys/class/net/{config.NETWORK_IFACE}/carrier').read_text().strip() == '1'
    except OSError:
        has_link = False

    if not has_link:
        _status = 'no_network'
        return _status

    try:
        socket.create_connection(_CHECK_HOST, timeout=_CHECK_TIMEOUT).close()
        _status = 'ok'
    except OSError:
        _status = 'no_internet'
    return _status
