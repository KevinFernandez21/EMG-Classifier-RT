"""
Ejemplo de uso del sistema modular de dataset de gestos
Muestra cómo usar cada módulo independientemente
"""

import cv2
import numpy as np
from datetime import datetime

# Importar módulos del sistema
from mediapipe_processor import MediaPipeHandProcessor, create_hand_processor
from dataset_manager import GestureDatasetManager, create_dataset_manager
from session_controller import GestureSessionController, SessionState

def ejemplo_uso_mediapipe():
    """Ejemplo de uso del procesador MediaPipe independiente"""
    print("🤖 EJEMPLO: Uso del Procesador MediaPipe")
    print("="*50)
    
    # Crear procesador
    processor = create_hand_processor(confidence=0.7)
    
    # Capturar de cámara
    cap = cv2.VideoCapture(0)
    
    print("📹 Mostrando detección en tiempo real...")
    print("   - Muestra tu mano frente a la cámara")
    print("   - Presiona 'q' para salir")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        
        # Procesar frame
        processed_frame, features, is_connected = processor.process_frame(frame)
        
        # Detectar gesto automáticamente
        if features:
            gesture_id, gesture_name = processor.detect_gesture(features)
            
            # Mostrar información en pantalla
            info_text = f"Gesto: {gesture_name}"
            if not is_connected:
                info_text = "SENSOR DESCONECTADO"
            
            cv2.putText(processed_frame, info_text, (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            
            # Mostrar scores
            if 'pinch_score' in features:
                score_text = f"Pinza: {features['pinch_score']:.2f}"
                cv2.putText(processed_frame, score_text, (10, 90), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.imshow('MediaPipe Processor Example', processed_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    processor.cleanup()
    print("✅ Ejemplo MediaPipe completado")

def ejemplo_uso_dataset_manager():
    """Ejemplo de uso del gestor de dataset independiente"""
    print("\n📊 EJEMPLO: Uso del Gestor de Dataset")
    print("="*50)
    
    # Crear gestor
    manager = create_dataset_manager()
    
    # Configurar nueva sesión
    session_config = {
        'selected_gestures': ['CERRAR_MANO', 'PINZA', 'SALUDAR'],
        'series_count': 3,
        'duration_per_gesture': 5,
        'rest_time': 2
    }
    
    session_id = manager.start_new_session(session_config)
    print(f"📋 Sesión iniciada: {session_id}")
    
    # Simular datos de muestra
    print("📝 Agregando muestras de ejemplo...")
    
    # Datos simulados para diferentes gestos
    sample_features = {
        'thumb_index_distance': 0.05,
        'pinch_score': 0.8,
        'open_hand_score': 0.2,
        'closed_fist_score': 0.1,
        'grasping_score': 0.3,
        'finger_1_extension': 0.9,
        'finger_2_extension': 0.9,
        'hand_compactness': 0.15
    }
    
    # Agregar muestras para cada gesto
    for gesture_name in ['CERRAR_MANO', 'PINZA', 'SALUDAR']:
        gesture_id = ['REPOSO', 'CERRAR_MANO', 'PINZA', 'SALUDAR', 'TOMAR_OBJETO'].index(gesture_name)
        
        for series in range(1, 4):  # 3 series
            for sample in range(50):  # 50 muestras por serie
                # Modificar características según el gesto
                modified_features = sample_features.copy()
                
                if gesture_name == 'PINZA':
                    modified_features['pinch_score'] = 0.8 + np.random.normal(0, 0.1)
                    modified_features['thumb_index_distance'] = 0.03 + np.random.normal(0, 0.01)
                elif gesture_name == 'SALUDAR':
                    modified_features['open_hand_score'] = 0.9 + np.random.normal(0, 0.1)
                    modified_features['fingers_average_separation'] = 0.15 + np.random.normal(0, 0.02)
                elif gesture_name == 'CERRAR_MANO':
                    modified_features['closed_fist_score'] = 0.9 + np.random.normal(0, 0.1)
                    modified_features['hand_compactness'] = 0.05 + np.random.normal(0, 0.01)
                
                manager.add_sample(
                    features=modified_features,
                    gesture_id=gesture_id,
                    gesture_name=gesture_name,
                    series_number=series
                )
    
    # Mostrar estadísticas
    stats = manager.get_dataset_statistics()
    print(f"📊 Dataset creado:")
    print(f"   Total de muestras: {stats['total_samples']}")
    print(f"   Distribución: {stats['gestures_distribution']}")
    
    # Obtener recomendaciones
    recommendations = manager.get_gesture_recommendations()
    if recommendations['suggested']:
        print(f"\n💡 Recomendaciones:")
        for rec in recommendations['suggested']:
            print(f"   {rec}")
    
    # Guardar dataset
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"example_dataset_{timestamp}.csv"
    success, result = manager.save_dataset(filename)
    
    if success:
        print(f"✅ Dataset guardado: {filename}")
    else:
        print(f"❌ Error al guardar: {result}")
    
    # Exportar para ML
    success, export_info = manager.export_for_ml("example_ml_export")
    if success:
        print(f"🤖 Dataset exportado para ML:")
        print(f"   Directorio: {export_info['output_dir']}")
        print(f"   Archivos: {list(export_info['files_created'].keys())}")

def ejemplo_uso_session_controller():
    """Ejemplo de uso del controlador de sesión independiente"""
    print("\n🎮 EJEMPLO: Uso del Controlador de Sesión")
    print("="*50)
    
    # Crear controlador
    controller = GestureSessionController()
    
    # Configurar callbacks
    def on_state_change(old_state, new_state):
        print(f"🔄 Estado: {old_state.value} → {new_state.value}")
    
    def on_gesture_change(gesture_info):
        print(f"🎯 Nuevo gesto: {gesture_info['gesture_name']} (Ciclo {gesture_info['cycle_number']})")
    
    def on_countdown_tick(remaining):
        if remaining > 0:
            print(f"⏱️ Countdown: {remaining}")
    
    def on_recording_start(gesture_info):
        print(f"🔴 GRABANDO: {gesture_info['gesture_name']}")
    
    def on_recording_end(gesture_info, samples):
        print(f"⏹️ Grabación terminada: {samples} muestras")
    
    def on_session_complete(stats):
        print(f"🎉 ¡Sesión completada! Total: {stats['total_samples']} muestras")
    
    # Asignar callbacks
    controller.on_state_change = on_state_change
    controller.on_gesture_change = on_gesture_change
    controller.on_countdown_tick = on_countdown_tick
    controller.on_recording_start = on_recording_start
    controller.on_recording_end = on_recording_end
    controller.on_session_complete = on_session_complete
    
    # Configurar sesión
    gestures = ['CERRAR_MANO', 'PINZA']
    success = controller.configure_session(
        selected_gestures=gestures,
        series_count=2,
        duration_per_gesture=3,  # 3 segundos por gesto
        rest_time=2,            # 2 segundos de preparación
        user_cycles=2           # 2 ciclos definidos por usuario
    )
    
    if not success:
        print("❌ Error configurando sesión")
        return
    
    # Iniciar sesión
    print("🚀 Iniciando sesión de ejemplo...")
    controller.start_session()
    
    # Simular loop principal
    import time
    start_time = time.time()
    sample_count = 0
    
    try:
        while controller.state != SessionState.COMPLETED and controller.state != SessionState.IDLE:
            # Actualizar controlador
            status = controller.update()
            
            # Simular captura de muestras durante grabación
            if status['recording_active']:
                # Simular ~10 muestras por segundo
                if time.time() - start_time > 0.1:  # Cada 100ms
                    controller.increment_sample_count()
                    sample_count += 1
                    start_time = time.time()
            
            # Mostrar progreso ocasionalmente
            if status['progress_percentage'] > 0:
                progress = status['progress_percentage']
                if int(progress) % 25 == 0:  # Cada 25%
                    print(f"📈 Progreso: {progress:.1f}%")
            
            time.sleep(0.1)  # 100ms de pausa
            
            # Límite de seguridad para el ejemplo
            if sample_count > 1000:
                print("⏱️ Límite de tiempo alcanzado, deteniendo...")
                controller.stop_session()
                break
                
    except KeyboardInterrupt:
        print("\n⏹️ Sesión interrumpida por usuario")
        controller.stop_session()
    
    # Mostrar resumen final
    final_status = controller.get_session_status()
    print(f"\n📋 Resumen final:")
    print(f"   Estado: {final_status['state']}")
    print(f"   Progreso: {final_status['progress_percentage']:.1f}%")
    print(f"   Muestras totales: {final_status['session_stats']['total_samples']}")

def ejemplo_uso_integrado():
    """Ejemplo de uso integrado de todos los módulos"""
    print("\n🔧 EJEMPLO: Uso Integrado de Todos los Módulos")
    print("="*50)
    
    # Crear instancias
    processor = create_hand_processor()
    manager = create_dataset_manager()
    controller = GestureSessionController()
    
    print("✅ Todos los módulos inicializados")
    print("📝 Este ejemplo muestra cómo integrar:")
    print("   • MediaPipe para detección de gestos")
    print("   • Dataset Manager para almacenar datos")  
    print("   • Session Controller para automatización")
    print("   • Detección de sensor desconectado")
    
    # Configurar sesión
    session_config = {
        'selected_gestures': ['PINZA'],
        'series_count': 1,
        'duration_per_gesture': 5,
        'rest_time': 3
    }
    
    manager.start_new_session(session_config)
    controller.configure_session(
        selected_gestures=['PINZA'],
        user_cycles=1,
        duration_per_gesture=5,
        rest_time=3
    )
    
    print("🎯 Configuración completada - todos los módulos trabajan juntos")
    print("💡 En la aplicación principal, estos módulos se integran")
    print("   para crear un sistema completo y automático")
    
    # Cleanup
    processor.cleanup()

def main():
    """Ejecutar todos los ejemplos"""
    print("🚀 EJEMPLOS DE USO DEL SISTEMA MODULAR")
    print("="*60)
    print("Este archivo muestra cómo usar cada módulo independientemente")
    print("="*60)
    
    try:
        # Ejemplo 1: MediaPipe Processor
        ejemplo_uso_mediapipe()
        
        # Ejemplo 2: Dataset Manager  
        ejemplo_uso_dataset_manager()
        
        # Ejemplo 3: Session Controller
        ejemplo_uso_session_controller()
        
        # Ejemplo 4: Uso integrado
        ejemplo_uso_integrado()
        
        print("\n🎉 ¡Todos los ejemplos completados!")
        print("💡 Para usar el sistema completo, ejecuta: python main_app.py")
        
    except KeyboardInterrupt:
        print("\n👋 Ejemplos interrumpidos por usuario")
    except Exception as e:
        print(f"\n❌ Error en ejemplos: {e}")

if __name__ == "__main__":
    main()