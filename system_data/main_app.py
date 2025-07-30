        # Panel izquierdo - Configuración
        left_panel = self._create_configuration_panel()
        main_layout.addWidget(left_panel, 1)
        
        # Panel central - Video y estado
        center_panel = self._create_video_panel()
        main_layout.addWidget(center_panel, 2)
        
        # Panel derecho - Estadísticas y datos
        right_panel = self._create_statistics_panel()
        main_layout.addWidget(right_panel, 1)
    
    def _create_configuration_panel(self):
        """Crear panel de configuración"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Título
        title = QLabel("⚙️ CONFIGURACIÓN")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #2196F3; padding: 10px; border-bottom: 2px solid #2196F3;")
        layout.addWidget(title)
        
        # Selección de gestos
        gestures_group = QGroupBox("Gestos a Capturar")
        gestures_layout = QVBoxLayout(gestures_group)
        
        self.gesture_checkboxes = {}
        self.available_gestures = ["REPOSO", "CERRAR_MANO", "PINZA", "SALUDAR", "TOMAR_OBJETO"]
        
        for gesture in self.available_gestures:
            cb = QCheckBox(gesture)
            cb.setChecked(gesture != "REPOSO")  # Por defecto, todos excepto REPOSO
            self.gesture_checkboxes[gesture] = cb
            gestures_layout.addWidget(cb)
        
        layout.addWidget(gestures_group)
        
        # Configuración de captura
        config_group = QGroupBox("Configuración de Captura")
        config_layout = QGridLayout(config_group)
        
        # Número de ciclos (definido por usuario)
        config_layout.addWidget(QLabel("Ciclos por gesto:"), 0, 0)
        self.cycles_spinbox = QSpinBox()
        self.cycles_spinbox.setRange(1, 50)
        self.cycles_spinbox.setValue(5)
        self.cycles_spinbox.setToolTip("Número de veces que se capturará cada gesto")
        config_layout.addWidget(self.cycles_spinbox, 0, 1)
        
        # Duración por captura
        config_layout.addWidget(QLabel("Duración por captura (seg):"), 1, 0)
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(3, 30)
        self.duration_spinbox.setValue(8)
        self.duration_spinbox.setToolTip("Tiempo de grabación por cada gesto")
        config_layout.addWidget(self.duration_spinbox, 1, 1)
        
        # Tiempo de descanso
        config_layout.addWidget(QLabel("Tiempo de preparación (seg):"), 2, 0)
        self.rest_spinbox = QSpinBox()
        self.rest_spinbox.setRange(1, 15)
        self.rest_spinbox.setValue(4)
        self.rest_spinbox.setToolTip("Tiempo para prepararse antes de cada captura")
        config_layout.addWidget(self.rest_spinbox, 2, 1)
        
        layout.addWidget(config_group)
        
        # Estado del sensor
        sensor_group = QGroupBox("Estado del Sensor")
        sensor_layout = QVBoxLayout(sensor_group)
        
        self.sensor_status_label = QLabel("🔴 SENSOR DESCONECTADO")
        self.sensor_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.sensor_status_label.setStyleSheet("color: #f44336; padding: 5px;")
        self.sensor_status_label.setAlignment(Qt.AlignCenter)
        sensor_layout.addWidget(self.sensor_status_label)
        
        self.connection_help_label = QLabel("Muestra tu mano frente a la cámara")
        self.connection_help_label.setAlignment(Qt.AlignCenter)
        self.connection_help_label.setStyleSheet("color: #666; font-size: 10px;")
        sensor_layout.addWidget(self.connection_help_label)
        
        layout.addWidget(sensor_group)
        
        # Controles principales
        controls_group = QGroupBox("Controles")
        controls_layout = QVBoxLayout(controls_group)
        
        self.start_button = QPushButton("🚀 INICIAR SESIÓN")
        self.start_button.setMinimumHeight(50)
        self.start_button.setStyleSheet("""
            QPushButton { 
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                font-size: 14px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.start_button.clicked.connect(self._start_session)
        controls_layout.addWidget(self.start_button)
        
        self.pause_button = QPushButton("⏸️ PAUSAR")
        self.pause_button.setMinimumHeight(40)
        self.pause_button.setStyleSheet("""
            QPushButton { 
                background-color: #FF9800; 
                color: white; 
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #e68900; }
        """)
        self.pause_button.clicked.connect(self._pause_session)
        self.pause_button.setEnabled(False)
        controls_layout.addWidget(self.pause_button)
        
        self.stop_button = QPushButton("⏹️ DETENER")
        self.stop_button.setMinimumHeight(40)
        self.stop_button.setStyleSheet("""
            QPushButton { 
                background-color: #f44336; 
                color: white; 
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #da190b; }
        """)
        self.stop_button.clicked.connect(self._stop_session)
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)
        
        layout.addWidget(controls_group)
        
        # Gestión de datos
        data_group = QGroupBox("Gestión de Datos")
        data_layout = QVBoxLayout(data_group)
        
        self.save_button = QPushButton("💾 GUARDAR DATASET")
        self.save_button.setStyleSheet("""
            QPushButton { 
                background-color: #2196F3; 
                color: white; 
                font-weight: bold;
                padding: 8px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.save_button.clicked.connect(self._save_dataset)
        data_layout.addWidget(self.save_button)
        
        self.load_button = QPushButton("📂 CARGAR DATASET")
        self.load_button.setStyleSheet("""
            QPushButton { 
                background-color: #9C27B0; 
                color: white; 
                font-weight: bold;
                padding: 8px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        self.load_button.clicked.connect(self._load_dataset)
        data_layout.addWidget(self.load_button)
        
        self.clear_button = QPushButton("🗑️ LIMPIAR DATOS")
        self.clear_button.setStyleSheet("""
            QPushButton { 
                background-color: #607D8B; 
                color: white; 
                font-weight: bold;
                padding: 8px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #455A64; }
        """)
        self.clear_button.clicked.connect(self._clear_dataset)
        data_layout.addWidget(self.clear_button)
        
        layout.addWidget(data_group)
        
        layout.addStretch()
        return panel
    
    def _create_video_panel(self):
        """Crear panel de video y estado de sesión"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Video
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("""
            border: 3px solid #2196F3; 
            background-color: #f5f5f5;
            border-radius: 10px;
        """)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setText("🎥 Iniciando cámara...")
        layout.addWidget(self.video_label)
        
        # Estado de la sesión
        session_group = QGroupBox("Estado de la Sesión")
        session_layout = QVBoxLayout(session_group)
        
        # Estado principal
        self.session_status_label = QLabel("💤 ESPERANDO")
        self.session_status_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.session_status_label.setAlignment(Qt.AlignCenter)
        self.session_status_label.setStyleSheet("color: #2196F3; padding: 15px;")
        session_layout.addWidget(self.session_status_label)
        
        # Información del gesto actual
        self.current_gesture_label = QLabel("Gesto: Ninguno")
        self.current_gesture_label.setFont(QFont("Arial", 14))
        self.current_gesture_label.setAlignment(Qt.AlignCenter)
        self.current_gesture_label.setStyleSheet("color: #333; padding: 5px;")
        session_layout.addWidget(self.current_gesture_label)
        
        # Countdown
        self.countdown_label = QLabel("")
        self.countdown_label.setFont(QFont("Arial", 36, QFont.Bold))
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("color: #f44336; padding: 10px;")
        session_layout.addWidget(self.countdown_label)
        
        # Información adicional
        info_layout = QHBoxLayout()
        
        self.cycle_info_label = QLabel("Ciclo: -/-")
        self.cycle_info_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.cycle_info_label)
        
        self.samples_info_label = QLabel("Muestras: 0")
        self.samples_info_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.samples_info_label)
        
        session_layout.addLayout(info_layout)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #cccccc;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setVisible(False)
        session_layout.addWidget(self.progress_bar)
        
        layout.addWidget(session_group)
        
        return panel
    
    def _create_statistics_panel(self):
        """Crear panel de estadísticas"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Título
        title = QLabel("📊 ESTADÍSTICAS")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #4CAF50; padding: 10px; border-bottom: 2px solid #4CAF50;")
        layout.addWidget(title)
        
        # Estadísticas de la sesión
        session_stats_group = QGroupBox("Sesión Actual")
        session_stats_layout = QVBoxLayout(session_stats_group)
        
        self.session_stats_text = QTextEdit()
        self.session_stats_text.setMaximumHeight(150)
        self.session_stats_text.setReadOnly(True)
        self.session_stats_text.setStyleSheet("background-color: #f9f9f9;")
        session_stats_layout.addWidget(self.session_stats_text)
        
        layout.addWidget(session_stats_group)
        
        # Estadísticas del dataset
        dataset_stats_group = QGroupBox("Dataset Total")
        dataset_stats_layout = QVBoxLayout(dataset_stats_group)
        
        self.dataset_stats_text = QTextEdit()
        self.dataset_stats_text.setMaximumHeight(200)
        self.dataset_stats_text.setReadOnly(True)
        self.dataset_stats_text.setStyleSheet("background-color: #f9f9f9;")
        dataset_stats_layout.addWidget(self.dataset_stats_text)
        
        layout.addWidget(dataset_stats_group)
        
        # Características en tiempo real
        features_group = QGroupBox("Características Detectadas")
        features_layout = QVBoxLayout(features_group)
        
        self.features_text = QTextEdit()
        self.features_text.setMaximumHeight(200)
        self.features_text.setReadOnly(True)
        self.features_text.setStyleSheet("background-color: #f9f9f9; font-family: monospace; font-size: 9px;")
        features_layout.addWidget(self.features_text)
        
        layout.addWidget(features_group)
        
        # Recomendaciones
        recommendations_group = QGroupBox("Recomendaciones")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setMaximumHeight(120)
        self.recommendations_text.setReadOnly(True)
        self.recommendations_text.setStyleSheet("background-color: #fff3cd; color: #856404;")
        recommendations_layout.addWidget(self.recommendations_text)
        
        layout.addWidget(recommendations_group)
        
        layout.addStretch()
        return panel
    
    def _setup_session_callbacks(self):
        """Configurar callbacks del controlador de sesión"""
        self.session_controller.on_state_change = self._on_session_state_change
        self.session_controller.on_gesture_change = self._on_gesture_change
        self.session_controller.on_countdown_tick = self._on_countdown_tick
        self.session_controller.on_recording_start = self._on_recording_start
        self.session_controller.on_recording_end = self._on_recording_end
        self.session_controller.on_session_complete = self._on_session_complete
        self.session_controller.on_error = self._on_session_error
    
    # Métodos de eventos de sesión
    
    def _on_session_state_change(self, old_state, new_state):
        """Callback para cambio de estado de sesión"""
        print(f"🔄 Estado: {old_state.value} → {new_state.value}")
        
        # Actualizar controles según el estado
        if new_state == SessionState.IDLE:
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.progress_bar.setVisible(False)
            
        elif new_state in [SessionState.PREPARING, SessionState.COUNTDOWN, SessionState.RECORDING, SessionState.RESTING]:
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.progress_bar.setVisible(True)
            
        elif new_state == SessionState.PAUSED:
            self.start_button.setEnabled(True)
            self.start_button.setText("▶️ REANUDAR")
    
    def _on_gesture_change(self, gesture_info):
        """Callback para cambio de gesto"""
        gesture_name = gesture_info['gesture_name']
        cycle_num = gesture_info['cycle_number']
        total_cycles = gesture_info['total_cycles']
        
        self.current_gesture_label.setText(f"Próximo: {gesture_name}")
        self.cycle_info_label.setText(f"Ciclo: {cycle_num}/{total_cycles}")
    
    def _on_countdown_tick(self, remaining):
        """Callback para tick de countdown"""
        if remaining > 0:
            self.countdown_label.setText(f"{remaining}")
            self.session_status_label.setText(f"⏱️ PREPÁRATE")
        else:
            self.countdown_label.setText("¡YA!")
    
    def _on_recording_start(self, gesture_info):
        """Callback para inicio de grabación"""
        gesture_name = gesture_info['gesture_name']
        self.session_status_label.setText("🔴 GRABANDO")
        self.current_gesture_label.setText(f"HAZ: {gesture_name}")
        self.countdown_label.setText("GRABANDO...")
        self.last_gesture_name = gesture_name
    
    def _on_recording_end(self, gesture_info, samples_captured):
        """Callback para fin de grabación"""
        self.session_status_label.setText("✅ COMPLETADO")
        self.countdown_label.setText("✓")
        print(f"✅ Grabación completada: {samples_captured} muestras")
    
    def _on_session_complete(self, session_stats):
        """Callback para sesión completada"""
        self.session_status_label.setText("🎉 ¡COMPLETADO!")
        self.current_gesture_label.setText("Todas las capturas terminadas")
        self.countdown_label.setText("🎉")
        
        # Mostrar resumen
        QMessageBox.information(
            self, 
            "Sesión Completada",
            f"¡Sesión completada exitosamente!\n\n"
            f"📊 Total de muestras: {session_stats['total_samples']}\n"
            f"⏱️ Duración: {self.session_controller._calculate_session_duration()}\n\n"
            f"¿Deseas guardar el dataset ahora?"
        )
    
    def _on_session_error(self, error_message):
        """Callback para errores de sesión"""
        self.session_status_label.setText("❌ ERROR")
        self.countdown_label.setText("❌")
        QMessageBox.critical(self, "Error de Sesión", error_message)
    
    # Métodos de control de sesión
    
    def _start_session(self):
        """Iniciar nueva sesión de captura"""
        # Verificar sensor
        if not self.is_sensor_connected:
            QMessageBox.warning(
                self, 
                "Sensor Desconectado", 
                "El sensor de mano no está detectando ninguna mano.\n\n"
                "Por favor, muestra tu mano frente a la cámara antes de iniciar."
            )
            return
        
        # Obtener gestos seleccionados
        selected_gestures = [
            gesture for gesture, cb in self.gesture_checkboxes.items() 
            if cb.isChecked()
        ]
        
        if not selected_gestures:
            QMessageBox.warning(self, "Error", "Selecciona al menos un gesto para capturar")
            return
        
        # Configurar sesión
        cycles = self.cycles_spinbox.value()
        duration = self.duration_spinbox.value()
        rest_time = self.rest_spinbox.value()
        
        success = self.session_controller.configure_session(
            selected_gestures=selected_gestures,
            series_count=1,  # No usado cuando user_cycles > 0
            duration_per_gesture=duration,
            rest_time=rest_time,
            user_cycles=cycles
        )
        
        if not success:
            return
        
        # Iniciar nueva sesión en dataset manager
        session_config = {
            'selected_gestures': selected_gestures,
            'series_count': cycles,
            'duration_per_gesture': duration,
            'rest_time': rest_time
        }
        
        session_id = self.dataset_manager.start_new_session(session_config)
        
        # Iniciar sesión
        if self.session_controller.start_session():
            self.start_button.setText("🚀 INICIAR SESIÓN")
    
    def _pause_session(self):
        """Pausar/reanudar sesión"""
        if self.session_controller.state == SessionState.PAUSED:
            self.session_controller.resume_session()
            self.start_button.setText("🚀 INICIAR SESIÓN")
        else:
            self.session_controller.pause_session()
    
    def _stop_session(self):
        """Detener sesión actual"""
        reply = QMessageBox.question(
            self, 
            "Confirmar", 
            "¿Estás seguro de que quieres detener la sesión?\n\nSe perderán los datos no guardados."
        )
        
        if reply == QMessageBox.Yes:
            self.session_controller.stop_session()
            self.session_status_label.setText("⏹️ DETENIDO")
            self.current_gesture_label.setText("Sesión detenida")
            self.countdown_label.setText("")
    
    # Métodos de gestión de datos
    
    def _save_dataset(self):
        """Guardar dataset actual"""
        if not self.dataset_manager.dataset:
            QMessageBox.information(self, "Info", "No hay datos para guardar")
            return
        
        # Diálogo de guardado
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Guardar Dataset", 
            f"gesture_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            success, result = self.dataset_manager.save_dataset(filename, include_metadata=True)
            if success:
                QMessageBox.information(self, "Éxito", f"Dataset guardado exitosamente:\n{filename}")
            else:
                QMessageBox.critical(self, "Error", f"Error al guardar:\n{result}")
    
    def _load_dataset(self):
        """Cargar dataset desde archivo"""
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Cargar Dataset", 
            "", 
            "CSV Files (*.csv)"
        )
        
        if filename:
            success, message = self.dataset_manager.load_dataset(filename)
            if success:
                QMessageBox.information(self, "Éxito", message)
                self._update_statistics()
            else:
                QMessageBox.critical(self, "Error", message)
    
    def _clear_dataset(self):
        """Limpiar dataset actual"""
        if not self.dataset_manager.dataset:
            QMessageBox.information(self, "Info", "El dataset ya está vacío")
            return
        
        reply = QMessageBox.question(
            self, 
            "Confirmar", 
            f"¿Estás seguro de que quieres eliminar todos los datos?\n\n"
            f"Se perderán {len(self.dataset_manager.dataset)} muestras."
        )
        
        if reply == QMessageBox.Yes:
            self.dataset_manager.clear_dataset()
            self._update_statistics()
    
    # Métodos de actualización de interfaz
    
    def _update_session(self):
        """Actualizar estado de la sesión"""
        session_status = self.session_controller.update()
        
        # Actualizar barra de progreso
        if session_status['progress_percentage'] > 0:
            self.progress_bar.setValue(int(session_status['progress_percentage']))
        
        # Actualizar información de muestras
        if session_status['recording_active']:
            total_samples = self.dataset_manager.session_info['total_samples']
            current_samples = session_status['samples_this_recording']
            self.samples_info_label.setText(f"Total: {total_samples} | Actual: {current_samples}")
        
        # Actualizar estadísticas de sesión
        self._update_session_statistics(session_status)
    
    def _update_session_statistics(self, session_status):
        """Actualizar estadísticas de sesión"""
        stats_text = f"""
🎯 Estado: {session_status['state'].upper()}
🎮 Gesto: {session_status['current_gesture']['gesture_name']}
🔄 Ciclo: {session_status['current_gesture']['cycle_number']}/{session_status['current_gesture']['total_cycles']}
📈 Progreso: {session_status['progress_percentage']:.1f}%
📊 Muestras capturadas: {session_status['session_stats']['total_samples']}
"""
        
        if session_status['estimated_time_remaining'] != "0:00:00":
            stats_text += f"⏰ Tiempo restante: {session_status['estimated_time_remaining']}\n"
        
        self.session_stats_text.setText(stats_text.strip())
    
    def _update_statistics(self):
        """Actualizar todas las estadísticas"""
        # Estadísticas del dataset
        dataset_stats = self.dataset_manager.get_dataset_statistics()
        
        stats_text = f"""
📊 Total de muestras: {dataset_stats['total_samples']}
⏱️ Duración de sesión: {dataset_stats['session_duration']}

📋 Distribución por gestos:
"""
        
        for gesture, count in dataset_stats['gestures_distribution'].items():
            if dataset_stats['total_samples'] > 0:
                percentage = (count / dataset_stats['total_samples']) * 100
                stats_text += f"  • {gesture}: {count} ({percentage:.1f}%)\n"
        
        self.dataset_stats_text.setText(stats_text.strip())
        
        # Recomendaciones
        recommendations = self.dataset_manager.get_gesture_recommendations()
        rec_text = ""
        
        for urgent in recommendations['urgent']:
            rec_text += f"{urgent}\n"
        
        for suggested in recommendations['suggested']:
            rec_text += f"{suggested}\n"
        
        if not rec_text:
            rec_text = "✅ Dataset bien balanceado"
        
        self.recommendations_text.setText(rec_text.strip())
    
    def _on_frame_ready(self, frame, features, is_connected):
        """Callback para frame de cámara listo"""
        # Actualizar estado del sensor
        self.is_sensor_connected = is_connected
        self.current_features = features
        
        # Actualizar UI del sensor
        if is_connected:
            self.sensor_status_label.setText("🟢 SENSOR CONECTADO")
            self.sensor_status_label.setStyleSheet("color: #4CAF50; padding: 5px;")
            self.connection_help_label.setText("Mano detectada correctamente")
        else:
            self.sensor_status_label.setText("🔴 SENSOR DESCONECTADO")
            self.sensor_status_label.setStyleSheet("color: #f44336; padding: 5px;")
            self.connection_help_label.setText("Muestra tu mano frente a la cámara")
        
        # Guardar muestra si se está grabando
        if (self.session_controller.state == SessionState.RECORDING and 
            features and is_connected):
            
            gesture_info = self.session_controller.get_current_gesture_info()
            gesture_name = gesture_info['gesture_name']
            
            # Mapear nombre a ID
            gesture_id = self.available_gestures.index(gesture_name) if gesture_name in self.available_gestures else 0
            
            # Agregar muestra al dataset
            self.dataset_manager.add_sample(
                features=features,
                gesture_id=gesture_id,
                gesture_name=gesture_name,
                series_number=gesture_info['cycle_number']
            )
            
            # Incrementar contador en sesión
            self.session_controller.increment_sample_count()
        
        # Actualizar display de video
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)
        
        # Actualizar características mostradas
        if features:
            features_text = ""
            important_features = [
                'pinch_score', 'open_hand_score', 'closed_fist_score', 'grasping_score',
                'thumb_index_distance', 'fingers_average_separation',
                'finger_1_extension', 'finger_2_extension', 'finger_3_extension'
            ]
            
            for feature in important_features:
                if feature in features:
                    value = features[feature]
                    if isinstance(value, (int, float)):
                        features_text += f"{feature}: {value:.3f}\n"
            
            self.features_text.setText(features_text)
        
        # Actualizar estadísticas
        self._update_statistics()
    
    def closeEvent(self, event):
        """Evento de cierre de aplicación"""
        # Detener cámara
        self.camera_worker.stop_capture()
        
        # Detener sesión si está activa
        if self.session_controller.state != SessionState.IDLE:
            self.session_controller.stop_session()
        
        # Preguntar si guardar datos antes de cerrar
        if self.dataset_manager.dataset:
            reply = QMessageBox.question(
                self, 
                "Guardar antes de salir", 
                f"Tienes {len(self.dataset_manager.dataset)} muestras sin guardar.\n\n"
                f"¿Deseas guardar antes de salir?"
            )
            
            if reply == QMessageBox.Yes:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"dataset_autosave_{timestamp}.csv"
                success, _ = self.dataset_manager.save_dataset(filename)
                if success:
                    QMessageBox.information(self, "Guardado", f"Dataset guardado como:\n{filename}")
        
        print("👋 Cerrando aplicación...")
        event.accept()

def main():
    """Función principal"""
    app = QApplication(sys.argv)
    
    # Configurar estilo de la aplicación
    app.setStyle('Fusion')
    
    # Configurar palette oscuro opcional
    # palette = QPalette()
    # palette.setColor(QPalette.Window, QColor(53, 53, 53))
    # app.setPalette(palette)
    
    # Crear y mostrar ventana principal
    window = MainGestureApp()
    window.show()
    
    # Mostrar mensaje de bienvenida
    QMessageBox.information(
        window,
        "Bienvenido al Sistema de Dataset de Gestos",
        "🤖 Sistema Modular de Dataset de Gestos v2.0\n\n"
        "Características principales:\n"
        "✅ Detección automática de sensor desconectado\n"
        "✅ Ciclos definidos por el usuario\n"
        "✅ Sistema modular y reutilizable\n"
        "✅ Guardado automático con metadatos\n\n"
        "¡Comienza mostrando tu mano frente a la cámara!"
    )
    
    # Ejecutar aplicación
    sys.exit(app.exec())

if __name__ == "__main__":
    main()"""
Aplicación Principal - Sistema Modular de Dataset de Gestos
Autor: Sistema de Dataset de Gestos
"""

import sys
import cv2
import numpy as np
from datetime import datetime
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

# Importar módulos personalizados
from mediapipe_processor import MediaPipeHandProcessor
from dataset_manager import GestureDatasetManager
from session_controller import GestureSessionController, SessionState

class CameraWorker(QThread):
    """Worker thread para captura de cámara"""
    frame_ready = Signal(np.ndarray, dict, bool)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.processor = MediaPipeHandProcessor()
        
    def run(self):
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Error: No se pudo abrir la cámara")
            return
        
        while self.running:
            ret, frame = cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                processed_frame, features, is_connected = self.processor.process_frame(frame)
                self.frame_ready.emit(processed_frame, features, is_connected)
            
            self.msleep(33)  # ~30 FPS
        
        cap.release()
        
    def start_capture(self):
        self.running = True
        self.start()
        
    def stop_capture(self):
        self.running = False
        self.wait()
        self.processor.cleanup()

class MainGestureApp(QMainWindow):
    """Aplicación principal del sistema de dataset de gestos"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Dataset de Gestos - Modular v2.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # Módulos del sistema
        self.dataset_manager = GestureDatasetManager()
        self.session_controller = GestureSessionController()
        self.camera_worker = CameraWorker()
        
        # Variables de estado
        self.current_features = {}
        self.is_sensor_connected = False
        self.last_gesture_name = "REPOSO"
        
        # Configurar callbacks del controlador de sesión
        self._setup_session_callbacks()
        
        # Timer para actualizar sesión
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._update_session)
        self.session_timer.start(100)  # Actualizar cada 100ms
        
        # Configurar UI
        self._setup_ui()
        
        # Iniciar cámara
        self.camera_worker.frame_ready.connect(self._on_frame_ready)
        self.camera_worker.start_capture()
        
        print("🚀 Aplicación principal iniciada")
    
    def _setup_ui(self):
        """Configurar interfaz de usuario"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        
        # Panel izquierdo - Configuración
        left_panel = self._create_configuration_panel()
        main_layout.addWidget(left_panel, 