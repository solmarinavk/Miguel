"""
🚀 DETECTOR DE PERSONA SENTADA - VERSIÓN PROFESIONAL
====================================================
Sistema avanzado de detección de postura sentada usando MediaPipe Pose.
Optimizado para Google Colab con análisis en tiempo real y métricas avanzadas.

Autor: Sistema de Análisis de Postura
Versión: 2.0 Pro
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict
from datetime import timedelta
from collections import deque
import statistics
import csv
import math
import base64

import cv2
import numpy as np
import mediapipe as mp
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from IPython.display import HTML, display


# ============================================================================
# CONFIGURACIÓN Y PARÁMETROS
# ============================================================================

@dataclass
class DetectorConfig:
    """Configuración centralizada del detector con valores optimizados."""

    # Video
    target_width: int = 720
    fps_target: Optional[float] = None  # None = mantener original

    # Suavizado EMA
    ema_alpha_height: float = 0.20
    ema_alpha_angle: float = 0.20

    # Umbrales de detección
    torso_max_deg: float = 30.0      # Torso vertical (≤30°)
    knee_sit_min: float = 75.0       # Rango rodilla sentado
    knee_sit_max: float = 120.0

    # Histéresis para transiciones
    enter_hip_drop: float = 0.62     # Bajada cadera para entrar
    exit_hip_drop: float = 0.55      # Bajada cadera para salir

    # Debounce temporal
    enter_min_sec: float = 0.35      # Segundos mínimos para confirmar
    exit_min_sec: float = 0.35

    # Calibración baseline
    baseline_warmup_sec: float = 1.0
    baseline_fallback_sec: float = 2.0

    # Visualización
    ekg_width: int = 400
    ekg_height: int = 30
    overlay_alpha: float = 0.30

    # Análisis
    enable_per_frame_csv: bool = True
    enable_quality_analysis: bool = True

    # MediaPipe
    mp_model_complexity: int = 1
    mp_min_detection_confidence: float = 0.5
    mp_min_tracking_confidence: float = 0.5

    def validate(self) -> None:
        """Validar parámetros de configuración."""
        assert 0 < self.ema_alpha_height <= 1, "EMA alpha debe estar en (0,1]"
        assert 0 < self.ema_alpha_angle <= 1, "EMA alpha debe estar en (0,1]"
        assert self.knee_sit_min < self.knee_sit_max, "Rango de rodilla inválido"
        assert self.enter_hip_drop > self.exit_hip_drop, "Histéresis inválida"


# ============================================================================
# UTILIDADES GEOMÉTRICAS
# ============================================================================

class GeometryUtils:
    """Utilidades para cálculos geométricos de pose."""

    @staticmethod
    def calculate_angle(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
        """
        Calcula el ángulo ABC en grados (b es el vértice).

        Args:
            a, b, c: Puntos 2D como arrays numpy

        Returns:
            Ángulo en grados [0, 180]
        """
        ba = a - b
        bc = c - b
        denominator = np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9
        cos_angle = np.clip(np.dot(ba, bc) / denominator, -1.0, 1.0)
        return float(np.degrees(np.arccos(cos_angle)))

    @staticmethod
    def torso_angle_from_vertical(hip_xy: np.ndarray, shoulder_xy: np.ndarray) -> float:
        """
        Calcula el ángulo del torso respecto a la vertical.

        Args:
            hip_xy: Coordenadas de la cadera
            shoulder_xy: Coordenadas del hombro

        Returns:
            Ángulo en grados (0° = perfectamente vertical)
        """
        vector = shoulder_xy - hip_xy
        vector_norm = vector / (np.linalg.norm(vector) + 1e-9)
        vertical = np.array([0.0, -1.0])  # Hacia arriba en imagen
        cos_angle = np.clip(np.dot(vector_norm, vertical), -1.0, 1.0)
        return float(np.degrees(np.arccos(cos_angle)))

    @staticmethod
    def select_best_leg(landmarks, width: int, height: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, str]:
        """
        Selecciona la pierna con mejor visibilidad.

        Returns:
            (hip, knee, ankle, side) donde side es 'L' o 'R'
        """
        lm = landmarks
        mp_pose = mp.solutions.pose.PoseLandmark

        # Visibilidades
        left_vis = min(lm[mp_pose.LEFT_KNEE].visibility,
                      lm[mp_pose.LEFT_ANKLE].visibility)
        right_vis = min(lm[mp_pose.RIGHT_KNEE].visibility,
                       lm[mp_pose.RIGHT_ANKLE].visibility)

        if right_vis > left_vis:
            side = 'R'
            hip = np.array([lm[mp_pose.RIGHT_HIP].x * width,
                           lm[mp_pose.RIGHT_HIP].y * height])
            knee = np.array([lm[mp_pose.RIGHT_KNEE].x * width,
                            lm[mp_pose.RIGHT_KNEE].y * height])
            ankle = np.array([lm[mp_pose.RIGHT_ANKLE].x * width,
                             lm[mp_pose.RIGHT_ANKLE].y * height])
            shoulder = np.array([lm[mp_pose.RIGHT_SHOULDER].x * width,
                                lm[mp_pose.RIGHT_SHOULDER].y * height])
        else:
            side = 'L'
            hip = np.array([lm[mp_pose.LEFT_HIP].x * width,
                           lm[mp_pose.LEFT_HIP].y * height])
            knee = np.array([lm[mp_pose.LEFT_KNEE].x * width,
                            lm[mp_pose.LEFT_KNEE].y * height])
            ankle = np.array([lm[mp_pose.LEFT_ANKLE].x * width,
                             lm[mp_pose.LEFT_ANKLE].y * height])
            shoulder = np.array([lm[mp_pose.LEFT_SHOULDER].x * width,
                                lm[mp_pose.LEFT_SHOULDER].y * height])

        return hip, knee, ankle, shoulder, side


# ============================================================================
# MÁQUINA DE ESTADOS
# ============================================================================

class PostureState:
    """Estados posibles de la postura."""
    STANDING = "STANDING"
    SITTING = "SITTING"


class StateMachine:
    """Máquina de estados con histéresis y debounce para transiciones suaves."""

    def __init__(self, config: DetectorConfig):
        self.config = config
        self.state = PostureState.STANDING
        self.enter_timer = 0.0
        self.exit_timer = 0.0
        self.intervals: List[Tuple[float, float]] = []
        self.current_interval_start: Optional[float] = None

    def update(self, t: float, dt: float, is_sitting_condition: bool,
               is_standing_condition: bool) -> str:
        """
        Actualiza el estado basado en condiciones con debounce.

        Args:
            t: Tiempo actual en segundos
            dt: Delta tiempo (1/fps)
            is_sitting_condition: Si se cumplen condiciones de sentado
            is_standing_condition: Si se cumplen condiciones de parado

        Returns:
            Estado actual
        """
        if self.state == PostureState.STANDING:
            if is_sitting_condition:
                self.enter_timer += dt
                if self.enter_timer >= self.config.enter_min_sec:
                    self._transition_to_sitting(t)
                    self.enter_timer = 0.0
            else:
                self.enter_timer = 0.0

        else:  # SITTING
            if is_standing_condition:
                self.exit_timer += dt
                if self.exit_timer >= self.config.exit_min_sec:
                    self._transition_to_standing(t)
                    self.exit_timer = 0.0
            else:
                self.exit_timer = 0.0

        return self.state

    def _transition_to_sitting(self, t: float) -> None:
        """Transición a estado sentado."""
        self.state = PostureState.SITTING
        self.current_interval_start = t

    def _transition_to_standing(self, t: float) -> None:
        """Transición a estado de pie."""
        self.state = PostureState.STANDING
        if self.current_interval_start is not None:
            self.intervals.append((self.current_interval_start, t))
            self.current_interval_start = None

    def finalize(self, final_time: float) -> None:
        """Cierra intervalo abierto al final del video."""
        if self.state == PostureState.SITTING and self.current_interval_start is not None:
            self.intervals.append((self.current_interval_start, final_time))


# ============================================================================
# DETECTOR DE POSTURA SENTADA
# ============================================================================

class SittingDetector:
    """Detector principal de postura sentada con análisis avanzado."""

    def __init__(self, config: DetectorConfig):
        self.config = config
        self.config.validate()

        # MediaPipe
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=config.mp_model_complexity,
            min_detection_confidence=config.mp_min_detection_confidence,
            min_tracking_confidence=config.mp_min_tracking_confidence
        )

        # Estado interno
        self.ema_hip_y: Optional[float] = None
        self.ema_knee_deg: Optional[float] = None
        self.ema_torso_deg: Optional[float] = None

        # Baseline (calibración)
        self.hip_baseline: Optional[float] = None
        self.baseline_samples: List[float] = []
        self.fallback_samples: List[Tuple[float, float, float]] = []

        # Máquina de estados
        self.state_machine = StateMachine(config)

        # Métricas y telemetría
        self.frame_data: List[Dict] = []
        self.quality_scores: deque = deque(maxlen=150)  # ~5 seg @ 30fps

    def process_frame(self, frame: np.ndarray, frame_idx: int, fps: float) -> Tuple[np.ndarray, Dict]:
        """
        Procesa un frame y devuelve frame anotado + datos.

        Args:
            frame: Frame BGR de OpenCV
            frame_idx: Índice del frame
            fps: FPS del video

        Returns:
            (frame_anotado, datos_frame)
        """
        t = frame_idx / fps
        dt = 1.0 / fps

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)

        data = {
            'time': t,
            'state': self.state_machine.state,
            'detected': False,
            'knee_deg': None,
            'torso_deg': None,
            'hip_drop_ratio': None,
            'sitting_score': 0.0,
            'quality_score': 0.0
        }

        if not results.pose_landmarks:
            return frame, data

        # Extraer geometría
        h, w = frame.shape[:2]
        hip, knee, ankle, shoulder, side = GeometryUtils.select_best_leg(
            results.pose_landmarks.landmark, w, h
        )

        # Calcular ángulos
        knee_deg = GeometryUtils.calculate_angle(hip, knee, ankle)
        torso_deg = GeometryUtils.torso_angle_from_vertical(hip, shoulder)

        # Altura normalizada de cadera
        mp_pose = self.mp_pose.PoseLandmark
        hip_y_norm = (results.pose_landmarks.landmark[mp_pose.RIGHT_HIP].y
                     if side == 'R'
                     else results.pose_landmarks.landmark[mp_pose.LEFT_HIP].y)

        # Aplicar EMA
        self._update_ema(hip_y_norm, knee_deg, torso_deg)

        # Calibrar baseline
        self._update_baseline(t, fps)

        # Calcular métricas
        hip_drop_ratio = self.ema_hip_y / max(self.hip_baseline or 1.0, 1e-6)
        sitting_score = self._calculate_sitting_score(hip_drop_ratio, self.ema_knee_deg)
        quality_score = self._calculate_quality_score(self.ema_knee_deg, self.ema_torso_deg)

        self.quality_scores.append(quality_score)

        # Evaluar condiciones
        is_sitting = self._check_sitting_condition(hip_drop_ratio)
        is_standing = self._check_standing_condition(hip_drop_ratio)

        # Actualizar estado
        state = self.state_machine.update(t, dt, is_sitting, is_standing)

        # Actualizar datos
        data.update({
            'detected': True,
            'knee_deg': self.ema_knee_deg,
            'torso_deg': self.ema_torso_deg,
            'hip_drop_ratio': hip_drop_ratio,
            'sitting_score': sitting_score,
            'quality_score': quality_score,
            'state': state
        })

        self.frame_data.append(data)

        return frame, data

    def _update_ema(self, hip_y: float, knee_deg: float, torso_deg: float) -> None:
        """Actualiza valores suavizados con EMA."""
        alpha_h = self.config.ema_alpha_height
        alpha_a = self.config.ema_alpha_angle

        if self.ema_hip_y is None:
            self.ema_hip_y = hip_y
            self.ema_knee_deg = knee_deg
            self.ema_torso_deg = torso_deg
        else:
            self.ema_hip_y = (1 - alpha_h) * self.ema_hip_y + alpha_h * hip_y
            self.ema_knee_deg = (1 - alpha_a) * self.ema_knee_deg + alpha_a * knee_deg
            self.ema_torso_deg = (1 - alpha_a) * self.ema_torso_deg + alpha_a * torso_deg

    def _update_baseline(self, t: float, fps: float) -> None:
        """Actualiza la línea base de cadera (posición de pie)."""
        # Detectar "de pie" para calibración
        if (self.ema_knee_deg > 150 and abs(self.ema_torso_deg) < 15):
            self.baseline_samples.append(self.ema_hip_y)

            if (len(self.baseline_samples) >= self.config.baseline_warmup_sec * fps
                and self.hip_baseline is None):
                self.hip_baseline = statistics.median(self.baseline_samples)

        # Fallback en primeros segundos
        if t <= self.config.baseline_fallback_sec:
            self.fallback_samples.append((self.ema_hip_y, self.ema_knee_deg, t))

        # Usar provisional si no hay baseline
        if self.hip_baseline is None:
            self.hip_baseline = self.ema_hip_y

    def _calculate_sitting_score(self, hip_drop: float, knee_deg: float) -> float:
        """
        Score continuo [0,1] que indica qué tan "sentado" está.
        Combina bajada de cadera y ángulo de rodilla óptimo (~90°).
        """
        hip_component = np.clip(
            (hip_drop - self.config.enter_hip_drop) / (1.0 - self.config.enter_hip_drop),
            0.0, 1.0
        )
        knee_component = np.clip(
            1.0 - abs(knee_deg - 90.0) / 90.0,
            0.0, 1.0
        )
        return 0.5 * hip_component + 0.5 * knee_component

    def _calculate_quality_score(self, knee_deg: float, torso_deg: float) -> float:
        """
        Score de calidad de la postura [0,1].
        1.0 = postura perfecta, 0.0 = postura muy mala.
        """
        # Rodilla ideal: 90° (rango bueno: 85-95°)
        knee_score = 1.0 - min(abs(knee_deg - 90.0) / 30.0, 1.0)

        # Torso ideal: vertical (rango bueno: 0-15°)
        torso_score = 1.0 - min(torso_deg / 45.0, 1.0)

        return 0.6 * knee_score + 0.4 * torso_score

    def _check_sitting_condition(self, hip_drop: float) -> bool:
        """Verifica si se cumplen condiciones de sentado."""
        return (hip_drop >= self.config.enter_hip_drop and
                self.config.knee_sit_min <= self.ema_knee_deg <= self.config.knee_sit_max and
                abs(self.ema_torso_deg) <= self.config.torso_max_deg)

    def _check_standing_condition(self, hip_drop: float) -> bool:
        """Verifica si se cumplen condiciones de parado (salir de sentado)."""
        return (hip_drop <= self.config.exit_hip_drop or
                self.ema_knee_deg > 130 or
                abs(self.ema_torso_deg) > (self.config.torso_max_deg + 10))

    def finalize(self, total_frames: int, fps: float) -> None:
        """Finaliza el procesamiento."""
        self.state_machine.finalize(total_frames / fps)

        # Fallback de baseline si nunca se calibró
        if not self.baseline_samples and self.fallback_samples:
            knees = [k for _, k, _ in self.fallback_samples if k is not None]
            if knees:
                threshold = np.percentile(knees, 70)
                candidates = [h for h, k, _ in self.fallback_samples if k >= threshold]
                if candidates:
                    self.hip_baseline = float(np.median(candidates))

    def get_intervals(self) -> List[Tuple[float, float]]:
        """Retorna intervalos de tiempo sentado."""
        return self.state_machine.intervals

    def close(self) -> None:
        """Libera recursos."""
        self.pose.close()


# ============================================================================
# VISUALIZADOR
# ============================================================================

class VideoVisualizer:
    """Renderiza overlays y anotaciones en el video."""

    def __init__(self, config: DetectorConfig, width: int, height: int):
        self.config = config
        self.width = width
        self.height = height

        # Barra EKG (historial temporal)
        self.ekg = np.zeros((config.ekg_height, config.ekg_width, 3), dtype=np.uint8)

        # MediaPipe drawing
        self.mp_pose = mp.solutions.pose
        self.mp_draw = mp.solutions.drawing_utils

        # Colores
        self.COLOR_SITTING = (0, 200, 100)   # Verde
        self.COLOR_STANDING = (200, 100, 50) # Azul-gris
        self.COLOR_GOOD = (0, 255, 0)
        self.COLOR_WARNING = (0, 200, 255)
        self.COLOR_BAD = (0, 100, 255)

    def draw(self, frame: np.ndarray, data: Dict, landmarks, hip_baseline: float) -> np.ndarray:
        """
        Dibuja todas las anotaciones en el frame.

        Args:
            frame: Frame BGR
            data: Diccionario con datos del frame
            landmarks: Pose landmarks de MediaPipe
            hip_baseline: Línea base de cadera (normalizada)

        Returns:
            Frame anotado
        """
        if landmarks:
            self._draw_skeleton(frame, landmarks)

        is_sitting = data['state'] == PostureState.SITTING

        self._draw_header_banner(frame, is_sitting)

        if data['detected']:
            self._draw_metrics_text(frame, data)
            self._draw_hip_lines(frame, data['hip_drop_ratio'], hip_baseline)
            self._draw_quality_indicator(frame, data['quality_score'], is_sitting)

        self._draw_ekg_bar(frame, is_sitting)

        return frame

    def _draw_skeleton(self, frame: np.ndarray, landmarks) -> None:
        """Dibuja el esqueleto de MediaPipe."""
        self.mp_draw.draw_landmarks(
            frame,
            landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            self.mp_draw.DrawingSpec(color=(0, 255, 100), thickness=2, circle_radius=3),
            self.mp_draw.DrawingSpec(color=(0, 150, 255), thickness=2)
        )

    def _draw_header_banner(self, frame: np.ndarray, is_sitting: bool) -> None:
        """Dibuja el banner superior con estado."""
        overlay = frame.copy()
        color = self.COLOR_SITTING if is_sitting else self.COLOR_STANDING
        cv2.rectangle(overlay, (0, 0), (self.width, 75), color, -1)
        cv2.addWeighted(overlay, self.config.overlay_alpha, frame, 1 - self.config.overlay_alpha, 0, frame)

        label = "✓ SENTADA/O" if is_sitting else "○ DE PIE"
        cv2.putText(frame, label, (20, 50), cv2.FONT_HERSHEY_DUPLEX, 1.4, (255, 255, 255), 3)

    def _draw_metrics_text(self, frame: np.ndarray, data: Dict) -> None:
        """Dibuja métricas en pantalla."""
        y_offset = 95
        line_height = 32

        metrics = [
            f"Rodilla: {data['knee_deg']:5.1f}°",
            f"Torso:   {data['torso_deg']:5.1f}°",
            f"Cadera:  {data['hip_drop_ratio']:4.2f}x",
            f"Score:   {data['sitting_score']:4.2f}"
        ]

        for i, text in enumerate(metrics):
            cv2.putText(frame, text, (20, y_offset + i * line_height),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    def _draw_hip_lines(self, frame: np.ndarray, hip_drop: float, baseline: float) -> None:
        """Dibuja líneas de referencia de cadera."""
        if baseline is None:
            return

        base_y = int(baseline * self.height)
        actual_y = int(hip_drop * baseline * self.height)

        # Línea baseline (blanca)
        cv2.line(frame, (0, base_y), (self.width, base_y), (255, 255, 255), 2, cv2.LINE_AA)

        # Línea actual (amarilla/verde)
        color = (0, 255, 200) if hip_drop > 0.6 else (0, 255, 255)
        cv2.line(frame, (0, actual_y), (self.width, actual_y), color, 3, cv2.LINE_AA)

    def _draw_quality_indicator(self, frame: np.ndarray, quality: float, is_sitting: bool) -> None:
        """Dibuja indicador de calidad de postura."""
        if not is_sitting or quality is None:
            return

        # Barra de calidad (esquina superior derecha)
        bar_w, bar_h = 160, 25
        x0, y0 = self.width - bar_w - 20, 15

        # Fondo
        cv2.rectangle(frame, (x0, y0), (x0 + bar_w, y0 + bar_h), (50, 50, 50), -1)

        # Barra de progreso
        fill_w = int(bar_w * quality)
        if quality > 0.7:
            color = self.COLOR_GOOD
        elif quality > 0.4:
            color = self.COLOR_WARNING
        else:
            color = self.COLOR_BAD

        cv2.rectangle(frame, (x0, y0), (x0 + fill_w, y0 + bar_h), color, -1)
        cv2.rectangle(frame, (x0, y0), (x0 + bar_w, y0 + bar_h), (200, 200, 200), 2)

        # Texto
        text = f"{quality*100:.0f}%"
        cv2.putText(frame, text, (x0 + 50, y0 + 18), cv2.FONT_HERSHEY_SIMPLEX,
                   0.5, (255, 255, 255), 1, cv2.LINE_AA)

    def _draw_ekg_bar(self, frame: np.ndarray, is_sitting: bool) -> None:
        """Dibuja barra EKG (historial temporal)."""
        # Desplazar izquierda
        self.ekg[:, :-1] = self.ekg[:, 1:]

        # Nuevo píxel
        color = self.COLOR_SITTING if is_sitting else self.COLOR_STANDING
        self.ekg[:, -1] = color

        # Pegar en esquina inferior derecha
        y0 = self.height - self.config.ekg_height - 10
        x0 = self.width - self.config.ekg_width - 10

        # Border
        cv2.rectangle(frame, (x0-2, y0-2),
                     (x0 + self.config.ekg_width + 2, y0 + self.config.ekg_height + 2),
                     (255, 255, 255), 2)

        frame[y0:y0 + self.config.ekg_height, x0:x0 + self.config.ekg_width] = self.ekg


# ============================================================================
# ANALIZADOR Y EXPORTADOR
# ============================================================================

class PostureAnalyzer:
    """Análisis avanzado y exportación de resultados."""

    def __init__(self, detector: SittingDetector, fps: float, total_frames: int):
        self.detector = detector
        self.fps = fps
        self.total_time = total_frames / fps
        self.intervals = detector.get_intervals()

    def calculate_summary_metrics(self) -> Dict:
        """Calcula métricas resumidas."""
        total_sitting = sum(end - start for start, end in self.intervals)
        ratio = total_sitting / self.total_time if self.total_time > 0 else 0.0
        avg_duration = total_sitting / len(self.intervals) if self.intervals else 0.0

        # Calidad promedio durante periodos sentados
        sitting_frames = [d for d in self.detector.frame_data
                         if d['detected'] and d['state'] == PostureState.SITTING]
        avg_quality = (statistics.mean([f['quality_score'] for f in sitting_frames])
                      if sitting_frames else 0.0)

        return {
            'total_duration': self.total_time,
            'sitting_duration': total_sitting,
            'sitting_ratio': ratio,
            'num_transitions': len(self.intervals),
            'avg_episode_duration': avg_duration,
            'avg_sitting_quality': avg_quality,
            'max_episode_duration': max((e-s for s,e in self.intervals), default=0.0),
            'min_episode_duration': min((e-s for s,e in self.intervals), default=0.0)
        }

    def export_intervals_csv(self, filename: str) -> None:
        """Exporta intervalos a CSV."""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['start_s', 'end_s', 'duration_s'])
            for start, end in self.intervals:
                writer.writerow([round(start, 3), round(end, 3), round(end - start, 3)])

    def export_frame_data_csv(self, filename: str) -> None:
        """Exporta datos por frame a CSV."""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['time_s', 'state', 'knee_deg', 'torso_deg',
                           'hip_drop_ratio', 'sitting_score', 'quality_score'])

            for data in self.detector.frame_data:
                if data['detected']:
                    writer.writerow([
                        round(data['time'], 3),
                        data['state'],
                        round(data['knee_deg'], 2),
                        round(data['torso_deg'], 2),
                        round(data['hip_drop_ratio'], 3),
                        round(data['sitting_score'], 3),
                        round(data['quality_score'], 3)
                    ])

    def create_analysis_plots(self, filename: str) -> None:
        """Crea gráficos de análisis avanzados."""
        frame_data = self.detector.frame_data
        detected_frames = [d for d in frame_data if d['detected']]

        if not detected_frames:
            return

        times = [d['time'] for d in detected_frames]
        hips = [d['hip_drop_ratio'] for d in detected_frames]
        knees = [d['knee_deg'] / 180.0 for d in detected_frames]
        torsos = [d['torso_deg'] / 90.0 for d in detected_frames]
        sitting = [1 if d['state'] == PostureState.SITTING else 0 for d in detected_frames]
        scores = [d['sitting_score'] for d in detected_frames]
        quality = [d['quality_score'] for d in detected_frames]

        fig, axes = plt.subplots(3, 1, figsize=(14, 10))

        # Plot 1: Señales principales
        ax1 = axes[0]
        ax1.plot(times, hips, label='Hip drop ratio', linewidth=2.5, color='#2E86AB')
        ax1.plot(times, knees, label='Knee (norm)', linewidth=2, color='#A23B72', alpha=0.8)
        ax1.plot(times, torsos, label='Torso (norm)', linewidth=2, color='#F18F01', alpha=0.8)
        ax1.fill_between(times, 0, sitting, color='#06A77D', alpha=0.25, label='Sitting state')
        ax1.set_ylim(-0.05, 1.1)
        ax1.set_ylabel('Normalized values', fontweight='bold')
        ax1.legend(loc='upper right', ncol=4, framealpha=0.9)
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.set_title('🔍 Pose Signals Analysis', fontsize=14, fontweight='bold', pad=10)

        # Plot 2: Scores
        ax2 = axes[1]
        ax2.plot(times, scores, label='Sitting score', linewidth=2.5, color='#8338EC')
        ax2.plot(times, quality, label='Posture quality', linewidth=2.5, color='#FF006E', linestyle='--')
        ax2.axhline(0.7, color='green', linestyle=':', alpha=0.5, label='Good threshold')
        ax2.axhline(0.4, color='orange', linestyle=':', alpha=0.5, label='Fair threshold')
        ax2.set_ylim(-0.05, 1.05)
        ax2.set_ylabel('Score [0-1]', fontweight='bold')
        ax2.legend(loc='upper right', ncol=4, framealpha=0.9)
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.set_title('📊 Sitting & Quality Scores', fontsize=14, fontweight='bold', pad=10)

        # Plot 3: Intervalos
        ax3 = axes[2]
        for i, (start, end) in enumerate(self.intervals):
            ax3.add_patch(Rectangle((start, 0), end - start, 1,
                                   facecolor='#06A77D', edgecolor='#045E47', linewidth=2))
        ax3.set_xlim(0, max(times) if times else 1)
        ax3.set_ylim(0, 1)
        ax3.set_xlabel('Time (seconds)', fontweight='bold', fontsize=11)
        ax3.set_ylabel('Sitting', fontweight='bold')
        ax3.set_yticks([])
        ax3.grid(True, axis='x', alpha=0.3, linestyle='--')
        ax3.set_title(f'⏱️ Sitting Episodes (Total: {len(self.intervals)})',
                     fontsize=14, fontweight='bold', pad=10)

        plt.tight_layout()
        plt.savefig(filename, dpi=200, bbox_inches='tight')
        plt.close()

    def print_summary(self) -> None:
        """Imprime resumen en consola."""
        metrics = self.calculate_summary_metrics()

        print("\n" + "="*70)
        print("📈 ANÁLISIS DE POSTURA - RESUMEN EJECUTIVO")
        print("="*70)
        print(f"⏱️  Duración total:        {metrics['total_duration']:.2f}s "
              f"(~{timedelta(seconds=int(metrics['total_duration']))})")
        print(f"🪑  Tiempo sentado:        {metrics['sitting_duration']:.2f}s "
              f"({metrics['sitting_ratio']*100:.1f}%)")
        print(f"🔄  Transiciones:          {metrics['num_transitions']} veces")
        print(f"📊  Promedio por episodio: {metrics['avg_episode_duration']:.2f}s")
        print(f"⏫  Episodio más largo:    {metrics['max_episode_duration']:.2f}s")
        print(f"⏬  Episodio más corto:    {metrics['min_episode_duration']:.2f}s")
        print(f"✨  Calidad promedio:      {metrics['avg_sitting_quality']*100:.1f}% ", end="")

        if metrics['avg_sitting_quality'] > 0.7:
            print("(Excelente ✓)")
        elif metrics['avg_sitting_quality'] > 0.4:
            print("(Aceptable ~)")
        else:
            print("(Mejorable ⚠)")

        print("="*70 + "\n")


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def process_video(video_path: str, config: DetectorConfig) -> Dict:
    """
    Procesa un video completo y genera todos los outputs.

    Args:
        video_path: Ruta al video de entrada
        config: Configuración del detector

    Returns:
        Diccionario con rutas de archivos generados
    """
    print("🚀 Iniciando procesamiento PRO...")
    print(f"📹 Video: {video_path}")

    # Abrir video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"No se pudo abrir el video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Escalar video
    scale = min(1.0, config.target_width / max(1, width))
    out_w, out_h = int(width * scale), int(height * scale)

    print(f"📐 Resolución: {width}x{height} → {out_w}x{out_h}")
    print(f"⚡ FPS: {fps:.2f}")
    print(f"🎬 Frames totales: {total_frames}")

    # Inicializar componentes
    detector = SittingDetector(config)
    visualizer = VideoVisualizer(config, out_w, out_h)

    # Writer
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    tmp_avi = "output_temp.avi"
    writer = cv2.VideoWriter(tmp_avi, fourcc, fps, (out_w, out_h))

    # Procesar frames
    print("\n🔄 Procesando frames...")
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1

        if scale != 1.0:
            frame = cv2.resize(frame, (out_w, out_h), interpolation=cv2.INTER_AREA)

        # Procesar
        frame_processed, data = detector.process_frame(frame, frame_idx, fps)

        # Visualizar
        landmarks = None
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = detector.pose.process(rgb)
        if results.pose_landmarks:
            landmarks = results.pose_landmarks

        frame_annotated = visualizer.draw(frame_processed, data, landmarks, detector.hip_baseline)

        writer.write(frame_annotated)

        # Progress
        if frame_idx % 30 == 0 or frame_idx == total_frames:
            progress = frame_idx / total_frames * 100
            print(f"  ▸ Progreso: {progress:.1f}% ({frame_idx}/{total_frames})", end='\r')

    print(f"\n✅ Procesamiento completado: {frame_idx} frames")

    # Finalizar
    cap.release()
    writer.release()
    detector.finalize(frame_idx, fps)
    detector.close()

    # Analizar
    analyzer = PostureAnalyzer(detector, fps, frame_idx)

    # Exportar
    print("\n📁 Generando archivos...")

    csv_intervals = "sitting_intervals_pro.csv"
    analyzer.export_intervals_csv(csv_intervals)
    print(f"  ✓ {csv_intervals}")

    csv_frames = None
    if config.enable_per_frame_csv:
        csv_frames = "sitting_frames_pro.csv"
        analyzer.export_frame_data_csv(csv_frames)
        print(f"  ✓ {csv_frames}")

    plot_file = "posture_analysis_pro.png"
    analyzer.create_analysis_plots(plot_file)
    print(f"  ✓ {plot_file}")

    # Convertir a MP4
    print("\n🎥 Convirtiendo a MP4...")
    out_mp4 = "sitting_detection_pro.mp4"
    import subprocess
    subprocess.run([
        'ffmpeg', '-y', '-loglevel', 'error',
        '-i', tmp_avi,
        '-vcodec', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        out_mp4
    ], check=True)
    print(f"  ✓ {out_mp4}")

    # Imprimir resumen
    analyzer.print_summary()

    return {
        'video': out_mp4,
        'intervals_csv': csv_intervals,
        'frames_csv': csv_frames,
        'plot': plot_file,
        'metrics': analyzer.calculate_summary_metrics()
    }


# ============================================================================
# EJECUCIÓN EN COLAB
# ============================================================================

def run_in_colab():
    """Función principal para ejecutar en Google Colab."""
    from google.colab import files

    print("="*70)
    print("🎯 DETECTOR DE PERSONA SENTADA - VERSIÓN PRO")
    print("="*70)
    print()

    # Subir video
    print("📤 Por favor, sube tu video (MP4, AVI, MOV):")
    uploaded = files.upload()

    if not uploaded:
        print("❌ No se subió ningún video.")
        return

    video_path = list(uploaded.keys())[0]
    print(f"✅ Video cargado: {video_path}\n")

    # Configuración
    config = DetectorConfig(
        target_width=720,
        ema_alpha_height=0.20,
        ema_alpha_angle=0.20,
        enable_per_frame_csv=True,
        enable_quality_analysis=True,
        ekg_width=400,
        ekg_height=30
    )

    # Procesar
    try:
        outputs = process_video(video_path, config)

        # Mostrar video inline
        print("\n🎬 Reproduciendo resultado:")
        with open(outputs['video'], 'rb') as f:
            video_b64 = base64.b64encode(f.read()).decode()

        video_html = f'''
        <video width="720" controls>
            <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
        </video>
        '''
        display(HTML(video_html))

        print("\n📦 Archivos generados:")
        print(f"  • Video:     {outputs['video']}")
        print(f"  • Intervalos: {outputs['intervals_csv']}")
        if outputs['frames_csv']:
            print(f"  • Frames:    {outputs['frames_csv']}")
        print(f"  • Gráficos:  {outputs['plot']}")

        print("\n💡 Tip: Puedes ajustar parámetros en DetectorConfig para afinar la detección.")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Error durante el procesamiento: {e}")
        raise


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Detectar si estamos en Colab
    try:
        import google.colab
        IN_COLAB = True
    except ImportError:
        IN_COLAB = False

    if IN_COLAB:
        run_in_colab()
    else:
        print("⚠️  Este script está optimizado para Google Colab.")
        print("Para usar localmente, llama a process_video() directamente.")
