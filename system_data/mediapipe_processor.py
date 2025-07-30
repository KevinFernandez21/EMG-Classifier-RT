"""
MediaPipe Processor - Módulo para procesamiento de gestos de mano
Autor: Sistema de Dataset de Gestos
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Dict, List, Tuple, Optional

class MediaPipeHandProcessor:
    """Procesador de gestos de mano usando MediaPipe"""
    
    def __init__(self, 
                 min_detection_confidence: float = 0.7,
                 min_tracking_confidence: float = 0.5,
                 max_num_hands: int = 1):
        """
        Inicializar el procesador de MediaPipe
        
        Args:
            min_detection_confidence: Confianza mínima para detección
            min_tracking_confidence: Confianza mínima para seguimiento
            max_num_hands: Número máximo de manos a detectar
        """
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.connected = True
        self.last_detection_time = None
        
    def is_sensor_connected(self, features: Dict) -> bool:
        """
        Verificar si el sensor (cámara) está detectando una mano
        
        Args:
            features: Diccionario de características extraídas
            
        Returns:
            bool: True si está conectado/detectando, False si no
        """
        import time
        current_time = time.time()
        
        if features and len(features) > 0:
            self.last_detection_time = current_time
            self.connected = True
            return True
        
        # Si no hay detección por más de 2 segundos, considerar desconectado
        if self.last_detection_time is None:
            self.connected = False
            return False
            
        time_since_last_detection = current_time - self.last_detection_time
        if time_since_last_detection > 2.0:  # 2 segundos sin detección
            self.connected = False
            return False
            
        return True
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict, bool]:
        """
        Procesar un frame y extraer características de la mano
        
        Args:
            frame: Frame de video en formato BGR
            
        Returns:
            Tuple[np.ndarray, Dict, bool]: Frame procesado, características, estado de conexión
        """
        if frame is None:
            return frame, {}, False
            
        # Convertir a RGB para MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        
        features = {}
        hand_detected = False
        
        # Dibujar landmarks si se detecta una mano
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Dibujar landmarks
                self.mp_drawing.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2)
                )
                
                # Extraer características
                features = self.extract_hand_features(hand_landmarks)
                hand_detected = True
                break  # Solo procesar la primera mano
        
        # Verificar estado de conexión
        is_connected = self.is_sensor_connected(features)
        
        # Mostrar estado en el frame
        self._draw_connection_status(frame, is_connected, hand_detected)
        
        return frame, features, is_connected
    
    def extract_hand_features(self, landmarks) -> Dict:
        """
        Extraer características detalladas de la mano
        
        Args:
            landmarks: Landmarks de MediaPipe
            
        Returns:
            Dict: Diccionario con características calculadas
        """
        points = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
        features = {}
        
        # Puntos clave
        thumb_tip = points[4]    # Punta del pulgar
        index_tip = points[8]    # Punta del índice
        middle_tip = points[12]  # Punta del medio
        ring_tip = points[16]    # Punta del anular
        pinky_tip = points[20]   # Punta del meñique
        wrist = points[0]        # Muñeca
        
        # 1. DISTANCIAS FUNDAMENTALES
        features['thumb_index_distance'] = self._calculate_distance(thumb_tip, index_tip)
        features['thumb_wrist_distance'] = self._calculate_distance(thumb_tip, wrist)
        features['index_wrist_distance'] = self._calculate_distance(index_tip, wrist)
        features['middle_wrist_distance'] = self._calculate_distance(middle_tip, wrist)
        features['ring_wrist_distance'] = self._calculate_distance(ring_tip, wrist)
        features['pinky_wrist_distance'] = self._calculate_distance(pinky_tip, wrist)
        
        # 2. SEPARACIÓN ENTRE DEDOS CONSECUTIVOS
        features['index_middle_separation'] = self._calculate_distance(index_tip, middle_tip)
        features['middle_ring_separation'] = self._calculate_distance(middle_tip, ring_tip)
        features['ring_pinky_separation'] = self._calculate_distance(ring_tip, pinky_tip)
        features['fingers_average_separation'] = np.mean([
            features['index_middle_separation'],
            features['middle_ring_separation'],
            features['ring_pinky_separation']
        ])
        
        # 3. EXTENSIÓN DE DEDOS
        finger_extensions = self._calculate_finger_extensions(points)
        for i, ext in enumerate(finger_extensions):
            features[f'finger_{i}_extension'] = ext
        
        # 4. ÁNGULOS DE FLEXIÓN
        finger_angles = self._calculate_finger_angles(points)
        for i, angle in enumerate(finger_angles):
            features[f'finger_{i}_angle'] = angle
        
        # 5. CARACTERÍSTICAS DE GESTOS ESPECÍFICOS
        features['pinch_score'] = self._calculate_pinch_score(points)
        features['open_hand_score'] = self._calculate_open_hand_score(points)
        features['closed_fist_score'] = self._calculate_closed_fist_score(points)
        features['grasping_score'] = self._calculate_grasping_score(points)
        
        # 6. GEOMETRÍA GENERAL DE LA MANO
        fingertips = [thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip]
        finger_center = np.mean(fingertips, axis=0)
        
        features['fingertips_center_x'] = finger_center[0]
        features['fingertips_center_y'] = finger_center[1]
        features['hand_span'] = self._calculate_distance(thumb_tip, pinky_tip)
        features['hand_compactness'] = np.mean([
            self._calculate_distance(tip, finger_center) for tip in fingertips
        ])
        
        # 7. ORIENTACIÓN Y POSICIÓN
        palm_center = np.mean([points[0], points[5], points[9], points[13], points[17]], axis=0)
        features['palm_center_x'] = palm_center[0]
        features['palm_center_y'] = palm_center[1]
        features['fingertips_to_palm_distance'] = self._calculate_distance(finger_center, palm_center)
        
        return features
    
    def _calculate_distance(self, point1: np.ndarray, point2: np.ndarray) -> float:
        """Calcular distancia euclidiana entre dos puntos"""
        return np.linalg.norm(point1 - point2)
    
    def _calculate_finger_extensions(self, points: np.ndarray) -> List[float]:
        """Calcular extensión de cada dedo"""
        finger_joints = [
            [1, 2, 3, 4],      # Pulgar
            [5, 6, 7, 8],      # Índice
            [9, 10, 11, 12],   # Medio
            [13, 14, 15, 16],  # Anular
            [17, 18, 19, 20]   # Meñique
        ]
        
        extensions = []
        for joints in finger_joints:
            base = points[joints[0]]
            tip = points[joints[3]]
            
            # Distancia directa vs articulada
            direct_distance = self._calculate_distance(tip, base)
            articulated_distance = sum(
                self._calculate_distance(points[joints[i+1]], points[joints[i]])
                for i in range(len(joints) - 1)
            )
            
            extension = direct_distance / (articulated_distance + 1e-6)
            extensions.append(extension)
        
        return extensions
    
    def _calculate_finger_angles(self, points: np.ndarray) -> List[float]:
        """Calcular ángulos de flexión de cada dedo"""
        finger_angle_points = [
            [2, 3, 4],         # Pulgar
            [6, 7, 8],         # Índice
            [10, 11, 12],      # Medio
            [14, 15, 16],      # Anular
            [18, 19, 20]       # Meñique
        ]
        
        angles = []
        for joints in finger_angle_points:
            p1, p2, p3 = points[joints[0]], points[joints[1]], points[joints[2]]
            
            v1 = p1 - p2
            v2 = p3 - p2
            
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
            angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
            angles.append(np.degrees(angle))
        
        return angles
    
    def _calculate_pinch_score(self, points: np.ndarray) -> float:
        """Calcular score de precisión para gesto de pinza"""
        thumb_tip, index_tip = points[4], points[8]
        
        # Distancia entre pulgar e índice
        distance = self._calculate_distance(thumb_tip, index_tip)
        distance_score = max(0, 1 - distance * 15)
        
        # Otros dedos deben estar extendidos
        extensions = self._calculate_finger_extensions(points)
        other_fingers_extension = np.mean(extensions[2:])  # Medio, anular, meñique
        extension_score = min(1.0, other_fingers_extension * 2)
        
        return (distance_score * 0.6 + extension_score * 0.4)
    
    def _calculate_open_hand_score(self, points: np.ndarray) -> float:
        """Calcular score para mano abierta (saludo)"""
        # Extensión de dedos
        extensions = self._calculate_finger_extensions(points)
        extension_score = np.mean(extensions[1:])  # Excluir pulgar
        
        # Separación entre dedos
        fingertips = [points[8], points[12], points[16], points[20]]
        separations = [
            self._calculate_distance(fingertips[i], fingertips[i+1])
            for i in range(len(fingertips) - 1)
        ]
        separation_score = min(1.0, np.mean(separations) * 6)
        
        return (extension_score * 0.4 + separation_score * 0.6)
    
    def _calculate_closed_fist_score(self, points: np.ndarray) -> float:
        """Calcular score para puño cerrado"""
        # Flexión de dedos
        extensions = self._calculate_finger_extensions(points)
        flexion_score = 1 - np.mean(extensions[1:])
        
        # Compactación hacia la palma
        fingertips = [points[8], points[12], points[16], points[20]]
        palm_center = np.mean([points[0], points[5], points[9], points[13], points[17]], axis=0)
        
        distances_to_palm = [self._calculate_distance(tip, palm_center) for tip in fingertips]
        compactness_score = max(0, 1 - np.mean(distances_to_palm) * 4)
        
        return (flexion_score * 0.6 + compactness_score * 0.4)
    
    def _calculate_grasping_score(self, points: np.ndarray) -> float:
        """Calcular score para gesto de tomar objeto"""
        # Flexión parcial
        extensions = self._calculate_finger_extensions(points)
        ideal_extension = 0.55
        extension_scores = [
            max(0, 1 - abs(ext - ideal_extension) * 3) for ext in extensions[1:]
        ]
        partial_flexion_score = np.mean(extension_scores)
        
        # Apertura controlada
        fingertips = [points[4], points[8], points[12], points[16], points[20]]
        center = np.mean(fingertips, axis=0)
        compactness = np.mean([self._calculate_distance(tip, center) for tip in fingertips])
        aperture_score = min(1.0, compactness * 5)
        
        return (partial_flexion_score * 0.6 + aperture_score * 0.4)
    
    def _draw_connection_status(self, frame: np.ndarray, is_connected: bool, hand_detected: bool):
        """Dibujar estado de conexión en el frame"""
        status_text = ""
        status_color = (0, 255, 0)  # Verde por defecto
        
        if not is_connected:
            status_text = "SENSOR DESCONECTADO - Muestra tu mano"
            status_color = (0, 0, 255)  # Rojo
        elif hand_detected:
            status_text = "MANO DETECTADA"
            status_color = (0, 255, 0)  # Verde
        else:
            status_text = "BUSCANDO MANO..."
            status_color = (0, 165, 255)  # Naranja
        
        # Dibujar fondo para el texto
        cv2.rectangle(frame, (10, 10), (400, 50), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (400, 50), status_color, 2)
        
        # Dibujar texto
        cv2.putText(frame, status_text, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Indicador visual adicional
        indicator_color = (0, 255, 0) if is_connected else (0, 0, 255)
        cv2.circle(frame, (frame.shape[1] - 30, 30), 15, indicator_color, -1)
    
    def detect_gesture(self, features: Dict) -> Tuple[int, str]:
        """
        Detectar automáticamente el gesto basado en las características
        
        Args:
            features: Diccionario de características
            
        Returns:
            Tuple[int, str]: ID del gesto y nombre del gesto
        """
        if not features:
            return 0, "REPOSO"
        
        gesture_names = ["REPOSO", "CERRAR_MANO", "PINZA", "SALUDAR", "TOMAR_OBJETO"]
        
        # Obtener scores
        pinch_score = features.get('pinch_score', 0)
        open_hand_score = features.get('open_hand_score', 0)
        closed_fist_score = features.get('closed_fist_score', 0)
        grasping_score = features.get('grasping_score', 0)
        
        # Umbrales
        PINCH_THRESHOLD = 0.4
        OPEN_HAND_THRESHOLD = 0.4
        CLOSED_FIST_THRESHOLD = 0.5
        GRASPING_THRESHOLD = 0.35
        
        # Lógica de detección con prioridades
        if (pinch_score > PINCH_THRESHOLD and 
            pinch_score > closed_fist_score * 1.3 and 
            pinch_score > grasping_score * 1.3):
            return 2, gesture_names[2]  # PINZA
        
        elif (closed_fist_score > CLOSED_FIST_THRESHOLD and 
              closed_fist_score > grasping_score * 1.4):
            return 1, gesture_names[1]  # CERRAR_MANO
        
        elif (open_hand_score > OPEN_HAND_THRESHOLD and 
              open_hand_score > grasping_score * 1.2):
            return 3, gesture_names[3]  # SALUDAR
        
        elif (grasping_score > GRASPING_THRESHOLD and 
              grasping_score > open_hand_score and
              closed_fist_score < 0.6):
            return 4, gesture_names[4]  # TOMAR_OBJETO
        
        return 0, gesture_names[0]  # REPOSO
    
    def cleanup(self):
        """Limpiar recursos de MediaPipe"""
        if hasattr(self, 'hands'):
            self.hands.close()

# Funciones de utilidad para usar el procesador
def create_hand_processor(confidence: float = 0.7) -> MediaPipeHandProcessor:
    """Crear una instancia del procesador de manos"""
    return MediaPipeHandProcessor(min_detection_confidence=confidence)

def process_video_frame(processor: MediaPipeHandProcessor, frame: np.ndarray) -> Tuple[np.ndarray, Dict, bool]:
    """Procesar un frame de video y retornar resultados"""
    return processor.process_frame(frame)

def extract_features_from_frame(processor: MediaPipeHandProcessor, frame: np.ndarray) -> Dict:
    """Extraer solo las características de un frame"""
    _, features, _ = processor.process_frame(frame)
    return features