import sys
import os

sys.dont_write_bytecode = True

if getattr(sys, "frozen", False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(base_dir)

from views.main_window import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
