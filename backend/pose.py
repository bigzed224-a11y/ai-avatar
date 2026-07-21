"""Real-time pose detection and mapping module."""
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class PoseData:
    """Normalized pose data from MediaPipe."""
    # Head pose
    head_tilt: float = 0.0      # Left/right tilt (-1 to 1)
    head_nod: float = 0.0       # Up/down nod (-1 to 1)
    head_turn: float = 0.0      # Left/right turn (-1 to 1)
    
    # Face landmarks (normalized 0-1)
    mouth_open: float = 0.0     # Mouth openness
    smile: float = 0.0          # Smile intensity
    eyebrow_raise: float = 0.0  # Eyebrow raise
    
    # Body pose
    shoulder_roll: float = 0.0  # Shoulder tilt
    body_lean: float = 0.0      # Forward/back lean
    
    # Confidence
    confidence: float = 0.0


def parse_mediapipe_landmarks(landmarks: list) -> PoseData:
    """
    Convert MediaPipe pose landmarks to normalized pose data.
    
    MediaPipe Pose provides 33 landmarks:
    - 0: nose
    - 11: left_shoulder
    - 12: right_shoulder
    - 13: left_elbow
    - 14: right_elbow
    - 23: left_hip
    - 24: right_hip
    """
    pose = PoseData()
    
    if not landmarks or len(landmarks) < 25:
        return pose
    
    try:
        # Nose position (landmark 0)
        nose = landmarks[0]
        
        # Shoulders (landmarks 11, 12)
        left_shoulder = landmarks[11]
        right_shoulder = landmarks[12]
        
        # Calculate head tilt from shoulder comparison
        shoulder_diff = left_shoulder.y - right_shoulder.y
        pose.head_tilt = max(-1, min(1, shoulder_diff * 5))
        
        # Calculate head turn from nose position relative to shoulders
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2
        pose.head_turn = max(-1, min(1, (nose.x - shoulder_center_x) * 3))
        
        # Head nod from nose vertical position
        pose.head_nod = max(-1, min(1, (nose.y - 0.5) * 2))
        
        # Shoulder roll
        pose.shoulder_roll = max(-1, min(1, shoulder_diff * 3))
        
        # Calculate confidence based on landmark visibility
        if hasattr(nose, 'visibility'):
            pose.confidence = nose.visibility
        
    except (IndexError, AttributeError):
        pass
    
    return pose


def pose_to_animation_params(pose: PoseData) -> Dict[str, Any]:
    """
    Convert pose data to animation parameters for face animation.
    
    Returns parameters that can drive:
    - Head rotation (x, y, z)
    - Mouth shape
    - Eyebrow position
    """
    return {
        # Head rotation in degrees
        "head_rotation": {
            "x": pose.head_nod * 15,    # ±15 degrees nod
            "y": pose.head_turn * 20,   # ±20 degrees turn
            "z": pose.head_tilt * 10,   # ±10 degrees tilt
        },
        # Face expressions
        "face": {
            "mouth_open": pose.mouth_open,
            "smile": pose.smile,
            "eyebrow_raise": pose.eyebrow_raise,
        },
        # Body offset for avatar
        "body": {
            "lean": pose.body_lean,
            "shoulder_roll": pose.shoulder_roll,
        },
        # Metadata
        "confidence": pose.confidence,
        "timestamp": None  # Will be set by caller
    }


class PoseTracker:
    """Track pose over time for smoothing."""
    
    def __init__(self, smoothing: float = 0.3):
        self.smoothing = smoothing
        self.prev_pose = PoseData()
        self.history = []
    
    def update(self, new_pose: PoseData) -> PoseData:
        """Apply smoothing to new pose data."""
        smoothed = PoseData(
            head_tilt=self._smooth(self.prev_pose.head_tilt, new_pose.head_tilt),
            head_nod=self._smooth(self.prev_pose.head_nod, new_pose.head_nod),
            head_turn=self._smooth(self.prev_pose.head_turn, new_pose.head_turn),
            mouth_open=self._smooth(self.prev_pose.mouth_open, new_pose.mouth_open),
            smile=self._smooth(self.prev_pose.smile, new_pose.smile),
            eyebrow_raise=self._smooth(self.prev_pose.eyebrow_raise, new_pose.eyebrow_raise),
            shoulder_roll=self._smooth(self.prev_pose.shoulder_roll, new_pose.shoulder_roll),
            body_lean=self._smooth(self.prev_pose.body_lean, new_pose.body_lean),
            confidence=new_pose.confidence,
        )
        
        self.prev_pose = smoothed
        self.history.append(smoothed)
        
        # Keep last 30 frames
        if len(self.history) > 30:
            self.history.pop(0)
        
        return smoothed
    
    def _smooth(self, prev: float, new: float) -> float:
        """Exponential moving average."""
        return prev * (1 - self.smoothing) + new * self.smoothing
    
    def get_velocity(self) -> Dict[str, float]:
        """Get rate of change of pose (for animation speed)."""
        if len(self.history) < 2:
            return {"head_tilt": 0, "head_nod": 0, "head_turn": 0}
        
        curr = self.history[-1]
        prev = self.history[-2]
        
        return {
            "head_tilt": curr.head_tilt - prev.head_tilt,
            "head_nod": curr.head_nod - prev.head_nod,
            "head_turn": curr.head_turn - prev.head_turn,
        }


# Global tracker instance
pose_tracker = PoseTracker()


def process_pose_frame(landmarks: list) -> Dict[str, Any]:
    """Process a single frame of pose data."""
    pose = parse_mediapipe_landmarks(landmarks)
    smoothed = pose_tracker.update(pose)
    return pose_to_animation_params(smoothed)
