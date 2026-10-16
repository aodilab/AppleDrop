import os
import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from config.settings import SUPERSAMPLE_SCALE as S, TOKENS


class DrawPrimitives:
    """Low-level 2x supersampled drawing primitives and vector icons following Apple Neo Design."""

    def __init__(self):
        self._fonts = {}

    def font(self, size, bold=False, mono=False):
        key = (size, bold, mono)
        if key not in self._fonts:
            scaled = int(size * S)
            fonts_dir = r"C:\Windows\Fonts"
            if mono:
                names = ["consolab.ttf", "consola.ttf", "msyh.ttc"]
            elif bold:
                names = ["msyhbd.ttc", "segoeuib.ttf", "simhei.ttf"]
            else:
                names = ["msyh.ttc", "segoeui.ttf", "simsun.ttc"]
            loaded = None
            for fn in names:
                p = os.path.join(fonts_dir, fn)
                if os.path.exists(p):
                    try:
                        loaded = ImageFont.truetype(p, scaled)
                        break
                    except Exception:
                        pass
            self._fonts[key] = loaded or ImageFont.load_default()
        return self._fonts[key]

    def text(self, draw, x, y, txt, size=14, color=TOKENS["space_black"], bold=False, mono=False, anchor="la"):
        f = self.font(size, bold=bold, mono=mono)
        draw.text((int(x * S), int(y * S)), txt, font=f, fill=color, anchor=anchor)

    def measure(self, draw, txt, size=14, bold=False, mono=False):
        f = self.font(size, bold=bold, mono=mono)
        bbox = draw.textbbox((0, 0), txt, font=f)
        return (bbox[2] - bbox[0]) / S, (bbox[3] - bbox[1]) / S

    def fit_text_size(self, draw, txt, max_w, start_size=14.0, min_size=10.5, bold=True):
        """Dynamically scale font size so long filenames never truncate with ellipsis."""
        sz = start_size
        while sz > min_size:
            w, _ = self.measure(draw, txt, size=sz, bold=bold)
            if w <= max_w:
                return sz
            sz -= 0.5
        return min_size

    def pill(self, draw, x, y, w, h, bg, border=None):
        X, Y, W, H = int(x * S), int(y * S), int(w * S), int(h * S)
        draw.rounded_rectangle(
            [X, Y, X + W, Y + H], radius=H // 2, fill=bg, outline=border, width=S if border else 0
        )

    def rounded_box(self, draw, x, y, w, h, radius, bg, border=None):
        X, Y, W, H = int(x * S), int(y * S), int(w * S), int(h * S)
        draw.rounded_rectangle(
            [X, Y, X + W, Y + H], radius=int(radius * S), fill=bg, outline=border, width=S if border else 0
        )

    def hairline(self, draw, x1, y, x2):
        Y = int(y * S)
        draw.line([(int(x1 * S), Y), (int(x2 * S), Y)], fill=TOKENS["hairline"], width=max(1, S // 2))

    def shadow_card(self, base_img, x, y, w, h, radius=20, bg=TOKENS["card_bg"],
                    border=None, shadow_alpha=9, shadow_blur=12, offset_y=2):
        """Apple Neo card with subtle 0 2px 12px rgba(0,0,0,0.03) ambient shadow."""
        X, Y, W, H = int(x * S), int(y * S), int(w * S), int(h * S)
        R = int(radius * S)
        pad = int((shadow_blur + 10) * S)

        patch = Image.new("RGBA", (W + pad * 2, H + pad * 2), (0, 0, 0, 0))
        pdraw = ImageDraw.Draw(patch)

        if shadow_alpha > 0:
            sy = pad + int(offset_y * S)
            pdraw.rounded_rectangle([pad, sy, pad + W, sy + H], radius=R, fill=(0, 0, 0, shadow_alpha))
            patch = patch.filter(ImageFilter.GaussianBlur(shadow_blur * S / 2))
            pdraw = ImageDraw.Draw(patch)

        pdraw.rounded_rectangle(
            [pad, pad, pad + W, pad + H], radius=R, fill=bg, outline=border, width=S if border else 0
        )
        base_img.alpha_composite(patch, (X - pad, Y - pad))

    def draw_brand_glyph(self, draw, cx, cy, r=13):
        """Apple Blue squircle with minimalist white AirDrop signal arcs."""
        CX, CY, R = int(cx * S), int(cy * S), int(r * S)
        draw.rounded_rectangle([CX - R, CY - R, CX + R, CY + R], radius=int(R * 0.46), fill=TOKENS["airdrop_blue"])
        for ratio, alpha in [(0.35, 255), (0.58, 200), (0.78, 135)]:
            ar = int(R * ratio)
            bbox = [CX - ar, CY - ar + int(2 * S), CX + ar, CY + ar + int(2 * S)]
            draw.arc(bbox, start=215, end=325, fill=(255, 255, 255, alpha), width=max(2, int(2 * S)))
        ay = CY + int(2 * S)
        aw, ah = int(R * 0.25), int(R * 0.28)
        draw.polygon([(CX, ay - ah), (CX - aw, ay + int(ah * 0.3)), (CX + aw, ay + int(ah * 0.3))], fill=(255, 255, 255, 255))

    def draw_hero_radar(self, draw, cx, cy, active=False):
        """Concentric Apple Blue radar rings with AirDrop Blue center core."""
        CX, CY = int(cx * S), int(cy * S)
        rings = [
            (60, (0, 122, 255, 12 if not active else 22)),
            (46, (0, 122, 255, 24 if not active else 38)),
            (33, TOKENS["airdrop_blue_hover"] if active else TOKENS["airdrop_blue"]),
        ]
        for r_px, col in rings:
            r = int(r_px * S)
            draw.ellipse([CX - r, CY - r, CX + r, CY + r], fill=col)

        for r_px, alpha in [(11, 255), (19, 210), (27, 145)]:
            ar = int(r_px * S)
            bbox = [CX - ar, CY - ar + int(4 * S), CX + ar, CY + ar + int(4 * S)]
            draw.arc(bbox, start=212, end=328, fill=(255, 255, 255, alpha), width=int(2.4 * S))

        ay = CY + int(2 * S)
        hw, hh, sw, sh = int(8 * S), int(8.5 * S), int(3 * S), int(10.5 * S)
        pts = [(CX, ay - hh), (CX - hw, ay), (CX - sw, ay), (CX - sw, ay + sh), (CX + sw, ay + sh), (CX + sw, ay), (CX + hw, ay)]
        draw.polygon(pts, fill=(255, 255, 255, 255))

    def draw_neutral_slot_plus(self, draw, cx, cy, r=19, hover=False):
        """Taboo 4 compliant: borderless solid neutral circle with subtle + sign."""
        CX, CY, R = int(cx * S), int(cy * S), int(r * S)
        bg = TOKENS["neutral_pill_hover"] if hover else TOKENS["neutral_pill"]
        draw.ellipse([CX - R, CY - R, CX + R, CY + R], fill=bg)
        plen = int(6.5 * S)
        col = TOKENS["space_black"]
        draw.line([(CX - plen, CY), (CX + plen, CY)], fill=col, width=int(2 * S))
        draw.line([(CX, CY - plen), (CX, CY + plen)], fill=col, width=int(2 * S))

    def draw_monochrome_media_icon(self, draw, cx, cy, is_video=True):
        """Zero-cast neutral circle with monochrome vector glyph (no rainbow icon patches)."""
        CX, CY, R = int(cx * S), int(cy * S), int(19 * S)
        draw.ellipse([CX - R, CY - R, CX + R, CY + R], fill=TOKENS["neutral_pill"])
        col = TOKENS["text_body"]
        if is_video:
            th = int(6.5 * S)
            pts = [(CX - int(3 * S), CY - th), (CX - int(3 * S), CY + th), (CX + int(6 * S), CY)]
            draw.polygon(pts, fill=col)
        else:
            fw, fh = int(7.5 * S), int(6 * S)
            draw.rounded_rectangle([CX - fw, CY - fh, CX + fw, CY + fh], radius=int(2 * S), outline=col, width=int(1.6 * S))
            draw.line([(CX - fw + int(2 * S), CY + fh - int(2 * S)), (CX, CY), (CX + fw - int(2 * S), CY + fh - int(2 * S))],
                      fill=col, width=int(1.5 * S))

    def draw_circle_close(self, draw, cx, cy, r=13, hover=False, subtle=False):
        CX, CY, R = int(cx * S), int(cy * S), int(r * S)
        if subtle:
            bg = TOKENS["semantic_red_bg"] if hover else TOKENS["neutral_pill"]
            fg = TOKENS["semantic_red_text"] if hover else TOKENS["text_secondary"]
            xr = int(3.5 * S)
        else:
            bg = TOKENS["neutral_pill_hover"] if hover else TOKENS["neutral_pill"]
            fg = TOKENS["space_black"]
            xr = int(4.2 * S)
        draw.ellipse([CX - R, CY - R, CX + R, CY + R], fill=bg)
        draw.line([(CX - xr, CY - xr), (CX + xr, CY + xr)], fill=fg, width=int(1.8 * S))
        draw.line([(CX + xr, CY - xr), (CX - xr, CY + xr)], fill=fg, width=int(1.8 * S))

    def draw_row_status(self, draw, status_str, right_anchor_x, row_top):
        """Conditional semantic color badge: neutral gray by default, color only on active/done."""
        if status_str == "已完成":
            txt, bg, fg = "已存相册", TOKENS["semantic_green_bg"], TOKENS["semantic_green_text"]
        elif "传输" in status_str:
            parts = status_str.split(" ")
            txt = f"{parts[0]} {parts[1]}" if len(parts) > 1 else status_str
            bg, fg = TOKENS["semantic_blue_bg"], TOKENS["semantic_blue_text"]
        else:
            txt = "等待接收"
            w, _ = self.measure(draw, txt, size=11.5, bold=False)
            self.text(draw, right_anchor_x - 2, row_top + 34, txt, size=11.5, bold=False, color=TOKENS["text_secondary"], anchor="rm")
            return right_anchor_x - w - 16

        w, _ = self.measure(draw, txt, size=11, bold=True)
        bx = right_anchor_x - (w + 14)
        self.rounded_box(draw, bx, row_top + 22, w + 14, 24, radius=6, bg=bg)
        self.text(draw, bx + (w + 14) / 2, row_top + 34, txt, size=11, bold=True, color=fg, anchor="mm")
        return bx - 12

    def paste_qr_code(self, canvas, url, center_x, top_y, size_px=128):
        qr_size = size_px * S
        qr = qrcode.QRCode(version=1, box_size=4, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA").resize((qr_size, qr_size), Image.Resampling.NEAREST)
        canvas.alpha_composite(qr_img, (int(center_x * S) - qr_size // 2, int(top_y * S)))
