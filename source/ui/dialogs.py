import tkinter as tk
from tkinter import ttk
import threading
import os
from typing import Callable


def show_text_window(root: tk.Tk, title: str, text: str) -> None:
    w = tk.Toplevel(root)
    w.title(title)
    txt = tk.Text(w, wrap="none")
    txt.insert("1.0", text)
    txt.config(state="disabled")
    txt.pack(fill="both", expand=True)


def make_ask_fn(root: tk.Tk, stop_ev: threading.Event) -> Callable[[str], str]:
    """Return an ask_fn(prompt) that shows a non-modal dialog on the main thread.

    The returned function blocks the caller thread until the user chooses an option
    or `stop_ev` is set. If `stop_ev` is set while waiting, it returns 'a' (abort).
    """

    def ask_fn(prompt: str) -> str:
        ev = threading.Event()
        res = {"value": ""}

        def _show_dialog(buttons):
            top = tk.Toplevel(root)
            top.title("입력 요청")
            top.transient(root)

            lbl = ttk.Label(top, text=prompt, wraplength=400)
            lbl.pack(padx=12, pady=8)

            def choose(v: str) -> None:
                res["value"] = v
                try:
                    top.destroy()
                finally:
                    ev.set()

            f = ttk.Frame(top)
            f.pack(pady=8)
            for lab, val in buttons:
                ttk.Button(f, text=lab, command=lambda v=val: choose(v)).pack(
                    side="left", padx=6
                )

            # map window close to abort
            top.protocol("WM_DELETE_WINDOW", lambda: choose("a"))

            # position at main window top-left
            try:
                root.update_idletasks()
                rx = root.winfo_rootx()
                ry = root.winfo_rooty()
                top.update_idletasks()
                top.geometry(f"+{rx}+{ry}")
            except Exception:
                pass

            return top

        # choose button set
        if "다시시도" in prompt or ("R" in prompt and "S" in prompt and "A" in prompt):
            buttons = [("다시시도", "r"), ("건너뛰기", "s"), ("중단", "a")]
        else:
            buttons = [("예", "y"), ("아니오", "n"), ("중단", "a")]

        dialog_ref = {"top": None}

        def _show_and_record():
            dialog_ref["top"] = _show_dialog(buttons)

        root.after(0, _show_and_record)

        while True:
            if ev.wait(timeout=0.1):
                return res["value"]
            if stop_ev.is_set():
                # close dialog if open
                if dialog_ref["top"]:
                    try:
                        root.after(0, lambda: dialog_ref["top"].destroy())
                    except Exception:
                        pass
                return "a"

    return ask_fn


def select_exclusions(root: tk.Tk, base_path: str) -> list:
    """Show a modal dialog that displays folder tree under `base_path`.

    The user can multi-select folders to exclude. Returns a list of
    absolute paths to the selected folders, or `None` if cancelled.
    """
    if not base_path or not os.path.isdir(base_path):
        return None

    # collect directories under base_path (include base_path itself)
    dirs = []
    try:
        for root_dir, subdirs, _ in os.walk(base_path):
            dirs.append(root_dir)
    except Exception:
        return None

    sel = None
    top = tk.Toplevel(root)
    top.title("제외할 폴더 선택")
    top.transient(root)
    top.grab_set()

    # position dialog at main window's current location
    try:
        root.update_idletasks()
        rx = root.winfo_rootx()
        ry = root.winfo_rooty()
        top.update_idletasks()
        top.geometry(f"+{rx}+{ry}")
    except Exception:
        pass

    lbl = ttk.Label(top, text="이진탐색에서 제외할 폴더들을 선택하세요:")
    lbl.pack(padx=12, pady=(12, 6))

    # Treeview to show folder hierarchy
    tree = ttk.Treeview(top, show="tree")
    tree.pack(padx=12, pady=6, fill="both", expand=True)

    # map absolute path -> tree item id
    nodes = {}
    # checkbox state map: abs path -> bool
    checked = {}

    def add_node(path_abs: str):
        parent = os.path.dirname(path_abs)
        parent_id = nodes.get(parent, "")
        name = os.path.basename(path_abs) or path_abs
        # display with checkbox glyph (unchecked by default)
        txt = f"☐ {name}"
        iid = path_abs
        tree.insert(parent_id, "end", iid=iid, text=txt)
        nodes[path_abs] = iid
        checked[path_abs] = False

    # ensure stable ordering
    dirs_sorted = sorted(dirs, key=lambda p: p.count(os.sep))
    for d in dirs_sorted:
        add_node(d)

    # clicking a row toggles its checkbox state
    def _on_click(event):
        item = tree.identify_row(event.y)
        if not item:
            return
        # toggle this item
        try:
            cur = checked.get(item, False)
            new = not cur
            checked[item] = new
            # update display text for this item
            name = os.path.basename(item) or item
            glyph = "☑" if new else "☐"
            tree.item(item, text=f"{glyph} {name}")
        except Exception:
            pass

    tree.bind("<Button-1>", _on_click)

    btn_frame = ttk.Frame(top)
    btn_frame.pack(pady=(6, 12))

    def on_ok():
        nonlocal sel
        sel = [p for p, v in checked.items() if v]
        top.grab_release()
        top.destroy()

    def on_cancel():
        nonlocal sel
        sel = None
        top.grab_release()
        top.destroy()

    ttk.Button(btn_frame, text="확인", command=on_ok).pack(side="left", padx=6)
    ttk.Button(btn_frame, text="취소", command=on_cancel).pack(side="left", padx=6)

    root.wait_window(top)
    return sel
