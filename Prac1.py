import tkinter as tk
from tkinter import scrolledtext

root = tk.Tk()
root.title("bruh")
root.geometry("600x300")

terminal = scrolledtext.ScrolledText(
    root,
    wrap=tk.WORD,
    bg = "#1E1E1E",
    fg = "#00ff00",
    borderwidth = 2
)

terminal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
terminal.insert(tk.END, "Welcome")

root.mainloop()
