# 🎯 Calle - Conversor CSV a Excel

**Calle** es una plataforma web moderna y elegante que te permite convertir archivos CSV a formato Excel de manera rápida y sencilla, con visualización de datos en tiempo real.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Características

- 📤 **Carga de archivos CSV** mediante drag & drop o selección manual
- 🔧 **Selección flexible de delimitadores** (coma, punto y coma, tabulación, pipe, personalizado)
- 👁️ **Visualización en tiempo real** de los datos en formato tabla
- 📊 **Conversión a Excel** (.xlsx) con un solo clic
- 📥 **Descarga instantánea** del archivo Excel generado
- 🎨 **Diseño moderno y responsive** con excelente UX/UI
- ⚡ **100% del lado del cliente** - sin necesidad de servidor
- 🌐 **Compatible con Netlify** y otros servicios de hosting estático
- ⌨️ **Atajos de teclado** para mayor productividad

## 🚀 Demo en Vivo

Una vez desplegado en Netlify, podrás acceder a la aplicación desde tu navegador.

## 📋 Requisitos

- Navegador web moderno (Chrome, Firefox, Safari, Edge)
- Conexión a internet (solo para cargar las fuentes y la librería SheetJS)

## 🛠️ Instalación y Despliegue

### Opción 1: Despliegue en Netlify (Recomendado)

1. **Conecta tu repositorio con Netlify:**
   - Ve a [Netlify](https://app.netlify.com/)
   - Click en "Add new site" → "Import an existing project"
   - Conecta tu cuenta de GitHub y selecciona este repositorio
   - La configuración se detectará automáticamente desde `netlify.toml`
   - Click en "Deploy site"

2. **¡Listo!** Tu sitio estará disponible en una URL de Netlify.

### Opción 2: Desarrollo Local

1. **Clona el repositorio:**
   ```bash
   git clone <tu-repositorio>
   cd Miguel
   ```

2. **Inicia un servidor local:**
   ```bash
   # Usando Python 3
   python3 -m http.server 8000

   # O usando Node.js
   npx serve .

   # O usando PHP
   php -S localhost:8000
   ```

3. **Abre tu navegador:**
   ```
   http://localhost:8000
   ```

## 📖 Cómo Usar

1. **Sube tu archivo CSV:**
   - Arrastra y suelta tu archivo CSV en la zona de carga
   - O haz clic para seleccionar el archivo desde tu computadora

2. **Selecciona el delimitador:**
   - Elige el delimitador que usa tu archivo CSV
   - Opciones: coma (,), punto y coma (;), tabulación (\t), pipe (|), o personalizado
   - Por defecto se usa la coma

3. **Procesa el archivo:**
   - Haz clic en "Procesar CSV"
   - Verás una vista previa de tus datos en formato tabla

4. **Descarga el Excel:**
   - Haz clic en "Descargar Excel"
   - El archivo .xlsx se descargará automáticamente

5. **Subir otro archivo:**
   - Haz clic en "Subir nuevo archivo" para empezar de nuevo

## ⌨️ Atajos de Teclado

- `Ctrl/Cmd + O` - Abrir selector de archivos
- `Ctrl/Cmd + S` - Descargar Excel (cuando hay datos cargados)

## 🏗️ Estructura del Proyecto

```
Miguel/
├── index.html          # Página principal
├── css/
│   └── styles.css      # Estilos CSS
├── js/
│   └── app.js          # Lógica de la aplicación
├── netlify.toml        # Configuración de Netlify
├── package.json        # Metadata del proyecto
├── .gitignore          # Archivos ignorados por Git
└── README.md           # Documentación
```

## 🎨 Tecnologías Utilizadas

- **HTML5** - Estructura semántica
- **CSS3** - Estilos modernos con variables CSS y Flexbox/Grid
- **JavaScript (ES6+)** - Lógica de la aplicación
- **SheetJS (xlsx)** - Librería para conversión a Excel
- **Google Fonts (Inter)** - Tipografía moderna
- **Netlify** - Plataforma de despliegue

## 🔒 Seguridad

- Todos los datos se procesan localmente en tu navegador
- No se envía información a ningún servidor
- Protección contra XSS mediante escape de HTML
- No se almacenan datos ni cookies

## 🌟 Características UX/UI

- ✅ Diseño responsive para móviles, tablets y desktop
- ✅ Animaciones suaves y transiciones elegantes
- ✅ Feedback visual en todas las interacciones
- ✅ Estados de carga claros
- ✅ Mensajes de error descriptivos
- ✅ Accesibilidad mejorada
- ✅ Esquema de colores profesional
- ✅ Tipografía legible y moderna

## 📱 Compatibilidad

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Dispositivos móviles (iOS y Android)

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Haz fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🐛 Reportar Problemas

Si encuentras algún problema o tienes sugerencias, por favor abre un issue en GitHub.

## 📧 Contacto

Para preguntas o comentarios, puedes abrir un issue en este repositorio.

---

**Hecho con ❤️ usando tecnologías web modernas**
