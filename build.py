import sys
from src.core.queue_manager import check_existing_instance_and_send
from src.ui.desktop_app import launch_desktop_app
from scripts.icon_builder import build_app_icons, create_desktop_shortcut
from scripts.visual_audit import audit_code_lines, render_audit_snapshots


def main():
    args = sys.argv[1:]

    if "--icon" in args:
        build_app_icons()
        print("Icons generated in assets/.")
        return

    if "--shortcut" in args:
        path = create_desktop_shortcut()
        print(f"Shortcut created: {path}")
        return

    if "--audit" in args:
        out_dir = None
        idx = args.index("--audit")
        if idx + 1 < len(args) and not args[idx + 1].startswith("--"):
            out_dir = args[idx + 1]
        paths = render_audit_snapshots(out_dir)
        for p in paths:
            print(f"Audit snapshot: {p}")
        results, violations = audit_code_lines()
        for rel, lines, golden, max_l, status in results:
            print(f"[LINE AUDIT] {rel:32s} | {lines:3d} lines | golden {golden:7s} | { max_l:6s} | {status}")
        if violations:
            raise SystemExit(f"Line count violations: {violations}")
        return

    if "--all" in args:
        build_app_icons()
        create_desktop_shortcut()
        render_audit_snapshots()
        _, violations = audit_code_lines()
        if violations:
            raise SystemExit(f"Line count violations: {violations}")
        print("All build and audit tasks completed.")
        return

    # Filter out CLI flags; remaining arguments are dropped file paths
    dropped_files = [a for a in args if not a.startswith("--")]

    if check_existing_instance_and_send(dropped_files):
        sys.exit(0)

    launch_desktop_app(initial_files=dropped_files)


if __name__ == "__main__":
    main()
