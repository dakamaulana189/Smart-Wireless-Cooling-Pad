import time
import requests
import serial

# ==================== KONFIGURASI ====================
COM_PORT = 'COM4' 
BAUD_RATE = 9600
OHM_URL = 'http://localhost:8085/data.json'
# =====================================================

def ambil_suhu_ohm(data):
    suhu_cpu = None
    suhu_gpu = None
    
    def cari_node(node):
        nonlocal suhu_cpu, suhu_gpu
        text_sensor = node.get('Text', '')
        val_str = node.get('Value', '')
        
        if val_str and '°C' in val_str:
            try:
                angka_suhu = int(float(val_str.replace(' °C', '').replace(',', '.')))
                if text_sensor in ['CPU Package', 'Core Max', 'Package']:
                    suhu_cpu = angka_suhu
                elif text_sensor == 'GPU Core':
                    suhu_gpu = angka_suhu
            except:
                pass
                
        if 'Children' in node:
            for child in node['Children']:
                cari_node(child)

    cari_node(data)
    return suhu_cpu, suhu_gpu

print("--- LOQ COOL Windows Bridge ---")

# LOOP UTAMA KONEKSI ARDUINO (RECONNECT OTOMATIS)
arduino = None
while arduino is None:
    try:
        print(f"Mencoba konek ke Arduino di {COM_PORT}...")
        arduino = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
        time.sleep(2) 
        print(f"BERHASIL TERKONEKSI ke Arduino di {COM_PORT}! Memulai pengiriman data...")
    except Exception as e:
        print(f"Gagal konek: {e}")
        print("Bluetooth belum siap atau HC-05 di luar jangkauan. Mencoba lagi dalam 5 detik...")
        time.sleep(5) # Nunggu 5 detik sebelum coba lagi, gak bakal nge-hang atau minta pencet key

# LOOP PENGIRIMAN DATA SUHU
while True:
    try:
        response = requests.get(OHM_URL)
        if response.status_code == 200:
            json_data = response.json()
            suhu_cpu, suhu_gpu = ambil_suhu_ohm(json_data)
            
            if suhu_cpu is None and suhu_gpu is not None: suhu_cpu = suhu_gpu
            if suhu_gpu is None and suhu_cpu is not None: suhu_gpu = suhu_cpu
            if suhu_cpu is None: suhu_cpu = 40
            if suhu_gpu is None: suhu_gpu = 40
            
            data_kirim = f"{suhu_cpu},{suhu_gpu}\n"
            arduino.write(data_kirim.encode('utf-8'))
            print(f"Dikirim -> CPU: {suhu_cpu}°C, GPU: {suhu_gpu}°C")
            
    except serial.SerialException:
        # Jalur penyelamat kalau tiba-tiba koneksi Bluetooth putus di tengah jalan
        print("\n[PERINGATAN] Koneksi Bluetooth terputus!")
        arduino = None
        while arduino is None:
            try:
                print("Mencoba menyambungkan ulang ke HC-05...")
                arduino = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
                time.sleep(2)
                print("Koneksi berhasil dipulihkan!")
            except:
                time.sleep(5)
                
    except Exception as e:
        print(f"Error membaca data LibreHardwareMonitor: {e}")
        
    time.sleep(2)