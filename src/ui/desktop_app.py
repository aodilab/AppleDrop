import os
import sys
import ctypes
import webbrowser
import winsound
import tkinter as tk
from tkinter import filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import ImageTk

from config.settings import DEFAULT_PORT, ICON_ICO_PATH, TOKENS, WIN_WIDTH, WIN_HEIGHT
from src.core.queue_manager import FileQueue
from src.core.http_server import ServerThread
from src.ui.renderer import AppleNeoRenderer


class AppleDropApp:
    """Main desktop window controller powered by TkinterDnD and AppleNeoRenderer."""

    def __init__(self, root, initial_files=None):
        self.root = root
        self.root.title("AppleDrop")
        self.root.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=TOKENS["canvas_bg_hex"])

        if os.path.exists(ICON_ICO_PATH):
            try:
                self.root.iconbitmap(ICON_ICO_PATH)
            except Exception:
                pass

        self.file_queue = FileQueue()
        self.server_thread = ServerThread(self.file_queue, port=DEFAULT_PORT)
        self.server_thread.start()

        self.renderer = AppleNeoRenderer(WIN_WIDTH, WIN_HEIGHT)
        self.scroll_y = 0
        self.hover_id = None
        self.modal_open = False
        self.copied_toast = False
        self.drag_active = False
        self.hitboxes = {}
        self.tk_img = None

        self.last_completed_count = 0
        self.last_queue_version = -1

        self.canvas = tk.Canvas(
            self.root, width=WIN_WIDTH, height=WIN_HEIGHT,
            bg=TOKENS["canvas_bg_hex"], highlightthickness=0, bd=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas_img_id = self.canvas.create_image(0, 0, anchor="nw")

        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Leave>", self.on_mouse_leave)
        self.canvas.bind("<Button-1>", self.on_mouse_click)
        self.canvas.bind_all("<MouseWheel>", self.on_mouse_wheel)

        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<DropEnter>>", self.on_drag_enter)
        self.root.dnd_bind("<<DropLeave>>", self.on_drag_leave)
        self.root.dnd_bind("<<Drop>>", self.on_tkdnd_drop)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        if initial_files:
            self.file_queue.add_files(initial_files)

        self.redraw()
        self.root.after(50, self._present_window)
        self.poll_queue()

    def _present_window(self):
        """Force the window to be visible, restored from minimize, and brought to front."""
        try:
            self.root.wm_state("normal")
            self.root.deiconify()
            self.root.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            self.root.attributes("-topmost", True)
            self.root.lift()
            self.root.focus_force()
            self.root.after(180, lambda: self.root.attributes("-topmost", False))
        except Exception:
            pass

    def redraw(self):
        items = self.file_queue.get_all()
        pil_img, self.hitboxes = self.renderer.render(
            items=items, host_ip=self.server_thread.host_ip, port=self.server_thread.port,
            scroll_y=self.scroll_y, hover_id=self.hover_id, modal_open=self.modal_open,
            copied_toast=self.copied_toast, drag_active=self.drag_active,
        )
        self.tk_img = ImageTk.PhotoImage(pil_img)
        self.canvas.itemconfig(self.canvas_img_id, image=self.tk_img)

    def _hit_test(self, x, y):
        if self.modal_open:
            for k in ("modal_close", "btn_copy_url", "btn_open_web", "modal_done"):
                box = self.hitboxes.get(k)
                if box and box[0] <= x <= box[2] and box[1] <= y <= box[3]:
                    return k
            cbox = self.hitboxes.get("modal_card_block")
            if cbox and cbox[0] <= x <= cbox[2] and cbox[1] <= y <= cbox[3]:
                return None
            return "modal_backdrop"
        for k, box in self.hitboxes.items():
            if box[0] <= x <= box[2] and box[1] <= y <= box[3]:
                return k
        return None

    def on_mouse_move(self, event):
        hit = self._hit_test(event.x, event.y)
        self.root.configure(cursor="hand2" if (hit and hit != "modal_backdrop") else "")
        if hit != self.hover_id:
            self.hover_id = hit
            self.redraw()

    def on_mouse_leave(self, event):
        if self.hover_id is not None:
            self.hover_id = None
            self.root.configure(cursor="")
            self.redraw()

    def on_mouse_click(self, event):
        hit = self._hit_test(event.x, event.y)
        if not hit:
            return
        if hit in ("btn_connect", "bento_guide"):
            self.modal_open, self.hover_id = True, None
            self.redraw()
        elif hit in ("modal_close", "modal_done", "modal_backdrop"):
            self.modal_open, self.copied_toast, self.hover_id = False, False, None
            self.redraw()
        elif hit == "btn_copy_url":
            api_url = f"http://{self.server_thread.host_ip}:{self.server_thread.port}/api/latest"
            self.root.clipboard_clear()
            self.root.clipboard_append(api_url)
            self.copied_toast = True
            self.redraw()
            self.root.after(1600, self._reset_copied_toast)
        elif hit == "btn_open_web":
            webbrowser.open(f"http://{self.server_thread.host_ip}:{self.server_thread.port}")
        elif hit == "btn_choose":
            self.choose_files()
        elif hit == "btn_clear":
            self.scroll_y = 0
            self.file_queue.clear_all()
        elif hit.startswith("del_"):
            self.file_queue.remove(hit.split("del_")[1])

    def _reset_copied_toast(self):
        if self.copied_toast:
            self.copied_toast = False
            self.redraw()

    def on_mouse_wheel(self, event):
        if self.modal_open:
            return
        items = self.file_queue.get_all()
        if len(items) <= 6:
            if self.scroll_y != 0:
                self.scroll_y = 0
                self.redraw()
            return
        max_scroll = max(0, (len(items) - 6) * 68)
        new_scroll = max(0, min(max_scroll, self.scroll_y + int(-1 * (event.delta / 120) * 68)))
        if new_scroll != self.scroll_y:
            self.scroll_y = new_scroll
            self.redraw()

    def on_drag_enter(self, event):
        if not self.drag_active:
            self.drag_active = True
            self.redraw()

    def on_drag_leave(self, event):
        if self.drag_active:
            self.drag_active = False
            self.redraw()

    def on_tkdnd_drop(self, event):
        self.drag_active = False
        if not event or not event.data:
            return self.redraw()
        try:
            raw_files = self.root.tk.splitlist(event.data)
        except Exception:
            raw_files = [event.data]
        file_paths = []
        for f in raw_files:
            if isinstance(f, bytes):
                try:
                    f = os.fsdecode(f)
                except Exception:
                    f = f.decode("utf-8", errors="ignore")
            file_paths.append(str(f))
        self.file_queue.add_files(file_paths)
        self.redraw()

    def choose_files(self):
        files = filedialog.askopenfilenames(
            title="选择要发送给苹果手机的视频或照片",
            filetypes=[
                ("所有支持的媒体", "*.mp4 *.mov *.m4v *.mkv *.jpg *.jpeg *.png *.heic *.heif *.gif *.webp"),
                ("视频文件", "*.mp4 *.mov *.m4v *.mkv *.avi"),
                ("图片照片", "*.jpg *.jpeg *.png *.heic *.heif *.gif *.webp"),
                ("所有文件", "*.*"),
            ],
        )
        if files:
            self.file_queue.add_files(files)

    def poll_queue(self):
        if self.file_queue.consume_wakeup():
            self._present_window()
        current_ver = self.file_queue.version
        if current_ver != self.last_queue_version:
            self.last_queue_version = current_ver
            items = self.file_queue.get_all()
            completed_count = sum(1 for it in items if it["status"] == "已完成")
            if completed_count > self.last_completed_count:
                try:
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
                except Exception:
                    pass
            self.last_completed_count = completed_count
            self.redraw()
        self.root.after(100, self.poll_queue)

    def on_close(self):
        try:
            self.server_thread.stop()
        except Exception:
            pass
        self.root.destroy()
        sys.exit(0)


def launch_desktop_app(initial_files=None):
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = TkinterDnD.Tk()
    AppleDropApp(root, initial_files=initial_files)
    root.mainloop()
