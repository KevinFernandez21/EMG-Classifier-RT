// Versión simple sin problemas de watchdog
#include <Arduino.h>
#include <uMyo_BLE.h>

// Configuración de pines
const int BUTTON_PINS[4] = {12, 15, 26, 21};
const int MASTER_BUTTON_PIN = 27;
String movementNames[4] = {"CERRAR_MANO", "PINZA", "SALUDAR", "TOMAR_OBJ"};

// Variables de estado simplificadas
bool buttonActive[4] = {false, false, false, false};
bool systemEnabled = false;
bool headersSent = false;
unsigned long sessionStartTime = 0;

void setup() {
  Serial.begin(115200);
  
  // Configurar pines
  for(int i = 0; i < 4; i++) {
    pinMode(BUTTON_PINS[i], INPUT_PULLUP);
  }
  pinMode(MASTER_BUTTON_PIN, INPUT_PULLUP);
  
  // Inicializar uMyo
  uMyo.begin();
  
  Serial.println("===============================");
  Serial.println("  SISTEMA SIMPLE EMG + CSV");
  Serial.println("===============================");
  Serial.println("Pin 27: Botón Maestro");
  Serial.println("Pin 12: Cerrar Mano");
  Serial.println("Pin 15: Pinza");
  Serial.println("Pin 26: Saludar");
  Serial.println("Pin 14: Tomar Objeto");
  Serial.println("===============================");
}

void loop() {
  // Leer botón maestro
  static bool lastMasterState = HIGH;
  bool masterState = digitalRead(MASTER_BUTTON_PIN);
  
  if(masterState == LOW && lastMasterState == HIGH) {
    delay(50); // Debounce simple
    systemEnabled = !systemEnabled;
    
    if(systemEnabled) {
      Serial.println("CSV_START");
      sessionStartTime = millis();
      headersSent = false;
      Serial.println(">>> SISTEMA ACTIVADO <<<");
    } else {
      Serial.println("CSV_END");
      Serial.println(">>> SISTEMA DESACTIVADO <<<");
      // Desactivar todos los botones
      for(int i = 0; i < 4; i++) {
        buttonActive[i] = false;
      }
    }
  }
  lastMasterState = masterState;
  
  // Leer botones de movimiento solo si sistema activo
  if(systemEnabled) {
    for(int i = 0; i < 4; i++) {
      static bool lastButtonState[4] = {HIGH, HIGH, HIGH, HIGH};
      bool currentState = digitalRead(BUTTON_PINS[i]);
      
      if(currentState == LOW && lastButtonState[i] == HIGH) {
        delay(50); // Debounce simple
        
        // Toggle del botón
        buttonActive[i] = !buttonActive[i];
        
        // Desactivar otros botones si este se activa
        if(buttonActive[i]) {
          for(int j = 0; j < 4; j++) {
            if(j != i) buttonActive[j] = false;
          }
          Serial.print(">>> ACTIVADO: ");
          Serial.println(movementNames[i]);
        } else {
          Serial.print(">>> DESACTIVADO: ");
          Serial.println(movementNames[i]);
        }
      }
      lastButtonState[i] = currentState;
    }
    
    // Procesar datos EMG
    uMyo.run();
    int dev_count = uMyo.getDeviceCount();
    
    if(dev_count > 0) {
      // Obtener movimiento activo
      int activeMovement = 0;
      for(int i = 0; i < 4; i++) {
        if(buttonActive[i]) {
          activeMovement = i + 1;
          break;
        }
      }
      
      if(activeMovement > 0) {
        // Enviar headers solo una vez
        if(!headersSent) {
          Serial.println("timestamp,session_time,emg1,emg2,emg3,movement_id,movement_name");
          headersSent = true;
        }
        
        // Obtener datos EMG (simplificado)
        float emg1 = uMyo.getMuscleLevel(0);
        float emg2 = uMyo.getMuscleLevel(1); // Ajustar según tu sensor
        float emg3 = uMyo.getMuscleLevel(2); // Ajustar según tu sensor
        
        // Enviar datos CSV
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
        Serial.print(activeMovement);
        Serial.print(",");
        Serial.println(movementNames[activeMovement - 1]);
      }
    }
  }
  
  // Mostrar estado cada segundo
  static unsigned long lastShow = 0;
  if(millis() - lastShow > 1000) {
    Serial.print("SISTEMA: ");
    Serial.print(systemEnabled ? "[ACTIVO]" : "[DESACTIVADO]");
    Serial.print(" | Botones: ");
    for(int i = 0; i < 4; i++) {
      Serial.print(buttonActive[i] ? "1" : "0");
    }
    Serial.println();
    lastShow = millis();
  }
  
  delay(30);
}