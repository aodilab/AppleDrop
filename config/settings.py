import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
SCRATCH_DIR = os.path.join(BASE_DIR, "scratch")

ICON_ICO_PATH = os.path.join(ASSETS_DIR, "app_icon_blue.ico")
ICON_PNG_PATH = os.path.join(ASSETS_DIR, "app_icon_blue.png")
MOBILE_HTML_PATH = os.path.join(TEMPLATES_DIR, "mobile_portal.html")

DEFAULT_PORT = 8899
WIN_WIDTH = 460
WIN_HEIGHT = 680
SUPERSAMPLE_SCALE = 2
STREAM_CHUNK_SIZE = 512 * 1024

VIDEO_EXTS = (".mp4", ".mov", ".m4v", ".mkv", ".avi")
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".heic", ".heif", ".gif", ".webp")

# Apple Neo Standard Design Tokens (.agents/skills/apple-neo-design/SKILL.md)
TOKENS = {
    "canvas_bg_hex": "#f5f5f7",
    "canvas_bg": (245, 245, 247, 255),
    "card_bg": (255, 255, 255, 255),
    "card_border": (235, 235, 240, 255),
    "hairline": (240, 242, 245, 255),
    "space_black": (29, 29, 31, 255),
    "space_black_hover": (48, 48, 52, 255),
    "text_body": (75, 75, 78, 255),
    "text_secondary": (134, 134, 139, 255),
    "neutral_pill": (244, 244, 246, 255),
    "neutral_pill_hover": (232, 232, 236, 255),
    "link_blue": (0, 102, 204, 255),
    "link_blue_hover": (0, 82, 168, 255),
    "semantic_blue_text": (0, 102, 204, 255),
    "semantic_blue_bg": (235, 244, 255, 255),
    "semantic_green_text": (27, 109, 47, 255),
    "semantic_green_bg": (233, 247, 238, 255),
    "semantic_red_text": (215, 0, 21, 255),
    "semantic_red_bg": (255, 235, 235, 255),
    "airdrop_blue": (0, 122, 255, 255),
    "airdrop_blue_hover": (0, 110, 235, 255),
}

# Engineering Line-Count Redlines (AGENTS.md Section IV)
CODE_LINE_RULES = {
    "src": {"golden": (120, 250), "max": 350},
    "templates": {"golden": (120, 250), "max": 350},
    "config": {"golden": (50, 150), "max": 250},
    "scripts": {"golden": (50, 150), "max": 250},
    "AGENTS.md": {"golden": (50, 65), "max": 80},
}
