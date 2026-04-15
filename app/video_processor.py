import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
from collections import defaultdict, Counter
import numpy as np
import json
import os
from ultralytics import YOLO

# --- 1. GLOBAL MODEL INITIALIZATION ---
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(f"Loading models on: {device}")

# Load YOLO tracking model
yolo_model = YOLO('yolov8m-seg.pt') 

# --- THE SMART LOADER (EFFICIENTNET) ---
model_path = 'best_model.pth' 
print(f"Attempting to load {model_path}...")

try:
    # Load whatever is inside the .pth file
    loaded_data = torch.load(model_path, map_location=device)
    
    # Check if it's a dictionary
    if isinstance(loaded_data, dict):
        # 🚨 THE FIX: Open the checkpoint "suitcase" if it exists
        if "model_state_dict" in loaded_data:
            print("🧳 Detected a Training Checkpoint! Extracting weights...")
            state_dict_to_load = loaded_data["model_state_dict"]
        else:
            print("🧠 Detected raw 'state_dict'.")
            state_dict_to_load = loaded_data

        print("Building EfficientNet-B0 architecture...")
        efficient_model = models.efficientnet_b0(weights=None)
        num_ftrs = efficient_model.classifier[1].in_features
        efficient_model.classifier[1] = nn.Linear(num_ftrs, 200) 
        
        # Now load the cleanly extracted weights!
        efficient_model.load_state_dict(state_dict_to_load)
    else:
        print("📦 Detected 'Full Model Object'. Loading directly...")
        efficient_model = loaded_data

    efficient_model = efficient_model.to(device)
    efficient_model.eval()
    print("✅ EfficientNet-B0 Classifier loaded successfully and is ready!")

except Exception as e:
    print(f"🛑 FATAL ERROR LOADING MODEL: {e}")
    # Fallback so the UI doesn't crash, but it will guess randomly
    efficient_model = models.efficientnet_b0(weights=None)
    efficient_model.classifier[1] = nn.Linear(efficient_model.classifier[1].in_features, 200)
    efficient_model = efficient_model.to(device)
    efficient_model.eval()

# --- 2. TRANSFORMS & CLASS NAMES ---
inference_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# Load the real bird names from your colleague's JSON file
try:
    with open('idx_to_class.json', 'r') as f:
        idx_to_class_dict = json.load(f)
        
    # The JSON keys are strings ("0", "1", etc.), so we map them to a clean list
    class_names = [idx_to_class_dict[str(i)] for i in range(len(idx_to_class_dict))]
    print(f"✅ Successfully loaded {len(class_names)} real bird species names!")
except Exception as e:
    print(f"⚠️ Could not load idx_to_class.json: {e}")
    # Safe fallback so it doesn't crash the app
    class_names = [f"Species {i}" for i in range(200)] 

# --- 3. THE MAIN PIPELINE ---
def process_video_pipeline(video_path, progress_callback=None):
    if progress_callback:
        progress_callback(0.1, desc="🔍 Initializing Video & Tracking...")

    id_frame_counts = Counter()
    id_top_crops = defaultdict(list)
    birds_per_frame = []
    frames_active_ids = []

    # Prepare the Video Writer to save the annotated overlay
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    output_video_path = "output_overlay.mp4"
    # Using mp4v codec for standard MP4 generation
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out_video = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    results = yolo_model.track(
        source=video_path, tracker="bytetrack.yaml", classes=[14],
        conf=0.15, iou=0.6, imgsz=640, persist=True, stream=True, verbose=False
    )

    for r in results:
        active_in_this_frame = []
        
        # Grab YOLO's beautiful annotated frame (bounding boxes + masks + IDs)
        annotated_frame = r.plot()
        out_video.write(annotated_frame) # Write it to our new video file!

        if r.boxes is not None and r.boxes.id is not None:
            boxes = r.boxes.xyxy.cpu().numpy()
            track_ids = r.boxes.id.int().cpu().numpy()
            orig_img = r.orig_img
            
            for box, track_id in zip(boxes, track_ids):
                active_in_this_frame.append(track_id)
                id_frame_counts[track_id] += 1
                
                # Grab sharpest crops (Max 5)
                if len(id_top_crops[track_id]) < 5:
                    x1, y1, x2, y2 = map(int, box)
                    x1, y1 = max(0, x1), max(0, y1)
                    x2, y2 = min(orig_img.shape[1], x2), min(orig_img.shape[0], y2)
                    crop = orig_img[y1:y2, x1:x2]
                    
                    if crop.size > 0:
                        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
                        id_top_crops[track_id].append((blur_score, crop))
                        id_top_crops[track_id].sort(key=lambda x: x[0], reverse=True)

        birds_per_frame.append(len(active_in_this_frame))
        frames_active_ids.append(set(active_in_this_frame))

    # Release the video writer when the video is done generating
    out_video.release()
    
    if progress_callback:
        progress_callback(0.5, desc="🧮 Running Ensemble Counting Logic...")

    # A. Temporal Smoothing Count (min 10 frames)
    valid_birds = sum(1 for count in id_frame_counts.values() if count >= 10)
    
    # B. Median Count
    median_count = int(np.median(birds_per_frame)) if birds_per_frame else 0
    
    # C. Scene-Aware Count
    scenes, current_scene, prev_ids = [], [], set()
    for active_ids in frames_active_ids:
        if active_ids:
            if prev_ids and len(active_ids.intersection(prev_ids)) == 0:
                scenes.append(current_scene)
                current_scene = []
            current_scene.append(len(active_ids))
            prev_ids = active_ids
        else:
            current_scene.append(0)
            prev_ids = set()
    if current_scene: scenes.append(current_scene)
    
    scene_aware_count = 0
    for scene_counts in scenes:
        if scene_counts:
            scene_aware_count += int(np.percentile(scene_counts, 90))
            
    # Ultimate Mean Equation
    official_count = (valid_birds + median_count + scene_aware_count) // 3

    if progress_callback:
        progress_callback(0.7, desc="🧠 Classifying Species via EfficientNet...")

   # --- 4. CLASSIFICATION ---
    valid_real_ids = [tid for tid, count in id_frame_counts.items() if count >= 10]
    species_tally = Counter()
    species_confidences = defaultdict(list) # Tracks confidences!
    
    for track_id in valid_real_ids:
        species_votes = Counter()
        track_confs = defaultdict(list) # Confidences for this specific track
        sharpest_crops = id_top_crops[track_id]
        
        for score, crop_bgr in sharpest_crops:
            try:
                crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(crop_rgb)
                input_tensor = inference_transform(image).unsqueeze(0).to(device)

                with torch.no_grad():
                    outputs = efficient_model(input_tensor) 
                    probabilities = F.softmax(outputs[0], dim=0)
                    top_prob, top_class = torch.max(probabilities, 0)
                    
                    if top_prob.item() >= 0.65: 
                        clean_name = class_names[top_class.item()].split('.')[-1].replace('_', ' ')
                        species_votes[clean_name] += 1
                        track_confs[clean_name].append(top_prob.item()) # Save the math!
            except Exception as e:
                pass
                
        consensus = species_votes.most_common(1)[0][0] if species_votes else "Unknown"
        species_tally[consensus] += 1
        
        # Save the average confidence of this specific bird
        if consensus != "Unknown" and track_confs[consensus]:
            avg_track_conf = sum(track_confs[consensus]) / len(track_confs[consensus])
            species_confidences[consensus].append(avg_track_conf)

    if progress_callback:
        progress_callback(0.9, desc="📊 Generating UI Data...")

    # --- 5. PROPORTIONAL DISTRIBUTION ---
    final_distribution = Counter()
    total_valid = sum(species_tally.values())
    
    if total_valid > 0 and official_count > 0:
        for species, count in species_tally.items():
            final_distribution[species] = round((count / total_valid) * official_count)
            
        current_sum = sum(final_distribution.values())
        if current_sum != official_count and final_distribution:
            diff = official_count - current_sum
            most_common = species_tally.most_common(1)[0][0]
            final_distribution[most_common] = max(1, final_distribution[most_common] + diff)

    # --- 6. PACKAGE FOR GRADIO UI ---
    final_ui_data = {}
    for species, count in final_distribution.items():
        if species == "Unknown" or not species_confidences[species]:
            conf_str = "N/A"
        else:
            # Average the confidences across ALL birds of this species
            overall_avg = sum(species_confidences[species]) / len(species_confidences[species])
            conf_str = f"{(overall_avg * 100):.1f}%"
            
        final_ui_data[species] = {"count": count, "confidence": conf_str}

    if progress_callback:
        progress_callback(0.95, desc="🎬 Converting video for web playback...")

    # 🚨 NEW: Convert the video to a web-safe H.264 format using FFmpeg
    web_output_path = "web_output_overlay.mp4"
    # The -y flag overwrites old files, -vcodec libx264 forces the web-safe codec
    os.system(f"ffmpeg -y -i {output_video_path} -vcodec libx264 -preset fast {web_output_path}")

    # Return the dictionary AND the newly converted web-safe video path
    return final_ui_data, web_output_path