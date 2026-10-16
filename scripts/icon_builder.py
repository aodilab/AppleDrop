import os
import sys
import win32com.client
from PIL import Image, ImageDraw
from config.settings import ASSETS_DIR, BASE_DIR, ICON_ICO_PATH, ICON_PNG_PATH


def build_app_icons():
    """Generate multi-resolution Space Black / Apple Blue AirDrop icons in assets/."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)
    for y in range(size):
        # Authentic Apple AirDrop blue gradient (#008cf8 -> #0062e3)
        g = int(140 - 42 * (y / size))
        b = int(255 - 28 * (y / size))
        bg_draw.line([(0, y), (size, y)], fill=(0, g, b, 255))

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(8, 8), (size - 8, size - 8)], radius=56, fill=255)
    img.paste(bg, (0, 0), mask)

    fg_draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2 + 10
    for r_val, w_val, alpha in [(46, 9, 245), (72, 9, 185), (98, 8, 125)]:
        bbox = [cx - r_val, cy - r_val, cx + r_val, cy + r_val]
        fg_draw.arc(bbox, start=215, end=325, fill=(255, 255, 255, alpha), width=w_val)

    ay = cy - 8
    arrow_pts = [
        (cx, ay - 28),
        (cx - 24, ay),
        (cx - 10, ay),
        (cx - 10, ay + 36),
        (cx + 10, ay + 36),
        (cx + 10, ay),
        (cx + 24, ay),
    ]
    fg_draw.polygon(arrow_pts, fill=(255, 255, 255, 255))

    img.save(ICON_PNG_PATH, "PNG")
    img.save(ICON_ICO_PATH, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])


def create_desktop_shortcut():
    """Create AppleDrop.lnk on Windows Desktop pointing to build.py."""
    if not os.path.exists(ICON_ICO_PATH):
        build_app_icons()

    desktop_dir = os.path.join(os.environ["USERPROFILE"], "Desktop")
    shortcut_path = os.path.join(desktop_dir, "AppleDrop.lnk")
    build_py = os.path.join(BASE_DIR, "build.py")

    pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pythonw_path):
        pythonw_path = sys.executable

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.TargetPath = pythonw_path
    shortcut.Arguments = f'"{build_py}"'
    shortcut.WorkingDirectory = BASE_DIR
    shortcut.IconLocation = f"{ICON_ICO_PATH}, 0"
    shortcut.Description = "AppleDrop - 局域网无损直传 iPhone 相册 (支持直接将视频拖入图标)"
    shortcut.Save()
    try:
        import ctypes
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, 0, 0)
    except Exception:
        pass
    return shortcut_path
