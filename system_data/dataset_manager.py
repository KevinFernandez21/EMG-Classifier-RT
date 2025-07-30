"""
Dataset Manager - CORREGIDO para evitar duplicados
Solo funciones esenciales para guardar CSV limpio
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class GestureDatasetManager:
    """Gestor simplificado de datasets EMG - CORREGIDO"""
    
    def __init__(self):
        """Inicializar el gestor de dataset"""
        self.dataset = []
        self.session_info = {
            'start_time': None,
            'total_samples': 0,
            'current_session_id': None
        }
        self.gesture_names = ["REPOSO", "CERRAR_MANO", "PINZA", "SALUDAR", "TOMAR_OBJ"]
    
    def start_new_session(self, session_config: Dict) -> str:
        """Iniciar una nueva sesión de captura"""
        session_id = f"emg_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.session_info = {
            'session_id': session_id,
            'start_time': datetime.now(),
            'total_samples': 0,
            'current_session_id': session_id
        }
        
        # Limpiar dataset anterior
        self.dataset.clear()
        
        print(f"🎯 Nueva sesión EMG iniciada: {session_id}")
        return session_id
    
    def add_sample(self, 
                   features: Dict, 
                   gesture_id: int, 
                   gesture_name: str,
                   series_number: int = 1,
                   additional_info: Optional[Dict] = None) -> bool:
        """Agregar una muestra EMG al dataset - ESTRUCTURA LIMPIA"""
        if not features:
            return False
        
        try:
            # Crear punto de datos LIMPIO - una sola estructura
            data_point = {
                # Información básica de la muestra
                'timestamp': datetime.now().isoformat(),
                'session_id': str(self.session_info.get('current_session_id', 'unknown')),
                'sample_number': int(len(self.dataset) + 1),
                'series_number': int(series_number),
                
                # Información del gesto
                'gesture_id': int(gesture_id),
                'gesture_name': str(gesture_name),
                
                # Datos EMG RAW (lo más importante)
                'emg1_raw': float(features.get('emg1_raw', 0.0)),
                'emg2_raw': float(features.get('emg2_raw', 0.0)),
                'emg3_raw': float(features.get('emg3_raw', 0.0)),
                
                # Timestamps del ESP32
                'session_time': int(features.get('session_time', 0)),
                'esp32_timestamp': int(features.get('esp32_timestamp', 0))
            }
            
            # OPCIONAL: Solo agregar datos adicionales si son necesarios
            if additional_info and isinstance(additional_info, dict):
                # Filtrar solo datos útiles, evitar duplicados
                useful_keys = ['movement_id', 'esp32_timestamp']  # Solo estos si son necesarios
                for key in useful_keys:
                    if key in additional_info and key not in data_point:
                        value = additional_info[key]
                        if isinstance(value, (int, float)):
                            data_point[key] = value
                        else:
                            data_point[key] = str(value)
            
            # Agregar al dataset
            self.dataset.append(data_point)
            self.session_info['total_samples'] += 1
            
            return True
            
        except Exception as e:
            print(f"❌ Error agregando muestra: {e}")
            return False
    
    def save_dataset(self, 
                     filename: Optional[str] = None, 
                     include_metadata: bool = False) -> Tuple[bool, str]:
        """Guardar el dataset a un archivo CSV - ESTRUCTURA LIMPIA"""
        if not self.dataset:
            return False, "No hay datos para guardar"
        
        # Generar nombre de archivo si no se proporciona
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = self.session_info.get('session_id', 'unknown')
            filename = f"emg_dataset_{session_id}_{timestamp}.csv"
        
        try:
            print(f"💾 Guardando {len(self.dataset)} muestras EMG...")
            
            # Crear DataFrame con estructura consistente
            df = pd.DataFrame(self.dataset)
            
            # Definir orden de columnas para CSV limpio
            column_order = [
                'timestamp',
                'session_id', 
                'sample_number',
                'series_number',
                'gesture_id',
                'gesture_name',
                'emg1_raw',
                'emg2_raw', 
                'emg3_raw',
                'session_time',
                'esp32_timestamp'
            ]
            
            # Reordenar columnas (solo las que existen)
            existing_columns = [col for col in column_order if col in df.columns]
            df = df[existing_columns]
            
            # Guardar CSV limpio
            df.to_csv(filename, index=False, encoding='utf-8')
            
            print(f"✅ Dataset EMG guardado: {filename}")
            print(f"📊 Total de muestras: {len(self.dataset)}")
            print(f"📋 Columnas: {list(df.columns)}")
            
            return True, filename
            
        except Exception as e:
            error_msg = f"Error al guardar dataset: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def load_dataset(self, filename: str) -> Tuple[bool, str]:
        """Cargar un dataset desde archivo CSV"""
        try:
            if not os.path.exists(filename):
                return False, f"Archivo no encontrado: {filename}"
            
            df = pd.read_csv(filename, encoding='utf-8')
            self.dataset = df.to_dict('records')
            
            # Limpiar tipos de datos
            for sample in self.dataset:
                for key, value in sample.items():
                    if pd.isna(value):
                        sample[key] = None
            
            print(f"✅ Dataset cargado: {len(self.dataset)} muestras")
            return True, f"Dataset cargado exitosamente: {len(self.dataset)} muestras"
            
        except Exception as e:
            error_msg = f"Error al cargar dataset: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def clear_dataset(self) -> bool:
        """Limpiar el dataset actual"""
        self.dataset.clear()
        self.session_info['total_samples'] = 0
        print("🗑️ Dataset limpiado")
        return True
    
    def get_dataset_info(self) -> Dict:
        """Obtener información del dataset actual"""
        if not self.dataset:
            return {'total_samples': 0, 'gestures': [], 'series': []}
        
        try:
            gestures = list(set(sample.get('gesture_name', 'UNKNOWN') for sample in self.dataset))
            series = list(set(sample.get('series_number', 1) for sample in self.dataset))
            
            return {
                'total_samples': len(self.dataset),
                'gestures': sorted(gestures),
                'series': sorted(series),
                'session_id': self.session_info.get('session_id', 'unknown'),
                'start_time': self.session_info.get('start_time')
            }
        except Exception as e:
            print(f"Error obteniendo info dataset: {e}")
            return {'total_samples': len(self.dataset), 'gestures': [], 'series': []}

# Función de utilidad
def create_dataset_manager() -> GestureDatasetManager:
    """Crear una instancia del gestor de dataset"""
    return GestureDatasetManager()