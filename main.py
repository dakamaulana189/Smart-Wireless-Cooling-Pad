import psutil, serial, time, subprocess, sqlite3, threading

# === SETUP DATABASE ===
db_file = "/opt/coolingpad_db/cooling_pad.db"
conn = sqlite3.connect(db_file, check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS log_suhu (
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    cpu_temp INTEGER, gpu_temp INTEGER, max_temp INTEGER)''')
conn.commit()

def delete_old_logs():
    try:
        cursor.execute("DELETE FROM log_suhu WHERE timestamp < datetime('now', '-1 day')")
        conn.commit()
    except: pass

def get_gpu_temp():
    try:
        out = subprocess.check_output(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader"], stderr=subprocess.DEVNULL, timeout=0.3)
        return int(out.decode('utf-8').strip())
    except: return 0

print("--- COOLING PAD SMART SYSTEM STARTING ---")

while True:
    try:
        ser = serial.Serial("/dev/rfcomm0", 9600, timeout=1)
        ser.reset_input_buffer()  # <--- TAMBAH INI
        time.sleep(2)
        
        while ser.is_open:
            # 1. Baca suhu
            temps = psutil.sensors_temperatures()
            cpu_temp = int(temps['coretemp'][0].current) if 'coretemp' in temps else 0
            gpu_temp = get_gpu_temp()
            
            # 2. Kirim ke Arduino
            ser.write(f"{cpu_temp},{gpu_temp}\n".encode())
            
            # 3. Cek Serial RFID (Perhatikan indentasi ini!)
            if ser.in_waiting > 0:
                respon = ser.readline().decode('utf-8', errors='replace').strip()
                # Debugging: Print apa saja yang diterima
                print(f"DITERIMA: '{respon}'", end="\r") 
                
                if "KUNCI_OKE" in respon:
                    print("\n[RFID] Kartu terdeteksi! Membuka layar...")
                    subprocess.run(["loginctl", "unlock-session"])
                elif len(respon) > 0:
                    print(f" (Arduino: {respon})", end="\r")
            
            # 4. Log ke DB
            cursor.execute("INSERT INTO log_suhu (cpu_temp, gpu_temp, max_temp) VALUES (?, ?, ?)",
                           (cpu_temp, gpu_temp, max(cpu_temp, gpu_temp)))
            conn.commit()
            
            print(f"Live Update -> CPU: {cpu_temp}C | GPU: {gpu_temp}C", end="\r")
            time.sleep(0.25)

    except Exception as e:
        print(f"\n[ERROR] Koneksi: {e}")
        time.sleep(2)