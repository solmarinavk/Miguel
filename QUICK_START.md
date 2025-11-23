# 🚀 Quick Start - Detector de Persona Sentada PRO

## Uso Rápido en Google Colab

### ⚡ Opción 1: Ejecutar el Notebook (Más Fácil)

1. Sube `DETECTOR_SENTADO_PRO.ipynb` a Google Colab
2. Ejecuta las celdas en orden
3. Sube tu video cuando te lo pida
4. ¡Listo! 🎉

### 💻 Opción 2: Usar el Script Python

```python
# 1. Instalar dependencias
!pip -q install mediapipe==0.10.14 opencv-python==4.10.0.84 matplotlib==3.9.0
!apt -y -qq install ffmpeg >/dev/null

# 2. Subir el script y tu video a Colab

# 3. Ejecutar
from sentado_detector_pro import DetectorConfig, process_video
from google.colab import files

# Subir video
uploaded = files.upload()
video_path = list(uploaded.keys())[0]

# Configuración por defecto (recomendada)
config = DetectorConfig()

# Procesar
outputs = process_video(video_path, config)

# Mostrar resultado
from IPython.display import HTML, display
import base64

with open(outputs['video'], 'rb') as f:
    video_b64 = base64.b64encode(f.read()).decode()

display(HTML(f'''
<video width="720" controls>
    <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
</video>
'''))
```

---

## ⚙️ Personalización Rápida

### Hacer detección MÁS sensible:
```python
config = DetectorConfig(
    enter_hip_drop=0.55,  # Default: 0.62
    knee_sit_max=140.0    # Default: 120.0
)
```

### Hacer detección MÁS estricta:
```python
config = DetectorConfig(
    enter_hip_drop=0.70,  # Default: 0.62
    knee_sit_min=85.0,    # Default: 75.0
    knee_sit_max=105.0    # Default: 120.0
)
```

### Respuesta MÁS rápida:
```python
config = DetectorConfig(
    enter_min_sec=0.15,   # Default: 0.35
    ema_alpha_height=0.30 # Default: 0.20 (más alto = más responsive)
)
```

### Video con MUCHO ruido:
```python
config = DetectorConfig(
    ema_alpha_height=0.10,  # Default: 0.20 (más bajo = más suave)
    ema_alpha_angle=0.10,   # Default: 0.20
    enter_min_sec=0.60      # Default: 0.35 (más debounce)
)
```

---

## 📁 Archivos Generados

Después de procesar, obtendrás:

1. **`sitting_detection_pro.mp4`**
   - Video con overlays profesionales
   - Indicador de calidad de postura
   - Barra temporal (EKG)
   - Métricas en pantalla

2. **`sitting_intervals_pro.csv`**
   ```csv
   start_s,end_s,duration_s
   2.340,8.120,5.780
   10.450,15.230,4.780
   ```

3. **`sitting_frames_pro.csv`**
   ```csv
   time_s,state,knee_deg,torso_deg,hip_drop_ratio,sitting_score,quality_score
   0.033,STANDING,168.5,8.2,0.45,0.12,0.95
   0.067,STANDING,167.8,8.5,0.46,0.13,0.94
   ```

4. **`posture_analysis_pro.png`**
   - Gráfico de 3 paneles con análisis completo

---

## 🎯 Parámetros Principales

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `target_width` | 720 | Ancho del video de salida |
| `ema_alpha_height` | 0.20 | Suavizado cadera (↑ = más reactive) |
| `ema_alpha_angle` | 0.20 | Suavizado ángulos (↑ = más reactive) |
| `enter_hip_drop` | 0.62 | Bajada cadera para detectar sentado |
| `exit_hip_drop` | 0.55 | Bajada para salir (histéresis) |
| `knee_sit_min` | 75.0 | Ángulo rodilla mínimo sentado |
| `knee_sit_max` | 120.0 | Ángulo rodilla máximo sentado |
| `enter_min_sec` | 0.35 | Segundos para confirmar sentado |
| `exit_min_sec` | 0.35 | Segundos para confirmar de pie |
| `torso_max_deg` | 30.0 | Máx inclinación torso sentado |

---

## 💡 Tips

### ¿No detecta cuando está sentado?
```python
config = DetectorConfig(
    enter_hip_drop=0.55,  # Menos exigente
    knee_sit_max=130.0     # Acepta rodilla más extendida
)
```

### ¿Detecta falsos positivos?
```python
config = DetectorConfig(
    enter_hip_drop=0.68,  # Más exigente
    enter_min_sec=0.50     # Más tiempo de confirmación
)
```

### ¿Transiciones muy rápidas/ruidosas?
```python
config = DetectorConfig(
    ema_alpha_height=0.10,  # Más suavizado
    enter_min_sec=0.50,     # Más debounce
    exit_min_sec=0.50
)
```

### ¿Quieres análisis en tiempo real?
```python
config = DetectorConfig(
    ema_alpha_height=0.40,  # Muy responsive
    enter_min_sec=0.10      # Respuesta inmediata
)
```

---

## 📊 Interpretando Resultados

### Calidad de Postura (Quality Score):

- **90-100%** 🟢 Excelente (rodilla ~90°, espalda recta)
- **70-89%** 🟡 Buena (pequeñas desviaciones)
- **40-69%** 🟠 Aceptable (mejorable)
- **0-39%** 🔴 Mala (revisar ergonomía)

### Sitting Score:

- **0.8-1.0** → Claramente sentado
- **0.5-0.8** → Zona de transición
- **0.0-0.5** → Claramente de pie

---

## 🐛 Troubleshooting

### Error: "No se detecta ninguna persona"
- Verifica que la persona esté completamente visible
- MediaPipe necesita ver caderas, rodillas y hombros
- Prueba con `mp_min_detection_confidence=0.3`

### Error: "Baseline no se calibra"
- El video debe empezar con la persona DE PIE
- O ajusta `baseline_warmup_sec` a menos tiempo
- O usa el fallback automático (primeros 2 segundos)

### Detección inestable
- Aumenta el suavizado: `ema_alpha_height=0.10`
- Aumenta debounce: `enter_min_sec=0.50`

---

## 📚 Documentación Completa

Para detalles de implementación, ver:
- `MEJORAS_CODIGO_SENTADO.md` - Documentación completa
- `sentado_detector_pro.py` - Código con docstrings
- `DETECTOR_SENTADO_PRO.ipynb` - Ejemplos interactivos

---

**¡Listo para usar! 🎉**
