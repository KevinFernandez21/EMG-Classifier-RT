# ESP32 EMG Real-Time Gesture Recognition

Este código permite a la ESP32 comunicarse con el sensor uMyo y realizar predicciones de gestos en tiempo real usando la API de red neuronal.

## Características

- ✅ **Conexión automática** a hotspot HOMBRENARANJA
- ✅ **Detección automática** del sensor uMyo vía BLE
- ✅ **Buffer deslizante** de 250 muestras con overlap del 80%
- ✅ **Predicción en tiempo real** cada 50ms
- ✅ **Monitoreo de estado** completo de conexiones
- ✅ **Estadísticas** detalladas de rendimiento
- ✅ **Recovery automático** de errores de conexión

## Archivos incluidos

```
ESP32code/
├── EMG_uMyo_RealTime.ino    # Código principal ESP32
├── uMyo_BLE.h               # Header librería uMyo
├── uMyo_BLE.cpp             # Implementación librería uMyo
├── quat_math.h              # Matemáticas quaterniones
├── quat_math.cpp            # Implementación quaterniones
└── README.md                # Este archivo
```

## Instalación

### 1. Librerías Arduino IDE requeridas:
```
- ArduinoBLE (por Arduino)
- ArduinoJson (por Benoit Blanchon)
- WiFi (incluida en ESP32)
- HTTPClient (incluida en ESP32)
```

### 2. Configuración de hardware:
- **Placa**: ESP32 Dev Module
- **Frecuencia CPU**: 240MHz
- **Flash**: 4MB
- **Partition Scheme**: Default 4MB

### 3. Configuración de red:
```cpp
const char* ssid = "HOMBRENARANJA";      // Tu hotspot
const char* password = "hola1234";       // Tu contraseña
const char* apiServer = "http://192.168.137.1:5000";  // IP del servidor
```

## Uso

### 1. **Iniciar API servidor**:
```bash
cd API/
python main.py
```

### 2. **Crear hotspot**:
- Nombre: `HOMBRENARANJA`
- Contraseña: `hola1234`
- IP del PC: `192.168.137.1` (típico Windows)

### 3. **Cargar código ESP32**:
- Abrir `EMG_uMyo_RealTime.ino` en Arduino IDE
- Verificar configuración de red
- Compilar y cargar

### 4. **Conectar sensor uMyo**:
- Encender sensor uMyo
- ESP32 detectará automáticamente vía BLE

## Funcionamiento

### Estado de conexiones:
- 🔗 **WiFi**: Conexión a hotspot HOMBRENARANJA
- 🔗 **uMyo**: Detección BLE del sensor
- 🔗 **API**: Disponibilidad del servidor de predicción

### Flujo de datos:
1. **Adquisición**: Lee 3 canales EMG a ~1000Hz
2. **Buffering**: Mantiene ventana deslizante de 250 muestras
3. **Predicción**: Envía datos cada 50ms para análisis
4. **Filtrado**: Solo muestra gestos con confianza > 70%

### Gestos detectados:
- `CERRAR_MANO`
- `PINZA`
- `SALUDAR`
- `TOMAR_OBJ`

## Monitor Serie

El código proporciona información detallada en el monitor serie:

```
========================================
    EMG REAL-TIME GESTURE RECOGNITION
    ESP32 + uMyo + Neural Network API
========================================
ESP32 ID: ESP32_UMYO_001
Target Network: HOMBRENARANJA
========================================

[WIFI] Conectando a HOMBRENARANJA...
[WIFI] ¡Conectado!
[WIFI] IP: 192.168.137.123
[API] Servidor disponible
[API] Modelo: CARGADO

🎯 GESTO DETECTADO: CERRAR_MANO (0.95)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 ESTADO DEL SISTEMA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔗 CONEXIONES:
  WiFi: ✅ CONECTADO
  uMyo: ✅ CONECTADO (1 dev)
  API:  ✅ DISPONIBLE

📊 BUFFER EMG:
  Muestras: 250/250
  Estado: ✅ LISTO

📈 ESTADÍSTICAS:
  Predicciones: 45/67
  Errores: 2
  Última predicción: CERRAR_MANO (0.95)

🌐 RED:
  IP: 192.168.137.123
  RSSI: -45 dBm
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Troubleshooting

### ❌ WiFi no conecta:
- Verificar nombre y contraseña del hotspot
- Revisar que el hotspot esté activo
- Comprobar que la ESP32 esté en rango

### ❌ uMyo no detecta:
- Encender el sensor uMyo
- Verificar batería del sensor
- Reiniciar ESP32 para resetear BLE

### ❌ API no responde:
- Verificar que el servidor Python esté ejecutándose
- Comprobar IP del servidor (192.168.137.1 es típica)
- Revisar firewall del PC

### ❌ Predicciones erráticas:
- Verificar calibración del sensor uMyo
- Asegurar buena conexión de electrodos
- Revisar que no hay interferencias BLE

## Personalización

### Cambiar frecuencia de predicción:
```cpp
#define PREDICTION_INTERVAL 50  // ms entre predicciones
```

### Cambiar filtro de confianza:
```cpp
if (confidence > 0.7 && gesture != last_gesture) {  // Cambiar 0.7
```

### Cambiar ID de dispositivo:
```cpp
String esp32_id = "ESP32_UMYO_001";  // Personalizar ID
```

## Arquitectura

```
ESP32 ┌─────────────┐
      │  uMyo BLE   │ ──┐
      └─────────────┘   │
                        ├─── Buffer(250) ──── HTTP POST ──── API Server
      ┌─────────────┐   │                                       │
      │    WiFi     │ ──┘                                       ├─ Neural Network
      └─────────────┘                                           │
                                                                └─ Gesture Classification
```

El sistema está diseñado para máxima robustez y recuperación automática de errores.