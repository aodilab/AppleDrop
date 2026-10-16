import os
import pathlib
from config.settings import BASE_DIR, CODE_LINE_RULES, SCRATCH_DIR, WIN_WIDTH, WIN_HEIGHT
from src.ui.renderer import AppleNeoRenderer


def render_audit_snapshots(output_dir=None):
    """Render 3 standard UI states (Empty, Queue with long names, Modal) for visual self-audit."""
    target_dir = output_dir or SCRATCH_DIR
    os.makedirs(target_dir, exist_ok=True)
    renderer = AppleNeoRenderer(WIN_WIDTH, WIN_HEIGHT)

    # 1. Zero state
    img_empty, _ = renderer.render([], "192.168.1.2", 8899)
    p_empty = os.path.join(target_dir, "audit_empty.png")
    img_empty.save(p_empty)

    # 2. Queue state with long boundary filenames (testing zero ellipsis truncation)
    sample_items = [
        {"id": "1", "name": "赵云_王者出装箱_实操演示视频.mp4", "size": 9084899, "size_str": "8.66 MB", "status": "传输中 68%"},
        {"id": "2", "name": "AODILAB_头像_高清2K.png", "size": 1117712, "size_str": "1.07 MB", "status": "已完成"},
        {"id": "3", "name": "IMG_8842_4K60FPS_杜比视界原片.MOV", "size": 154829100, "size_str": "147.66 MB", "status": "等待发送"},
    ]
    img_queue, _ = renderer.render(sample_items, "192.168.1.2", 8899)
    p_queue = os.path.join(target_dir, "audit_queue.png")
    img_queue.save(p_queue)

    # 3. In-window frosted glass modal state
    img_modal, _ = renderer.render(sample_items, "192.168.1.2", 8899, modal_open=True)
    p_modal = os.path.join(target_dir, "audit_modal.png")
    img_modal.save(p_modal)

    return [p_empty, p_queue, p_modal]


def audit_code_lines():
    """Verify all project files strictly comply with AGENTS.md Section IV line-count redlines."""
    base = pathlib.Path(BASE_DIR)
    results = []
    violations = []

    targets = [
        ("AGENTS.md", [base / "AGENTS.md"]),
        ("config", sorted((base / "config").rglob("*.py"))),
        ("scripts", sorted((base / "scripts").rglob("*.py"))),
        ("src", [p for p in sorted((base / "src").rglob("*.py")) if p.name != "__init__.py"]),
        ("templates", sorted((base / "templates").rglob("*.html"))),
    ]

    for category, files in targets:
        rule = CODE_LINE_RULES[category]
        g_min, g_max = rule["golden"]
        hard_max = rule["max"]
        for fp in files:
            if not fp.exists():
                continue
            lines = len(fp.read_text(encoding="utf-8").splitlines())
            rel = str(fp.relative_to(base)).replace("\\", "/")
            in_golden = g_min <= lines <= g_max
            under_redline = lines <= hard_max
            status = "GOLDEN" if in_golden else ("OK (<=MAX)" if under_redline else "VIOLATION")
            results.append((rel, lines, f"{g_min}~{g_max}", f"<={hard_max}", status))
            if not under_redline or not in_golden:
                violations.append(f"{rel}: {lines} lines (expected {g_min}~{g_max}, max {hard_max})")

    return results, violations
