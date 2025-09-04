// ESP32 + uMyo_BLE - Funcionamiento AUTOMÁTICO sin botones
// Solo envía datos EMG continuamente para que Python los procese
#include <Arduino.h>
#include <uMyo_BLE.h>

// Variables de estado simplificadas
bool systemEnabled = true;  // SIEMPRE ACTIVO
bool headersSent = false;
unsigned long sessionStartTime = 0;
unsigned long lastDataSent = 0;

void setup() {
  Serial.begin(115200);
  
  // Inicializar uMyo
  uMyo.begin();
  
  sessionStartTime = millis();
  
  Serial.println("===============================");
  Serial.println("  SISTEMA EMG AUTOMÁTICO");
  Serial.println("===============================");
  Serial.println("- Funcionamiento continuo");
  Serial.println("- Python define los movimientos");
  Serial.println("- Solo envía datos EMG raw");
  Serial.println("===============================");
  
  // Enviar señal de inicio automático
  Serial.println("CSV_START");
  delay(1000);
}

void loop() {
  // Procesar datos EMG continuamente
  uMyo.run();
  int dev_count = uMyo.getDeviceCount();
  
  if(dev_count > 0) {
    // Enviar headers solo una vez
    if(!headersSent) {
      Serial.println("timestamp,session_time,emg1,emg2,emg3,movement_id,movement_name");
      headersSent = true;
      delay(100);
    }
    
    // Obtener datos EMG raw
    float emg1 = uMyo.getMuscleLevel(0);
    float emg2 = uMyo.getMuscleLevel(1);
    float emg3 = uMyo.getMuscleLevel(2);
    
    // Enviar datos cada 50ms (20Hz) - SIEMPRE ACTIVO
    if(millis() - lastDataSent >= 50) {
      Serial.print(millis());
      Serial.print(",");
      Serial.print(millis() - sessionStartTime);
      Serial.print(",");
      Serial.print(emg1, 2);
      Serial.print(",");
      Serial.print(emg2, 2);
      Serial.print(",");
      Serial.print(emg3, 2);
      Serial.print(",");
      Serial.print("0");  // movement_id = 0 (Python define el movimiento)
      Serial.print(",");
      Serial.println("AUTO");  // movement_name = AUTO (Python controla)
      
      lastDataSent = millis();
    }
  } else {
    // Si no hay sensor, enviar datos de prueba
    if(millis() - lastDataSent >= 50) {
      if(!headersSent) {
        Serial.println("timestamp,session_time,emg1,emg2,emg3,movement_id,movement_name");
        headersSent = true;
      }
      
      Serial.print(millis());
      Serial.print(",");
      Serial.print(millis() - sessionStartTime);
      Serial.print(",");
      Serial.print("0.00,0.00,0.00,0,AUTO");
      Serial.println();
      
      lastDataSent = millis();
    }
  }
  
  // Mostrar estado cada 5 segundos (menos verbose)
  static unsigned long lastShow = 0;
  if(millis() - lastShow > 5000) {
    Serial.print("SISTEMA: [ACTIVO] | EMG Devices: ");
    Serial.print(dev_count);
    Serial.print(" | Tiempo: ");
    Serial.print((millis() - sessionStartTime) / 1000);
    Serial.println("s");
    lastShow = millis();
  }
  
  delay(10);  // Delay mínimo para estabilidad
}