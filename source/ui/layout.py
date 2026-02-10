import tkinter as tk
from tkinter import ttk

def build_ui(root: tk.Tk) -> None:
	"""Build the main window layout into the given root."""
	frm = ttk.Frame(root, padding=12)
	frm.pack(fill='both', expand=True)

	lbl = ttk.Label(frm, text="mod-bisector", font=("Segoe UI", 18))
	lbl.pack(pady=(10, 8))

	msg = ttk.Label(frm, text="This is a minimal GUI. Click Quit to exit.")
	msg.pack(pady=(0, 12))

	btn_frame = ttk.Frame(frm)
	btn_frame.pack()

	quit_btn = ttk.Button(btn_frame, text="Quit", command=root.destroy)
	quit_btn.pack()

if __name__ == "__main__":
	root = tk.Tk()
	build_ui(root)
	root.mainloop()
