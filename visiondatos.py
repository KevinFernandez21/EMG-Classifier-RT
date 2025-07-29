print("🤖 SISTEMA MEDIAPIPE AVANZADO - DATASET DE GESTOS")
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import os
from datetime import datetime
import math

class MediaPipeGestureDataset:
    def __init__(self):
        # Inicializar MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Configuración del dataset
        self.dataset = []
        self.recording = False
        self.current_gesture = 0  # 0=nada, 1=cerrar, 2=pinza, 3=saludo, 4=tomar
        self.gesture_names = ["REPOSO", "CERRAR_MANO", "PINZA", "SALUDAR", "TOMAR_OBJETO"]
        
        # Contadores
        self.frame_count = 0
        self.session_start = None
        
        print("🤖 SISTEMA MEDIAPIPE PARA DATASET DE GESTOS")
        print("=" * 50)
        print("CONTROLES:")
        print("📹 ESPACIO: Iniciar/Detener grabación")
        print("🔢 1: Cerrar mano")
        print("🔢 2: Pinza (pulgar + índice)")
        print("🔢 3: Saludar (palma abierta)")
        print("🔢 4: Tomar objeto")
        print("🔢 0: Reposo (sin gesto)")
        print("💾 S: Guardar dataset")
        print("❌ Q: Salir")
        print("=" * 50)
    
    def calculate_hand_features(self, landmarks):
        """Calcular características avanzadas de la mano desde los landmarks"""
        features = {}
        
        # Convertir landmarks a array numpy
        points = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])
        
        # ===== CARACTERÍSTICAS BÁSICAS =====
        
        # 1. DISTANCIAS CLAVE
        thumb_tip = points[4]    # Punta del pulgar
        index_tip = points[8]    # Punta del índice
        middle_tip = points[12]  # Punta del medio
        ring_tip = points[16]    # Punta del anular
        pinky_tip = points[20]   # Punta del meñique
        wrist = points[0]        # Muñeca
        
        # Distancia pulgar-índice (crítica para pinza)
        features['thumb_index_distance'] = np.linalg.norm(thumb_tip - index_tip)
        
        # Distancias de cada dedo a la muñeca
        features['thumb_wrist_distance'] = np.linalg.norm(thumb_tip - wrist)
        features['index_wrist_distance'] = np.linalg.norm(index_tip - wrist)
        features['middle_wrist_distance'] = np.linalg.norm(middle_tip - wrist)
        features['ring_wrist_distance'] = np.linalg.norm(ring_tip - wrist)
        features['pinky_wrist_distance'] = np.linalg.norm(pinky_tip - wrist)
        
        # 2. EXTENSIÓN DE DEDOS (clave para saludo)
        finger_extensions = self.calculate_finger_extensions(points)
        for i, ext in enumerate(finger_extensions):
            features[f'finger_{i}_extension'] = ext
        
        # 3. SEPARACIÓN ENTRE DEDOS (importante para saludo vs tomar)
        features['index_middle_separation'] = np.linalg.norm(index_tip - middle_tip)
        features['middle_ring_separation'] = np.linalg.norm(middle_tip - ring_tip)
        features['ring_pinky_separation'] = np.linalg.norm(ring_tip - pinky_tip)
        
        # Separación promedio (dedos abiertos vs cerrados)
        avg_separation = (features['index_middle_separation'] + 
                         features['middle_ring_separation'] + 
                         features['ring_pinky_separation']) / 3
        features['fingers_average_separation'] = avg_separation
        
        # 4. ÁNGULOS DE FLEXIÓN MEJORADOS
        finger_angles = self.calculate_finger_angles_improved(points)
        for i, angle in enumerate(finger_angles):
            features[f'finger_{i}_flexion_angle'] = angle
        
        # 5. APERTURA TOTAL DE LA MANO
        # Span entre dedos extremos
        features['hand_span_thumb_pinky'] = np.linalg.norm(thumb_tip - pinky_tip)
        features['hand_span_index_pinky'] = np.linalg.norm(index_tip - pinky_tip)
        
        # 6. CENTRO DE GRAVEDAD DE LOS DEDOS
        fingertips = [thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip]
        finger_center = np.mean(fingertips, axis=0)
        features['fingertips_center_x'] = finger_center[0]
        features['fingertips_center_y'] = finger_center[1]
        
        # Distancia del centro de dedos a la muñeca
        features['fingertips_center_to_wrist'] = np.linalg.norm(finger_center - wrist)
        
        # 7. COMPACIDAD Y DISPERSIÓN
        # Qué tan agrupados están los dedos
        distances_to_center = [np.linalg.norm(tip - finger_center) for tip in fingertips]
        features['fingertips_compactness'] = np.mean(distances_to_center)
        features['fingertips_spread'] = np.std(distances_to_center)
        
        # 8. ORIENTACIÓN DE LA PALMA (mejorada)
        palm_normal = self.calculate_palm_normal(points)
        features['palm_normal_x'] = palm_normal[0]
        features['palm_normal_y'] = palm_normal[1]
        features['palm_normal_z'] = palm_normal[2] if len(palm_normal) > 2 else 0
        
        # 9. CURVATURA INDIVIDUAL DE CADA DEDO
        finger_curvatures = self.calculate_all_finger_curvatures(points)
        for i, curv in enumerate(finger_curvatures):
            features[f'finger_{i}_curvature'] = curv
        
        # 10. CARACTERÍSTICAS ESPECÍFICAS PARA GESTOS
        
        # Para PINZA: precisión del agarre
        features['pinch_precision'] = self.calculate_pinch_precision(points)
        
        # Para SALUDO: dedos extendidos y separados
        features['open_hand_score'] = self.calculate_open_hand_score(points)
        
        # Para CERRAR MANO: todos los dedos flexionados
        features['closed_fist_score'] = self.calculate_closed_fist_score(points)
        
        # Para TOMAR OBJETO: forma de copa/agarre
        features['grasping_score'] = self.calculate_grasping_score(points)
        
        return features
    
    def calculate_finger_extensions(self, points):
        """Calcular qué tan extendido está cada dedo"""
        extensions = []
        
        # Definir articulaciones de cada dedo
        finger_joints = [
            [1, 2, 3, 4],      # Pulgar: base, art1, art2, punta
            [5, 6, 7, 8],      # Índice
            [9, 10, 11, 12],   # Medio
            [13, 14, 15, 16],  # Anular
            [17, 18, 19, 20]   # Meñique
        ]
        
        wrist = points[0]
        
        for joints in finger_joints:
            base = points[joints[0]]
            tip = points[joints[3]]
            
            # Distancia directa base-punta vs distancia articulada
            direct_distance = np.linalg.norm(tip - base)
            
            # Distancia siguiendo las articulaciones
            articulated_distance = 0
            for i in range(len(joints) - 1):
                articulated_distance += np.linalg.norm(points[joints[i+1]] - points[joints[i]])
            
            # Ratio de extensión (1.0 = completamente extendido)
            extension = direct_distance / (articulated_distance + 1e-6)
            extensions.append(extension)
        
        return extensions
    
    def calculate_finger_angles_improved(self, points):
        """Calcular ángulos de flexión mejorados"""
        angles = []
        
        # Articulaciones mejoradas para cada dedo
        finger_angle_points = [
            [2, 3, 4],         # Pulgar
            [6, 7, 8],         # Índice  
            [10, 11, 12],      # Medio
            [14, 15, 16],      # Anular
            [18, 19, 20]       # Meñique
        ]
        
        for joints in finger_angle_points:
            p1, p2, p3 = points[joints[0]], points[joints[1]], points[joints[2]]
            
            # Vectores desde la articulación media
            v1 = p1 - p2
            v2 = p3 - p2
            
            # Calcular ángulo
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            angle = np.arccos(cos_angle)
            angles.append(np.degrees(angle))
        
        return angles
    
    def calculate_palm_normal(self, points):
        """Calcular vector normal de la palma"""
        # Usar puntos de la base de los dedos para definir el plano de la palma
        palm_points = [points[0], points[5], points[9], points[13], points[17]]  # Muñeca y bases
        
        # Calcular centroide
        centroid = np.mean(palm_points, axis=0)
        
        # Vectores desde el centroide
        vectors = [p - centroid for p in palm_points[:3]]
        
        # Producto cruzado para obtener normal
        normal = np.cross(vectors[0], vectors[1])
        normal = normal / (np.linalg.norm(normal) + 1e-6)
        
        return normal
    
    def calculate_all_finger_curvatures(self, points):
        """Calcular curvatura de todos los dedos"""
        curvatures = []
        
        finger_sets = [
            [1, 2, 3, 4],      # Pulgar
            [5, 6, 7, 8],      # Índice
            [9, 10, 11, 12],   # Medio
            [13, 14, 15, 16],  # Anular
            [17, 18, 19, 20]   # Meñique
        ]
        
        for finger in finger_sets:
            total_curvature = 0
            for i in range(len(finger) - 2):
                p1, p2, p3 = points[finger[i]], points[finger[i+1]], points[finger[i+2]]
                
                v1 = p1 - p2
                v2 = p3 - p2
                
                cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
                cos_angle = np.clip(cos_angle, -1.0, 1.0)
                angle = np.arccos(cos_angle)
                total_curvature += angle
            
            curvatures.append(total_curvature)
        
        return curvatures
    
    def calculate_pinch_precision(self, points):
        """Calcular precisión del gesto de pinza"""
        thumb_tip = points[4]
        index_tip = points[8]
        
        # Distancia entre pulgar e índice
        distance = np.linalg.norm(thumb_tip - index_tip)
        
        # Ángulo entre pulgar e índice
        thumb_direction = points[4] - points[3]
        index_direction = points[8] - points[7]
        
        cos_angle = np.dot(thumb_direction, index_direction) / (
            np.linalg.norm(thumb_direction) * np.linalg.norm(index_direction) + 1e-6)
        angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
        
        # Score de pinza (mayor score = mejor pinza)
        distance_score = max(0, 1 - distance * 10)  # Penalizar distancia
        angle_score = max(0, 1 - abs(angle - np.pi/2) / (np.pi/2))  # Ángulo ideal ~90°
        
        return (distance_score + angle_score) / 2
    
    def calculate_open_hand_score(self, points):
        """Calcular score para mano abierta (saludo) - MEJORADO"""
        # 1. Todos los dedos (excepto pulgar) deben estar muy extendidos
        extensions = self.calculate_finger_extensions(points)
        main_fingers_extensions = extensions[1:4]  # Índice, medio, anular (excluir meñique por anatomía)
        extension_score = np.mean(main_fingers_extensions)  # Debe ser alto
        
        # 2. Los dedos deben estar MUY separados entre sí
        fingertips = [points[8], points[12], points[16], points[20]]  # Sin pulgar
        separations = []
        
        # Distancia entre dedos consecutivos
        for i in range(len(fingertips) - 1):
            separation = np.linalg.norm(fingertips[i] - fingertips[i+1])
            separations.append(separation)
        
        # También medir separación total (índice a meñique)
        total_span = np.linalg.norm(fingertips[0] - fingertips[-1])
        
        avg_separation = np.mean(separations)
        separation_score = min(1.0, avg_separation * 6 + total_span * 2)  # Más peso a separación
        
        # 3. Los dedos deben estar en el mismo "plano" (todos extendidos hacia adelante)
        # Calcular varianza en la dirección Z (profundidad)
        z_coords = [points[8][2], points[12][2], points[16][2], points[20][2]]
        z_variance = np.var(z_coords)
        planarity_score = max(0, 1 - z_variance * 50)  # Penalizar mucha varianza
        
        # 4. La mano debe estar "abierta" - dedos alejados del centro de la palma
        palm_center = np.mean([points[0], points[5], points[9], points[13], points[17]], axis=0)
        distances_from_palm = [np.linalg.norm(tip - palm_center) for tip in fingertips]
        avg_distance_from_palm = np.mean(distances_from_palm)
        openness_score = min(1.0, avg_distance_from_palm * 3)  # Debe estar lejos de la palma
        
        # 5. Los ángulos de flexión deben ser mínimos (dedos rectos)
        finger_angles = self.calculate_finger_angles_improved(points)
        # Ángulos pequeños = dedos rectos
        straightness_score = max(0, 1 - np.mean(finger_angles[1:]) / 180)  # Normalizar a 0-1
        
        # Combinar scores con pesos para saludo
        final_score = (
            extension_score * 0.25 +       # Dedos extendidos
            separation_score * 0.35 +      # Separación es clave
            planarity_score * 0.15 +       # Dedos en el mismo plano
            openness_score * 0.15 +        # Lejos de la palma
            straightness_score * 0.1       # Dedos rectos
        )
        
        return final_score
    
    def calculate_closed_fist_score(self, points):
        """Calcular score para puño cerrado"""
        # 1. Todos los dedos deben estar flexionados
        extensions = self.calculate_finger_extensions(points)
        flexion_score = 1 - np.mean(extensions[1:])  # Menos extensión = más flexión
        
        # 2. Las puntas de los dedos deben estar cerca de la palma
        fingertips = [points[8], points[12], points[16], points[20]]
        palm_center = np.mean([points[0], points[5], points[9], points[13], points[17]], axis=0)
        
        distances_to_palm = [np.linalg.norm(tip - palm_center) for tip in fingertips]
        compactness_score = max(0, 1 - np.mean(distances_to_palm) * 3)
        
        # 3. Los dedos deben estar juntos
        fingertip_spread = np.std([np.linalg.norm(tip - np.mean(fingertips, axis=0)) for tip in fingertips])
        grouping_score = max(0, 1 - fingertip_spread * 10)
        
        return (flexion_score * 0.5 + compactness_score * 0.3 + grouping_score * 0.2)
    
    def calculate_grasping_score(self, points):
        """Calcular score para gesto de tomar objeto"""
        # 1. Los dedos forman una "copa" o "garra"
        fingertips = [points[4], points[8], points[12], points[16], points[20]]
        center = np.mean(fingertips, axis=0)
        
        # 2. Todos los dedos apuntan hacia un punto central
        palm_center = np.mean([points[0], points[5], points[9], points[13], points[17]], axis=0)
        convergence_vectors = [tip - palm_center for tip in fingertips]
        
        # Calcular qué tan paralelos son los vectores
        convergence_score = 0
        for i in range(len(convergence_vectors)):
            for j in range(i+1, len(convergence_vectors)):
                v1 = convergence_vectors[i] / (np.linalg.norm(convergence_vectors[i]) + 1e-6)
                v2 = convergence_vectors[j] / (np.linalg.norm(convergence_vectors[j]) + 1e-6)
                dot_product = np.dot(v1, v2)
                convergence_score += max(0, dot_product)
        
        convergence_score /= (len(convergence_vectors) * (len(convergence_vectors) - 1) / 2)
        
        # 3. Flexión parcial (no completamente cerrado, no completamente abierto)
        extensions = self.calculate_finger_extensions(points)
        partial_flexion_score = 1 - abs(np.mean(extensions[1:]) - 0.5) * 2  # Óptimo en 0.5
        
        return (convergence_score * 0.6 + partial_flexion_score * 0.4)
    
    def detect_gesture_automatically(self, features):
        """Detectar gesto automáticamente con lógica mejorada y umbrales ajustados"""
        
        # Obtener scores específicos
        pinch_score = features.get('pinch_precision', 0)
        open_hand_score = features.get('open_hand_score', 0)
        closed_fist_score = features.get('closed_fist_score', 0)
        grasping_score = features.get('grasping_score', 0)
        
        # Umbrales más estrictos y ajustados
        PINCH_THRESHOLD = 0.4       # Más bajo para detectar mejor
        OPEN_HAND_THRESHOLD = 0.4   # Más bajo para saludo
        CLOSED_FIST_THRESHOLD = 0.5 # Mantener alto para puño
        GRASPING_THRESHOLD = 0.35   # Más bajo para tomar objeto
        
        # Crear array de scores
        scores = [
            0,  # REPOSO (por defecto)
            closed_fist_score,
            pinch_score,
            open_hand_score,
            grasping_score
        ]
        
        thresholds = [0, CLOSED_FIST_THRESHOLD, PINCH_THRESHOLD, OPEN_HAND_THRESHOLD, GRASPING_THRESHOLD]
        
        # Lógica de prioridad mejorada
        # 1. Si hay un gesto que supera significativamente a los demás
        max_score = max(scores[1:])  # Excluir reposo
        max_idx = scores.index(max_score)
        
        # 2. Verificar que supere el umbral Y que sea claramente superior
        if max_score > thresholds[max_idx]:
            # Verificar que sea al menos 20% mejor que el segundo mejor
            sorted_scores = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
            best_gesture, best_score = sorted_scores[0]
            second_best_gesture, second_best_score = sorted_scores[1]
            
            # Si el mejor gesto es significativamente mejor que el segundo
            if best_score > second_best_score * 1.2 or best_score > 0.6:
                return best_gesture
        
        # 3. Casos especiales para diferenciación
        
        # PINZA: Debe tener score alto Y otros scores bajos
        if (pinch_score > PINCH_THRESHOLD and 
            pinch_score > closed_fist_score * 1.3 and 
            pinch_score > grasping_score * 1.3):
            return 2  # PINZA
        
        # PUÑO CERRADO: Debe ser claramente superior a grasping
        if (closed_fist_score > CLOSED_FIST_THRESHOLD and 
            closed_fist_score > grasping_score * 1.4):
            return 1  # CERRAR_MANO
        
        # SALUDO: Dedos extendidos y separados
        if (open_hand_score > OPEN_HAND_THRESHOLD and 
            open_hand_score > grasping_score * 1.2):
            return 3  # SALUDAR
        
        # TOMAR OBJETO: Solo si no es claramente ninguno de los otros
        if (grasping_score > GRASPING_THRESHOLD and 
            grasping_score > open_hand_score and
            closed_fist_score < 0.6):  # No debe ser puño cerrado
            return 4  # TOMAR_OBJETO
        
        return 0  # REPOSO si ningún gesto es claro
    
    def save_dataset(self):
        """Guardar dataset en CSV"""
        if not self.dataset:
            print("❌ No hay datos para guardar")
            return
        
        # Crear DataFrame
        df = pd.DataFrame(self.dataset)
        
        # Generar nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gesture_dataset_mediapipe_{timestamp}.csv"
        
        # Guardar
        df.to_csv(filename, index=False)
        
        print(f"✅ Dataset guardado: {filename}")
        print(f"📊 Total de registros: {len(df)}")
        print(f"📈 Distribución por gesto:")
        
        gesture_counts = df['gesture_name'].value_counts()
        total_samples = len(df)
        
        for gesture, count in gesture_counts.items():
            percentage = (count / total_samples) * 100
            print(f"   {gesture}: {count} muestras ({percentage:.1f}%)")
        
        # Mostrar estadísticas de calidad
        if 'pinch_score' in df.columns:
            print(f"\n📋 Estadísticas de calidad:")
            print(f"   Promedio score pinza: {df['pinch_score'].mean():.3f}")
            print(f"   Promedio score saludo: {df['open_hand_score'].mean():.3f}")
            print(f"   Promedio score cerrar: {df['closed_fist_score'].mean():.3f}")
            print(f"   Promedio score tomar: {df['grasping_score'].mean():.3f}")
        
        # Recomendaciones
        print(f"\n💡 Recomendaciones:")
        min_samples = 100
        for gesture in ["REPOSO", "CERRAR_MANO", "PINZA", "SALUDAR", "TOMAR_OBJETO"]:
            count = gesture_counts.get(gesture, 0)
            if count < min_samples:
                print(f"   ⚠️ {gesture}: Necesita más muestras ({count}/{min_samples})")
            else:
                print(f"   ✅ {gesture}: Suficientes muestras ({count})")
    
    def run(self):
        """Ejecutar el sistema principal"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ No se pudo abrir la cámara")
            return
        
        print("🎥 Cámara iniciada. Presiona ESPACIO para comenzar a grabar.")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Voltear frame horizontalmente
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Procesar con MediaPipe
            results = self.hands.process(rgb_frame)
            
            # Dibujar landmarks
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_drawing.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                    
                    # Calcular características
                    features = self.calculate_hand_features(hand_landmarks)
                    
                    # Detectar gesto automáticamente
                    auto_gesture = self.detect_gesture_automatically(features)
                    
                    # Mostrar scores de detección para debugging
                    pinch_score = features.get('pinch_precision', 0)
                    open_hand_score = features.get('open_hand_score', 0)
                    closed_fist_score = features.get('closed_fist_score', 0)
                    grasping_score = features.get('grasping_score', 0)
                    
                    # Guardar datos si está grabando
                    if self.recording:
                        data_point = {
                            'timestamp': datetime.now().isoformat(),
                            'frame_number': self.frame_count,
                            'gesture_id': self.current_gesture,
                            'gesture_name': self.gesture_names[self.current_gesture],
                            'auto_detected_gesture': auto_gesture,
                            'auto_detected_name': self.gesture_names[auto_gesture],
                            'pinch_score': pinch_score,
                            'open_hand_score': open_hand_score,
                            'closed_fist_score': closed_fist_score,
                            'grasping_score': grasping_score
                        }
                        
                        # Agregar todas las características
                        data_point.update(features)
                        
                        self.dataset.append(data_point)
                        self.frame_count += 1
                    
                    # Mostrar gesto detectado automáticamente con color
                    auto_color = (0, 255, 0) if auto_gesture == self.current_gesture else (0, 165, 255)
                    cv2.putText(frame, f"Detectado: {self.gesture_names[auto_gesture]}", 
                              (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, auto_color, 2)
                    
                    # Mostrar scores de detección
                    y_offset = 160
                    cv2.putText(frame, f"Cerrar: {closed_fist_score:.2f}", 
                              (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(frame, f"Pinza: {pinch_score:.2f}", 
                              (150, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(frame, f"Saludo: {open_hand_score:.2f}", 
                              (10, y_offset + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    cv2.putText(frame, f"Tomar: {grasping_score:.2f}", 
                              (150, y_offset + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    # Mostrar extensión de dedos
                    extensions = [features.get(f'finger_{i}_extension', 0) for i in range(5)]
                    cv2.putText(frame, f"Ext: {extensions[1]:.2f} {extensions[2]:.2f} {extensions[3]:.2f} {extensions[4]:.2f}", 
                              (10, y_offset + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            
            # Mostrar información en pantalla
            status_color = (0, 255, 0) if self.recording else (0, 0, 255)
            status_text = "GRABANDO" if self.recording else "PAUSADO"
            
            cv2.putText(frame, f"Estado: {status_text}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
            
            cv2.putText(frame, f"Gesto Manual: {self.gesture_names[self.current_gesture]}", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            cv2.putText(frame, f"Muestras: {len(self.dataset)}", 
                       (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Mostrar distribución de gestos
            if self.dataset:
                gesture_counts = {}
                for data in self.dataset:
                    gesture_name = data['gesture_name']
                    gesture_counts[gesture_name] = gesture_counts.get(gesture_name, 0) + 1
                
                y_pos = 220
                cv2.putText(frame, "Distribución:", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                for i, (gesture, count) in enumerate(gesture_counts.items()):
                    y_pos += 20
                    cv2.putText(frame, f"{gesture}: {count}", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
            
            # Mostrar frame
            cv2.imshow('MediaPipe Gesture Dataset Creator', frame)
            
            # Manejar teclas
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' '):  # Espacio - toggle grabación
                self.recording = not self.recording
                if self.recording:
                    self.session_start = datetime.now()
                    print(f"🔴 INICIANDO GRABACIÓN - Gesto: {self.gesture_names[self.current_gesture]}")
                else:
                    print("⏸️ GRABACIÓN PAUSADA")
            
            elif key == ord('0'):  # Reposo
                self.current_gesture = 0
                print(f"👋 Gesto seleccionado: {self.gesture_names[0]}")
            
            elif key == ord('1'):  # Cerrar mano
                self.current_gesture = 1
                print(f"✊ Gesto seleccionado: {self.gesture_names[1]}")
            
            elif key == ord('2'):  # Pinza
                self.current_gesture = 2
                print(f"🤏 Gesto seleccionado: {self.gesture_names[2]}")
            
            elif key == ord('3'):  # Saludar
                self.current_gesture = 3
                print(f"🖐️ Gesto seleccionado: {self.gesture_names[3]}")
            
            elif key == ord('4'):  # Tomar objeto
                self.current_gesture = 4
                print(f"🤲 Gesto seleccionado: {self.gesture_names[4]}")
            
            elif key == ord('r') or key == ord('R'):  # Reset dataset
                if self.dataset:
                    self.dataset.clear()
                    self.frame_count = 0
                    print("🔄 Dataset reseteado")
                else:
                    print("⚠️ Dataset ya está vacío")
            
            elif key == ord('s') or key == ord('S'):  # Guardar
                self.save_dataset()
            
            elif key == ord('q') or key == ord('Q'):  # Salir
                break
        
        # Guardar automáticamente al salir
        if self.dataset:
            self.save_dataset()
        
        cap.release()
        cv2.destroyAllWindows()

def main():
    creator = MediaPipeGestureDataset()
    creator.run()

if __name__ == "__main__":
    main()