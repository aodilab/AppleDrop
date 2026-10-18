import os
import io
import json
import time
import zipfile
import mimetypes
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

from config.settings import DEFAULT_PORT, MOBILE_HTML_PATH, STREAM_CHUNK_SIZE
from src.core.queue_manager import get_local_ip, format_size


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = False


def make_handler(file_queue, host_ip, port):
    class AppleDropHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def send_cors_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Range")

        def do_OPTIONS(self):
            self.send_response(200)
            self.send_cors_headers()
            self.end_headers()

        def do_POST(self):
            path = urllib.parse.urlparse(self.path).path
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length > 0 else b""
            if path == "/api/add":
                try:
                    data = json.loads(body.decode("utf-8"))
                    added = file_queue.add_files(data.get("paths", []))
                    file_queue.request_wakeup()
                    self._send_json({"success": True, "added": added})
                except Exception as e:
                    self._send_text(str(e), status=400)
            elif path == "/api/clear":
                file_queue.clear_all()
                self._send_json({"success": True})
            else:
                self._send_text("Not Found", status=404)

        def do_GET(self):
            path = urllib.parse.urlparse(self.path).path
            if path == "/api/ping":
                file_queue.request_wakeup()
                return self._send_json({"status": "ok", "app": "AppleDrop"})
            if path == "/api/files":
                base = f"http://{host_ip}:{port}"
                files_out = [
                    {**{k: it[k] for k in ("id", "name", "size", "size_str", "status")}, "url": f"{base}/download/{it['id']}"}
                    for it in file_queue.get_all()
                ]
                return self._send_json({"count": len(files_out), "files": files_out})
            if path.startswith("/api/latest") or path.startswith("/api/next"):
                item = file_queue.get_next_pending()
                return self._stream_file(item) if item else self._send_text("电脑端 AppleDrop 暂无待发送文件", status=404)
            if path.startswith("/download/"):
                item = file_queue.get_by_id(path.split("/download/")[1])
                return self._stream_file(item) if item else self._send_text("Not Found", status=404)
            if path == "/download_zip":
                return self._send_zip_archive()
            if path in ("/", "/index.html"):
                return self._render_mobile_portal()
            self._send_text("Not Found", status=404)

        def _send_text(self, text, status=200, content_type="text/plain; charset=utf-8"):
            payload = text.encode("utf-8") if isinstance(text, str) else text
            self.send_response(status)
            self.send_cors_headers()
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _send_json(self, obj):
            self._send_text(json.dumps(obj, ensure_ascii=False), content_type="application/json; charset=utf-8")

        def _stream_file(self, item):
            file_path = item["path"]
            if not os.path.exists(file_path):
                return self._send_text("File Missing", status=404)

            file_size = os.path.getsize(file_path)
            ext = os.path.splitext(item["name"])[1].lower() or ".bin"
            content_type = mimetypes.guess_type(file_path)[0]
            if not content_type:
                ext_map = {
                    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                    ".heic": "image/heic", ".heif": "image/heif", ".webp": "image/webp",
                    ".gif": "image/gif", ".mp4": "video/mp4", ".mov": "video/quicktime",
                }
                content_type = ext_map.get(ext, "application/octet-stream")
            range_header = self.headers.get("Range")
            start, end = 0, file_size - 1
            if range_header and range_header.startswith("bytes="):
                parts = range_header[6:].split("-")
                start = int(parts[0]) if parts[0] else 0
                end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1

            content_length = end - start + 1
            self.send_response(206 if range_header else 200)
            if range_header:
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_cors_headers()
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(content_length))
            self.send_header("Accept-Ranges", "bytes")
            fallback_ascii = f"AppleDrop_Media{ext}"
            safe_utf8 = urllib.parse.quote(item["name"])
            self.send_header("Content-Disposition", f'attachment; filename="{fallback_ascii}"; filename*=UTF-8\'\'{safe_utf8}')
            self.end_headers()

            bytes_sent, start_ts, last_notify = 0, time.time(), 0.0
            file_queue.update_status(item["id"], status="正在传输", progress=0)
            try:
                with open(file_path, "rb") as f:
                    f.seek(start)
                    remaining = content_length
                    while remaining > 0:
                        chunk = f.read(min(STREAM_CHUNK_SIZE, remaining))
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        remaining -= len(chunk)
                        bytes_sent += len(chunk)
                        now = time.time()
                        if now - last_notify > 0.25:
                            speed_str = f"{format_size(bytes_sent / max(now - start_ts, 0.001))}/s"
                            pct = int(((start + bytes_sent) / file_size) * 100)
                            file_queue.update_status(item["id"], status=f"传输中 {pct}%", progress=pct, speed=speed_str)
                            last_notify = now
                file_queue.update_status(item["id"], status="已完成", progress=100, speed="")
            except Exception:
                pass

        def _send_zip_archive(self):
            items = file_queue.get_all()
            if not items:
                return self._send_text("Empty Queue", status=404)
            if len(items) == 1:
                return self._stream_file(items[0])

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
                for it in items:
                    if os.path.exists(it["path"]):
                        zf.write(it["path"], arcname=it["name"])
            payload = buf.getvalue()
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Content-Disposition", "attachment; filename=AppleDrop_Bundle.zip")
            self.end_headers()
            self.wfile.write(payload)
            for it in items:
                file_queue.update_status(it["id"], status="已完成", progress=100)

        def _render_mobile_portal(self):
            items = file_queue.get_all()
            if not items:
                rows_html = '<div class="empty-box">电脑端暂未放入文件<br>请将视频或照片拖入电脑端 AppleDrop 窗口</div>'
            else:
                rows_html = "\n".join(
                    f'<div class="file-row"><div class="file-info"><div class="file-name">{it["name"]}</div>'
                    f'<div class="file-meta">{it["size_str"]} · {it["status"]}</div></div>'
                    f'<a class="link-action" href="/download/{it["id"]}" download="{it["name"]}">原画保存 ›</a></div>'
                    for it in items
                )
            zip_html = f'<a class="btn-space-black" href="/download_zip">打包下载全部 ({len(items)} 项)</a>' if len(items) > 1 else ""
            with open(MOBILE_HTML_PATH, "r", encoding="utf-8") as f:
                tpl = f.read()
            html = (
                tpl.replace("{{HOST_IP}}", host_ip)
                .replace("{{PORT}}", str(port))
                .replace("{{FILE_COUNT}}", str(len(items)))
                .replace("{{FILE_ROWS_HTML}}", rows_html)
                .replace("{{ZIP_BUTTON_HTML}}", zip_html)
            )
            self._send_text(html, content_type="text/html; charset=utf-8")

    return AppleDropHandler


class ServerThread:
    def __init__(self, file_queue, port=DEFAULT_PORT):
        self.file_queue = file_queue
        self.port = port
        self.host_ip = get_local_ip()
        self.httpd = None
        self.thread = None

    def start(self):
        handler_cls = make_handler(self.file_queue, self.host_ip, self.port)
        for p in range(self.port, self.port + 10):
            try:
                self.httpd = ThreadedHTTPServer(("0.0.0.0", p), handler_cls)
                self.port = p
                break
            except OSError:
                continue
        if not self.httpd:
            raise RuntimeError(f"无法绑定局域网服务端口 {self.port}")
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
