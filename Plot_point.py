import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.animation as animation

# 1. Caricamento dei Dati
try:
    df = pd.read_csv("filtered_data.csv")
except FileNotFoundError:
    print("Errore: Il file 'filtered_data.csv' non è stato trovato nella cartella dello script.")
    exit()

# --- Configurazione Geometria ---
origin_x = 3.6
origin_y = 0.0
radius = 12.0
grid_angles = range(-90, 91, 5)

# --- Setup del Grafico ---
# Crea la finestra della figura
fig, ax = plt.subplots(figsize=(10, 10))

# Disegna lo sfondo statico (raggiera grigia)
for angle_deg in grid_angles:
    math_angle = 90 - angle_deg
    rad = np.radians(math_angle)
    x_end = origin_x + radius * np.cos(rad)
    y_end = origin_y + radius * np.sin(rad)
    
    ax.plot([origin_x, x_end], [origin_y, y_end], 
            color='lightgray', linestyle='--', linewidth=0.5, zorder=1)
    
    if angle_deg % 15 == 0:
        ax.text(x_end, y_end, f"{angle_deg}°", fontsize=8, ha='center', va='center')

ax.plot(origin_x, origin_y, 'ro', markersize=8, zorder=3, label='Origine (3.6m)')

# --- Elementi Dinamici ---
active_line, = ax.plot([], [], color='red', linewidth=3, zorder=2)
info_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=12, 
                    bbox=dict(boxstyle="round", fc="white", ec="gray", alpha=0.8))

ax.set_aspect('equal')
ax.set_xlim(origin_x - radius/1.5, origin_x + radius/1.5)
ax.set_ylim(origin_y - 1, radius + 1)
ax.set_title("Live Monitor: Rilevamento Radar")
ax.set_xlabel("X (m)")
ax.set_ylabel("Y (m)")

# --- Funzione di Inizializzazione ---
def init():
    active_line.set_data([], [])
    info_text.set_text('In attesa di dati...')
    return active_line, info_text

# --- Funzione di Aggiornamento ---
def update(frame_idx):
    # Gestione fine dati: ricomincia da capo o ferma
    if frame_idx >= len(df):
        active_line.set_data([], [])
        info_text.set_text("Fine Dati")
        return active_line, info_text

    row = df.iloc[frame_idx]
    x_curr = row['x']
    y_curr = row['y']
    
    # 1. Calcolo Angolo
    dx = x_curr - origin_x
    dy = y_curr - origin_y
    real_angle_deg_math = np.degrees(np.arctan2(dy, dx))
    user_angle_deg = 90 - real_angle_deg_math
    
    # 2. Snapping alla griglia (5°)
    snapped_angle = round(user_angle_deg / 5.0) * 5.0
    if snapped_angle < -90: snapped_angle = -90
    if snapped_angle > 90: snapped_angle = 90
    
    # 3. Aggiorna Linea Rossa
    math_snap_angle = 90 - snapped_angle
    rad_snap = np.radians(math_snap_angle)
    x_line_end = origin_x + radius * np.cos(rad_snap)
    y_line_end = origin_y + radius * np.sin(rad_snap)
    
    active_line.set_data([origin_x, x_line_end], [origin_y, y_line_end])
    
    # Aggiorna Testo
    info_text.set_text(f"Frame: {frame_idx}/{len(df)}\n"
                       f"Pos: ({x_curr:.2f}, {y_curr:.2f})\n"
                       f"Angolo Rilevato: {int(snapped_angle)}°")
    
    return active_line, info_text

# --- Esecuzione Live ---
# frames: numero totale di passi
# interval: ms tra un frame e l'altro (100ms = 10fps)
# repeat: True per ricominciare il video alla fine
ani = animation.FuncAnimation(fig, update, frames=len(df), 
                              init_func=init, blit=True, interval=100, repeat=False)

# Questo comando apre la finestra
plt.show()