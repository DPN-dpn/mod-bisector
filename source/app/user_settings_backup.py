"""User settings backup/load helpers separated from path_manager.

These functions present file dialogs to the user and copy files to/from
the application's `config.ini`. They are UI-facing but kept separate
so `path_manager` remains focused on path logic.
"""
from typing import Optional
import os
import json
import config


def backup_settings(parent: Optional[object] = None) -> None:
    """Read ..\d3dx_user.ini relative to the configured path and save a
    JSON backup in the application's directory.

    The resulting JSON will contain a single key `d3dx_user` with the
    contents of the INI file as a string.
    """
    try:
        from tkinter import messagebox
    except Exception:
        messagebox = None

    # determine configured base path
    try:
        base = config.load_last_path()
    except Exception:
        base = ""

    if not base:
        if messagebox:
            try:
                messagebox.showwarning("백업 실패", "설정된 경로가 없습니다.", parent=parent)
            except Exception:
                pass
        return

    ini_path = os.path.abspath(os.path.join(base, os.pardir, "d3dx_user.ini"))
    if not os.path.exists(ini_path):
        if messagebox:
            try:
                messagebox.showwarning("백업 실패", f"d3dx_user.ini을 찾을 수 없습니다:\n{ini_path}", parent=parent)
            except Exception:
                pass
        return

    try:
        with open(ini_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception:
        if messagebox:
            try:
                messagebox.showerror("백업 실패", "d3dx_user.ini을 읽는 중 오류가 발생했습니다.", parent=parent)
            except Exception:
                pass
        return

    # write backup into application base directory
    backup_fname = "backup.json"
    backup_dir = config._BASE_DIR if hasattr(config, "_BASE_DIR") else os.getcwd()
    backup_path = os.path.join(backup_dir, backup_fname)

    try:
        mods = find_mod_folders(start_path=base)
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump({"d3dx_user": content, "mods": mods}, f, ensure_ascii=False, indent=2)
        if messagebox:
            try:
                messagebox.showinfo("백업 완료", f"백업 파일을 생성했습니다:\n{backup_path}", parent=parent)
            except Exception:
                pass
    except Exception:
        if messagebox:
            try:
                messagebox.showerror("백업 실패", "백업 파일을 저장하는 중 오류가 발생했습니다.", parent=parent)
            except Exception:
                pass


def load_settings(parent: Optional[object] = None) -> None:
    """불러오기 기능은 아직 구현되지 않았습니다 (플레이스홀더).

    실제 불러오기 동작은 향후 구현될 예정이며, 현재는 호출해도 아무 동작을 하지 않습니다.
    """
    return


def find_mod_folders(start_path: Optional[str] = None):
    """Return a list of mod folders found under `start_path`.

    Behavior:
    - If `start_path` is None, use `config.load_last_path()`.
    - Treat any file with a `.ini` extension as a match.
    - Inspect each immediate child directory of `start_path`; if any child
      contains a `.ini` file anywhere in its subtree, that child is
      considered a mod folder (the "topmost" folder for that branch).
    - If no immediate child contains an ini but `start_path` itself does,
      include `start_path` as a mod folder.

    Returns a list of dicts: {"name": <folder name>, "path": <abs path>}.
    """
    try:
        if not start_path:
            start_path = config.load_last_path()
    except Exception:
        start_path = start_path or ""

    start_path = os.path.abspath(start_path) if start_path else ""
    if not start_path or not os.path.isdir(start_path):
        return []

    mods = []
    try:
        # topdown=True so we can skip descending into subdirs when a parent
        # directory already contains an .ini (we treat parent as the mod).
        for dirpath, dirnames, files in os.walk(start_path, topdown=True):
            has_ini = any(fn.lower().endswith(".ini") for fn in files)
            if has_ini:
                mods.append({"name": os.path.basename(dirpath), "path": os.path.abspath(dirpath)})
                # do not descend into children of this dir
                dirnames[:] = []
    except Exception:
        return mods

    return mods
