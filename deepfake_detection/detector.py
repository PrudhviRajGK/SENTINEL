"""
Deepfake Detection using Computer Vision
Supports both images and videos (frame sampling)
"""

import os
import cv2
import numpy as np
from typing import Dict, Optional, List
from PIL import Image
import io

class DeepfakeDetector:
    """
    Deepfake detector using heuristic analysis
    
    NOTE: This is a lightweight implementation for demonstration.
    Production systems should use:
    - Pretrained Xception/EfficientNet models
    - FaceForensics++ trained weights
    - Ensemble methods
    """
    
    def __init__(self):
        self.face_cascade = None
        self._load_face_detector()
    
    def _load_face_detector(self):
        """Load OpenCV face detector"""
        try:
            # Try to load Haar Cascade for face detection
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
        except Exception as e:
            print(f"Face detector load warning: {e}")
            self.face_cascade = None
    
    def analyze_image(self, image_path: str) -> Dict:
        """
        Analyze image for deepfake indicators
        
        Returns structured result with confidence and reasoning
        """
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                return {
                    'error': 'Unable to load image',
                    'authentic': None,
                    'confidence': 0
                }
            
            # Detect faces
            faces = self._detect_faces(img)
            
            if len(faces) == 0:
                return {
                    'authentic': None,
                    'confidence': 0,
                    'verdict': 'No faces detected',
                    'reasoning': 'Cannot assess authenticity without facial features',
                    'indicators': [],
                    'limitations': 'Face detection required for deepfake analysis'
                }
            
            # Analyze each face
            indicators = []
            scores = []
            
            for (x, y, w, h) in faces:
                face_roi = img[y:y+h, x:x+w]
                face_score, face_indicators = self._analyze_face_region(face_roi)
                scores.append(face_score)
                indicators.extend(face_indicators)
            
            # Calculate overall score
            avg_score = np.mean(scores) if scores else 50
            
            # Determine verdict
            if avg_score >= 70:
                verdict = 'Likely Authentic'
                authentic = True
                confidence = avg_score
            elif avg_score >= 40:
                verdict = 'Uncertain'
                authentic = None
                confidence = 50
            else:
                verdict = 'Potentially Manipulated'
                authentic = False
                confidence = 100 - avg_score
            
            return {
                'authentic': authentic,
                'confidence': round(confidence, 1),
                'verdict': verdict,
                'reasoning': self._generate_reasoning(indicators, avg_score),
                'indicators': indicators,
                'faces_detected': len(faces),
                'limitations': 'Heuristic analysis only. Professional forensics recommended for critical cases.'
            }
            
        except Exception as e:
            return {
                'error': f'Analysis failed: {str(e)}',
                'authentic': None,
                'confidence': 0
            }
    
    def analyze_video(self, video_path: str, sample_frames: int = 10) -> Dict:
        """
        Analyze video by sampling frames
        """
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return {
                    'error': 'Unable to open video',
                    'authentic': None,
                    'confidence': 0
                }
            
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if total_frames == 0:
                return {
                    'error': 'Video has no frames',
                    'authentic': None,
                    'confidence': 0
                }
            
            # Sample frames evenly
            frame_indices = np.linspace(0, total_frames - 1, min(sample_frames, total_frames), dtype=int)
            
            frame_results = []
            
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if ret:
                    # Save frame temporarily
                    temp_path = f'/tmp/sentinel_frame_{frame_idx}.jpg'
                    cv2.imwrite(temp_path, frame)
                    
                    # Analyze frame
                    result = self.analyze_image(temp_path)
                    
                    if 'error' not in result and result.get('authentic') is not None:
                        frame_results.append(result)
                    
                    # Cleanup
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            
            cap.release()
            
            if not frame_results:
                return {
                    'authentic': None,
                    'confidence': 0,
                    'verdict': 'Unable to analyze video frames',
                    'reasoning': 'No faces detected in sampled frames',
                    'frames_analyzed': 0
                }
            
            # Aggregate results
            confidences = [r['confidence'] for r in frame_results]
            authentics = [r['authentic'] for r in frame_results if r['authentic'] is not None]
            
            avg_confidence = np.mean(confidences)
            
            if authentics:
                authentic_ratio = sum(authentics) / len(authentics)
                if authentic_ratio >= 0.7:
                    verdict = 'Likely Authentic'
                    authentic = True
                elif authentic_ratio <= 0.3:
                    verdict = 'Potentially Manipulated'
                    authentic = False
                else:
                    verdict = 'Inconsistent - Mixed Signals'
                    authentic = None
            else:
                verdict = 'Uncertain'
                authentic = None
            
            return {
                'authentic': authentic,
                'confidence': round(avg_confidence, 1),
                'verdict': verdict,
                'reasoning': f'Analyzed {len(frame_results)} frames from video',
                'frames_analyzed': len(frame_results),
                'total_frames': total_frames,
                'duration_seconds': round(total_frames / fps, 1) if fps > 0 else 0,
                'limitations': 'Frame sampling analysis. Full forensic analysis recommended for verification.'
            }
            
        except Exception as e:
            return {
                'error': f'Video analysis failed: {str(e)}',
                'authentic': None,
                'confidence': 0
            }
    
    def _detect_faces(self, img) -> List:
        """Detect faces in image"""
        if self.face_cascade is None:
            return []
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        return faces
    
    def _analyze_face_region(self, face_roi) -> tuple:
        """
        Analyze face region for manipulation indicators
        
        Heuristic checks:
        - Color consistency
        - Edge sharpness
        - Noise patterns
        - Compression artifacts
        """
        indicators = []
        score = 50  # Start neutral
        
        # Check 1: Color consistency
        color_std = np.std(face_roi)
        if color_std < 20:
            indicators.append('Unusually uniform color distribution')
            score -= 15
        elif color_std > 60:
            score += 10
        
        # Check 2: Edge analysis
        edges = cv2.Canny(face_roi, 100, 200)
        edge_density = np.sum(edges > 0) / edges.size
        
        if edge_density < 0.05:
            indicators.append('Low edge definition')
            score -= 10
        elif edge_density > 0.15:
            indicators.append('Natural edge patterns detected')
            score += 10
        
        # Check 3: Noise analysis
        noise_level = self._estimate_noise(face_roi)
        if noise_level < 5:
            indicators.append('Suspiciously low noise level')
            score -= 10
        
        # Check 4: Compression artifacts
        if self._detect_compression_artifacts(face_roi):
            indicators.append('Compression artifacts detected')
            score -= 5
        
        # Clamp score
        score = max(0, min(100, score))
        
        return score, indicators
    
    def _estimate_noise(self, img) -> float:
        """Estimate noise level in image"""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        
        # Use Laplacian variance as noise estimate
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        noise = np.var(laplacian)
        
        return noise
    
    def _detect_compression_artifacts(self, img) -> bool:
        """Detect JPEG compression artifacts"""
        # Simple check: look for block patterns
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        
        # Check for 8x8 block patterns (JPEG)
        h, w = gray.shape
        if h < 16 or w < 16:
            return False
        
        # Sample a few blocks
        block_variances = []
        for i in range(0, min(h-8, 32), 8):
            for j in range(0, min(w-8, 32), 8):
                block = gray[i:i+8, j:j+8]
                block_variances.append(np.var(block))
        
        # High variance in block boundaries suggests compression
        if len(block_variances) > 0:
            variance_std = np.std(block_variances)
            return variance_std > 100
        
        return False
    
    def _generate_reasoning(self, indicators: List[str], score: float) -> str:
        """Generate human-readable reasoning"""
        if score >= 70:
            base = "Image shows characteristics consistent with authentic media."
        elif score >= 40:
            base = "Analysis inconclusive. Some indicators present but not definitive."
        else:
            base = "Image shows characteristics that may indicate manipulation."
        
        if indicators:
            details = " Detected: " + ", ".join(indicators[:3])
            return base + details
        
        return base
