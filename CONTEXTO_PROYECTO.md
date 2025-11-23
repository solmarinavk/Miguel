# 📋 Contexto del Proyecto - Sistema de Detección de Postura Sentada

## 🎯 Escenario de Aplicación

### **Evaluación Ergonómica en Espacios de Trabajo y Salud Ocupacional**

Este sistema se enfoca en el **monitoreo automatizado de postura corporal en entornos laborales**, específicamente para:

1. **Control de pausas activas** en oficinas
2. **Evaluación de calidad postural** durante jornadas laborales
3. **Detección de malas prácticas ergonómicas**
4. **Sistemas de asistencia para adultos mayores**

---

## 📹 Descripción del Video de Entrada

### **Qué representa el video:**

El video captura a una persona en su ambiente de trabajo (oficina, taller, hogar) realizando transiciones entre dos posturas principales:

- **De pie**: Persona en posición erguida, realizando tareas que requieren estar parado
- **Sentada**: Persona en silla/asiento, realizando tareas sedentarias

### **Características del video esperado:**

- Persona visible de cuerpo completo (o al menos de cintura para arriba + piernas)
- Vista lateral o frontal que permita ver caderas, rodillas y hombros
- Iluminación adecuada para detección de pose
- Resolución mínima recomendada: 480p (el sistema escala automáticamente)

---

## 📊 Información Esperada del Sistema

### **Datos primarios:**

1. **Instantes de transición**
   - Momento exacto (en segundos) cuando la persona se sienta
   - Momento exacto cuando la persona se levanta
   - Duración de cada episodio sentado

2. **Métricas de postura**
   - Ángulo de rodilla durante posición sentada
   - Inclinación del torso (evaluación ergonómica)
   - Altura relativa de cadera (baseline vs actual)

3. **Calidad postural** (sistema avanzado)
   - Score de ergonomía (0-100%)
   - Detección de posturas inadecuadas
   - Recomendaciones implícitas (visual en gráficos)

### **Salidas del sistema:**

- **Video anotado** con overlays en tiempo real
- **CSV de intervalos** con cada episodio de estar sentado
- **CSV por frame** con datos granulares para análisis profundo
- **Gráficos de análisis** mostrando patrones temporales

---

## 💡 Relevancia y Utilidad

### **¿Por qué es importante detectar este evento?**

#### **1. Salud Ocupacional**

**Problema:** El sedentarismo prolongado está asociado con:
- Problemas musculoesqueléticos (dolor lumbar, cervical)
- Reducción de la circulación sanguínea
- Síndrome metabólico
- Fatiga y reducción de productividad

**Solución con este sistema:**
- Detectar periodos prolongados sin levantarse (>30 min)
- Alertar para pausas activas obligatorias
- Generar reportes de hábitos posturales

#### **2. Ergonomía y Prevención**

**Problema:** Las malas posturas al sentarse causan:
- Lesiones por esfuerzo repetitivo (LER)
- Hernias discales
- Cifosis y lordosis
- Ausentismo laboral por dolores crónicos

**Solución con este sistema:**
- Evaluar **calidad de postura** (ángulo de rodilla, torso)
- Identificar patrones de mala ergonomía
- Proporcionar evidencia objetiva para intervenciones

#### **3. Asistencia para Adultos Mayores**

**Problema:** Personas mayores necesitan supervisión de:
- Caídas al sentarse/levantarse
- Tiempos prolongados sentados (riesgo de úlceras)
- Actividad física insuficiente

**Solución con este sistema:**
- Detectar transiciones bruscas (posibles caídas)
- Alertar si no hay movimiento por X tiempo
- Monitoreo remoto no invasivo

#### **4. Control de Aforo y Ocupación**

**Problema:** En transportes, aulas, salas de espera:
- Contar asientos ocupados
- Detectar capacidad disponible
- Optimizar espacios

**Solución con este sistema:**
- Conteo automático de personas sentadas
- Estadísticas de ocupación temporal
- Sin necesidad de sensores de presión

#### **5. Análisis de Comportamiento en IoT**

**Problema:** Ambientes inteligentes necesitan entender:
- Patrones de uso de espacios
- Momentos de actividad vs descanso
- Personalización de confort (iluminación, temperatura)

**Solución con este sistema:**
- Entrada para sistemas de domótica
- Ajustar automáticamente ambiente cuando detecta sentado
- Optimización energética

---

## 🔬 Aplicaciones Específicas

### **Caso de Uso 1: Oficina Corporativa**

**Escenario:**
Una empresa quiere implementar un programa de bienestar laboral.

**Implementación:**
- Cámara en estación de trabajo (opcional, con consentimiento)
- Sistema detecta tiempo sentado continuo
- Alerta visual/sonora cada 45 minutos sentado
- Genera reporte semanal de hábitos posturales

**Métricas clave:**
- % tiempo sentado vs de pie
- Frecuencia de pausas activas
- Calidad promedio de postura sentada

### **Caso de Uso 2: Centro Geriátrico**

**Escenario:**
Supervisión no invasiva de residentes.

**Implementación:**
- Cámara en sala común
- Detecta si residente lleva >2 horas sentado
- Alerta a cuidadores para fomentar movimiento
- Detecta transiciones rápidas (posible caída)

**Métricas clave:**
- Tiempo máximo sentado continuo
- Número de transiciones diarias
- Alertas de posibles caídas

### **Caso de Uso 3: Investigación Ergonómica**

**Escenario:**
Universidad estudia impacto de diferentes sillas de oficina.

**Implementación:**
- Grabar sujetos usando diferentes sillas
- Analizar calidad postural con cada modelo
- Comparar ángulos de rodilla/torso
- Generar datos cuantitativos objetivos

**Métricas clave:**
- Quality score promedio por silla
- Desviación estándar de ángulos
- Correlación con reportes subjetivos de comodidad

---

## 📈 Ventajas del Sistema Desarrollado

### **Frente a soluciones alternativas:**

| Aspecto | Sensores de Presión | Wearables | **Nuestro Sistema** |
|---------|---------------------|-----------|---------------------|
| **Costo** | Alto (por asiento) | Moderado | Bajo (solo cámara) |
| **Invasividad** | Baja | Alta (usar dispositivo) | Baja (visión) |
| **Datos posturales** | ❌ No | ❌ Limitado | ✅ Completo |
| **Escalabilidad** | Difícil | Personal | Fácil |
| **Mantenimiento** | Hardware | Baterías/pérdidas | Software |

### **Características únicas:**

✅ **No requiere contacto físico**
✅ **Análisis de calidad postural** (no solo detección binaria)
✅ **Datos granulares** para investigación
✅ **Visualización en tiempo real**
✅ **Histórico y tendencias**

---

## 🎯 Objetivos del Proyecto

### **Objetivo General:**

Desarrollar un sistema automatizado de detección de postura sentada mediante visión por computadora que proporcione datos objetivos para evaluación ergonómica y salud ocupacional.

### **Objetivos Específicos:**

1. ✅ **Implementar detección robusta** de transición de pie a sentado usando MediaPipe Pose
2. ✅ **Calcular métricas geométricas** (ángulos, alturas relativas) para clasificación
3. ✅ **Desarrollar sistema de alerta** visual en tiempo real
4. ✅ **Generar datasets** (CSV) para análisis posterior
5. ✅ **Evaluar calidad postural** con scoring automático
6. ✅ **Crear visualizaciones** intuitivas de patrones temporales

---

## 🔍 Comprensión de Landmarks Corporales

### **¿Por qué landmarks normalizados?**

MediaPipe Pose proporciona 33 puntos corporales con coordenadas normalizadas [0,1]:

**Ventajas:**
- ✅ **Independencia de resolución**: Funciona con cualquier tamaño de video
- ✅ **Comparabilidad**: Personas de diferente altura son comparables
- ✅ **Robustez**: Menos sensible a distancia de cámara

**Aplicación en este proyecto:**

1. **Altura de cadera normalizada** (`hip.y`):
   - Valor cercano a 0.5 cuando está de pie
   - Aumenta a >0.6 cuando se sienta
   - Independiente de la altura de la persona

2. **Ángulos articulares**:
   - Calculados con vectores entre landmarks
   - No afectados por escala o perspectiva
   - Reflejan geometría corporal real

3. **Ratios y proporciones**:
   - Bajada de cadera relativa al baseline personal
   - Comparación intra-sujeto (no inter-sujeto)

---

## 🏥 Impacto en Contextos Reales

### **Ergonomía:**
- Evaluación objetiva de estaciones de trabajo
- Datos cuantitativos para ajustes ergonómicos
- Validación de intervenciones (antes/después)

### **Salud Ocupacional:**
- Identificación de trabajadores en riesgo
- Evidencia para programas de prevención
- Cumplimiento de normativas de seguridad

### **Interacción Inteligente:**
- Sistemas adaptativos (escritorio motorizado que se ajusta)
- Domótica contextual (luz se ajusta al estar sentado)
- Gamificación de pausas activas

---

## 📚 Referencias y Normativas

### **Estándares aplicables:**

- **ISO 11226**: Evaluación de posturas de trabajo estáticas
- **OSHA Guidelines**: Ergonomía en oficinas
- **REBA/RULA**: Métodos de evaluación postural

### **Investigación relacionada:**

- Efectos del sedentarismo prolongado en salud cardiovascular
- Ergonomía de estaciones de trabajo con pantallas
- Sistemas de visión por computadora para análisis de movimiento

---

## 🚀 Conclusión

Este sistema de detección de postura sentada representa una **solución moderna, no invasiva y escalable** para problemas reales en:

- **Prevención de lesiones** musculoesqueléticas
- **Mejora de hábitos** laborales
- **Investigación ergonómica** basada en datos
- **Asistencia a poblaciones vulnerables**

Al combinar **MediaPipe Pose con análisis geométrico avanzado**, el sistema no solo detecta eventos binarios (sentado/de pie), sino que proporciona **evaluación de calidad postural**, permitiendo intervenciones preventivas y personalizadas.

---

**Versión:** 1.0
**Fecha:** 2025
**Aplicación:** Ergonomía, Salud Ocupacional, IoT, Asistencia
