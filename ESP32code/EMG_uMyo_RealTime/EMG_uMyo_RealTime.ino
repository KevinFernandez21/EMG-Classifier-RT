/*
  EMG Real-Time Gesture Recognition with uMyo
  ESP32 + uMyo_BLE - Predicción en tiempo real con API
  
  Funcionalidades:
  - Conexión automática a hotspot HOMBRENARANJA
  - Detección automática de sensor uMyo
  - Envío de datos EMG para predicción en tiempo real
  - Monitoreo de estado de conexiones
  - Buffer deslizante para predicción continua
*/

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <uMyo_BLE.h>

// ===== CONFIGURACIÓN WIFI =====
const char* ssid = "NETLIFE-SANCHEZ";
const char* password = "kd200421";

// ===== CONFIGURACIÓN API =====
const char* apiServer = "http://192.168.100.4:5000";  // IP de tu PC en NETLIFE-SANCHEZ
String esp32_id = "ESP32_UMYO_001";

// ===== CONFIGURACIÓN EMG =====
#define BUFFER_SIZE 250
#define OVERLAP_SIZE 200
#define PREDICTION_INTERVAL 50  // ms entre predicciones
#define STATUS_INTERVAL 5000    // ms entre reportes de estado

// ===== BUFFERS EMG =====
float emg1_buffer[BUFFER_SIZE];
float emg2_buffer[BUFFER_SIZE];
float emg3_buffer[BUFFER_SIZE];
int buffer_index = 0;
bool buffer_ready = false;

// ===== ESTADO SISTEMA =====
bool wifi_connected = false;
bool sensor_connected = false;
bool api_available = false;
unsigned long last_prediction = 0;
unsigned long last_status_report = 0;
unsigned long last_data_time = 0;
String last_gesture = "NONE";
float last_confidence = 0.0;

// ===== ESTADÍSTICAS =====
int total_predictions = 0;
int successful_predictions = 0;
int connection_errors = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Mostrar información de inicio
  Serial.println("========================================");
  Serial.println("    EMG REAL-TIME GESTURE RECOGNITION");
  Serial.println("    ESP32 + uMyo + Neural Network API");
  Serial.println("========================================");
  Serial.println("ESP32 ID: " + esp32_id);
  Serial.println("Target Network: " + String(ssid));
  Serial.println("========================================");
  
  // Inicializar uMyo
  Serial.println("[INIT] Inicializando uMyo BLE...");
  uMyo.begin();
  delay(2000);
  
  // Conectar WiFi
  connectWiFi();
  
  // Verificar API
  if (wifi_connected) {
    checkAPIHealth();
  }
  
  // Inicializar buffer
  clearBuffer();
  
  Serial.println("[READY] Sistema listo para funcionar!");
  Serial.println("========================================");
}

void loop() {
  unsigned long currentTime = millis();
  
  // Verificar conexión WiFi
  if (WiFi.status() != WL_CONNECTED) {
    if (wifi_connected) {
      Serial.println("[WIFI] Conexión perdida, reintentando...");
      wifi_connected = false;
    }
    connectWiFi();
  }
  
  // Procesar datos EMG
  uMyo.run();
  int device_count = uMyo.getDeviceCount();
  sensor_connected = (device_count > 0);
  
  if (sensor_connected) {
    // Obtener datos EMG
    float emg1 = uMyo.getMuscleLevel(0);
    float emg2 = uMyo.getMuscleLevel(1);
    float emg3 = uMyo.getMuscleLevel(2);
    
    // Agregar al buffer
    addToBuffer(emg1, emg2, emg3);
    last_data_time = currentTime;
    
    // Hacer predicción si el buffer está listo
    if (buffer_ready && (currentTime - last_prediction >= PREDICTION_INTERVAL)) {
      if (wifi_connected && api_available) {
        makePrediction();
        last_prediction = currentTime;
      }
    }
  } else {
    // Si no hay sensor, limpiar buffer
    if (currentTime - last_data_time > 1000) {
      buffer_ready = false;
      buffer_index = 0;
    }
  }
  
  // Reportar estado periódicamente
  if (currentTime - last_status_report >= STATUS_INTERVAL) {
    reportStatus();
    last_status_report = currentTime;
  }
  
  // Mostrar información en consola
  static unsigned long lastShow = 0;
  if (currentTime - lastShow > 2000) {
    showStatus();
    lastShow = currentTime;
  }
  
  delay(1);  // Sampling rate ~1000Hz
}

void connectWiFi() {
  if (WiFi.status() == WL_CONNECTED) {
    wifi_connected = true;
    return;
  }
  
  Serial.println("[WIFI] Iniciando conexión WiFi...");
  Serial.println("[WIFI] SSID: " + String(ssid));
  Serial.println("[WIFI] Password: " + String(password));
  
  // Resetear WiFi completamente
  WiFi.disconnect();
  WiFi.mode(WIFI_OFF);
  delay(1000);
  WiFi.mode(WIFI_STA);
  delay(1000);
  
  // Escanear redes disponibles
  Serial.println("[WIFI] Escaneando redes...");
  int n = WiFi.scanNetworks();
  Serial.println("[WIFI] Redes encontradas: " + String(n));
  
  bool network_found = false;
  for (int i = 0; i < n; ++i) {
    Serial.println("[WIFI] " + String(i+1) + ": " + WiFi.SSID(i) + " (RSSI: " + WiFi.RSSI(i) + ")");
    if (WiFi.SSID(i) == ssid) {
      network_found = true;
      Serial.println("[WIFI] ✅ Red objetivo encontrada!");
    }
  }
  
  if (!network_found) {
    Serial.println("[WIFI] ❌ Red '" + String(ssid) + "' no encontrada!");
    Serial.println("[WIFI] Verifica que el hotspot esté activo");
    wifi_connected = false;
    connection_errors++;
    return;
  }
  
  // Intentar conectar
  Serial.println("[WIFI] Conectando a " + String(ssid) + "...");
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(1000);
    Serial.print(".");
    Serial.print(getWiFiStatusText(WiFi.status()));
    attempts++;
    
    // Mostrar progreso cada 5 intentos
    if (attempts % 5 == 0) {
      Serial.println("\n[WIFI] Intento " + String(attempts) + "/30 - Estado: " + getWiFiStatusText(WiFi.status()));
    }
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    wifi_connected = true;
    Serial.println("\n[WIFI] ✅ ¡CONECTADO EXITOSAMENTE!");
    Serial.println("[WIFI] IP: " + WiFi.localIP().toString());
    Serial.println("[WIFI] Gateway: " + WiFi.gatewayIP().toString());
    Serial.println("[WIFI] DNS: " + WiFi.dnsIP().toString());
    Serial.println("[WIFI] RSSI: " + String(WiFi.RSSI()) + " dBm");
  } else {
    wifi_connected = false;
    Serial.println("\n[WIFI] ❌ ERROR DE CONEXIÓN");
    Serial.println("[WIFI] Estado final: " + getWiFiStatusText(WiFi.status()));
    Serial.println("[WIFI] Posibles causas:");
    Serial.println("[WIFI] - Contraseña incorrecta");
    Serial.println("[WIFI] - Hotspot no disponible"); 
    Serial.println("[WIFI] - Problema de señal");
    connection_errors++;
  }
}

String getWiFiStatusText(wl_status_t status) {
  switch (status) {
    case WL_IDLE_STATUS: return "IDLE";
    case WL_NO_SSID_AVAIL: return "NO_SSID";
    case WL_SCAN_COMPLETED: return "SCAN_COMPLETED";
    case WL_CONNECTED: return "CONNECTED";
    case WL_CONNECT_FAILED: return "CONNECT_FAILED";
    case WL_CONNECTION_LOST: return "CONNECTION_LOST";
    case WL_DISCONNECTED: return "DISCONNECTED";
    default: return "UNKNOWN";
  }
}

void checkAPIHealth() {
  if (!wifi_connected) return;
  
  HTTPClient http;
  http.begin(String(apiServer) + "/health");
  http.setTimeout(3000);
  
  int httpCode = http.GET();
  
  if (httpCode == 200) {
    String response = http.getString();
    api_available = true;
    Serial.println("[API] Servidor disponible");
    
    // Parsear respuesta para obtener información
    DynamicJsonDocument doc(1024);
    if (deserializeJson(doc, response) == DeserializationError::Ok) {
      bool model_loaded = doc["model_loaded"];
      int total_preds = doc["total_predictions"];
      Serial.println("[API] Modelo: " + String(model_loaded ? "CARGADO" : "ERROR"));
      Serial.println("[API] Predicciones totales: " + String(total_preds));
    }
  } else {
    api_available = false;
    Serial.println("[API] Error de conexión: " + String(httpCode));
    connection_errors++;
  }
  
  http.end();
}

void addToBuffer(float emg1, float emg2, float emg3) {
  emg1_buffer[buffer_index] = emg1;
  emg2_buffer[buffer_index] = emg2;
  emg3_buffer[buffer_index] = emg3;
  
  buffer_index++;
  
  // Buffer completo por primera vez
  if (buffer_index >= BUFFER_SIZE) {
    buffer_ready = true;
    
    // Desplazar buffer (mantener overlap)
    for (int i = 0; i < OVERLAP_SIZE; i++) {
      int src_idx = BUFFER_SIZE - OVERLAP_SIZE + i;
      emg1_buffer[i] = emg1_buffer[src_idx];
      emg2_buffer[i] = emg2_buffer[src_idx];
      emg3_buffer[i] = emg3_buffer[src_idx];
    }
    buffer_index = OVERLAP_SIZE;
  }
}

void clearBuffer() {
  for (int i = 0; i < BUFFER_SIZE; i++) {
    emg1_buffer[i] = 0.0;
    emg2_buffer[i] = 0.0;
    emg3_buffer[i] = 0.0;
  }
  buffer_index = 0;
  buffer_ready = false;
}

void makePrediction() {
  HTTPClient http;
  http.begin(String(apiServer) + "/predict_simple");
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(2000);
  
  // Crear JSON con datos EMG
  DynamicJsonDocument doc(8192);
  JsonArray emg1_array = doc.createNestedArray("emg1");
  JsonArray emg2_array = doc.createNestedArray("emg2");
  JsonArray emg3_array = doc.createNestedArray("emg3");
  
  // Usar las últimas 250 muestras
  int start_idx = max(0, buffer_index - BUFFER_SIZE);
  for (int i = 0; i < BUFFER_SIZE; i++) {
    int idx = (start_idx + i) % BUFFER_SIZE;
    emg1_array.add(emg1_buffer[idx]);
    emg2_array.add(emg2_buffer[idx]);
    emg3_array.add(emg3_buffer[idx]);
  }
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  // Enviar predicción
  int httpCode = http.POST(jsonString);
  total_predictions++;
  
  if (httpCode == 200) {
    String response = http.getString();
    
    DynamicJsonDocument responseDoc(1024);
    if (deserializeJson(responseDoc, response) == DeserializationError::Ok) {
      String gesture = responseDoc["gesture"];
      float confidence = responseDoc["confidence"];
      
      // Solo mostrar predicciones con alta confianza
      if (confidence > 0.7 && gesture != last_gesture) {
        Serial.println("🎯 GESTO DETECTADO: " + gesture + " (" + String(confidence, 2) + ")");
        last_gesture = gesture;
        last_confidence = confidence;
        successful_predictions++;
      }
    }
  } else {
    Serial.println("[PRED] Error HTTP: " + String(httpCode));
    connection_errors++;
    
    // Verificar API si hay muchos errores
    if (connection_errors % 10 == 0) {
      checkAPIHealth();
    }
  }
  
  http.end();
}

void reportStatus() {
  if (!wifi_connected) return;
  
  HTTPClient http;
  http.begin(String(apiServer) + "/esp32_status");
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(2000);
  
  // Crear JSON con estado
  DynamicJsonDocument doc(512);
  doc["esp32_id"] = esp32_id;
  doc["sensor_connected"] = sensor_connected;
  doc["wifi_connected"] = wifi_connected;
  doc["api_available"] = api_available;
  doc["buffer_ready"] = buffer_ready;
  doc["total_predictions"] = total_predictions;
  doc["successful_predictions"] = successful_predictions;
  doc["connection_errors"] = connection_errors;
  doc["last_gesture"] = last_gesture;
  doc["last_confidence"] = last_confidence;
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  int httpCode = http.POST(jsonString);
  
  if (httpCode != 200) {
    Serial.println("[STATUS] Error reportando estado: " + String(httpCode));
  }
  
  http.end();
}

void showStatus() {
  Serial.println("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  Serial.println("📊 ESTADO DEL SISTEMA");
  Serial.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
  
  // Estado de conexiones
  Serial.println("🔗 CONEXIONES:");
  Serial.println("  WiFi: " + String(wifi_connected ? "✅ CONECTADO" : "❌ DESCONECTADO"));
  Serial.println("  uMyo: " + String(sensor_connected ? "✅ CONECTADO (" + String(uMyo.getDeviceCount()) + " dev)" : "❌ DESCONECTADO"));
  Serial.println("  API:  " + String(api_available ? "✅ DISPONIBLE" : "❌ NO DISPONIBLE"));
  
  // Estado del buffer
  Serial.println("\n📊 BUFFER EMG:");
  Serial.println("  Muestras: " + String(buffer_index) + "/" + String(BUFFER_SIZE));
  Serial.println("  Estado: " + String(buffer_ready ? "✅ LISTO" : "⏳ LLENANDO"));
  
  // Estadísticas
  Serial.println("\n📈 ESTADÍSTICAS:");
  Serial.println("  Predicciones: " + String(successful_predictions) + "/" + String(total_predictions));
  Serial.println("  Errores: " + String(connection_errors));
  Serial.println("  Última predicción: " + last_gesture + " (" + String(last_confidence, 2) + ")");
  
  // Información de red
  if (wifi_connected) {
    Serial.println("\n🌐 RED:");
    Serial.println("  IP: " + WiFi.localIP().toString());
    Serial.println("  RSSI: " + String(WiFi.RSSI()) + " dBm");
  }
  
  Serial.println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");
}