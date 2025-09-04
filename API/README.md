# EMG Gesture Recognition API

API REST para reconocimiento de gestos basado en señales EMG usando TensorFlow Lite, diseñada para comunicación con ESP32.

## Características

- **Modelo**: Red neuronal CNN + LSTM entrenada en PyTorch y convertida a TensorFlow Lite
- **Gestos**: 4 clases (CERRAR_MANO, PINZA, SALUDAR, TOMAR_OBJ)
- **Entrada**: 3 canales EMG, ventana de 250 muestras (250ms a 1000Hz)
- **Preprocesamiento**: Filtrado Butterworth, rectificación, normalización Z-score

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

### Iniciar el servidor
```bash
python main.py
```
El servidor estará disponible en `http://localhost:5000`

### Endpoints

#### `/health` (GET)
Verificación de estado del servidor y modelo.

**Respuesta:**
```json
{
    "status": "healthy",
    "model_loaded": true
}
```

#### `/predict` (POST)
Predicción completa con formato detallado.

**Entrada:**
```json
{
    "emg_data": [[emg1_t0, emg2_t0, emg3_t0], ...],  // 250 muestras
    "timestamp": "opcional"
}
```

**Salida:**
```json
{
    "success": true,
    "prediction": {
        "gesture": "CERRAR_MANO",
        "confidence": 0.95,
        "probabilities": {
            "CERRAR_MANO": 0.95,
            "PINZA": 0.03,
            "SALUDAR": 0.01,
            "TOMAR_OBJ": 0.01
        }
    },
    "timestamp": "opcional"
}
```

#### `/predict_simple` (POST) - **Recomendado para ESP32**
Predicción simplificada optimizada para microcontroladores.

**Entrada:**
```json
{
    "emg1": [val1, val2, ..., val250],
    "emg2": [val1, val2, ..., val250],
    "emg3": [val1, val2, ..., val250]
}
```

**Salida:**
```json
{
    "gesture": "CERRAR_MANO",
    "confidence": 0.95
}
```

#### `/info` (GET)
Información del modelo y endpoints disponibles.

## Integración con ESP32

### Librerías requeridas
```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
```

### Ejemplo de uso
Ver `esp32_client_example.cpp` para un ejemplo completo de implementación.

### Flujo recomendado para ESP32:

1. **Adquisición de datos**: Muestrear 3 canales EMG a 1000Hz
2. **Buffer circular**: Mantener ventana deslizante de 250 muestras
3. **Predicción**: Enviar datos cada 50ms (overlap del 80%)
4. **Filtrado**: Solo mostrar predicciones con confianza > 0.7

### Configuración de hardware típica:
- **ADC**: 12-bit, 3.3V referencia
- **Frecuencia de muestreo**: 1000Hz
- **Canales**: 3 sensores EMG diferencial

## Especificaciones técnicas

- **Modelo**: TensorFlow Lite
- **Tamaño**: ~774KB
- **Ventana de entrada**: 250 muestras × 3 canales
- **Latencia**: <50ms en hardware típico
- **Precisión**: ~95% en dataset de validación

## Preprocesamiento de señales

1. **Filtro paso-banda**: Butterworth 4º orden (20-450 Hz)
2. **Rectificación**: Valor absoluto
3. **Envelope**: Filtro paso-bajo 2º orden (5 Hz)
4. **Normalización**: Z-score por canal

## Códigos de error

- `400`: Datos de entrada inválidos
- `500`: Error interno del modelo
- `404`: Endpoint no encontrado

## Optimizaciones para producción

- Usar servidor WSGI (Gunicorn)
- Implementar cache para modelo
- Añadir logging detallado
- Configurar CORS si necesario

## Troubleshooting

### Error "Modelo no disponible"
- Verificar que existe `weight/tflite_learn_774610_3.tflite`
- Comprobar permisos de lectura

### Baja precisión
- Verificar calibración de sensores EMG
- Asegurar frecuencia de muestreo correcta (1000Hz)
- Validar que el preprocesamiento coincida con el entrenamiento