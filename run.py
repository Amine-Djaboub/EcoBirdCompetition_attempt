import tkinter as tk
from app.main_gui import NatureThemeGUI

if __name__ == "__main__":
    root = tk.Tk()
    app = NatureThemeGUI(root)
    root.mainloop()

# from app.main_gui import build_ui

# if __name__ == "__main__":
#     demo = build_ui()
#     # Opens locally at http://localhost:7860
#     demo.launch(server_name="0.0.0.0", server_port=7860, share=False, show_error=True)