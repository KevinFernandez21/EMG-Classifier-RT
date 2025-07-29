import serial
import csv
import os
from datetime import datetime
import time

class ESP32DataLogger:
    def __init__(self, port='COM6', baudrate=115200):  # Cambia COM6 por tu puerto
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None
        self.csv_file = None
        self.csv_writer = None
        self.logging_active = False
        self.session_number = 1
        
    def connect(self):
        """Conectar al ESP32"""
        try:
            self.serial_connection = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"✅ Conectado al ESP32 en {self.port} a {self.baudrate} baudios")
            print("Esperando datos del ESP32...")
            return True
        except Exception as e:
            print(f"❌ Error conectando al ESP32: {e}")
            return False
    
    def create_csv_file(self):
        """Crear archivo CSV con timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dataset_emg_session_{self.session_number}_{timestamp}.csv"
        
        try:
            self.csv_file = open(filename, 'w', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.csv_file)
            print(f"📁 Archivo creado: {filename}")
            return filename
        except Exception as e:
            print(f"❌ Error creando archivo CSV: {e}")
            return None
    
    def close_csv_file(self):
        """Cerrar archivo CSV"""
        if self.csv_file:
            self.csv_file.close()
            print("📁 Archivo CSV guardado y cerrado")
            self.csv_file = None
            self.csv_writer = None
    
    def process_data_line(self, line):
        """Procesar línea de datos CSV"""
        try:
            # Verificar si es una línea de datos CSV válida
            parts = line.split(',')
            if len(parts) == 7:  # timestamp,session_time,emg1,emg2,emg3,movement_id,movement_name
                # Escribir al archivo CSV
                self.csv_writer.writerow(parts)
                self.csv_file.flush()  # Forzar escritura inmediata
                
                # Mostrar progreso
                movement_name = parts[6].strip()
                emg_values = f"EMG1:{parts[2]}, EMG2:{parts[3]}, EMG3:{parts[4]}"
                print(f"📊 {movement_name} - {emg_values}")
                
                return True
        except Exception as e:
            print(f"⚠️ Error procesando línea: {e}")
        return False
    
    def listen_and_log(self):
        """Escuchar datos del ESP32 y guardar automáticamente"""
        if not self.connect():
            return
        
        print("\n" + "="*60)
        print("🎯 SISTEMA DE CAPTURA AUTOMÁTICA INICIADO")
        print("="*60)
        print("👆 Presiona el botón maestro del ESP32 para iniciar/detener")
        print("🔄 Los datos se guardarán automáticamente en archivos CSV")
        print("❌ Presiona Ctrl+C para salir")
        print("="*60 + "\n")
        
        try:
            while True:
                if self.serial_connection.in_waiting > 0:
                    try:
                        line = self.serial_connection.readline().decode('utf-8').strip()
                        
                        if line:
                            # Detectar inicio de sesión
                            if "CSV_START" in line:
                                print("\n🟢 SESIÓN INICIADA - Creando archivo CSV...")
                                filename = self.create_csv_file()
                                if filename:
                                    self.logging_active = True
                                    print(f"📝 Guardando en: {filename}")
                            
                            # Detectar fin de sesión
                            elif "CSV_END" in line:
                                print("\n🔴 SESIÓN TERMINADA")
                                if self.logging_active:
                                    self.close_csv_file()
                                    self.session_number += 1
                                    self.logging_active = False
                                    print("✅ Datos guardados exitosamente")
                            
                            # Detectar headers CSV
                            elif line.startswith("timestamp,session_time"):
                                if self.logging_active and self.csv_writer:
                                    headers = line.split(',')
                                    self.csv_writer.writerow(headers)
                                    self.csv_file.flush()
                                    print("📋 Headers CSV guardados")
                            
                            # Procesar datos CSV
                            elif self.logging_active and ',' in line:
                                self.process_data_line(line)
                            
                            # Mostrar otros mensajes del ESP32
                            elif not line.startswith("SISTEMA:") and len(line) > 5:
                                print(f"ESP32: {line}")
                    
                    except UnicodeDecodeError:
                        # Ignorar caracteres no válidos
                        pass
                
                time.sleep(0.01)  # Pequeña pausa para no saturar CPU
                
        except KeyboardInterrupt:
            print("\n\n🛑 Captura detenida por el usuario")
        except Exception as e:
            print(f"\n❌ Error durante la captura: {e}")
        finally:
            if self.logging_active:
                self.close_csv_file()
            if self.serial_connection:
                self.serial_connection.close()
                print("🔌 Conexión serial cerrada")

def main():
    # Configuración del puerto serie
    PORT = 'COM3'  #  CAMBIAR POR TU PUERTO (COM3, COM4, etc. en Windows; /dev/ttyUSB0 en Linux)
    BAUDRATE = 115200
    
    print(" CAPTURADOR AUTOMÁTICO DE DATOS ESP32")
    print(f"Puerto: {PORT} | Baudrate: {BAUDRATE}")
    
    # Crear y ejecutar el logger
    logger = ESP32DataLogger(port=PORT, baudrate=BAUDRATE)
    logger.listen_and_log()

if __name__ == "__main__":
    main()