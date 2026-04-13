# app/detector.py
import cv2
import numpy as np
from collections import defaultdict

class MockBirdDetector:
    """Placeholder for YOLO / SAM + ByteTrack. Swap with real models."""
    def __init__(self):
        self.track_counts = defaultdict(int)
        self.species_cache = {}

    def process_frame(self, frame, video_id):
        # Mock: Generate 3-8 bounding boxes with random species labels
        h, w = frame.shape[:2]
        detections = []
        known_species = ["Sparrow", "Finch", "Warbler", "Robin"]
        num_birds = np.random.randint(3, 9)
        
        for i in range(num_birds):
            x = np.random.randint(0, w-80)
            y = np.random.randint(0, h-80)
            species = np.random.choice(known_species)
            detections.append({"box": [x, y, 60, 80], "species": species, "conf": 0.85})
            
        return detections

    def aggregate_counts(self, all_detections):
        # Simple deduplication mock: average per-frame counts
        species_frames = defaultdict(list)
        for frame_det in all_detections:
            for d in frame_det:
                species_frames[d["species"]].append(1)
                
        return {sp: int(np.mean(counts)) for sp, counts in species_frames.items()}