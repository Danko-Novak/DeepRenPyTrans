# 🎮 DeepRenPyTrans

**Traductor universal para novelas visuales Ren'Py basado en Inteligencia Artificial.**

🌐 [English](README.md) | [Русский](README.ru.md) | [Español](README.es.md) | [Português](README.pt.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [简体中文](README.zh.md)

---

Traduce cualquier juego de Ren'Py a cualquier idioma utilizando DeepSeek (incluyendo `deepseek-v4-flash` / `deepseek-v4-pro`), OpenAI o LLMs locales, sin modificar el código fuente del juego.

---

## ✨ Características

- **🔍 Extracción Inteligente** — Encuentra automáticamente todas las cadenas traducibles en los archivos `.rpy`, filtrando el código, los IDs y los mensajes de depuración.
- **🤖 Traducción con IA** — Traducción por lotes a través de DeepSeek, OpenAI u Ollama local con contexto contextual de la escena/capítulo.
- **🔌 Inyección en Tiempo de Ejecución** — Sistema de ganchos (hooks) con cero modificaciones en los archivos del juego original, utilizando la función nativa de Ren'Py `config.replace_text`.
- **📊 Auditoría de Calidad** — Encuentra cadenas no traducidas, traducciones huérfanas y registros basura.
- **🧹 Limpieza de Diccionario** — Elimina automáticamente mensajes de depuración, cadenas de documentación y artefactos de código.
- **⚡ Incremental** — Reanuda traducciones interrumpidas, procesando únicamente las cadenas nuevas o faltantes.
- **📱 Multiplataforma** — Funciona con versiones para PC, Android (inyección en APK) e iOS.

## 🚀 Inicio Rápido

### 1. Instalar

```bash
git clone https://github.com/Danko-Novak/DeepRenPyTrans.git
cd DeepRenPyTrans

# Opción A: Instalar como un paquete (recomendado: proporciona el comando `deeprenpytrans` globalmente)
pip install -e .

# Opción B: Instalar solo las dependencias
pip install -r requirements.txt
```

> Después de hacer `pip install -e .` puedes usar `deeprenpytrans` directamente en lugar de `python -m deeprenpytrans`.

### 2. Configurar

```bash
# Copiar las configuraciones de ejemplo
cp .env.example .env
cp config.example.yaml config.yaml

# Edita .env con tu clave API
# Edita config.yaml con la ruta del juego y el idioma de destino
```

Puedes ejecutar la herramienta de dos maneras:

#### Opción A: Interfaz Gráfica Web (Recomendado)
Inicia el servidor web local y utiliza la interfaz para gestionar configuraciones, alternar flags de compilación y ejecutar tareas:
```bash
python gui_server.py
```
Esto abrirá automáticamente tu navegador en `http://localhost:8000`.

#### Opción B: Interfaz de Línea de Comandos (CLI)
```bash
# Paso 1: Extraer cadenas del juego
python -m deeprenpytrans extract --game "./MiJuego/game"

# Paso 2: Traducir con IA
python -m deeprenpytrans translate --strings strings_by_file.json --dict "./MiJuego/game/tl/spanish/dictionary.json"

# Paso 3: Generar los ganchos de tiempo de ejecución
python -m deeprenpytrans inject --game "./MiJuego/game" --lang spanish
```


## 📖 Comandos

### `extract` — Buscar cadenas traducibles

```bash
python -m deeprenpytrans extract --game ./MiJuego/game --output strings.json
```

Analiza todos los archivos `.rpy`, extrae las cadenas entre comillas y aplica filtros inteligentes para omitir:
- IDs internos (`ITM_Sword`, `LOC_Bridge`, `ACT_NPC01`)
- Código Python y aserciones
- Rutas de archivos y códigos de color hexadecimales
- Mensajes de depuración/registro
- Texto ya traducido (detección de caracteres del idioma de destino)

Opciones:
| Parámetro | Descripción |
|------|-------------|
| `--game PATH` | Ruta al directorio `game/` del juego |
| `--output FILE` | Archivo JSON de salida (por defecto: `strings_by_file.json`) |
| `--include-log PATH` | Fusionar con las cadenas no traducidas de `untranslated.log` |

### `translate` — Traducción con IA

```bash
python -m deeprenpytrans translate --strings strings.json --dict dictionary.json
```

Envía las cadenas a la API de IA en lotes inteligentes (agrupados por archivo de origen para mantener el contexto).
Admite traducción incremental: las cadenas ya traducidas se omiten automáticamente.

### `audit` — Control de calidad

```bash
python -m deeprenpytrans audit --dict dictionary.json --strings strings.json
```

Genera un informe detallado que muestra:
- ❌ Cadenas no traducidas (presentes en el código, pero no en el diccionario)
- 👻 Traducciones huérfanas (presentes en el diccionario, pero ya no existen en el código)
- 🔁 Claves y valores idénticos (posiblemente omitidos en la traducción)
- 📭 Traducciones vacías
- 🗑️ Registros basura (mensajes de depuración, fragmentos de código)

### `clean` — Limpieza del diccionario

```bash
python -m deeprenpytrans clean --dict dictionary.json --dry-run
python -m deeprenpytrans clean --dict dictionary.json --remove-orphaned
```

Opciones:
| Parámetro | Descripción |
|------|-------------|
| `--dry-run` | Vista previa de lo que se eliminaría |
| `--keep-junk` | No eliminar cadenas de depuración/código |
| `--remove-orphaned` | Eliminar también las traducciones que ya no existen en el código |

### `inject` — Generar hooks.rpy

```bash
python -m deeprenpytrans inject --game ./MiJuego/game --lang spanish
```

Genera un archivo `hooks.rpy` que:
- Carga el archivo `dictionary.json` al arrancar el juego.
- Intercepta todo el texto en pantalla mediante `config.replace_text`.
- Guarda las cadenas no traducidas en `untranslated.log` en tiempo real mientras juegas.
- Añade una tecla de acceso rápido para activar/desactivar la traducción en vivo.
- Reemplaza las fuentes originales con tipografías compatibles con el idioma de destino.

## ⚙️ Configuración

### `config.yaml`

```yaml
game_dir: "./MiJuego/game"
target_language: "Spanish"
translation_dir: "spanish"

api:
  provider: "deepseek"    # o "openai", "ollama"
  model: "deepseek-chat"  # admite nuevos modelos deepseek-v4-flash / deepseek-v4-pro
  temperature: 0.2
  batch_size: 40

fonts:
  default: "DejaVuSans.ttf"
  replacements:
    "OriginalFont.ttf": "DejaVuSans.ttf"

extraction:
  skip_prefixes: ["ITM", "ACT", "LOC", "QST"]
  force_include: ["Q.Save", "Q.Load"]
```

### `.env`

```bash
DEEPSEEK_API_KEY=sk-tu-clave-aqui
# o
OPENAI_API_KEY=sk-tu-clave-openai-aqui
```

## 🏗️ Cómo Funciona

```
┌────────────────┐     ┌──────────────┐     ┌────────────────┐
│ Archivos .rpy  │────▶│  Extractor   │────▶│  strings.json  │
│ (código juego) │     │   (filtros)  │     │ (por archivos) │
└────────────────┘     └──────────────┘     └───────┬────────┘
                                                    │
                                                    ▼
┌────────────────┐     ┌──────────────┐     ┌────────────────┐
│  Diccionario   │◀────│ Traductor IA │◀────│ Proveedor API  │
│     .json      │     │   (lotes)    │     │ (DeepSeek/etc) │
└───────┬────────┘     └──────────────┘     └────────────────┘
        │
        ▼
┌────────────────┐     ┌──────────────┐
│   hooks.rpy    │────▶│ Juego Ren'Py │ ← ¡El jugador ve el texto traducido!
│  (ejecución)   │     │ (ejecución)  │
└────────────────┘     └──────────────┘
```

## 📱 Despliegue en Dispositivos Móviles

### Android (Inyección en APK)
1. Utiliza nuestro script automatizado `build_apk.bat` que realiza todo el proceso:
   - Extrae los recursos del juego del APK antiguo.
   - Restaura los recursos ya comprimidos del APK original para ahorrar hasta un 60% del tamaño total (ahorro promedio de ~400-500 MB).
   - Realiza compresión de audio wav a ogg.
   - Optimiza las nuevas imágenes para móviles omitiendo las que ya estaban comprimidas.
   - Empaqueta el APK usando compresión ultra y lo firma de forma automática.
2. **Personalización**: Puedes personalizar el proceso de compilación editando las variables (flags) en la parte superior de `build_apk.bat`:
   - `RESTORE_OLD_ASSETS` (1/0): Habilitar/deshabilitar la restauración de recursos ya comprimidos del APK original.
   - `COMPRESS_AUDIO` (1/0): Habilitar/deshabilitar la conversión de wav a ogg y el parcheo de scripts.
   - `COMPRESS_IMAGES` (1/0): Habilitar/deshabilitar la compresión de nuevas imágenes.
   - `INJECT_TRANSLATION` (1/0): Habilitar/deshabilitar la inyección de traducción. Ponlo en `0` para compilar un port limpio sin traducir (en idioma original).
   - `LANG_FOLDER`: Nombre de la carpeta de idioma de destino dentro de `game/tl/` (por ejemplo, `spanish`).
   - `COMPRESSION_LEVEL` (0-9): Nivel de compresión de 7-Zip (9 = compresión ultra, 0 = sin compresión).
3. Si lo haces manualmente: descomprime el APK, reemplaza los archivos dentro de `assets/x-game/game/`, limpia las firmas en `META-INF/` y vuelve a empaquetar y firmar.

### iOS
1. Genera el proyecto Xcode desde el Ren'Py Launcher.
2. Añade la carpeta `tl/spanish/` al proyecto.
3. Compila e instala en el dispositivo.
## ⚠️ Nota Importante y Limitaciones

- **Estado de Pruebas**: Hasta el momento, esta herramienta ha sido probada y verificada en un solo juego, donde todo se tradujo y compiló correctamente.
- **Código Específico del Juego**: Aunque el objetivo fue diseñar una herramienta de traducción universal perfecta, otros juegos de Ren'Py podrían (y probablemente lo harán) requerir algunos ajustes para adaptarse a su base de código particular, prefijos personalizados o peculiaridades de scripting.
- **¿No sabes programar?**: Si no sabes programar o te da pereza modificar los scripts, te recomendamos encarecidamente utilizar asistentes de codificación con IA como **Antigravity**, **Cursor** u otras herramientas similares para ayudarte a adaptar el extractor y los filtros a tu juego específico.

## 🤝 Contribuir

¡Toda contribución es bienvenida! Áreas en las que puedes ayudar:
- Integración de nuevos proveedores de LLM.
- Soporte y pruebas para idiomas CJK (chino, japonés, coreano).
- Mejora de los heurísticos de extracción de texto para juegos complejos.

## 🗺️ Hoja de Ruta y Funciones

Realizamos el seguimiento del desarrollo, planeamos nuevas funciones y priorizamos las tareas en función de los comentarios de la comunidad. Si tienes una idea o deseas solicitar una función, ve a la pestaña **Discussions** (Debates) en GitHub, envía tu propuesta o vota por las ideas existentes.

| Función | Votos | Estado | Progreso |
| :--- | :--- | :--- | :--- |
| **Consola Web GUI (Dashboard)** | - | 🚀 Lanzado | `[████████████████████]` 100% |
| **Empaquetador y Optimizador de APK** | - | 🚀 Lanzado | `[████████████████████]` 100% |
| **Soporte para LLMs Locales y Ollama** | - | 🚀 Lanzado | `[████████████████████]` 100% |
| **Soporte para macOS y Linux** | 0 | 📋 Planificado | `[██░░░░░░░░░░░░░░░░░░]` 10% |
| **Auditorías de Traducción CJK** | 0 | 📋 Planificado | `[█░░░░░░░░░░░░░░░░░░░]` 5% |

---

## 💖 Apoya el Proyecto

DeepRenPyTrans es un proyecto impulsado por la pasión para simplificar el proceso de traducción de novelas visuales. Si esta herramienta te ha ahorrado tiempo o te ha ayudado a llevar un juego a una nueva audiencia, considera apoyar su desarrollo.

**Objetivo de Hardware:** Actualmente estoy ahorrando para actualizar mi estación de trabajo a una tarjeta gráfica **AMD Radeon 9070xt**. Esta actualización es esencial para probar y optimizar el soporte para **LLMs locales**, lo que mejorará significativamente la calidad y velocidad de traducción para todos.

**Fondo Actual:** 0 / 2,000 USD

### Cómo ayudar:
* **Dar una estrella al repositorio (Star):** ¡Ayuda a la visibilidad del proyecto y me motiva a seguir programando!
* **Contribute:** Reporta errores, sugiere funciones o envía un PR.
* **Donar (USDT - TON / Red TON):**
  `UQBdHUyR8nG5p_Rwhw_Rtmgc7QJdJ-G5nOPJa7Pq0mh2A27K`

## 📄 Licencia

GNU AGPL v3 — ver archivo [LICENSE](LICENSE) para más detalles.
