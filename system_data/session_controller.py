"""
Session Controller - Simplificado para EMG
Solo funciones esenciales sin errores
"""

import time
from typing import Dict, List, Callable, Optional
from datetime import datetime
from enum import Enum

class SessionState(Enum):
    """Estados de la sesión de captura"""
    IDLE = "idle"
    COUNTDOWN = "countdown"
    RECORDING = "recording"
    COMPLETED = "completed"
    PAUSED = "paused"

class GestureSessionController:
    """Controlador simplificado para sesiones EMG"""
    
    def __init__(self):
        """Inicializar el controlador de sesión"""
        self.state = SessionState.IDLE
        self.config = {}
        self.current_gesture_index = 0
        self.current_cycle = 0
        self.total_cycles = 0
        self.samples_captured_this_recording = 0
        
        # Callbacks para eventos
        self.on_state_change: Optional[Callable] = None
        self.on_gesture_change: Optional[Callable] = None
        self.on_countdown_tick: Optional[Callable] = None
        self.on_recording_start: Optional[Callable] = None
        self.on_recording_end: Optional[Callable] = None
        self.on_session_complete: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        
        # Control de tiempo
        self.countdown_remaining = 0
        self.recording_start_time = 0
        
        # Estadísticas básicas
        self.session_stats = {
            'start_time': None,
            'total_samples': 0,
            'total_recordings_planned': 0
        }
        
        print("🎮 Controlador de sesión EMG inicializado")
    
    def configure_session(self, 
                         selected_gestures: List[str],
                         duration_per_gesture: int = 5,
                         rest_time: int = 3,
                         user_cycles: int = 1,
                         **kwargs) -> bool:
        """Configurar una nueva sesión de captura"""
        if not selected_gestures:
            self._trigger_error("No se seleccionaron gestos para capturar")
            return False
        
        if duration_per_gesture < 1 or duration_per_gesture > 60:
            self._trigger_error("Duración por gesto debe estar entre 1 y 60 segundos")
            return False
        
        # Configurar sesión simplificada
        self.config = {
            'selected_gestures': selected_gestures.copy(),
            'duration_per_gesture': duration_per_gesture,
            'rest_time': rest_time,
            'total_gestures': len(selected_gestures)
        }
        
        # Configurar ciclos
        self.total_cycles = user_cycles if user_cycles > 0 else 1
        
        # Resetear contadores
        self.current_gesture_index = 0
        self.current_cycle = 0
        self.samples_captured_this_recording = 0
        
        # Estadísticas básicas
        self.session_stats = {
            'start_time': None,
            'total_samples': 0,
            'total_recordings_planned': len(selected_gestures) * self.total_cycles
        }
        
        print(f"✅ Sesión EMG configurada:")
        print(f"   📋 Gestos: {', '.join(selected_gestures)}")
        print(f"   🔄 Ciclos: {self.total_cycles}")
        print(f"   ⏱️ Duración: {duration_per_gesture}s")
        
        return True
    
    def start_session(self) -> bool:
        """Iniciar la sesión de captura"""
        if self.state != SessionState.IDLE:
            self._trigger_error(f"No se puede iniciar sesión en estado {self.state.value}")
            return False
        
        if not self.config:
            self._trigger_error("Sesión no configurada")
            return False
        
        # Inicializar sesión
        self.session_stats['start_time'] = datetime.now()
        self.current_gesture_index = 0
        self.current_cycle = 0
        
        print(f"🚀 Iniciando sesión EMG")
        
        self._start_next_recording()
        return True
    
    def stop_session(self) -> bool:
        """Detener la sesión actual"""
        if self.state == SessionState.IDLE:
            return True
        
        print(f"⏹️ Deteniendo sesión EMG...")
        self._change_state(SessionState.IDLE)
        return True
    
    def pause_session(self) -> bool:
        """Pausar la sesión actual"""
        if self.state in [SessionState.COUNTDOWN, SessionState.RECORDING]:
            print("⏸️ Sesión pausada")
            self._change_state(SessionState.PAUSED)
            return True
        return False
    
    def resume_session(self) -> bool:
        """Reanudar la sesión pausada"""
        if self.state == SessionState.PAUSED:
            print("▶️ Reanudando sesión")
            self._start_next_recording()
            return True
        return False
    
    def update(self) -> Dict:
        """Actualizar el estado de la sesión"""
        current_time = time.time()
        
        try:
            # Procesar estado actual
            if self.state == SessionState.COUNTDOWN:
                self._update_countdown(current_time)
            elif self.state == SessionState.RECORDING:
                self._update_recording(current_time)
            
            return self.get_session_status()
        except Exception as e:
            print(f"Error en update: {e}")
            return self.get_session_status()
    
    def increment_sample_count(self) -> bool:
        """Incrementar contador de muestras capturadas"""
        if self.state == SessionState.RECORDING:
            self.samples_captured_this_recording += 1
            self.session_stats['total_samples'] += 1
            return True
        return False
    
    def get_current_gesture_info(self) -> Dict:
        """Obtener información del gesto actual"""
        try:
            if not self.config or not hasattr(self, 'config') or 'selected_gestures' not in self.config:
                return {
                    'gesture_name': 'NINGUNO',
                    'gesture_index': 0,
                    'cycle_number': 1,
                    'total_cycles': 1
                }
            
            if self.current_gesture_index >= len(self.config['selected_gestures']):
                return {
                    'gesture_name': 'COMPLETADO',
                    'gesture_index': self.current_gesture_index,
                    'cycle_number': self.current_cycle + 1,
                    'total_cycles': self.total_cycles
                }
            
            return {
                'gesture_name': self.config['selected_gestures'][self.current_gesture_index],
                'gesture_index': self.current_gesture_index,
                'cycle_number': self.current_cycle + 1,
                'total_cycles': self.total_cycles
            }
        except Exception as e:
            print(f"Error en get_current_gesture_info: {e}")
            return {
                'gesture_name': 'ERROR',
                'gesture_index': 0,
                'cycle_number': 1,
                'total_cycles': 1
            }
    
    def get_session_status(self) -> Dict:
        """Obtener estado completo de la sesión"""
        try:
            # Calcular progreso de forma segura
            progress = 0
            total_planned = self.session_stats.get('total_recordings_planned', 1)
            if total_planned > 0:
                completed = (self.current_cycle * len(self.config.get('selected_gestures', [])) + 
                            self.current_gesture_index)
                progress = min(100, (completed / total_planned) * 100)
            
            return {
                'state': self.state,
                'current_gesture': self.get_current_gesture_info(),
                'countdown_remaining': getattr(self, 'countdown_remaining', 0),
                'progress_percentage': progress,
                'session_stats': self.session_stats.copy(),
                'recording_active': self.state == SessionState.RECORDING,
                'samples_this_recording': getattr(self, 'samples_captured_this_recording', 0),
                'estimated_time_remaining': "0:00:00"  # Simplificado
            }
        except Exception as e:
            print(f"Error en get_session_status: {e}")
            return {
                'state': self.state,
                'current_gesture': {'gesture_name': 'ERROR', 'cycle_number': 0, 'total_cycles': 0},
                'countdown_remaining': 0,
                'progress_percentage': 0,
                'session_stats': {'total_samples': 0},
                'recording_active': False,
                'samples_this_recording': 0,
                'estimated_time_remaining': "0:00:00"
            }
    
    # Métodos privados simplificados
    
    def _start_next_recording(self):
        """Iniciar la siguiente grabación"""
        try:
            # Verificar si la sesión está completa
            if self.current_cycle >= self.total_cycles:
                self._complete_session()
                return
            
            # Verificar si necesitamos pasar al siguiente ciclo
            if hasattr(self, 'config') and 'selected_gestures' in self.config:
                if self.current_gesture_index >= len(self.config['selected_gestures']):
                    self.current_gesture_index = 0
                    self.current_cycle += 1
                    
                    if self.current_cycle >= self.total_cycles:
                        self._complete_session()
                        return
            else:
                print("❌ Error: Configuración no válida")
                return
            
            # Preparar siguiente grabación
            gesture_info = self.get_current_gesture_info()
            print(f"📋 Preparando: {gesture_info['gesture_name']} (Ciclo {gesture_info['cycle_number']})")
            
            # Solo llamar callback si existe
            if self.on_gesture_change and callable(self.on_gesture_change):
                try:
                    self.on_gesture_change(gesture_info)
                except Exception as e:
                    print(f"Error en callback gesture_change: {e}")
            
            # Iniciar countdown
            rest_time = self.config.get('rest_time', 2)
            self.countdown_remaining = rest_time
            self._change_state(SessionState.COUNTDOWN)
            self._countdown_start_time = time.time()
            
        except Exception as e:
            print(f"Error en _start_next_recording: {e}")
            self._trigger_error(f"Error iniciando grabación: {e}")
    
    def _update_countdown(self, current_time):
        """Actualizar countdown antes de grabación"""
        try:
            if not hasattr(self, '_countdown_start_time'):
                self._countdown_start_time = current_time
            
            rest_time = self.config.get('rest_time', 2)
            elapsed = current_time - self._countdown_start_time
            self.countdown_remaining = max(0, rest_time - int(elapsed))
            
            # Solo llamar callback si existe
            if self.on_countdown_tick and callable(self.on_countdown_tick):
                try:
                    self.on_countdown_tick(self.countdown_remaining)
                except Exception as e:
                    print(f"Error en callback countdown_tick: {e}")
            
            if self.countdown_remaining <= 0:
                self._start_recording()
                
        except Exception as e:
            print(f"Error en _update_countdown: {e}")
    
    def _start_recording(self):
        """Iniciar grabación del gesto actual"""
        try:
            self.recording_start_time = time.time()
            self.samples_captured_this_recording = 0
            
            gesture_info = self.get_current_gesture_info()
            print(f"🔴 GRABANDO: {gesture_info['gesture_name']}")
            
            self._change_state(SessionState.RECORDING)
            
            # Solo llamar callback si existe
            if self.on_recording_start and callable(self.on_recording_start):
                try:
                    self.on_recording_start(gesture_info)
                except Exception as e:
                    print(f"Error en callback recording_start: {e}")
                
        except Exception as e:
            print(f"Error en _start_recording: {e}")
    
    def _update_recording(self, current_time):
        """Actualizar estado durante grabación"""
        try:
            duration = self.config.get('duration_per_gesture', 8)
            elapsed = current_time - self.recording_start_time
            
            if elapsed >= duration:
                self._stop_recording()
                
        except Exception as e:
            print(f"Error en _update_recording: {e}")
    
    def _stop_recording(self):
        """Detener grabación actual"""
        try:
            gesture_info = self.get_current_gesture_info()
            gesture_name = gesture_info['gesture_name']
            
            print(f"⏹️ Grabación completada: {gesture_name}")
            print(f"   📊 Muestras capturadas: {self.samples_captured_this_recording}")
            
            # Solo llamar callback si existe
            if self.on_recording_end and callable(self.on_recording_end):
                try:
                    self.on_recording_end(gesture_info, self.samples_captured_this_recording)
                except Exception as e:
                    print(f"Error en callback recording_end: {e}")
            
            # Avanzar al siguiente gesto
            self.current_gesture_index += 1
            
            # Breve pausa antes del siguiente
            time.sleep(0.5)
            self._start_next_recording()
            
        except Exception as e:
            print(f"Error en _stop_recording: {e}")
    
    def _complete_session(self):
        """Completar la sesión"""
        try:
            print(f"🎉 ¡SESIÓN EMG COMPLETADA!")
            print(f"   📊 Total de muestras: {self.session_stats['total_samples']}")
            
            self._change_state(SessionState.COMPLETED)
            
            if self.on_session_complete:
                self.on_session_complete(self.session_stats)
                
        except Exception as e:
            print(f"Error en _complete_session: {e}")
    
    def _change_state(self, new_state: SessionState):
        """Cambiar estado de la sesión"""
        try:
            old_state = self.state
            self.state = new_state
            
            # Solo llamar callback si existe
            if self.on_state_change and callable(self.on_state_change):
                try:
                    self.on_state_change(old_state, new_state)
                except Exception as e:
                    print(f"Error en callback state_change: {e}")
                
        except Exception as e:
            print(f"Error en _change_state: {e}")
    
    def _trigger_error(self, message: str):
        """Activar error en la sesión"""
        print(f"❌ Error: {message}")
        
        if self.on_error:
            self.on_error(message)
    
    def _calculate_session_duration(self) -> str:
        """Calcular duración de la sesión"""
        try:
            if not self.session_stats.get('start_time'):
                return "0:00:00"
            
            duration = datetime.now() - self.session_stats['start_time']
            hours, remainder = divmod(duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        except:
            return "0:00:00"

# Función de utilidad
def create_session_controller() -> GestureSessionController:
    """Crear una instancia del controlador de sesión"""
    return GestureSessionController()