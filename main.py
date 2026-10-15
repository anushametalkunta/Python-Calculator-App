# main.py
# This is the file you run to start the calculator.
#   python main.py            -> modern look (needs: pip install customtkinter)
#   python main.py --classic  -> the classic look

import os
import sys
import tkinter as tk

from calculator.app import build_app_class


def resource_path(file_name):
    """Find a file that sits next to our code.
    This works both when running main.py and inside the finished .exe."""
    base_folder = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_folder, file_name)


def create_window():
    """Return (window, app class). Uses the modern look if it is available."""
    if "--classic" not in sys.argv:
        try:
            import customtkinter as ctk
            app_class = build_app_class(modern=True)
            return ctk.CTk(), app_class
        except ImportError:
            print("CustomTkinter is not installed, so the classic look is used.")

    return tk.Tk(), build_app_class(modern=False)


def set_icon(root):
    """Use our icon for the main window AND every window it opens (like History)."""
    path = resource_path("calculator.ico")
    for options in ({"bitmap": path}, {"default": path}):
        try:
            root.iconbitmap(**options)
        except Exception:
            pass                 # if the icon file is missing, use the default one


def main():
    root, app_class = create_window()

    set_icon(root)
    root.after(300, lambda: set_icon(root))   # CustomTkinter sets its own icon a moment later

    app_class(root)          # build the calculator inside that window
    root.mainloop()          # keep the window open and listen for clicks


# This runs main() only when you start THIS file directly.
if __name__ == "__main__":
    main()