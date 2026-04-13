import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import os
from .detector import MockBirdDetector
from .agent import fetch_species_info

class NatureThemeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EcoBird Counter - 24h Hackathon Starter")
        self.root.geometry("1100x700")
        self.root.configure(bg="#F4F9F4")
        
        self.detector = MockBirdDetector()
        self.video_path = None
        self.cap = None
        self.current_frame = None
        
        self.setup_style()
        self.build_layout()
        self.bind_events()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#F4F9F4")
        style.configure("TLabel", background="#F4F9F4", foreground="#1B4332", font=("Segoe UI", 11))
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8, background="#40916C")
        style.configure("Success.TButton", background="#2D6A4F")
        style.configure("Info.TLabel", background="#E8F5E9", foreground="#0B2A1D", padding=10)

    def build_layout(self):
        # Header
        header = ttk.Frame(self.root, padding=10)
        header.pack(fill=tk.X)
        ttk.Label(header, text="AI Ecology Bird Counter", style="Title.TLabel").pack()

        # Main Grid
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=2)
        main.columnconfigure(1, weight=1)

        # Video Area
        vid_frame = ttk.LabelFrame(main, text="Video Viewer", padding=10)
        vid_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.canvas = tk.Canvas(vid_frame, bg="#2E4A35", width=600, height=400)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Controls
        ctrl_frame = ttk.Frame(vid_frame)
        ctrl_frame.pack(fill=tk.X, pady=5)
        ttk.Button(ctrl_frame, text="Load Video", command=self.load_video).pack(side=tk.LEFT, padx=5)
        self.btn_count = ttk.Button(ctrl_frame, text="Count & Detect", state=tk.DISABLED, style="Success.TButton", command=self.run_count)
        self.btn_count.pack(side=tk.LEFT, padx=5)

        # Results & Info Panel
        info_frame = ttk.LabelFrame(main, text="Results & Species Info", padding=10)
        info_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        self.tree = ttk.Treeview(info_frame, columns=("Species", "Count", "Confidence"), show="headings", height=8)
        self.tree.heading("Species", text="Species")
        self.tree.heading("Count", text="Count")
        self.tree.heading("Confidence", text="Avg Confidence")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Agent Info Box
        agent_box = ttk.LabelFrame(main, text="Agentic AI Species Panel", padding=10)
        agent_box.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=10)
        self.agent_text = tk.Text(agent_box, bg="#E8F5E9", fg="#0B2A1D", font=("Consolas", 10), wrap=tk.WORD, state=tk.DISABLED)
        self.agent_text.pack(fill=tk.BOTH, expand=True)
        ttk.Button(agent_box, text="Fetch Selected Species Info", command=self.show_species_info).pack(pady=5)

    def bind_events(self):
        self.tree.bind("<<TreeviewSelect>>", self.update_agent_panel)

    def load_video(self):
        path = filedialog.askopenfilename(filetypes=[("Videos", "*.mp4 *.avi *.mov")])
        if path:
            self.video_path = path
            self.cap = cv2.VideoCapture(path)
            self.btn_count.config(state=tk.NORMAL)
            ret, frame = self.cap.read()
            if ret:
                self.show_frame(frame)

    def show_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        img_tk = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
        self.canvas.image = img_tk

    def run_count(self):
        if not self.cap: return
        detections, frames_processed = [], 0
        while True:
            ret, frame = self.cap.read()
            if not ret: break
            detections.append(self.detector.process_frame(frame, "vid"))
            frames_processed += 1
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # reset
        
        counts = self.detector.aggregate_counts(detections)
        for sp, cnt in counts.items():
            self.tree.insert("", tk.END, values=(sp, cnt, "0.82"))
            
        messagebox.showinfo("Counting Complete", f"Processed {frames_processed} frames. Results updated.")

    def update_agent_panel(self, event):
        item = self.tree.selection()
        if item:
            sp = self.tree.item(item, "values")[0]
            self.agent_text.config(state=tk.NORMAL)
            self.agent_text.delete(1.0, tk.END)
            info = fetch_species_info(sp)
            for k, v in info.items():
                self.agent_text.insert(tk.END, f"{k}: {v}\n")
            self.agent_text.config(state=tk.DISABLED)

    def show_species_info(self):
        self.update_agent_panel(None)

# # app/main_gui.py
# import gradio as gr
# import time
# import pandas as pd
# from .detector import MockBirdDetector
# from .agent import fetch_species_info

# # 🎨 Custom Nature Theme CSS
# NATURE_CSS = """
# .gradio-container {
#     background: linear-gradient(160deg, #f8faf8 0%, #eef5ee 100%);
#     font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
#     max-width: 1200px !important;
#     margin: 0 auto;
#     padding: 24px;
# }
# h1 {
#     color: #1b4332;
#     font-weight: 800;
#     text-align: center;
#     margin-bottom: 4px;
#     letter-spacing: -0.5px;
# }
# .subtitle {
#     text-align: center;
#     color: #40916c;
#     font-size: 1.05em;
#     margin-bottom: 20px;
#     font-weight: 500;
# }
# .gr-box {
#     background: #ffffff !important;
#     border: 1px solid #d1e7d1 !important;
#     border-radius: 16px !important;
#     box-shadow: 0 6px 20px rgba(45, 106, 79, 0.08) !important;
#     transition: all 0.2s ease;
# }
# .gr-box:hover {
#     box-shadow: 0 8px 24px rgba(45, 106, 79, 0.12) !important;
# }
# .gr-button-primary {
#     background: linear-gradient(135deg, #2d6a4f 0%, #40916c 100%) !important;
#     border: none !important;
#     border-radius: 12px !important;
#     font-weight: 600 !important;
#     font-size: 1em !important;
#     box-shadow: 0 4px 12px rgba(45, 106, 79, 0.25) !important;
# }
# .gr-button-primary:hover {
#     background: linear-gradient(135deg, #1b4332 0%, #2d6a4f 100%) !important;
#     transform: translateY(-1px);
# }
# table th {
#     background: #e8f5e9 !important;
#     color: #0b2a1d !important;
#     font-weight: 600 !important;
# }
# .ai-panel {
#     background: linear-gradient(135deg, #f0f9f0 0%, #e6f2e6 100%) !important;
#     border-left: 4px solid #40916c !important;
#     padding: 18px !important;
#     border-radius: 12px !important;
#     min-height: 180px;
# }
# .gr-form {
#     border-radius: 16px !important;
# }
# """

# detector = MockBirdDetector()
# RESULTS_STATE = pd.DataFrame()

# def process_video(video_path, progress=gr.Progress()):
#     """Mock pipeline with realistic progress tracking."""
#     global RESULTS_STATE
#     if not video_path:
#         gr.Warning("Please upload a video file to begin.")
#         return "*Upload a video to start detection.*"

#     progress(0, desc="🔍 Initializing model & loading frames...")
#     time.sleep(0.3)
    
#     # Simulate frame-by-frame processing
#     detections = []
#     for i in range(100):
#         progress((i+1)/100, desc=f"🖼️ Processing batch {i+1}/100...")
#         time.sleep(0.02)
#         # In real pipeline: detections.append(detector.process_frame(frame, vid_id))
#         detections.append(detector.process_frame(None, "mock"))
        
#     progress(1.0, desc="✅ Aggregating tracks & generating counts...")
#     counts = detector.aggregate_counts(detections)
#     RESULTS_STATE = pd.DataFrame(counts.items(), columns=["Species", "Count"])
#     RESULTS_STATE["Confidence"] = 0.84
    
#     return f"✅ Detection complete. Found **{len(counts)} species**. Click a row below to view AI insights."

# def get_species_info(evt: gr.SelectData):
#     """Triggered when user clicks a table row."""
#     if evt is None or not evt.value:
#         return "*Click a species in the table above to fetch biodiversity data.*"
    
#     # Gradio passes selected cell value. For dataframe, we extract species name.
#     species = str(evt.value[0]) if isinstance(evt.value, (list, tuple)) else str(evt.value)
#     info = fetch_species_info(species)
    
#     md = f"### 🌿 {species}\n\n"
#     for k, v in info.items():
#         emoji = {"Scientific Name": "🔬", "Conservation Status": "🛡️", "Habitat": "🌲", "Diet": "🐛", "Fun Fact": "💡"}.get(k, "📌")
#         md += f"**{emoji} {k}:** {v}\n"
#     return md

# def build_ui():
#     with gr.Blocks(css=NATURE_CSS, title="🌿 EcoBird AI Counter") as demo:
#         gr.Markdown("# 🌿 AI Ecology Bird Counter")
#         gr.Markdown('<p class="subtitle">24h Hackathon Starter • Open-Set Counting & Agentic Profiling</p>')

#         with gr.Row(equal_height=True):
#             # Left: Video & Controls
#             with gr.Column(scale=3):
#                 video_input = gr.Video(
#                     label="📹 Drop Video Here", 
#                     format="mp4", 
#                     interactive=True, 
#                     elem_id="video-area"
#                 )
#                 btn_process = gr.Button("🔍 Run Detection & Count", variant="primary")
                
#             # Right: Results & AI Panel
#             with gr.Column(scale=2):
#                 results_table = gr.Dataframe(
#                     label="📊 Species Counts",
#                     headers=["Species", "Count", "Confidence"],
#                     interactive=False,
#                     wrap=True,
#                     type="pandas"
#                 )
#                 ai_panel = gr.Markdown(
#                     label="🤖 Agentic AI Species Panel", 
#                     value="*Click a species row to retrieve real-time ecological data.*", 
#                     elem_classes=["ai-panel"]
#                 )

#         # Event Bindings
#         btn_process.click(
#             fn=process_video,
#             inputs=video_input,
#             outputs=ai_panel,
#             show_progress=True
#         )

#         results_table.select(
#             fn=get_species_info,
#             inputs=None,
#             outputs=ai_panel
#         )

#     return demo