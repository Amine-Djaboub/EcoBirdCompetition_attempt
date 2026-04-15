from app.main_gui import build_ui

if __name__ == "__main__":
    demo = build_ui()
    # share=True creates a public web link you can open on your phone or give to judges!
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True, show_error=True)