import os
import json
import socket
import threading
import urllib.request
from config.settings import DEFAULT_PORT


def get_local_ip():
    """Detect primary LAN IPv4 address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def format_size(bytes_val):
    """Format byte size into human-readable string."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    if bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    if bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.2f} MB"
    return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"


def check_existing_instance_and_send(files, port=DEFAULT_PORT):
    """If AppleDrop is already running, forward dropped files via local HTTP IPC and exit."""
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/ping",
            headers={"User-Agent": "AppleDrop-CLI"},
        )
        with urllib.request.urlopen(req, timeout=0.8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("app") == "AppleDrop":
                if files:
                    abs_paths = [os.path.abspath(f) for f in files]
                    payload = json.dumps({"paths": abs_paths}).encode("utf-8")
                    post_req = urllib.request.Request(
                        f"http://127.0.0.1:{port}/api/add",
                        data=payload,
                        headers={"Content-Type": "application/json"},
                    )
                    with urllib.request.urlopen(post_req, timeout=1.2):
                        pass
                return True
    except Exception:
        pass
    return False


class FileQueue:
    """Thread-safe zero-copy file queue storing only original disk paths."""

    def __init__(self):
        self.lock = threading.Lock()
        self.files = []
        self.next_id = 1
        self.version = 0
        self.wakeup_requested = False

    def _bump_version(self):
        self.version += 1

    def request_wakeup(self):
        with self.lock:
            self.wakeup_requested = True
            self._bump_version()

    def consume_wakeup(self):
        with self.lock:
            if self.wakeup_requested:
                self.wakeup_requested = False
                return True
            return False

    def add_files(self, paths):
        added = 0
        with self.lock:
            for p in paths:
                if not p:
                    continue
                abs_p = os.path.abspath(p)
                if not os.path.exists(abs_p):
                    continue
                if os.path.isdir(abs_p):
                    for root, _, filenames in os.walk(abs_p):
                        for fn in filenames:
                            fp = os.path.join(root, fn)
                            if not any(f["path"] == fp for f in self.files):
                                self._add_single_file(fp)
                                added += 1
                else:
                    if not any(f["path"] == abs_p for f in self.files):
                        self._add_single_file(abs_p)
                        added += 1
            if added > 0:
                self._bump_version()
        return added

    def _add_single_file(self, file_path):
        size = os.path.getsize(file_path)
        item = {
            "id": str(self.next_id),
            "path": file_path,
            "name": os.path.basename(file_path),
            "size": size,
            "size_str": format_size(size),
            "status": "等待发送",
            "progress": 0,
            "speed": "",
        }
        self.next_id += 1
        self.files.append(item)

    def get_all(self):
        with self.lock:
            return [dict(f) for f in self.files]

    def get_by_id(self, file_id):
        with self.lock:
            for f in self.files:
                if f["id"] == str(file_id):
                    return dict(f)
            return None

    def get_next_pending(self):
        with self.lock:
            for f in self.files:
                if f["status"] == "等待发送":
                    return dict(f)
            return dict(self.files[-1]) if self.files else None

    def update_status(self, file_id, status=None, progress=None, speed=None):
        with self.lock:
            for f in self.files:
                if f["id"] == str(file_id):
                    if status is not None:
                        f["status"] = status
                    if progress is not None:
                        f["progress"] = progress
                    if speed is not None:
                        f["speed"] = speed
                    self._bump_version()
                    break

    def remove(self, file_id):
        with self.lock:
            self.files = [f for f in self.files if f["id"] != str(file_id)]
            self._bump_version()

    def clear_all(self):
        with self.lock:
            self.files.clear()
            self._bump_version()
