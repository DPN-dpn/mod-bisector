import tkinter as tk
from tkinter import ttk
import threading
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
