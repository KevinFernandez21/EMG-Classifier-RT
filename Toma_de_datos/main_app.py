"""
Aplicación Principal EMG AUTOMÁTICA
Python define los movimientos y captura automáticamente
"""

import sys
from datetime import datetime
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

# Importar módulos personalizados
from emg_processor import EMGProcessor
from dataset_manager import GestureDatasetManager
from session_controller import GestureSessionController, SessionState

class EMGMonitorWorker(QThread):
    """Worker thread para EMG automático"""
    data_ready = Signal(dict, dict, bool)
    error_occurred = Signal(str)
    
    def __init__(self, port='COM3'):
        super().__init__()
        self.running = False
        self.processor = None
        self.port = port
        
    def run(self):
        try:
            self.processor = EMGProcessor(port=self.port)
            
            if not self.processor.connect():
                self.error_occurred.emit(f"No se pudo conectar al ESP32 en {self.port}")
                return
            
            while self.running:
                try:
                    _, features, is_connected = self.processor.process_frame()
                    
                    # Crear datos simulados si no hay sensor
                    raw_data = self.processor.get_latest_emg_data() or {}
                    
                    self.data_ready.emit(raw_data, features, is_connected)
                    self.msleep(50)  # 20 Hz
                    
                except Exception as e:
                    self.error_occurred.emit(f"Error procesando EMG: {str(e)}")
                    self.msleep(100)
                    
        except Exception as e:
            self.error_occurred.emit(f"Error en worker EMG: {str(e)}")
        finally:
            if self.processor:
                self.processor.cleanup()
    
    def start_monitoring(self, port='COM3'):
        self.port = port
        self.running = True
        self.start()
        
    def stop_monitoring(self):
        self.running = False
        self.wait(5000)
        if self.isRunning():
            self.terminate()

class AutoEMGApp(QMainWindow):
    """Aplicación EMG AUTOMÁTICA - Python define los movimientos"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema EMG - Captura AUTOMÁTICA")
        self.setGeometry(200, 200, 700, 600)
        
        # Módulos básicos
        self.dataset_manager = GestureDatasetManager()
        self.session_controller = GestureSessionController()
        self.emg_worker = EMGMonitorWorker()
        
        # Variables de estado
        self.is_sensor_connected = False
        self.current_features = {}
        self.auto_capture_active = False
        
        # Setup
        self._setup_ui()
        self._setup_session_callbacks()
        
        # Timer para sesión automática
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._update_session)
        self.session_timer.start(100)
        
        # Configurar EMG worker
        self.emg_worker.data_ready.connect(self._on_emg_data_ready)
        self.emg_worker.error_occurred.connect(self._on_emg_error)
        
        # Auto-conectar
        self._auto_connect()
        
        print("🚀 Aplicación EMG AUTOMÁTICA iniciada")
    
    def _auto_connect(self):
        """Auto-conectar al ESP32"""
        # Lista de puertos comunes
        ports = ['COM3', 'COM4', 'COM5', 'COM6', 'COM7']
        
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        
        print(f"🔍 Auto-conectando a {ports[0]}...")
        self.emg_worker.start_monitoring(ports[0])
    
    def _setup_ui(self):
        """Configurar interfaz AUTOMÁTICA"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Título
        title = QLabel("🤖 Sistema EMG AUTOMÁTICO - ESP32 + uMyo_BLE")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("background-color: #2196F3; color: white; padding: 10px; border-radius: 5px;")
        layout.addWidget(title)
        
        info = QLabel("✅ Python define automáticamente los movimientos a capturar")
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 5px;")
        layout.addWidget(info)
        
        # Conexión ESP32
        connection_group = QGroupBox("🔌 Conexión ESP32")
        connection_layout = QHBoxLayout(connection_group)
        
        connection_layout.addWidget(QLabel("Puerto:"))
        self.port_combo = QComboBox()
        connection_layout.addWidget(self.port_combo)
        
        reconnect_btn = QPushButton("🔄 Reconectar")
        reconnect_btn.clicked.connect(self._reconnect_esp32)
        connection_layout.addWidget(reconnect_btn)
        
        self.status_label = QLabel("🔴 Desconectado")
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px;")
        connection_layout.addWidget(self.status_label)
        
        layout.addWidget(connection_group)
        
        # Configuración automática
        config_group = QGroupBox("⚙️ Configuración Automática")
        config_layout = QGridLayout(config_group)
        
        config_layout.addWidget(QLabel("Duración por gesto (seg):"), 0, 0)
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(5, 30)
        self.duration_spin.setValue(8)
        config_layout.addWidget(self.duration_spin, 0, 1)
        
        config_layout.addWidget(QLabel("Repeticiones por gesto:"), 1, 0)
        self.cycles_spin = QSpinBox()
        self.cycles_spin.setRange(1, 10)
        self.cycles_spin.setValue(3)
        config_layout.addWidget(self.cycles_spin, 1, 1)
        
        config_layout.addWidget(QLabel("Tiempo de descanso (seg):"), 2, 0)
        self.rest_spin = QSpinBox()
        self.rest_spin.setRange(2, 10)
        self.rest_spin.setValue(3)
        config_layout.addWidget(self.rest_spin, 2, 1)
        
        layout.addWidget(config_group)
        
        # Estado de captura
        status_group = QGroupBox("📊 Estado de Captura")
        status_layout = QVBoxLayout(status_group)
        
        self.session_status = QLabel("💤 Sistema listo - Presiona INICIAR")
        self.session_status.setFont(QFont("Arial", 12, QFont.Bold))
        self.session_status.setAlignment(Qt.AlignCenter)
        self.session_status.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        status_layout.addWidget(self.session_status)
        
        # MOSTRAR MOVIMIENTO ACTUAL (SOLUCIÓN A LA BARRA BLANCA)
        self.current_gesture = QLabel("🎯 Movimiento: Ninguno")
        self.current_gesture.setFont(QFont("Arial", 14, QFont.Bold))
        self.current_gesture.setAlignment(Qt.AlignCenter)
        self.current_gesture.setStyleSheet("""
            padding: 15px; 
            background-color: #4CAF50; 
            color: white; 
            border-radius: 8px;
            border: 2px solid #45a049;
        """)
        status_layout.addWidget(self.current_gesture)
        
        self.countdown = QLabel("")
        self.countdown.setFont(QFont("Arial", 24, QFont.Bold))
        self.countdown.setAlignment(Qt.AlignCenter)
        self.countdown.setStyleSheet("color: #f44336; padding: 10px;")
        status_layout.addWidget(self.countdown)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                height: 30px;
                border: 2px solid #ddd;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(status_group)
        
        # Controles principales
        controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 INICIAR CAPTURA AUTOMÁTICA")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                font-size: 14px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_btn.clicked.connect(self._start_auto_session)
        controls_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ DETENER")
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336; 
                color: white; 
                font-weight: bold; 
                font-size: 14px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.stop_btn.clicked.connect(self._stop_session)
        self.stop_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_btn)
        
        layout.addLayout(controls_layout)
        
        # Información y guardado
        info_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 GUARDAR DATASET")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; 
                color: white; 
                font-weight: bold; 
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.save_btn.clicked.connect(self._save_dataset)
        info_layout.addWidget(self.save_btn)
        
        self.samples_label = QLabel("📊 Muestras capturadas: 0")
        self.samples_label.setAlignment(Qt.AlignCenter)
        self.samples_label.setStyleSheet("font-weight: bold; padding: 10px;")
        info_layout.addWidget(self.samples_label)
        
        layout.addLayout(info_layout)
    
    def _setup_session_callbacks(self):
        """Configurar callbacks seguros"""
        self.session_controller.on_state_change = self._on_state_change
        self.session_controller.on_gesture_change = self._on_gesture_change
        self.session_controller.on_countdown_tick = self._on_countdown_tick
        self.session_controller.on_recording_start = self._on_recording_start
        self.session_controller.on_recording_end = self._on_recording_end
        self.session_controller.on_session_complete = self._on_session_complete
        self.session_controller.on_error = self._on_error
    
    def _reconnect_esp32(self):
        """Reconectar ESP32"""
        port = self.port_combo.currentText()
        print(f"🔄 Reconectando a {port}...")
        self.emg_worker.stop_monitoring()
        
        self.emg_worker = EMGMonitorWorker()
        self.emg_worker.data_ready.connect(self._on_emg_data_ready)
        self.emg_worker.error_occurred.connect(self._on_emg_error)
        self.emg_worker.start_monitoring(port)
    
    def _start_auto_session(self):
        """Iniciar sesión AUTOMÁTICA"""
        # Gestos definidos automáticamente por Python
        auto_gestures = ["CERRAR_MANO", "PINZA", "SALUDAR", "TOMAR_OBJ"]
        
        duration = self.duration_spin.value()
        cycles = self.cycles_spin.value()
        rest_time = self.rest_spin.value()
        
        success = self.session_controller.configure_session(
            selected_gestures=auto_gestures,
            duration_per_gesture=duration,
            rest_time=rest_time,
            user_cycles=cycles
        )
        
        if not success:
            return
        
        session_config = {
            'selected_gestures': auto_gestures,
            'duration_per_gesture': duration,
            'cycles': cycles,
            'rest_time': rest_time,
            'mode': 'automatic'
        }
        
        self.dataset_manager.start_new_session(session_config)
        self.session_controller.start_session()
        self.auto_capture_active = True
        
        print("🤖 Sesión AUTOMÁTICA iniciada - Python controla los movimientos")
    
    def _stop_session(self):
        """Detener sesión"""
        print("⏹️ Deteniendo sesión automática...")
        
        self.session_controller.stop_session()
        self.auto_capture_active = False
        
        # Actualizar UI
        self.session_status.setText("⏹️ Sesión detenida")
        self.current_gesture.setText("🎯 Movimiento: Detenido")
        self.countdown.setText("")
        self.progress_bar.setVisible(False)
        
        self.start_btn.setEnabled(True)
        self.start_btn.setText("🚀 INICIAR CAPTURA AUTOMÁTICA")
        self.stop_btn.setEnabled(False)
    
    def _save_dataset(self):
        """Guardar dataset"""
        if not self.dataset_manager.dataset:
            QMessageBox.information(self, "Info", "No hay datos para guardar")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Guardar Dataset EMG Automático", 
            f"emg_auto_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)")
        
        if filename:
            success, result = self.dataset_manager.save_dataset(filename)
            if success:
                QMessageBox.information(self, "Éxito", f"Dataset guardado:\n{filename}")
            else:
                QMessageBox.critical(self, "Error", f"Error al guardar:\n{result}")
    
    def _update_session(self):
        """Actualizar estado de sesión"""
        try:
            status = self.session_controller.update()
            
            if status.get('progress_percentage', 0) > 0:
                self.progress_bar.setValue(int(status['progress_percentage']))
            
            total_samples = self.dataset_manager.session_info.get('total_samples', 0)
            self.samples_label.setText(f"📊 Muestras capturadas: {total_samples}")
            
        except Exception as e:
            print(f"Error actualizando sesión: {e}")
    
    # Callbacks de sesión
    def _on_state_change(self, old_state, new_state):
        if new_state == SessionState.IDLE:
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.progress_bar.setVisible(False)
        else:
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.progress_bar.setVisible(True)
    
    def _on_gesture_change(self, gesture_info):
        try:
            gesture_name = gesture_info.get('gesture_name', 'DESCONOCIDO')
            cycle = gesture_info.get('cycle_number', 0)
            total = gesture_info.get('total_cycles', 0)
            
            # SOLUCIÓN: Mostrar claramente el próximo movimiento
            self.current_gesture.setText(f"🎯 PRÓXIMO: {gesture_name} ({cycle}/{total})")
            self.current_gesture.setStyleSheet("""
                padding: 15px; 
                background-color: #FF9800; 
                color: white; 
                border-radius: 8px;
                border: 2px solid #F57C00;
                font-size: 14px;
            """)
            
        except Exception as e:
            print(f"Error en gesture_change: {e}")
    
    def _on_countdown_tick(self, remaining):
        try:
            if remaining > 0:
                self.countdown.setText(f"⏱️ {remaining}")
                self.session_status.setText("🔄 Prepárate para el siguiente movimiento...")
            else:
                self.countdown.setText("¡YA!")
        except Exception as e:
            print(f"Error en countdown: {e}")
    
    def _on_recording_start(self, gesture_info):
        try:
            gesture_name = gesture_info.get('gesture_name', 'DESCONOCIDO')
            
            self.session_status.setText("🔴 CAPTURANDO DATOS EMG")
            
            # SOLUCIÓN: Mostrar claramente qué movimiento hacer
            self.current_gesture.setText(f"💪 HAZ: {gesture_name}")
            self.current_gesture.setStyleSheet("""
                padding: 15px; 
                background-color: #f44336; 
                color: white; 
                border-radius: 8px;
                border: 2px solid #d32f2f;
                font-size: 16px;
                animation: pulse 1s infinite;
            """)
            
            self.countdown.setText("📊 GRABANDO...")
            
        except Exception as e:
            print(f"Error en recording_start: {e}")
    
    def _on_recording_end(self, gesture_info, samples):
        try:
            self.session_status.setText("✅ Captura completada")
            self.current_gesture.setText("✓ Movimiento completado")
            self.current_gesture.setStyleSheet("""
                padding: 15px; 
                background-color: #4CAF50; 
                color: white; 
                border-radius: 8px;
                border: 2px solid #45a049;
            """)
            self.countdown.setText("✓")
        except Exception as e:
            print(f"Error en recording_end: {e}")
    
    def _on_session_complete(self, stats):
        try:
            self.session_status.setText("🎉 ¡CAPTURA AUTOMÁTICA COMPLETADA!")
            self.current_gesture.setText("🏆 Todos los movimientos capturados")
            self.current_gesture.setStyleSheet("""
                padding: 15px; 
                background-color: #4CAF50; 
                color: white; 
                border-radius: 8px;
                border: 2px solid #45a049;
            """)
            self.countdown.setText("🎉")
            
            reply = QMessageBox.question(self, "Captura Completada", 
                f"¡Captura automática completada!\nTotal: {stats.get('total_samples', 0)} muestras\n\n¿Guardar dataset ahora?")
            if reply == QMessageBox.Yes:
                self._save_dataset()
        except Exception as e:
            print(f"Error en session_complete: {e}")
    
    def _on_error(self, error_msg):
        QMessageBox.critical(self, "Error", error_msg)
    
    def _on_emg_error(self, error_msg):
        QMessageBox.critical(self, "Error EMG", error_msg)
        self.status_label.setText("❌ ERROR")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def _on_emg_data_ready(self, raw_data, features, is_connected):
        """Procesar datos EMG automáticamente"""
        try:
            self.is_sensor_connected = is_connected
            self.current_features = features
            
            # Actualizar estado de conexión
            if is_connected:
                self.status_label.setText("🟢 ESP32 Conectado")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.status_label.setText("🔴 Desconectado")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
            
            # Capturar AUTOMÁTICAMENTE si está grabando
            if (self.session_controller.state == SessionState.RECORDING and 
                self.auto_capture_active and features):
                
                gesture_info = self.session_controller.get_current_gesture_info()
                current_gesture_name = gesture_info.get('gesture_name', 'REPOSO')
                
                # Mapear gestos automáticamente
                gesture_mapping = {
                    'CERRAR_MANO': 1,
                    'PINZA': 2, 
                    'SALUDAR': 3,
                    'TOMAR_OBJ': 4
                }
                
                gesture_id = gesture_mapping.get(current_gesture_name, 0)
                
                # Crear datos limpios
                clean_features = {
                    'emg1_raw': float(features.get('emg1_raw', raw_data.get('emg1', 0))),
                    'emg2_raw': float(features.get('emg2_raw', raw_data.get('emg2', 0))), 
                    'emg3_raw': float(features.get('emg3_raw', raw_data.get('emg3', 0))),
                    'session_time': int(features.get('session_time', raw_data.get('session_time', 0))),
                    'esp32_timestamp': int(features.get('esp32_timestamp', raw_data.get('timestamp', 0)))
                }
                
                success = self.dataset_manager.add_sample(
                    features=clean_features,
                    gesture_id=gesture_id,
                    gesture_name=current_gesture_name,
                    series_number=gesture_info.get('cycle_number', 1)
                )
                
                if success:
                    self.session_controller.increment_sample_count()
                    
        except Exception as e:
            print(f"Error procesando EMG automático: {e}")
    
    def closeEvent(self, event):
        """Cerrar aplicación"""
        self.emg_worker.stop_monitoring()
        
        if self.session_controller.state != SessionState.IDLE:
            self.session_controller.stop_session()
        
        if self.dataset_manager.dataset:
            reply = QMessageBox.question(self, "Guardar", 
                f"¿Guardar {len(self.dataset_manager.dataset)} muestras antes de salir?")
            if reply == QMessageBox.Yes:
                filename = f"emg_auto_save_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                self.dataset_manager.save_dataset(filename)
        
        event.accept()

def main():
    """Función principal"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    try:
        window = AutoEMGApp()
        window.show()
        
        QMessageBox.information(window, "Sistema EMG Automático", 
            "🤖 Sistema EMG AUTOMÁTICO\n\n"
            "✅ Funciones automáticas:\n"
            "• ESP32 envía datos continuamente\n"
            "• Python define los movimientos\n"
            "• No necesita botones físicos\n"
            "• Captura automática por tiempo\n\n"
            "📋 Instrucciones:\n"
            "1. Conecta el ESP32 con el nuevo código\n"
            "2. Configura duración y repeticiones\n"
            "3. Presiona 'INICIAR CAPTURA AUTOMÁTICA'\n"
            "4. Sigue las instrucciones en pantalla\n"
            "5. El sistema te dirá qué movimiento hacer\n\n"
            "🎯 ¡La barra ahora mostrará el movimiento actual!")
        
        sys.exit(app.exec())
        
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Error iniciando aplicación:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()