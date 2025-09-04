"""
EMG Processor AUTOMÁTICO - Para ESP32 sin botones
Procesa datos EMG continuos enviados automáticamente por ESP32
"""

import serial
import time
import numpy as np
from typing import Dict, Tuple, Optional
import threading
from datetime import datetime
import queue

class EMGProcessor:
    """Procesador AUTOMÁTICO para ESP32 + uMyo_BLE"""
    
    def __init__(self, 
                 port: str = 'COM3',
                 baudrate: int = 115200,
                 timeout: float = 1.0):
        """
        Inicializar procesador EMG automático
        
        Args:
            port: Puerto serie del ESP32
            baudrate: Velocidad (115200 para ESP32)
            timeout: Timeout para lectura
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        
        # Variables de conexión
        self.serial_connection = None
        self.connected = False
        self.reading_thread = None
        self.stop_reading = False
        
        # Buffer de datos
        self.data_queue = queue.Queue(maxsize=100)
        self.last_emg_data = None
        self.last_detection_time = None
        
        # Estado del sistema AUTOMÁTICO
        self.session_active = True  # SIEMPRE ACTIVO
        self.current_movement = {"id": 0, "name": "AUTO"}
        
        print("🤖 Procesador EMG AUTOMÁTICO inicializado")
        
    def connect(self) -> bool:
        """Conectar al ESP32"""
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Esperar inicialización ESP32
            time.sleep(3)
            
            # Limpiar buffer
            self.serial_connection.flushInput()
            self.serial_connection.flushOutput()
            
            self.connected = True
            print(f"✅ Conectado al ESP32 automático en {self.port}")
            
            # Iniciar hilo de lectura
            self.start_reading_thread()
            
            return True
            
        except Exception as e:
            print(f"❌ Error conectando ESP32: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Desconectar del ESP32"""
        self.stop_reading = True
        self.connected = False
        
        if self.reading_thread and self.reading_thread.is_alive():
            self.reading_thread.join(timeout=2.0)
        
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            
        print("🔌 Desconectado del ESP32 automático")
    
    def start_reading_thread(self):
        """Iniciar hilo de lectura"""
        self.stop_reading = False
        self.reading_thread = threading.Thread(target=self._read_serial_data, daemon=True)
        self.reading_thread.start()
        print("🔄 Hilo de lectura ESP32 automático iniciado")
    
    def _read_serial_data(self):
        """Leer datos del ESP32 en hilo separado - MODO AUTOMÁTICO"""
        while not self.stop_reading and self.connected:
            try:
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode('utf-8').strip()
                    
                    if line:
                        self._process_serial_line(line)
                        
            except Exception as e:
                print(f"⚠️ Error leyendo ESP32: {e}")
                time.sleep(0.1)
                
            time.sleep(0.01)
    
    def _process_serial_line(self, line: str):
        """Procesar línea del ESP32 - MODO AUTOMÁTICO"""
        try:
            # Mensajes de control del ESP32 automático
            if line == "CSV_START":
                self.session_active = True
                print("🤖 ESP32: Sistema automático iniciado")
                return
            elif line == "CSV_END":
                self.session_active = False
                print("⏹️ ESP32: Sistema automático terminado")
                return
            elif "timestamp,session_time" in line:
                print("📋 ESP32: Headers CSV recibidos (modo automático)")
                return
            elif "SISTEMA EMG AUTOMÁTICO" in line or "===" in line:
                print(f"ℹ️ ESP32: {line}")
                return
            
            # Filtrar mensajes de estado (menos verbose)
            elif line.startswith("SISTEMA:"):
                self.last_detection_time = time.time()
                # No imprimir todos los mensajes de estado
                return
            
            # PROCESAR DATOS CSV AUTOMÁTICOS
            # Formato: timestamp,session_time,emg1,emg2,emg3,movement_id,movement_name
            if "," in line and len(line.split(",")) >= 6:
                parts = line.split(",")
                try:
                    timestamp = int(parts[0])
                    session_time = int(parts[1])
                    emg1 = float(parts[2])
                    emg2 = float(parts[3])  
                    emg3 = float(parts[4])
                    movement_id = int(parts[5]) if parts[5].isdigit() else 0
                    movement_name = parts[6] if len(parts) > 6 else "AUTO"
                    
                    # Crear estructura de datos EMG automática
                    emg_data = {
                        'timestamp': timestamp,
                        'session_time': session_time,
                        'emg1': emg1,
                        'emg2': emg2,
                        'emg3': emg3,
                        'movement_id': movement_id,
                        'movement_name': movement_name,
                        'esp32_timestamp': datetime.now().isoformat(),
                        'mode': 'automatic'
                    }
                    
                    # Actualizar datos actuales
                    self.last_emg_data = emg_data
                    self.last_detection_time = time.time()
                    self.current_movement = {"id": movement_id, "name": movement_name}
                    
                    # Agregar a cola si no está llena
                    if not self.data_queue.full():
                        self.data_queue.put(emg_data)
                    
                    # Imprimir datos EMG menos frecuentemente (cada 10 muestras)
                    if hasattr(self, '_sample_count'):
                        self._sample_count += 1
                    else:
                        self._sample_count = 1
                        
                    if self._sample_count % 10 == 0:  # Solo cada 10 muestras
                        print(f"📊 EMG Auto: EMG1:{emg1:.2f} EMG2:{emg2:.2f} EMG3:{emg3:.2f}")
                        
                except (ValueError, IndexError) as e:
                    # Manejo silencioso de errores de parsing
                    pass
                        
        except Exception as e:
            if "timeout" not in str(e).lower():
                print(f"❌ Error procesando línea ESP32: {e}")
    
    def is_sensor_connected(self) -> bool:
        """
        Verificar si ESP32 está conectado y enviando datos automáticamente
        """
        if not self.connected:
            return False
            
        if self.last_detection_time is None:
            return False
            
        # Considerar conectado si hay actividad del ESP32 en los últimos 5 segundos
        time_since_last_data = time.time() - self.last_detection_time
        return time_since_last_data <= 5.0
    
    def get_latest_emg_data(self) -> Optional[Dict]:
        """Obtener los últimos datos EMG del ESP32 automático"""
        return self.last_emg_data
    
    def get_emg_features(self) -> Dict:
        """
        Extraer características EMG del modo automático
        """
        if not self.last_emg_data:
            # Retornar datos por defecto si no hay datos
            return {
                'emg1_raw': 0.0,
                'emg2_raw': 0.0,
                'emg3_raw': 0.0,
                'session_time': 0,
                'esp32_timestamp': 0,
                'mode': 'automatic'
            }
        
        emg_data = self.last_emg_data
        features = {}
        
        try:
            # Datos raw del uMyo_BLE v3 en modo automático
            features['emg1_raw'] = float(emg_data.get('emg1', 0.0))
            features['emg2_raw'] = float(emg_data.get('emg2', 0.0))
            features['emg3_raw'] = float(emg_data.get('emg3', 0.0))
            
            # Información temporal
            features['session_time'] = int(emg_data.get('session_time', 0))
            features['esp32_timestamp'] = int(emg_data.get('timestamp', 0))
            
            # Modo automático
            features['mode'] = 'automatic'
            
        except Exception as e:
            print(f"⚠️ Error extrayendo características: {e}")
            # Retornar datos por defecto en caso de error
            features = {
                'emg1_raw': 0.0,
                'emg2_raw': 0.0,
                'emg3_raw': 0.0,
                'session_time': 0,
                'esp32_timestamp': 0,
                'mode': 'automatic'
            }
            
        return features
    
    def detect_gesture(self, features: Dict) -> Tuple[int, str]:
        """
        En modo automático, Python define el gesto, no el ESP32
        """
        # En modo automático, siempre retornar gesto neutral
        # Python controlará qué gesto se está capturando
        return 0, "AUTO"
    
    def process_frame(self, frame=None) -> Tuple[None, Dict, bool]:
        """
        Procesar 'frame' - Compatible con interfaz existente
        Para EMG automático no hay frame visual, solo características
        
        Args:
            frame: No usado para EMG
            
        Returns:
            Tuple: (None, características, estado_conexión)
        """
        features = self.get_emg_features()
        is_connected = self.is_sensor_connected()
        
        return None, features, is_connected
    
    def get_status_info(self) -> Dict:
        """Obtener información de estado del ESP32 automático"""
        return {
            'connected': self.connected,
            'session_active': self.session_active,
            'current_movement': self.current_movement,
            'last_data_time': self.last_detection_time,
            'port': self.port,
            'baudrate': self.baudrate,
            'device_type': 'ESP32 + uMyo_BLE v3 (Automático)',
            'mode': 'automatic'
        }
    
    def cleanup(self):
        """Limpiar recursos"""
        print("🧹 Limpiando procesador ESP32 automático...")
        self.disconnect()

# Funciones de utilidad
def create_emg_processor(port='COM3', baudrate=115200) -> EMGProcessor:
    """Crear procesador EMG automático para ESP32 + uMyo_BLE"""
    processor = EMGProcessor(port=port, baudrate=baudrate)
    if processor.connect():
        return processor
    else:
        print("❌ No se pudo conectar al ESP32 automático")
        return processor

def detect_esp32_ports():
    """Detectar puertos ESP32"""
    import serial.tools.list_ports
    
    ports = []
    for port in serial.tools.list_ports.comports():
        # Buscar ESP32 o puertos serie comunes
        if any(keyword in port.description.lower() for keyword in 
               ['cp210x', 'ch340', 'esp32', 'usb-serial', 'uart']):
            ports.append(port.device)
        elif (port.device.startswith('COM') or 
              port.device.startswith('/dev/ttyUSB') or 
              port.device.startswith('/dev/ttyACM')):
            ports.append(port.device)
    
    return ports if ports else ['COM3', 'COM4', 'COM5']

def test_esp32_connection(port='COM3', timeout=10.0) -> bool:
    """Probar conexión con ESP32 automático"""
    try:
        processor = EMGProcessor(port=port, timeout=2.0)
        if processor.connect():
            print(f"✅ ESP32 automático conectado en {port}")
            time.sleep(3)  # Esperar datos
            
            # Verificar datos
            test_data = processor.get_latest_emg_data()
            processor.cleanup()
            
            if test_data:
                print(f"📊 Datos automáticos recibidos: EMG1={test_data.get('emg1', 0):.3f}")
                return True
            else:
                print(f"⚠️ Conectado pero esperando datos automáticos...")
                return True  # Consideramos exitoso si se conecta
        else:
            return False
    except Exception as e:
        print(f"❌ Error probando ESP32 automático: {e}")
        return False