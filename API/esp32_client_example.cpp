#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Configuración WiFi
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Configuración del servidor API
const char* apiServer = "http://YOUR_SERVER_IP:5000";

// Buffer para datos EMG
float emg1_buffer[250];
float emg2_buffer[250];
float emg3_buffer[250];
int buffer_index = 0;

void setup() {
    Serial.begin(115200);
    
    // Conectar a WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Conectando a WiFi...");
    }
    Serial.println("WiFi conectado!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
    
    // Verificar conexión con API
    checkAPIHealth();
}

void loop() {
    // Simular lectura de sensores EMG (reemplazar con lectura real)
    float emg1 = analogRead(A0) * (3.3 / 4095.0); // Ajustar según tu hardware
    float emg2 = analogRead(A1) * (3.3 / 4095.0);
    float emg3 = analogRead(A2) * (3.3 / 4095.0);
    
    // Agregar al buffer
    emg1_buffer[buffer_index] = emg1;
    emg2_buffer[buffer_index] = emg2;
    emg3_buffer[buffer_index] = emg3;
    
    buffer_index++;
    
    // Cuando el buffer esté lleno, hacer predicción
    if (buffer_index >= 250) {
        String prediction = predictGesture();
        if (prediction != "") {
            Serial.println("Gesto detectado: " + prediction);
        }
        
        // Desplazar buffer (mantener últimas 200 muestras)
        for (int i = 0; i < 200; i++) {
            emg1_buffer[i] = emg1_buffer[i + 50];
            emg2_buffer[i] = emg2_buffer[i + 50];
            emg3_buffer[i] = emg3_buffer[i + 50];
        }
        buffer_index = 200;
    }
    
    delay(1); // 1000 Hz sampling rate
}

void checkAPIHealth() {
    HTTPClient http;
    http.begin(String(apiServer) + "/health");
    
    int httpResponseCode = http.GET();
    
    if (httpResponseCode == 200) {
        String response = http.getString();
        Serial.println("API Status: " + response);
    } else {
        Serial.println("Error conectando con API: " + String(httpResponseCode));
    }
    
    http.end();
}

String predictGesture() {
    HTTPClient http;
    http.begin(String(apiServer) + "/predict_simple");
    http.addHeader("Content-Type", "application/json");
    
    // Crear JSON con datos EMG
    DynamicJsonDocument doc(8192);
    JsonArray emg1_array = doc.createNestedArray("emg1");
    JsonArray emg2_array = doc.createNestedArray("emg2");
    JsonArray emg3_array = doc.createNestedArray("emg3");
    
    for (int i = 0; i < 250; i++) {
        emg1_array.add(emg1_buffer[i]);
        emg2_array.add(emg2_buffer[i]);
        emg3_array.add(emg3_buffer[i]);
    }
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    // Enviar POST request
    int httpResponseCode = http.POST(jsonString);
    
    String result = "";
    if (httpResponseCode == 200) {
        String response = http.getString();
        
        DynamicJsonDocument responseDoc(1024);
        deserializeJson(responseDoc, response);
        
        String gesture = responseDoc["gesture"];
        float confidence = responseDoc["confidence"];
        
        if (confidence > 0.7) { // Solo mostrar predicciones con alta confianza
            result = gesture + " (" + String(confidence, 2) + ")";
        }
    } else {
        Serial.println("Error en predicción: " + String(httpResponseCode));
    }
    
    http.end();
    return result;
}

// Función auxiliar para obtener información del modelo
void getModelInfo() {
    HTTPClient http;
    http.begin(String(apiServer) + "/info");
    
    int httpResponseCode = http.GET();
    
    if (httpResponseCode == 200) {
        String response = http.getString();
        Serial.println("Model Info: " + response);
    }
    
    http.end();
}