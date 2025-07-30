"""
Session Controller - Módulo para control de sesiones de captura
Autor: Sistema de Dataset de Gestos
"""

import time
from typing import Dict, List, Callable, Optional
from datetime import datetime
from enum import Enum

class SessionState(Enum):
    """Estados de la sesión de captura"""
    IDLE = "idle"
    PREPARING = "preparing" 
    COUNTDOWN = "countdown"
    RECORDING = "recording"
    RESTING = "resting"
    COMPLETED = "completed"
    PAUSED = "paused"
    ERROR = "error"

class GestureSessionController:
    """Controlador para sesiones automatizadas de captura de gestos"""
    
    def __init__(self):
        """Inicializar el controlador de sesión"""
        self.state = SessionState.IDLE
        self.config = {}
        self.current_gesture_index = 0
        self.current_series = 0
        self.current_cycle = 0
        self.total_cycles_user_defined = 0
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
        self.last_update_time = 0
        
        # Estadísticas
        self.session_stats = {
            'start_time': None,
            'total_samples': 0,
            'gestures_completed': {},
            'series_completed': 0
        }
        
        print("🎮 Controlador de sesión inicializado")
    
    def configure_session(self, 
                         selected_gestures: List[str],
                         series_count: int = 3,
                         duration_per_gesture: int = 5,
                         rest_time: int = 3,
                         user_cycles: int = 0) -> bool:
        """
        Configurar una nueva sesión de captura
        
        Args:
            selected_gestures: Lista de nombres de gestos a capturar
            series_count: Número de series por gesto
            duration_per_gesture: Duración en segundos de cada captura
            rest_time: Tiempo de descanso entre capturas
            user_cycles: Número de ciclos definidos por el usuario (0 = usar series_count)
            
        Returns:
            bool: True si la configuración es válida
        """
        if not selected_gestures:
            self._trigger_error("No se seleccionaron gestos para capturar")
            return False
        
        if duration_per_gesture < 1 or duration_per_gesture > 60:
            self._trigger_error("Duración por gesto debe estar entre 1 y 60 segundos")
            return False
        
        # Configurar sesión
        self.config = {
            'selected_gestures': selected_gestures.copy(),
            'series_count': series_count,
            'duration_per_gesture': duration_per_gesture,
            'rest_time': rest_time,
            'total_gestures': len(selected_gestures),
            'samples_per_gesture_target': 30 * duration_per_gesture  # ~30 FPS
        }
        
        # Configurar ciclos del usuario
        self.total_cycles_user_defined = user_cycles if user_cycles > 0 else series_count
        
        # Resetear contadores
        self.current_gesture_index = 0
        self.current_series = 0
        self.current_cycle = 0
        self.samples_captured_this_recording = 0
        
        # Estadísticas
        self.session_stats = {
            'start_time': None,
            'total_samples': 0,
            'gestures_completed': {gesture: 0 for gesture in selected_gestures},
            'series_completed': 0,
            'total_recordings_planned': len(selected_gestures) * self.total_cycles_user_defined
        }
        
        print(f"✅ Sesión configurada:")
        print(f"   📋 Gestos: {', '.join(selected_gestures)}")
        print(f"   🔄 Ciclos: {self.total_cycles_user_defined}")
        print(f"   ⏱️ Duración por captura: {duration_per_gesture}s")
        print(f"   😴 Tiempo de descanso: {rest_time}s")
        
        return True
    
    def start_session(self) -> bool:
        """
        Iniciar la sesión de captura
        
        Returns:
            bool: True si se inició correctamente
        """
        if self.state != SessionState.IDLE:
            self._trigger_error(f"No se puede iniciar sesión en estado {self.state.value}")
            return False
        
        if not self.config:
            self._trigger_error("Sesión no configurada")
            return False
        
        # Inicializar sesión
        self.session_stats['start_time'] = datetime.now()
        self.current_gesture_index = 0
        self.current_series = 0
        self.current_cycle = 0
        
        print(f"🚀 Iniciando sesión de captura")
        print(f"   📊 Total de grabaciones: {self.session_stats['total_recordings_planned']}")
        
        self._change_state(SessionState.PREPARING)
        self._start_next_recording()
        
        return True
    
    def stop_session(self) -> bool:
        """
        Detener la sesión actual
        
        Returns:
            bool: True si se detuvo correctamente
        """
        if self.state == SessionState.IDLE:
            return True
        
        print(f"⏹️ Deteniendo sesión...")
        print(f"   📊 Muestras capturadas: {self.session_stats['total_samples']}")
        
        self._change_state(SessionState.IDLE)
        return True
    
    def pause_session(self) -> bool:
        """Pausar la sesión actual"""
        if self.state in [SessionState.COUNTDOWN, SessionState.RECORDING, SessionState.RESTING]:
            print("⏸️ Sesión pausada")
            self._change_state(SessionState.PAUSED)
            return True
        return False
    
    def resume_session(self) -> bool:
        """Reanudar la sesión pausada"""
        if self.state == SessionState.PAUSED:
            print("▶️ Reanudando sesión")
            self._change_state(SessionState.PREPARING)
            self._start_next_recording()
            return True
        return False
    
    def update(self) -> Dict:
        """
        Actualizar el estado de la sesión (llamar en loop principal)
        
        Returns:
            Dict: Estado actual de la sesión
        """
        current_time = time.time()
        
        # Procesar estado actual
        if self.state == SessionState.COUNTDOWN:
            self._update_countdown(current_time)
        elif self.state == SessionState.RECORDING:
            self._update_recording(current_time)
        elif self.state == SessionState.RESTING:
            self._update_resting(current_time)
        
        self.last_update_time = current_time
        
        return self.get_session_status()
    
    def increment_sample_count(self) -> bool:
        """
        Incrementar contador de muestras capturadas
        
        Returns:
            bool: True si se incrementó correctamente
        """
        if self.state == SessionState.RECORDING:
            self.samples_captured_this_recording += 1
            self.session_stats['total_samples'] += 1
            return True
        return False
    
    def get_current_gesture_info(self) -> Dict:
        """
        Obtener información del gesto actual
        
        Returns:
            Dict: Información del gesto actual
        """
        if not self.config or self.current_gesture_index >= len(self.config['selected_gestures']):
            return {
                'gesture_name': 'NINGUNO',
                'gesture_index': -1,
                'series_number': 0,
                'cycle_number': 0
            }
        
        return {
            'gesture_name': self.config['selected_gestures'][self.current_gesture_index],
            'gesture_index': self.current_gesture_index,
            'series_number': self.current_series + 1,
            'cycle_number': self.current_cycle + 1,
            'total_cycles': self.total_cycles_user_defined
        }
    
    def get_session_status(self) -> Dict:
        """
        Obtener estado completo de la sesión
        
        Returns:
            Dict: Estado completo de la sesión
        """
        progress = 0
        if self.session_stats['total_recordings_planned'] > 0:
            completed = (self.current_cycle * len(self.config.get('selected_gestures', [])) + 
                        self.current_gesture_index)
            progress = min(100, (completed / self.session_stats['total_recordings_planned']) * 100)
        
        return {
            'state': self.state.value,
            'current_gesture': self.get_current_gesture_info(),
            'countdown_remaining': self.countdown_remaining,
            'progress_percentage': progress,
            'session_stats': self.session_stats.copy(),
            'recording_active': self.state == SessionState.RECORDING,
            'samples_this_recording': self.samples_captured_this_recording,
            'estimated_time_remaining': self._calculate_time_remaining()
        }
    
    def get_session_summary(self) -> str:
        """
        Obtener resumen de la sesión
        
        Returns:
            str: Resumen formateado de la sesión
        """
        status = self.get_session_status()
        
        summary = f"""
🎯 ESTADO DE LA SESIÓN
{'='*40}
📊 Estado: {status['state'].upper()}
🎮 Gesto actual: {status['current_gesture']['gesture_name']}
🔄 Ciclo: {status['current_gesture']['cycle_number']}/{status['current_gesture']['total_cycles']}
📈 Progreso: {status['progress_percentage']:.1f}%
📋 Muestras totales: {status['session_stats']['total_samples']}
"""
        
        if status['countdown_remaining'] > 0:
            summary += f"⏱️ Countdown: {status['countdown_remaining']}s\n"
        
        if status['estimated_time_remaining']:
            summary += f"⏰ Tiempo estimado restante: {status['estimated_time_remaining']}\n"
        
        return summary
    
    # Métodos privados
    
    def _start_next_recording(self):
        """Iniciar la siguiente grabación"""
        # Verificar si la sesión está completa
        if self.current_cycle >= self.total_cycles_user_defined:
            self._complete_session()
            return
        
        # Verificar si necesitamos pasar al siguiente ciclo
        if self.current_gesture_index >= len(self.config['selected_gestures']):
            self.current_gesture_index = 0
            self.current_cycle += 1
            
            if self.current_cycle >= self.total_cycles_user_defined:
                self._complete_session()
                return
        
        # Preparar siguiente grabación
        gesture_info = self.get_current_gesture_info()
        print(f"📋 Preparando: {gesture_info['gesture_name']} (Ciclo {gesture_info['cycle_number']})")
        
        if self.on_gesture_change:
            self.on_gesture_change(gesture_info)
        
        # Iniciar countdown
        self.countdown_remaining = self.config['rest_time']
        self._change_state(SessionState.COUNTDOWN)
    
    def _update_countdown(self, current_time):
        """Actualizar countdown antes de grabación"""
        if not hasattr(self, '_countdown_start_time'):
            self._countdown_start_time = current_time
        
        elapsed = current_time - self._countdown_start_time
        self.countdown_remaining = max(0, self.config['rest_time'] - int(elapsed))
        
        if self.on_countdown_tick:
            self.on_countdown_tick(self.countdown_remaining)
        
        if self.countdown_remaining <= 0:
            self._start_recording()
    
    def _start_recording(self):
        """Iniciar grabación del gesto actual"""
        self.recording_start_time = time.time()
        self.samples_captured_this_recording = 0
        
        gesture_info = self.get_current_gesture_info()
        print(f"🔴 GRABANDO: {gesture_info['gesture_name']}")
        
        self._change_state(SessionState.RECORDING)
        
        if self.on_recording_start:
            self.on_recording_start(gesture_info)
    
    def _update_recording(self, current_time):
        """Actualizar estado durante grabación"""
        elapsed = current_time - self.recording_start_time
        
        if elapsed >= self.config['duration_per_gesture']:
            self._stop_recording()
    
    def _stop_recording(self):
        """Detener grabación actual"""
        gesture_info = self.get_current_gesture_info()
        gesture_name = gesture_info['gesture_name']
        
        # Actualizar estadísticas
        self.session_stats['gestures_completed'][gesture_name] += 1
        
        print(f"⏹️ Grabación completada: {gesture_name}")
        print(f"   📊 Muestras capturadas: {self.samples_captured_this_recording}")
        
        if self.on_recording_end:
            self.on_recording_end(gesture_info, self.samples_captured_this_recording)
        
        # Avanzar al siguiente gesto
        self.current_gesture_index += 1
        
        # Cambiar a estado de descanso antes del siguiente
        self._change_state(SessionState.RESTING)
        self._rest_start_time = time.time()
    
    def _update_resting(self, current_time):
        """Actualizar estado de descanso"""
        if not hasattr(self, '_rest_start_time'):
            self._rest_start_time = current_time
        
        elapsed = current_time - self._rest_start_time
        
        # Descanso breve antes del siguiente
        if elapsed >= 1.0:  # 1 segundo de descanso
            self._change_state(SessionState.PREPARING)
            self._start_next_recording()
    
    def _complete_session(self):
        """Completar la sesión"""
        print(f"🎉 ¡SESIÓN COMPLETADA!")
        print(f"   📊 Total de muestras: {self.session_stats['total_samples']}")
        print(f"   ⏱️ Duración: {self._calculate_session_duration()}")
        
        self._change_state(SessionState.COMPLETED)
        
        if self.on_session_complete:
            self.on_session_complete(self.session_stats)
    
    def _change_state(self, new_state: SessionState):
        """Cambiar estado de la sesión"""
        old_state = self.state
        self.state = new_state
        
        if hasattr(self, '_countdown_start_time') and new_state != SessionState.COUNTDOWN:
            delattr(self, '_countdown_start_time')
        
        if self.on_state_change:
            self.on_state_change(old_state, new_state)
    
    def _trigger_error(self, message: str):
        """Activar error en la sesión"""
        print(f"❌ Error: {message}")
        self._change_state(SessionState.ERROR)
        
        if self.on_error:
            self.on_error(message)
    
    def _calculate_session_duration(self) -> str:
        """Calcular duración de la sesión"""
        if not self.session_stats['start_time']:
            return "0:00:00"
        
        duration = datetime.now() - self.session_stats['start_time']
        hours, remainder = divmod(duration.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    
    def _calculate_time_remaining(self) -> str:
        """Calcular tiempo estimado restante"""
        if not self.config or self.state in [SessionState.IDLE, SessionState.COMPLETED]:
            return "0:00:00"
        
        # Cálculo de grabaciones restantes
        remaining_in_current_cycle = len(self.config['selected_gestures']) - self.current_gesture_index
        remaining_cycles = self.total_cycles_user_defined - self.current_cycle - 1
        total_remaining = remaining_in_current_cycle + (remaining_cycles * len(self.config['selected_gestures']))
        
        # Tiempo por grabación (captura + descanso)
        time_per_recording = self.config['duration_per_gesture'] + self.config['rest_time']
        
        # Tiempo total restante en segundos
        total_seconds = total_remaining * time_per_recording
        
        # Convertir a formato HH:MM:SS
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"

# Funciones de utilidad
def create_session_controller() -> GestureSessionController:
    """Crear una instancia del controlador de sesión"""
    return GestureSessionController()

def setup_session_callbacks(controller: GestureSessionController, 
                           callbacks: Dict[str, Callable]) -> bool:
    """
    Configurar callbacks para eventos de la sesión
    
    Args:
        controller: Instancia del controlador
        callbacks: Diccionario con callbacks {evento: función}
        
    Returns:
        bool: True si se configuraron correctamente
    """
    callback_mapping = {
        'state_change': 'on_state_change',
        'gesture_change': 'on_gesture_change', 
        'countdown_tick': 'on_countdown_tick',
        'recording_start': 'on_recording_start',
        'recording_end': 'on_recording_end',
        'session_complete': 'on_session_complete',
        'error': 'on_error'
    }
    
    for event, callback in callbacks.items():
        if event in callback_mapping:
            setattr(controller, callback_mapping[event], callback)
    
    return True