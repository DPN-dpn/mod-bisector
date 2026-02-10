import tkinter as tk
from tkinter import ttk
from app import path_manager


def build_ui(root: tk.Tk) -> tk.StringVar:
    """Build the main window layout into the given root.

    Returns the `StringVar` that holds the selected folder path.
    """
    # 상단: 폴더 경로 입력 + 찾아보기
    top = ttk.Frame(root, padding=(12, 8))
    top.pack(fill="x")

    path_var = tk.StringVar()

    lbl = ttk.Label(top, text="Mods :")
    lbl.pack(side="left")

    entry = ttk.Entry(top, textvariable=path_var, state="readonly")
    entry.pack(side="left", padx=8, expand=True, fill="x")

    browse_btn = ttk.Button(
        top,
        text="찾아보기...",
        command=lambda: (
            path_var.set(p) if (p := path_manager.browse_directory(root)) else None
        ),
    )
    browse_btn.pack(side="left")

    # 본문 자리 (추후 컴포넌트 추가)
    content = ttk.Frame(root, padding=12)
    content.pack(fill="both", expand=True)

    # 작업 버튼
    btn_find_hash = ttk.Button(content, text="중복 해시 찾기", command=lambda: None)
    btn_find_hash.pack(fill="x", pady=(8, 6), ipady=8)

    btn_binary_search = ttk.Button(content, text="모드 이진 탐색", command=lambda: None)
    btn_binary_search.pack(fill="x", pady=(0, 8), ipady=8)

    # 초기값 설정 (저장된 경로가 있으면 불러오기)
    try:
        last = path_manager.load_last_path()
        if last:
            path_var.set(last)
    except Exception:
        pass

    return path_var
