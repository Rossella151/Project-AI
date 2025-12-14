import json
import bisect
import math
import csv

# --- CONFIGURAZIONE FILE ---
file_serial = 'serial_test_8.txt'
file_results = 'results_rtls.txt'
file_output = 'filtered_data8.csv'

# --- FUNZIONI DI SUPPORTO ---

def hex_to_twos_complement(hex_str):
    try:
        val = int(hex_str, 16)
        if val >= 0x8000:
            val -= 0x10000
        return val
    except ValueError:
        return 0

def calculate_g_force(hex_part):
    val_int = hex_to_twos_complement(hex_part)
    return (val_int / 32768.0) * 2.0

def calculate_ang_contr(x, y):
    """
    Calcola l'angolo rispetto all'origine (x=3.6, y=0).
    Sistema di riferimento:
    0°   = Avanti (Asse Y positivo)
    +90° = Destra (Asse X positivo)
    -90° = Sinistra (Asse X negativo)
    """
    dx = x - 3.6
    dy = y - 0.0
    
    # atan2 restituisce l'angolo matematico (0 a Est, antiorario)
    math_angle = math.degrees(math.atan2(dy, dx))
    
    # Conversione: UserAngle = 90 - MathAngle
    angle = 90.0 - math_angle
    
    # Normalizzazione tra -180 e 180
    if angle > 180:
        angle -= 360
    elif angle <= -180:
        angle += 360
        
    return angle

def get_nearest_record(target_idx, records_list, indices_list):
    if not records_list:
        return None

    pos = bisect.bisect_left(indices_list, target_idx)
    candidates = []
    if pos > 0:
        candidates.append(pos - 1)
    if pos < len(indices_list):
        candidates.append(pos)

    best_idx = min(candidates, key=lambda k: abs(indices_list[k] - target_idx))
    return records_list[best_idx][1]

# --- MAIN ---

def main():
    print("1. Caricamento dati...")

    results_map = {}
    # Lettura results_rtls.txt
    try:
        with open(file_results, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if 'seconds' in data:
                        results_map[int(data['seconds'])] = data
                except json.JSONDecodeError:
                    pass
    except FileNotFoundError:
        print(f"Errore: File {file_results} non trovato.")
        return

    matches = []
    imu_records = []
    aoa_records = []

    # Lettura serial_test_7.txt
    try:
        with open(file_serial, 'r') as f:
            for line_idx, line in enumerate(f):
                try:
                    data = json.loads(line)
                    if 'data' in data:
                        imu_records.append((line_idx, data))
                    elif 'angleOfArrival' in data:
                        aoa_records.append((line_idx, data))
                    elif 'fr_no' in data:
                        fr_no = int(data['fr_no'])
                        if fr_no in results_map:
                            matches.append((line_idx, fr_no))
                except json.JSONDecodeError:
                    pass
    except FileNotFoundError:
        print(f"Errore: File {file_serial} non trovato.")
        return

    imu_indices = [r[0] for r in imu_records]
    aoa_indices = [r[0] for r in aoa_records]

    print(f"2. Elaborazione di {len(matches)} record...")

    with open(file_output, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # HEADER
        writer.writerow([
            'x', 'y', 'ang_contr',
            'pdoa',
            'imu_x_g', 'imu_y_g', 'imu_z_g'
        ])

        saved = 0

        for m_idx, fr_no in matches:
            res_data = results_map[fr_no]

            imu_data = get_nearest_record(m_idx, imu_records, imu_indices)
            aoa_data = get_nearest_record(m_idx, aoa_records, aoa_indices)

            x = float(res_data.get('x', 0.0))
            y = float(res_data.get('y', 0.0))

            gx = gy = gz = 0.0
            if imu_data:
                hex_s = imu_data.get('data', '')
                if len(hex_s) >= 16:
                    gx = calculate_g_force(hex_s[4:8])
                    gy = calculate_g_force(hex_s[8:12])
                    gz = calculate_g_force(hex_s[12:16])

            pdoa = aoa_data.get('pdoa') if aoa_data and aoa_data.get('pdoa') is not None else 0.0

            # Calcolo corretto dell'angolo
            ang_contr = calculate_ang_contr(x, y)

            writer.writerow([
                round(x, 6),
                round(y, 6),
                round(ang_contr, 4),
                round(float(pdoa), 6),
                round(gx, 4),
                round(gy, 4),
                round(gz, 4)
            ])

            saved += 1

    print(f"Finito! Record CSV salvati: {saved} in {file_output}")

if __name__ == "__main__":
    main()