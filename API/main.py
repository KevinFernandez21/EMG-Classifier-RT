from flask import Flask, request, jsonify
import numpy as np
import tensorflow as tf
from scipy import signal
import json
import logging
import threading
import time
from datetime import datetime

def convert_numpy_types(obj):
    """Convierte numpy types a tipos nativos de Python para JSON"""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)

# Estado global para monitorear conexiones
app_state = {
    'esp32_connections': {},
    'last_prediction': None,
    'total_predictions': 0,
    'start_time': datetime.now()
}

class EMGPreprocessor:
    def __init__(self, fs=1000):
        self.fs = fs
        
    def preprocess_signal(self, signal_data):
        """Preprocesamiento con filtrado y normalizaci�n Z-score"""
        
        # Filtro Butterworth paso-banda (20-450 Hz)
        nyquist = 0.5 * self.fs
        low = 20 / nyquist
        high = 450 / nyquist
        b, a = signal.butter(4, [low, high], btype='band')
        
        processed = np.zeros_like(signal_data)
        
        for i in range(signal_data.shape[1]):
            # Aplicar filtro
            filtered = signal.filtfilt(b, a, signal_data[:, i])
            
            # Rectificaci�n
            rectified = np.abs(filtered)
            
            # Envelope (filtro paso-bajo a 5 Hz)
            b_env, a_env = signal.butter(2, 5/nyquist, btype='low')
            envelope = signal.filtfilt(b_env, a_env, rectified)
            
            # Normalizaci�n Z-score
            mean_val = np.mean(envelope)
            std_val = np.std(envelope) + 1e-8
            processed[:, i] = (envelope - mean_val) / std_val
            
        return processed

class GestureClassifier:
    def __init__(self, model_path):
        self.interpreter = tf.lite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
        
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        self.preprocessor = EMGPreprocessor()
        
        # Mapeo de clases (basado en el notebook)
        self.class_names = ['CERRAR_MANO', 'PINZA', 'SALUDAR', 'TOMAR_OBJ']
        
        logging.info(f"Modelo cargado. Input shape: {self.input_details[0]['shape']}")
        
    def predict(self, emg_data):
        """Realizar predicci�n con datos EMG"""
        try:
            # Preprocesar datos
            processed_data = self.preprocessor.preprocess_signal(emg_data)
            
            # Redimensionar para el modelo [batch, timesteps, channels]
            input_data = processed_data.reshape(1, processed_data.shape[0], processed_data.shape[1])
            input_data = input_data.astype(np.float32)
            
            # Configurar tensor de entrada
            self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
            
            # Realizar inferencia
            self.interpreter.invoke()
            
            # Obtener resultados
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
            predictions = output_data[0]
            
            # Obtener clase predicha y confianza
            predicted_class = np.argmax(predictions)
            confidence = float(np.max(predictions))
            
            return {
                'gesture': self.class_names[predicted_class],
                'confidence': confidence,
                'probabilities': {
                    self.class_names[i]: float(predictions[i]) 
                    for i in range(len(self.class_names))
                }
            }
            
        except Exception as e:
            logging.error(f"Error en predicci�n: {e}")
            return None

# Inicializar clasificador
try:
    classifier = GestureClassifier('weight/tflite_learn_774610_3.tflite')
    logging.info("Clasificador inicializado correctamente")
except Exception as e:
    logging.error(f"Error inicializando clasificador: {e}")
    classifier = None

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de verificaci�n de estado"""
    uptime = datetime.now() - app_state['start_time']
    return jsonify({
        'status': 'healthy',
        'model_loaded': classifier is not None,
        'uptime_seconds': int(uptime.total_seconds()),
        'total_predictions': app_state['total_predictions'],
        'active_connections': len(app_state['esp32_connections']),
        'last_prediction': app_state['last_prediction']
    }), 200

@app.route('/esp32_status', methods=['POST'])
def esp32_status():
    """Endpoint para registrar estado de ESP32"""
    try:
        data = request.get_json()
        esp32_id = data.get('esp32_id', 'unknown')
        sensor_connected = data.get('sensor_connected', False)
        wifi_connected = data.get('wifi_connected', True)
        
        # Actualizar estado de conexión
        app_state['esp32_connections'][esp32_id] = {
            'last_seen': datetime.now(),
            'sensor_connected': sensor_connected,
            'wifi_connected': wifi_connected,
            'ip_address': request.remote_addr
        }
        
        logging.info(f"ESP32 {esp32_id}: Sensor={'ON' if sensor_connected else 'OFF'}, WiFi={'ON' if wifi_connected else 'OFF'}")
        
        return jsonify({
            'status': 'registered',
            'esp32_id': esp32_id,
            'server_time': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logging.error(f"Error en esp32_status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict_gesture():
    """Endpoint principal para predicci�n de gestos"""
    if classifier is None:
        return jsonify({'error': 'Modelo no disponible'}), 500
    
    try:
        data = request.get_json()
        
        if 'emg_data' not in data:
            return jsonify({'error': 'Datos EMG requeridos'}), 400
        
        emg_data = np.array(data['emg_data'])
        
        # Validar dimensiones (esperamos [timesteps, 3_channels])
        if emg_data.shape[1] != 3:
            return jsonify({'error': 'Se requieren exactamente 3 canales EMG'}), 400
        
        if emg_data.shape[0] < 250:
            return jsonify({'error': 'Se requieren al menos 250 muestras'}), 400
        
        # Tomar ventana de 250 muestras
        if emg_data.shape[0] > 250:
            emg_data = emg_data[-250:, :]  # Tomar las �ltimas 250 muestras
        
        # Realizar predicci�n
        result = classifier.predict(emg_data)
        
        if result is None:
            return jsonify({'error': 'Error en predicci�n'}), 500
        
        # Actualizar estado global
        app_state['total_predictions'] += 1
        app_state['last_prediction'] = {
            'gesture': result['gesture'],
            'confidence': result['confidence'],
            'timestamp': datetime.now().isoformat()
        }
        
        logging.info(f"Predicci�n: {result['gesture']} (conf: {result['confidence']:.2f})")
        
        return jsonify({
            'success': True,
            'prediction': result,
            'timestamp': data.get('timestamp', None)
        }), 200
        
    except Exception as e:
        logging.error(f"Error en endpoint predict: {e}")
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/predict_simple', methods=['POST'])
def predict_simple():
    """Endpoint simplificado para ESP32"""
    if classifier is None:
        return jsonify({'error': 'Modelo no disponible'}), 500
    
    try:
        data = request.get_json()
        
        # Formato esperado: {"emg1": [...], "emg2": [...], "emg3": [...]}
        if not all(key in data for key in ['emg1', 'emg2', 'emg3']):
            return jsonify({'error': 'Se requieren emg1, emg2 y emg3'}), 400
        
        # Convertir a array numpy
        emg_data = np.column_stack([
            np.array(data['emg1']),
            np.array(data['emg2']),
            np.array(data['emg3'])
        ])
        
        # Validar longitud
        if emg_data.shape[0] < 250:
            return jsonify({'error': f'Se requieren 250 muestras, recibidas: {emg_data.shape[0]}'}), 400
        
        # Tomar ventana de 250 muestras
        if emg_data.shape[0] > 250:
            emg_data = emg_data[-250:, :]
        
        # Realizar predicci�n
        result = classifier.predict(emg_data)
        
        if result is None:
            return jsonify({'error': 'Error en predicci�n'}), 500
        
        # Actualizar estado global
        app_state['total_predictions'] += 1
        app_state['last_prediction'] = {
            'gesture': result['gesture'],
            'confidence': result['confidence'],
            'timestamp': datetime.now().isoformat()
        }
        
        logging.info(f"ESP32 Predicci�n: {result['gesture']} (conf: {result['confidence']:.2f})")
        
        # Respuesta simplificada para ESP32
        return jsonify({
            'gesture': result['gesture'],
            'confidence': round(result['confidence'], 3)
        }), 200
        
    except Exception as e:
        logging.error(f"Error en endpoint predict_simple: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/info', methods=['GET'])
def model_info():
    """Informaci�n del modelo y API"""
    if classifier is None:
        return jsonify({'error': 'Modelo no disponible'}), 500
    
    try:
        # Preparar información del modelo de forma segura
        model_info_data = {
            'input_shape': list(classifier.input_details[0]['shape']) if classifier.input_details[0]['shape'] is not None else [],
            'output_shape': list(classifier.output_details[0]['shape']) if classifier.output_details[0]['shape'] is not None else [],
            'classes': classifier.class_names,
            'window_size': 250,
            'channels': 3,
            'sampling_frequency': 1000
        }
        
        endpoints_info = {
            '/health': 'Verificacion de estado',
            '/predict': 'Prediccion completa con formato detallado',
            '/predict_simple': 'Prediccion simplificada para ESP32',
            '/info': 'Informacion del modelo y API',
            '/esp32_status': 'Registro de estado de dispositivos ESP32'
        }
        
        response_data = {
            'model_info': model_info_data,
            'endpoints': endpoints_info
        }
        
        # Convertir todos los numpy types recursivamente
        response_data = convert_numpy_types(response_data)
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logging.error(f"Error en model_info: {e}")
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)