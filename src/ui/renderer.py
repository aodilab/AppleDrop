from PIL import Image, ImageDraw, ImageFilter
from config.settings import SUPERSAMPLE_SCALE as S, TOKENS, VIDEO_EXTS, WIN_WIDTH, WIN_HEIGHT
from src.core.queue_manager import format_size
from src.ui.components import DrawPrimitives


class AppleNeoRenderer:
    """
    Renders the AppleDrop desktop viewport strictly adhering to
    .agents/skills/apple-neo-design/SKILL.md (Zero-Patch, Frameless Hierarchy, Zero-Cast Gray).
    """

    def __init__(self, width=WIN_WIDTH, height=WIN_HEIGHT):
        self.width = width
        self.height = height
        self.W = width * S
        self.H = height * S
        self.p = DrawPrimitives()

    def render(self, items, host_ip, port, scroll_y=0, hover_id=None, modal_open=False, copied_toast=False, drag_active=False):
        hitboxes = {}
        canvas = Image.new("RGBA", (self.W, self.H), TOKENS["canvas_bg"])
        draw = ImageDraw.Draw(canvas)

        # 1. Top Navigation Bar (54px pure white + 1px hairline)
        nav_h = 54
        draw.rectangle([0, 0, self.W, int(nav_h * S)], fill=TOKENS["card_bg"])
        self.p.hairline(draw, 0, nav_h, self.width)

        self.p.draw_brand_glyph(draw, 30, 27, r=13)
        self.p.text(draw, 51, 27, "AppleDrop", size=16, bold=True, color=TOKENS["space_black"], anchor="lm")
        ip_display = f"·  {host_ip}" if port == 8899 else f"·  {host_ip}:{port}"
        self.p.text(draw, 148, 28, ip_display, size=12, bold=False, color=TOKENS["text_secondary"], anchor="lm")

        btn_w, btn_h = 88, 30
        btn_x, btn_y = self.width - 18 - btn_w, 12
        is_conn_hover = hover_id == "btn_connect"
        self.p.pill(draw, btn_x, btn_y, btn_w, btn_h, bg=TOKENS["neutral_pill_hover"] if is_conn_hover else TOKENS["neutral_pill"])
        self.p.text(
            draw, btn_x + btn_w / 2, btn_y + btn_h / 2, "手机连接",
            size=12, bold=True, color=TOKENS["space_black"] if is_conn_hover else TOKENS["text_body"], anchor="mm"
        )
        hitboxes["btn_connect"] = (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h)

        pad_x = 18
        card_w = self.width - pad_x * 2

        if not items:
            self._render_zero_state(canvas, hitboxes, pad_x, card_w, hover_id, drag_active)
        else:
            self._render_queue_state(canvas, hitboxes, items, pad_x, card_w, scroll_y, hover_id, drag_active)

        if modal_open:
            canvas = self._render_modal_sheet(canvas, hitboxes, host_ip, port, hover_id, copied_toast)

        return canvas.resize((self.width, self.height), Image.Resampling.LANCZOS), hitboxes

    def _render_zero_state(self, canvas, hitboxes, pad_x, card_w, hover_id, drag_active):
        hero_y, hero_h = 74, 386
        border = TOKENS["space_black"] if drag_active else None
        self.p.shadow_card(canvas, pad_x, hero_y, card_w, hero_h, radius=20, border=border)
        draw = ImageDraw.Draw(canvas)

        cx = self.width // 2
        self.p.draw_hero_radar(draw, cx, hero_y + 114, active=(hover_id == "btn_choose" or drag_active))
        self.p.text(draw, cx, hero_y + 210, "拖入视频或照片", size=20, bold=True, color=TOKENS["space_black"], anchor="mm")
        self.p.text(draw, cx, hero_y + 240, "同一 Wi-Fi 原画直传  ·  零缓存复制  ·  秒存 iPhone 相册", size=12, color=TOKENS["text_secondary"], anchor="mm")

        cbtn_w, cbtn_h = 176, 42
        cbtn_x, cbtn_y = cx - cbtn_w // 2, hero_y + 278
        is_hover = hover_id == "btn_choose"
        self.p.shadow_card(
            canvas, cbtn_x, cbtn_y, cbtn_w, cbtn_h, radius=21,
            bg=TOKENS["airdrop_blue_hover"] if is_hover else TOKENS["airdrop_blue"],
            shadow_alpha=35, shadow_blur=10, offset_y=2
        )
        draw = ImageDraw.Draw(canvas)
        self.p.text(draw, cx, cbtn_y + cbtn_h / 2, "选择文件添加", size=13.5, bold=True, color=(255, 255, 255, 255), anchor="mm")
        hitboxes["btn_choose"] = (cbtn_x, cbtn_y, cbtn_x + cbtn_w, cbtn_y + cbtn_h)

        bento_y, bento_h = hero_y + hero_h + 16, 108
        bento_w = (card_w - 12) // 2
        self.p.shadow_card(canvas, pad_x, bento_y, bento_w, bento_h, radius=18)
        self.p.shadow_card(canvas, pad_x + bento_w + 12, bento_y, bento_w, bento_h, radius=18)
        draw = ImageDraw.Draw(canvas)

        lx = pad_x + 18
        self.p.text(draw, lx, bento_y + 24, "零内存损耗", size=11.5, bold=True, color=TOKENS["text_secondary"], anchor="lm")
        self.p.text(draw, lx, bento_y + 50, "100% 原始画质", size=15, bold=True, color=TOKENS["space_black"], anchor="lm")
        self.p.text(draw, lx, bento_y + 76, "直读磁盘路径，不建副本", size=11.5, color=TOKENS["text_secondary"], anchor="lm")

        rx = pad_x + bento_w + 12 + 18
        is_guide_hover = hover_id == "bento_guide"
        self.p.text(draw, rx, bento_y + 24, "iOS 快捷指令", size=11.5, bold=True, color=TOKENS["text_secondary"], anchor="lm")
        self.p.text(draw, rx, bento_y + 50, "一键直存系统相册", size=15, bold=True, color=TOKENS["space_black"], anchor="lm")
        self.p.text(
            draw, rx, bento_y + 76, "查看手机端 2 步配置 ›",
            size=11.5, bold=True,
            color=TOKENS["space_black"] if is_guide_hover else TOKENS["text_body"],
            anchor="lm"
        )
        hitboxes["bento_guide"] = (pad_x + bento_w + 12, bento_y, pad_x + card_w, bento_y + bento_h)

    def _render_queue_state(self, canvas, hitboxes, items, pad_x, card_w, scroll_y, hover_id, drag_active):
        top_y, top_h = 72, 78
        is_add_hover = hover_id == "btn_choose"
        border = TOKENS["space_black"] if drag_active else None
        self.p.shadow_card(canvas, pad_x, top_y, card_w, top_h, radius=18, border=border)
        draw = ImageDraw.Draw(canvas)

        self.p.draw_neutral_slot_plus(draw, pad_x + 34, top_y + top_h // 2, r=19, hover=is_add_hover)
        self.p.text(draw, pad_x + 66, top_y + 28, "继续拖入视频或照片", size=14.5, bold=True, color=TOKENS["space_black"], anchor="lm")
        self.p.text(draw, pad_x + 66, top_y + 50, "支持多文件批量投递  ·  零缓存直传", size=11.5, color=TOKENS["text_secondary"], anchor="lm")
        self.p.text(
            draw, pad_x + card_w - 18, top_y + top_h // 2, "选择文件 ›",
            size=12.5, bold=True, color=TOKENS["link_blue_hover"] if is_add_hover else TOKENS["link_blue"], anchor="rm"
        )
        hitboxes["btn_choose"] = (pad_x, top_y, pad_x + card_w, top_y + top_h)

        sec_y = top_y + top_h + 24
        total_bytes = sum(it.get("size", 0) for it in items)
        self.p.text(draw, pad_x + 2, sec_y, "待发送队列", size=16, bold=True, color=TOKENS["space_black"], anchor="lm")
        self.p.text(draw, pad_x + 92, sec_y + 1, f"{len(items)} 项  ·  {format_size(total_bytes)}", size=12, color=TOKENS["text_secondary"], anchor="lm")
        is_clr_hover = hover_id == "btn_clear"
        self.p.text(
            draw, pad_x + card_w - 2, sec_y, "清空队列",
            size=12.5, bold=False, color=TOKENS["space_black"] if is_clr_hover else TOKENS["text_secondary"], anchor="rm"
        )
        hitboxes["btn_clear"] = (pad_x + card_w - 64, sec_y - 12, pad_x + card_w, sec_y + 12)

        card_top = sec_y + 18
        row_h = 68
        container_h = max(row_h, min(len(items), 6) * row_h)
        self.p.shadow_card(canvas, pad_x, card_top, card_w, container_h, radius=20)
        draw = ImageDraw.Draw(canvas)

        start_idx = max(0, int(scroll_y // row_h))
        for idx, it in enumerate(items[start_idx : start_idx + 6]):
            ry = card_top + idx * row_h
            if idx > 0:
                self.p.hairline(draw, pad_x + 64, ry, pad_x + card_w - 16)

            is_video = it["name"].lower().endswith(VIDEO_EXTS)
            self.p.draw_monochrome_media_icon(draw, pad_x + 34, ry + row_h // 2, is_video=is_video)
            right_limit_x = self.p.draw_row_status(draw, it["status"], pad_x + card_w - 50, ry)

            fname = it["name"]
            max_name_w = max(120, right_limit_x - (pad_x + 64))
            fit_sz = self.p.fit_text_size(draw, fname, max_w=max_name_w, start_size=14.0, min_size=10.5, bold=True)
            self.p.text(draw, pad_x + 64, ry + 24, fname, size=fit_sz, bold=True, color=TOKENS["space_black"], anchor="lm")

            media_tag = "原画视频" if is_video else "原始图像"
            self.p.text(draw, pad_x + 64, ry + 46, f"{it['size_str']}  ·  {media_tag}", size=11.5, color=TOKENS["text_secondary"], anchor="lm")

            del_id = f"del_{it['id']}"
            dx, dy = pad_x + card_w - 26, ry + row_h // 2
            self.p.draw_circle_close(draw, dx, dy, r=12, hover=(hover_id == del_id), subtle=True)
            hitboxes[del_id] = (dx - 14, dy - 14, dx + 14, dy + 14)

    def _render_modal_sheet(self, canvas, hitboxes, host_ip, port, hover_id, copied_toast):
        blurred = canvas.filter(ImageFilter.GaussianBlur(10 * S))
        overlay = Image.new("RGBA", (self.W, self.H), (20, 20, 24, 76))
        canvas = Image.alpha_composite(blurred, overlay)

        hitboxes.clear()
        hitboxes["modal_backdrop"] = (0, 0, self.width, self.height)

        mw, mh = 412, 488
        mx, my = (self.width - mw) // 2, (self.height - mh) // 2
        self.p.shadow_card(canvas, mx, my, mw, mh, radius=24, shadow_alpha=36, shadow_blur=22, offset_y=6)
        draw = ImageDraw.Draw(canvas)
        hitboxes["modal_card_block"] = (mx, my, mx + mw, my + mh)

        self.p.text(draw, mx + 24, my + 26, f"局域网直连  ·  {host_ip}", size=11.5, bold=True, color=TOKENS["link_blue"], anchor="lm")
        self.p.text(draw, mx + 24, my + 48, "iPhone 手机连接", size=19, bold=True, color=TOKENS["space_black"], anchor="lm")

        ccx, ccy = mx + mw - 34, my + 38
        self.p.draw_circle_close(draw, ccx, ccy, r=14, hover=(hover_id == "modal_close"), subtle=False)
        hitboxes["modal_close"] = (ccx - 16, ccy - 16, ccx + 16, ccy + 16)
        self.p.hairline(draw, mx + 24, my + 72, mx + mw - 24)

        self.p.paste_qr_code(canvas, f"http://{host_ip}:{port}", mx + mw // 2, my + 86, size_px=128)
        draw = ImageDraw.Draw(canvas)
        self.p.text(draw, mx + mw // 2, my + 228, "相机扫码可在 Safari 直接查看或下载原片", size=12, color=TOKENS["text_secondary"], anchor="mm")
        self.p.hairline(draw, mx + 24, my + 248, mx + mw - 24)

        self.p.text(draw, mx + 24, my + 268, "01", size=12.5, bold=True, color=TOKENS["space_black"], anchor="lm")
        self.p.text(draw, mx + 50, my + 268, "iPhone 打开「快捷指令」点 +，添加「获取 URL 的内容」", size=12.5, color=TOKENS["text_body"], anchor="lm")

        api_url = f"http://{host_ip}:{port}/api/latest"
        ub_x, ub_y, ub_w, ub_h = mx + 24, my + 288, mw - 48, 36
        self.p.rounded_box(draw, ub_x, ub_y, ub_w, ub_h, radius=10, bg=TOKENS["neutral_pill"])
        self.p.text(draw, ub_x + 12, ub_y + ub_h / 2, api_url, size=11.5, bold=True, mono=True, color=TOKENS["space_black"], anchor="lm")

        cp_txt = "已复制 ✓" if copied_toast else "复制网址"
        cp_col = TOKENS["semantic_green_text"] if copied_toast else (TOKENS["link_blue_hover"] if hover_id == "btn_copy_url" else TOKENS["link_blue"])
        self.p.text(draw, ub_x + ub_w - 12, ub_y + ub_h / 2, cp_txt, size=12, bold=True, color=cp_col, anchor="rm")
        hitboxes["btn_copy_url"] = (ub_x + ub_w - 76, ub_y, ub_x + ub_w, ub_y + ub_h)

        self.p.hairline(draw, mx + 24, my + 338, mx + mw - 24)
        self.p.text(draw, mx + 24, my + 358, "02", size=12.5, bold=True, color=TOKENS["space_black"], anchor="lm")
        self.p.text(draw, mx + 50, my + 358, "添加「存储到相簿」，添加到主屏幕即可一键收片", size=12.5, color=TOKENS["text_body"], anchor="lm")

        act_y, act_h, wbtn_w = my + mh - 58, 40, 122
        wbtn_x = mx + 24
        self.p.pill(draw, wbtn_x, act_y, wbtn_w, act_h, bg=TOKENS["neutral_pill_hover"] if hover_id == "btn_open_web" else TOKENS["neutral_pill"])
        self.p.text(draw, wbtn_x + wbtn_w / 2, act_y + act_h / 2, "网页端预览", size=13, bold=True, color=TOKENS["text_body"], anchor="mm")
        hitboxes["btn_open_web"] = (wbtn_x, act_y, wbtn_x + wbtn_w, act_y + act_h)

        dbtn_x, dbtn_w = wbtn_x + wbtn_w + 12, mw - 48 - wbtn_w - 12
        self.p.pill(draw, dbtn_x, act_y, dbtn_w, act_h, bg=TOKENS["space_black_hover"] if hover_id == "modal_done" else TOKENS["space_black"])
        self.p.text(draw, dbtn_x + dbtn_w / 2, act_y + act_h / 2, "完成", size=13.5, bold=True, color=(255, 255, 255, 255), anchor="mm")
        hitboxes["modal_done"] = (dbtn_x, act_y, dbtn_x + dbtn_w, act_y + act_h)

        return canvas
