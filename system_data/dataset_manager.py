"""
Dataset Manager - Módulo para gestión de datasets de gestos
Autor: Sistema de Dataset de Gestos
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json

class GestureDatasetManager:
    """Gestor de datasets de gestos con funcionalidades avanzadas"""
    
    def __init__(self):
        """Inicializar el gestor de dataset"""
        self.dataset = []
        self.session_info = {
            'start_time': None,
            'total_samples': 0,
            'gestures_captured': [],
            'series_completed': 0,
            'current_session_id': None
        }
        self.gesture_names = ["REPOSO", "CERRAR_MANO", "PINZA", "SALUDAR", "TOMAR_OBJETO"]
    
    def start_new_session(self, session_config: Dict) -> str:
        """
        Iniciar una nueva sesión de captura
        
        Args:
            session_config: Configuración de la sesión
            
        Returns:
            str: ID de la sesión creada
        """
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.session_info = {
            'session_id': session_id,
            'start_time': datetime.now(),
            'total_samples': 0,
            'gestures_captured': session_config.get('selected_gestures', []),
            'series_planned': session_config.get('series_count', 1),
            'series_completed': 0,
            'duration_per_gesture': session_config.get('duration_per_gesture', 5),
            'rest_time': session_config.get('rest_time', 3),
            'current_session_id': session_id
        }
        
        print(f"🎯 Nueva sesión iniciada: {session_id}")
        print(f"📋 Gestos a capturar: {', '.join(self.session_info['gestures_captured'])}")
        print(f"🔄 Series planificadas: {self.session_info['series_planned']}")
        
        return session_id
    
    def add_sample(self, 
                   features: Dict, 
                   gesture_id: int, 
                   gesture_name: str,
                   series_number: int = 1,
                   additional_info: Optional[Dict] = None) -> bool:
        """
        Agregar una muestra al dataset
        
        Args:
            features: Características extraídas de MediaPipe
            gesture_id: ID del gesto (0-4)
            gesture_name: Nombre del gesto
            series_number: Número de serie actual
            additional_info: Información adicional opcional
            
        Returns:
            bool: True si se agregó exitosamente
        """
        if not features:
            print("⚠️ No se pueden agregar muestras sin características")
            return False
        
        # Crear punto de datos
        data_point = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_info.get('current_session_id', 'unknown'),
            'sample_number': len(self.dataset) + 1,
            'series_number': series_number,
            'gesture_id': gesture_id,
            'gesture_name': gesture_name,
        }
        
        # Agregar características de MediaPipe
        data_point.update(features)
        
        # Agregar información adicional si está disponible
        if additional_info:
            data_point.update(additional_info)
        
        # Agregar al dataset
        self.dataset.append(data_point)
        self.session_info['total_samples'] += 1
        
        return True
    
    def get_dataset_statistics(self) -> Dict:
        """
        Obtener estadísticas del dataset actual
        
        Returns:
            Dict: Estadísticas completas del dataset
        """
        if not self.dataset:
            return {
                'total_samples': 0,
                'gestures_distribution': {},
                'series_distribution': {},
                'session_info': self.session_info,
                'quality_metrics': {}
            }
        
        df = pd.DataFrame(self.dataset)
        
        # Distribución por gestos
        gesture_counts = df['gesture_name'].value_counts().to_dict()
        
        # Distribución por series
        series_counts = df['series_number'].value_counts().to_dict() if 'series_number' in df.columns else {}
        
        # Métricas de calidad (si están disponibles)
        quality_metrics = {}
        quality_columns = ['pinch_score', 'open_hand_score', 'closed_fist_score', 'grasping_score']
        for col in quality_columns:
            if col in df.columns:
                quality_metrics[col] = {
                    'mean': df[col].mean(),
                    'std': df[col].std(),
                    'min': df[col].min(),
                    'max': df[col].max()
                }
        
        # Calcular progreso de la sesión
        total_planned = len(self.session_info.get('gestures_captured', [])) * self.session_info.get('series_planned', 1)
        progress_percentage = (len(self.dataset) / (total_planned * 100)) * 100 if total_planned > 0 else 0
        
        return {
            'total_samples': len(self.dataset),
            'gestures_distribution': gesture_counts,
            'series_distribution': series_counts,
            'session_info': self.session_info,
            'quality_metrics': quality_metrics,
            'progress_percentage': min(progress_percentage, 100),
            'samples_per_gesture_target': 100,  # Objetivo recomendado
            'session_duration': self._calculate_session_duration()
        }
    
    def save_dataset(self, 
                     filename: Optional[str] = None, 
                     include_metadata: bool = True) -> Tuple[bool, str]:
        """
        Guardar el dataset a un archivo CSV
        
        Args:
            filename: Nombre del archivo (opcional)
            include_metadata: Si incluir archivo de metadatos
            
        Returns:
            Tuple[bool, str]: Éxito y ruta del archivo guardado
        """
        if not self.dataset:
            return False, "No hay datos para guardar"
        
        # Generar nombre de archivo si no se proporciona
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = self.session_info.get('session_id', 'unknown')
            filename = f"gesture_dataset_{session_id}_{timestamp}.csv"
        
        try:
            # Crear DataFrame y guardar
            df = pd.DataFrame(self.dataset)
            df.to_csv(filename, index=False)
            
            # Guardar metadatos si se solicita
            if include_metadata:
                metadata_filename = filename.replace('.csv', '_metadata.json')
                self._save_metadata(metadata_filename)
            
            # Generar reporte de guardado
            stats = self.get_dataset_statistics()
            report = self._generate_save_report(filename, stats)
            
            print(f"✅ Dataset guardado exitosamente: {filename}")
            print(report)
            
            return True, filename
            
        except Exception as e:
            error_msg = f"Error al guardar dataset: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def load_dataset(self, filename: str) -> Tuple[bool, str]:
        """
        Cargar un dataset desde archivo CSV
        
        Args:
            filename: Ruta del archivo CSV
            
        Returns:
            Tuple[bool, str]: Éxito y mensaje de resultado
        """
        try:
            if not os.path.exists(filename):
                return False, f"Archivo no encontrado: {filename}"
            
            df = pd.read_csv(filename)
            self.dataset = df.to_dict('records')
            
            # Intentar cargar metadatos
            metadata_filename = filename.replace('.csv', '_metadata.json')
            if os.path.exists(metadata_filename):
                self._load_metadata(metadata_filename)
            
            print(f"✅ Dataset cargado: {len(self.dataset)} muestras")
            return True, f"Dataset cargado exitosamente: {len(self.dataset)} muestras"
            
        except Exception as e:
            error_msg = f"Error al cargar dataset: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def clear_dataset(self) -> bool:
        """
        Limpiar el dataset actual
        
        Returns:
            bool: True si se limpió exitosamente
        """
        self.dataset.clear()
        self.session_info['total_samples'] = 0
        print("🗑️ Dataset limpiado")
        return True
    
    def get_gesture_recommendations(self) -> Dict:
        """
        Obtener recomendaciones para mejorar el dataset
        
        Returns:
            Dict: Recomendaciones específicas
        """
        stats = self.get_dataset_statistics()
        recommendations = {
            'urgent': [],
            'suggested': [],
            'quality_improvements': []
        }
        
        # Verificar balance entre gestos
        gesture_counts = stats['gestures_distribution']
        min_samples_per_gesture = 50
        ideal_samples_per_gesture = 100
        
        for gesture in self.gesture_names:
            count = gesture_counts.get(gesture, 0)
            
            if count < min_samples_per_gesture:
                recommendations['urgent'].append(
                    f"⚠️ {gesture}: Solo {count} muestras (mínimo {min_samples_per_gesture})"
                )
            elif count < ideal_samples_per_gesture:
                recommendations['suggested'].append(
                    f"📈 {gesture}: {count} muestras (ideal {ideal_samples_per_gesture})"
                )
        
        # Verificar calidad de los gestos
        quality_metrics = stats['quality_metrics']
        for metric, values in quality_metrics.items():
            if values['mean'] < 0.3:
                recommendations['quality_improvements'].append(
                    f"🎯 Mejorar calidad de {metric}: promedio {values['mean']:.2f}"
                )
        
        # Recomendaciones generales
        if stats['total_samples'] < 200:
            recommendations['suggested'].append(
                f"📊 Total de muestras: {stats['total_samples']} (recomendado mínimo 200)"
            )
        
        return recommendations
    
    def export_for_ml(self, 
                      output_dir: str = "ml_export",
                      train_test_split: float = 0.8) -> Tuple[bool, Dict]:
        """
        Exportar dataset optimizado para machine learning
        
        Args:
            output_dir: Directorio de salida
            train_test_split: Proporción para entrenamiento
            
        Returns:
            Tuple[bool, Dict]: Éxito y información de los archivos exportados
        """
        if not self.