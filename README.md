# Sistema de Detección de Movimientos con EMG

Sistema completo de reconocimiento de gestos en tiempo real basado en señales electromiográficas (EMG), utilizando ESP32, sensor uMyo, redes neuronales profundas y una API REST.

## Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Características Principales](#características-principales)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Componentes del Proyecto](#componentes-del-proyecto)
- [Instalación](#instalación)
- [Uso del Sistema](#uso-del-sistema)
- [Gestos Detectados](#gestos-detectados)
- [Especificaciones Técnicas](#especificaciones-técnicas)
- [Troubleshooting](#troubleshooting)

---

## Descripción General

Este proyecto implementa un sistema de reconocimiento de gestos en tiempo real utilizando señales EMG (electromiografía). El sistema captura señales musculares a través del sensor uMyo, procesa los datos en un ESP32, y los envía a una API que utiliza una red neuronal (CNN + LSTM) para clasificar los gestos realizados.

### Flujo completo del sistema:

```
Músculo → Sensor uMyo → ESP32 (BLE) → WiFi → API REST → Red Neuronal → Predicción
```

### Estructura del Proyecto

```
MovementDetection/
├── API/                          # Servidor de inferencia REST
│   ├── main.py                   # Servidor Flask principal
│   ├── requirements.txt          # Dependencias Python
│   ├── weight/                   # Modelos de red neuronal
│   │   └── tflite_learn_774610_3.tflite
│   └── README.md                 # Documentación de API
│
├── ESP32code/                    # Firmware para ESP32
│   ├── EMG_uMyo_RealTime/        # Código principal
│   │   └── EMG_uMyo_RealTime.ino # Predicción en tiempo real
│   ├── uMyo_BLE.h/.cpp           # Librería BLE para sensor uMyo
│   ├── quat_math.h/.cpp          # Matemáticas quaterniones (IMU)
│   └── README.md                 # Documentación ESP32
│
├── Toma_de_datos/                # Sistema de captura de datasets
│   ├── main_app.py               # Aplicación GUI principal (PySide6)
│   ├── emg_processor.py          # Procesamiento señales EMG
│   ├── dataset_manager.py        # Gestión de datasets CSV
│   ├── session_controller.py     # Control de sesiones
│   ├── mediapipe_processor.py    # Procesamiento video (opcional)
│   └── requirements.txt          # Dependencias Python
│
├── uMyo_IMU/                     # Código adicional para IMU
│   ├── uMyo_IMU_sinbotones.ino   # Lectura datos IMU
│   └── uMyo_BLE.h/.cpp           # Librería BLE
│
├── REDNEURONAL.ipynb             # Notebook entrenamiento red neuronal
└── README.md                     # Este archivo
```

### Descripción de Carpetas

| Carpeta | Propósito | Tecnología |
|---------|-----------|------------|
| **API/** | Servidor de inferencia que recibe datos EMG y devuelve predicciones de gestos | Flask + TensorFlow Lite |
| **ESP32code/** | Firmware que captura señales EMG del sensor uMyo y las envía a la API vía WiFi | Arduino C++ |
| **Toma_de_datos/** | Aplicación de escritorio para capturar y etiquetar datasets EMG para entrenamiento | Python + PySide6 |
| **uMyo_IMU/** | Código adicional para trabajar con datos del IMU (acelerómetro/giroscopio) del sensor | Arduino C++ |
| **REDNEURONAL.ipynb** | Notebook Jupyter para entrenar y evaluar modelos de clasificación de gestos | PyTorch + TensorFlow |

---

## Características Principales

### Tiempo Real
- Predicción de gestos cada **50ms**
- Latencia total < **100ms**
- Buffer deslizante con overlap del 80%

### Inteligencia Artificial
- Red neuronal **CNN + LSTM** entrenada en PyTorch
- Modelo convertido a **TensorFlow Lite** para inferencia rápida
- Precisión de **~95%** en dataset de validación

### Conectividad
- Comunicación **BLE** con sensor uMyo
- Conexión **WiFi** automática
- API REST para inferencia en la nube o local

### Captura de Datos
- Sistema automatizado de captura de datasets
- Interfaz gráfica intuitiva con PySide6
- Sesiones configurables con múltiples repeticiones

### Robustez
- Reconexión automática ante pérdida de conexión
- Monitoreo de estado completo
- Manejo de errores y recuperación

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                      SISTEMA COMPLETO                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────┐        ┌────────────┐        ┌────────────┐ │
│  │   uMyo     │  BLE   │   ESP32    │  WiFi  │  API REST  │ │
│  │  Sensor    │───────▶│  Buffer    │───────▶│  Flask     │ │
│  │  (3 EMG)   │        │  (250ms)   │  HTTP  │  TF Lite   │ │
│  └────────────┘        └────────────┘        └────────────┘ │
│                                                      │        │
│                                               ┌──────▼─────┐ │
│                                               │   Neural   │ │
│                                               │   Network  │ │
│                                               │  CNN+LSTM  │ │
│                                               └──────┬─────┘ │
│                                                      │        │
│                                               ┌──────▼─────┐ │
│                                               │  Gesture   │ │
│                                               │Prediction  │ │
│                                               └────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Componentes del Proyecto

### 1. **API/** - Servidor de Inferencia

API REST desarrollada en Flask para realizar predicciones de gestos en tiempo real.

**Archivos:**
- `main.py` - Servidor Flask con endpoints REST
- `requirements.txt` - Dependencias Python
- `weight/tflite_learn_774610_3.tflite` - Modelo de red neuronal (774KB)

**Endpoints:**
- `GET /health` - Verificación de estado del servidor
- `POST /predict` - Predicción detallada con probabilidades
- `POST /predict_simple` - Predicción simplificada para ESP32
- `GET /info` - Información del modelo
- `POST /esp32_status` - Registro de estado de dispositivos

**Características:**
- Preprocesamiento de señales EMG (filtrado Butterworth 20-450Hz)
- Rectificación y extracción de envelope
- Normalización Z-score
- Inferencia con TensorFlow Lite
- Logging completo de actividad

**Instalación:**
```bash
cd API/
pip install -r requirements.txt
python main.py
```

---

### 2. **ESP32code/** - Código para Microcontrolador

Firmware para ESP32 que captura señales EMG del sensor uMyo y se comunica con la API.

**Archivos:**
- `EMG_uMyo_RealTime/EMG_uMyo_RealTime.ino` - Código principal
- `uMyo_BLE.h/.cpp` - Librería para comunicación BLE con uMyo
- `quat_math.h/.cpp` - Matemáticas para quaterniones (IMU)

**Características:**
- Conexión automática a WiFi
- Detección automática de sensor uMyo vía BLE
- Buffer circular de 250 muestras (250ms @ 1000Hz)
- Envío de predicciones cada 50ms
- Overlap del 80% para continuidad
- Monitoreo de conexiones (WiFi, BLE, API)
- Estadísticas en tiempo real

**Configuración:**
```cpp
const char* ssid = "TU_RED_WIFI";
const char* password = "TU_CONTRASEÑA";
const char* apiServer = "http://192.168.1.X:5000";
```

**Librerías requeridas:**
- ArduinoBLE
- ArduinoJson
- WiFi (ESP32)
- HTTPClient (ESP32)

---

### 3. **Toma_de_datos/** - Sistema de Captura de Datasets

Aplicación Python con interfaz gráfica para capturar y etiquetar datos EMG.

**Archivos:**
- `main_app.py` - Aplicación principal con GUI (PySide6)
- `emg_processor.py` - Procesamiento de señales EMG del ESP32
- `dataset_manager.py` - Gestión y guardado de datasets
- `session_controller.py` - Control de sesiones de captura
- `mediapipe_processor.py` - Procesamiento de video (opcional)
- `requirements.txt` - Dependencias Python

**Características:**
- **Captura automática**: Python define los movimientos a realizar
- **Interfaz intuitiva**: Muestra claramente qué gesto realizar
- **Sesiones configurables**: Duración, repeticiones y descanso
- **Formato CSV limpio**: Datos listos para entrenamiento
- **Control de calidad**: Validación de conexión ESP32

**Gestos capturados:**
1. CERRAR_MANO
2. PINZA
3. SALUDAR
4. TOMAR_OBJ

**Instalación:**
```bash
cd Toma_de_datos/
pip install -r requirements.txt
python main_app.py
```

**Uso:**
1. Conectar ESP32 al puerto COM (ej: COM3)
2. Configurar duración por gesto (5-30 segundos)
3. Configurar repeticiones (1-10 ciclos)
4. Presionar "INICIAR CAPTURA AUTOMÁTICA"
5. Seguir instrucciones en pantalla
6. Guardar dataset al finalizar

---

### 4. **REDNEURONAL.ipynb** - Entrenamiento del Modelo

Jupyter Notebook para entrenar la red neuronal con los datos capturados.

**Contenido:**
- Carga y preprocesamiento de datasets EMG
- Arquitectura de red neuronal (CNN + LSTM)
- Entrenamiento con PyTorch
- Evaluación y métricas de rendimiento
- Conversión a TensorFlow Lite
- Optimización del modelo para inferencia

**Arquitectura del modelo:**
```
Input (250, 3) → Conv1D → MaxPool → LSTM → Dense → Softmax (4 clases)
```

**Métricas:**
- Precisión (Accuracy): ~95%
- F1-Score por clase
- Matriz de confusión
- Curvas de entrenamiento

---

### 5. **uMyo_IMU/** - Código Adicional IMU

Código adicional para trabajar con datos IMU del sensor uMyo (giroscopio, acelerómetro).

**Archivos:**
- `uMyo_IMU_sinbotones.ino` - Lectura de datos IMU
- `uMyo_BLE.h/.cpp` - Librería BLE
- `quat_math.h/.cpp` - Cálculos con quaterniones

---

## Instalación

### Requisitos Generales

**Hardware:**
- ESP32 (Dev Module)
- Sensor uMyo (3 canales EMG + IMU)
- Electrodos EMG
- Cable USB para ESP32
- PC con Python 3.8+

**Software:**
- Arduino IDE (para ESP32)
- Python 3.8 o superior
- pip (gestor de paquetes Python)

---

### Instalación Paso a Paso

#### 1. Configurar ESP32

**a) Instalar Arduino IDE:**
```
https://www.arduino.cc/en/software
```

**b) Agregar ESP32 Board Manager:**
```
File → Preferences → Additional Boards Manager URLs:
https://dl.espressif.com/dl/package_esp32_index.json
```

**c) Instalar librerías:**
```
Tools → Manage Libraries:
- ArduinoBLE (por Arduino)
- ArduinoJson (por Benoit Blanchon)
```

**d) Configurar placa:**
```
Tools → Board → ESP32 Arduino → ESP32 Dev Module
Tools → CPU Frequency → 240MHz
Tools → Flash Size → 4MB
```

**e) Configurar red WiFi en el código:**
```cpp
// Editar en EMG_uMyo_RealTime.ino
const char* ssid = "TU_RED_WIFI";
const char* password = "TU_CONTRASEÑA";
const char* apiServer = "http://TU_IP:5000";
```

**f) Cargar código:**
```
Sketch → Upload
```

---

#### 2. Configurar API

```bash
# Clonar repositorio o navegar a API/
cd API/

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Verificar que el modelo existe
ls weight/tflite_learn_774610_3.tflite

# Iniciar servidor
python main.py
```

El servidor estará disponible en `http://0.0.0.0:5000`

---

#### 3. Configurar Sistema de Captura (Opcional)

```bash
cd Toma_de_datos/

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Iniciar aplicación
python main_app.py
```

---

## Uso del Sistema

### Modo 1: Predicción en Tiempo Real

**1. Iniciar API:**
```bash
cd API/
python main.py
```

**2. Configurar red WiFi:**
- Crear hotspot o conectarse a red local
- Anotar IP del servidor (ej: `192.168.1.100`)

**3. Cargar código ESP32:**
- Configurar SSID, password y API IP
- Cargar código a ESP32

**4. Encender sensor uMyo:**
- El ESP32 detectará automáticamente

**5. Ver predicciones:**
- Abrir Monitor Serie (115200 baud)
- Realizar gestos
- Ver predicciones en tiempo real

**Salida esperada:**
```
GESTO DETECTADO: CERRAR_MANO (0.95)
GESTO DETECTADO: PINZA (0.89)
GESTO DETECTADO: SALUDAR (0.92)
```

---

### Modo 2: Captura de Datos

**1. Conectar ESP32:**
- Conectar al puerto COM

**2. Iniciar aplicación:**
```bash
python main_app.py
```

**3. Configurar sesión:**
- Seleccionar puerto COM
- Duración por gesto: 8 segundos (recomendado)
- Repeticiones: 3 ciclos (recomendado)
- Descanso: 3 segundos

**4. Iniciar captura:**
- Click en "INICIAR CAPTURA AUTOMÁTICA"
- Seguir instrucciones en pantalla
- Realizar cada gesto cuando se indique

**5. Guardar dataset:**
- Click en "GUARDAR DATASET"
- Seleccionar ubicación y nombre

---

### Modo 3: Entrenar Modelo Propio

**1. Capturar datos** con `Toma_de_datos/`

**2. Abrir notebook:**
```bash
jupyter notebook REDNEURONAL.ipynb
```

**3. Cargar datasets:**
```python
df = pd.read_csv('tu_dataset.csv')
```

**4. Entrenar modelo:**
- Ejecutar celdas secuencialmente
- Ajustar hiperparámetros si necesario

**5. Exportar modelo:**
```python
# El notebook exportará a weight/tflite_learn_XXXXX.tflite
```

**6. Actualizar API:**
```python
# En main.py, cambiar ruta del modelo
classifier = GestureClassifier('weight/tu_nuevo_modelo.tflite')
```

---

## Gestos Detectados

El sistema reconoce **4 gestos** principales:

### 1. CERRAR_MANO
- Cerrar la mano en puño
- Alta activación de flexores
- **Aplicaciones**: Control de agarre, señal de parada

### 2. PINZA
- Juntar dedo pulgar e índice
- Activación precisa de músculos
- **Aplicaciones**: Selección fina, zoom, control de precisión

### 3. SALUDAR
- Movimiento de saludo con mano
- Patrón rítmico de flexión/extensión
- **Aplicaciones**: Activación de comandos, saludo en interfaz

### 4. TOMAR_OBJ
- Gesto de tomar un objeto
- Activación combinada de músculos
- **Aplicaciones**: Manipulación de objetos virtuales

---

## Especificaciones Técnicas

### Hardware

**Sensor uMyo:**
- 3 canales EMG diferenciales
- IMU 6-axis (giroscopio + acelerómetro)
- Comunicación BLE
- Batería recargable

**ESP32:**
- CPU: Dual-core 240MHz
- RAM: 520KB
- Flash: 4MB
- WiFi 802.11 b/g/n
- BLE 4.2
- ADC 12-bit

### Software

**API:**
- Framework: Flask 2.3.3
- ML: TensorFlow 2.13.0
- DSP: SciPy 1.11.4
- Puerto: 5000

**Modelo:**
- Tipo: CNN + LSTM
- Tamaño: 774KB (TFLite)
- Input: (250, 3) - 250 muestras × 3 canales
- Output: (4,) - 4 clases
- Precisión: ~95%

**Señales:**
- Frecuencia de muestreo: 1000 Hz
- Ventana de predicción: 250 ms
- Overlap: 80% (200 muestras)
- Frecuencia de predicción: 20 Hz (cada 50ms)

**Preprocesamiento:**
1. Filtro paso-banda Butterworth 4° orden (20-450 Hz)
2. Rectificación (valor absoluto)
3. Envelope: filtro paso-bajo 2° orden (5 Hz)
4. Normalización Z-score por canal

---

## Troubleshooting

### Problemas Comunes

#### ESP32 no conecta a WiFi

**Síntomas:**
```
[WIFI] ERROR DE CONEXIÓN
[WIFI] Estado final: CONNECT_FAILED
```

**Soluciones:**
1. Verificar SSID y contraseña exactos
2. Comprobar que la red está activa
3. Verificar que es una red 2.4GHz (ESP32 no soporta 5GHz)
4. Acercar ESP32 al router
5. Revisar que no hay filtrado MAC

---

#### Sensor uMyo no detecta

**Síntomas:**
```
uMyo: DESCONECTADO
```

**Soluciones:**
1. Encender sensor uMyo
2. Verificar batería del sensor
3. Reiniciar ESP32 para resetear BLE
4. Acercar sensor a ESP32 (<5 metros)
5. Verificar que no hay otros dispositivos conectados

---

#### API no responde

**Síntomas:**
```
[API] Error de conexión: -1
[PRED] Error HTTP: 404
```

**Soluciones:**
1. Verificar que el servidor está ejecutándose:
   ```bash
   python main.py
   ```
2. Comprobar IP correcta del servidor
3. Verificar puerto 5000 abierto
4. Revisar firewall de Windows/Linux
5. Probar desde navegador: `http://IP:5000/health`

---

#### Predicciones erráticas

**Síntomas:**
- Cambios rápidos entre gestos
- Baja confianza (<0.7)
- Predicciones incorrectas

**Soluciones:**
1. Verificar buena conexión de electrodos
2. Limpiar piel antes de colocar electrodos
3. Asegurar que los electrodos están en músculo activo
4. Evitar interferencias eléctricas
5. Aumentar umbral de confianza en código:
   ```cpp
   if (confidence > 0.8)  // Aumentar de 0.7 a 0.8
   ```
6. Recalibrar o reentrenar modelo con nuevos datos

---

#### Aplicación de captura no detecta ESP32

**Síntomas:**
```
No se pudo conectar al ESP32 en COM3
```

**Soluciones:**
1. Verificar que el ESP32 está conectado
2. Identificar puerto COM correcto en Device Manager
3. Cerrar Arduino IDE o Monitor Serie (bloquean puerto)
4. Instalar drivers CP2102 o CH340 si necesario
5. Probar diferentes puertos COM

---

#### Error al guardar dataset

**Síntomas:**
```
Error al guardar dataset: Permission denied
```

**Soluciones:**
1. Verificar permisos de escritura en carpeta
2. Cerrar Excel si el archivo está abierto
3. Seleccionar carpeta con permisos adecuados
4. Ejecutar como administrador si necesario

---

### Logs y Diagnóstico

**Ver logs de API:**
```bash
tail -f api.log  # Linux/Mac
type api.log  # Windows
```

**Monitor Serie ESP32:**
```
Tools → Serial Monitor (115200 baud)
```

**Verificar salud de API:**
```bash
curl http://localhost:5000/health
```

**Respuesta esperada:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "uptime_seconds": 3600,
  "total_predictions": 1234
}
```

---

## Notas Adicionales

### Optimizaciones Recomendadas

**Para producción:**
1. Usar Gunicorn para servir API:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 main:app
   ```

2. Implementar HTTPS para seguridad

3. Agregar autenticación en endpoints

4. Implementar caché de modelo en memoria

5. Configurar CORS si se accede desde navegador

### Ampliaciones Futuras

- [ ] Agregar más gestos (hasta 10 clases)
- [ ] Implementar modelo edge en ESP32
- [ ] Agregar calibración automática
- [ ] Dashboard web en tiempo real
- [ ] Soporte multi-usuario
- [ ] Integración con ROS para robótica

---

## Licencia

Este proyecto incluye código de la librería uMyo_BLE con licencia LGPL 2.1.

```
uMyo_BLE Copyright (c) 2022, Ultimate Robotics
Licensed under GNU Lesser General Public License v2.1
```

---

## Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## Contacto

Para preguntas, sugerencias o reportar bugs, por favor abre un issue en el repositorio.

---

## Agradecimientos

- **Ultimate Robotics** por la librería uMyo_BLE
- **Comunidad ESP32** por soporte y documentación
- **TensorFlow** y **PyTorch** por frameworks de ML

---

**¡Feliz detección de gestos!**
