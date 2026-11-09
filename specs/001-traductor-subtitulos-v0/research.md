# Investigación (Fase 0): TraductorIngles v0

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Fecha**: 2026-11-08

Este documento resuelve las incógnitas técnicas del plan. Cada decisión sigue el formato
*Decisión / Razón / Alternativas consideradas*. Equipo de referencia para las metas de rendimiento:
**HP ZBook 15 G1** (Intel Core i7 de 4.ª generación, Haswell, 4 núcleos / 8 hilos, AVX2; GPU NVIDIA
Kepler sin soporte en CTranslate2), con Windows 10.

---

## R-01. Lenguaje y versión

- **Decisión**: Python 3.12 (64 bits).
- **Razón**: es el ecosistema con las mejores librerías de voz a texto y traducción que funcionan
  sin internet (faster-whisper, CTranslate2). Todas las dependencias elegidas publican *wheels*
  para Windows y Python 3.12, así que no hace falta compilar nada.
- **Alternativas consideradas**:
  - *C# / .NET 8 + WPF + NAudio + Whisper.net*: instalador más ligero y más nativo, pero no hay una
    traducción sin internet madura para .NET (habría que montar Marian sobre ONNX a mano). Se
    descarta por riesgo y esfuerzo.
  - *Python 3.13*: algunas dependencias de audio tardan en publicar *wheels*; 3.12 es la versión
    estable con soporte más amplio.

## R-02. Captura del audio de bocinas o audífonos (RF-006, RF-010, RF-011)

- **Decisión**: **WASAPI loopback en modo compartido** con `PyAudioWPatch`, sobre el dispositivo de
  salida predeterminado de Windows. Se convierte a 16 kHz, mono y float32 con `soxr`.
- **Razón**:
  - El loopback recibe la mezcla final que Windows manda a la salida, sin importar qué aplicación
    produce el sonido (RF-006).
  - En modo compartido se lee una copia del audio y no se toca la reproducción: no la silencia, no
    la pausa ni le cambia el volumen (RF-010). **Nunca** se abre la salida en modo exclusivo.
  - El loopback solo ve la salida, nunca el micrófono (RF-011). El micrófono jamás se abre.
- **Detalles que el diseño debe cubrir**:
  - **Silencio sin datos**: cuando nada suena, WASAPI loopback deja de entregar paquetes. La captura
    usa lecturas con tiempo límite y trata la falta de datos como silencio, no como error.
  - **Cambio de bocinas a audífonos**: cada 2 s se revisa cuál es el dispositivo de salida
    predeterminado. También se revisa cuando la lectura falla. Si cambió, se cierra el *stream* y
    se abre el loopback del nuevo dispositivo sin cambiar el estado de traducción (caso límite de
    la spec).
  - Cada dispositivo tiene su propio formato (48 kHz, estéreo, int16 o float32). Por eso se
    remuestrea a 16 kHz mono, que es lo que esperan VAD y Whisper.
- **Alternativas consideradas**:
  - `soundcard`: también hace loopback, pero falla más con cambios de dispositivo y tiene menos
    mantenimiento.
  - `sounddevice`: no expone el loopback de WASAPI de forma sencilla.
  - *Mezcla estéreo* del controlador: no existe en todos los equipos y hay que activarla a mano.

## R-03. Detección de voz y segmentación en frases (RF-012, casos límite de silencio y música)

- **Decisión**: **Silero VAD** en ONNX, usando el que ya trae `faster-whisper`
  (`faster_whisper.vad`), con un **segmentador propio** que corta el audio en frases:
  - ventanas de 512 muestras (32 ms) a 16 kHz;
  - una frase empieza cuando la probabilidad de voz pasa de 0.5;
  - la frase termina tras **0.6 s de silencio**, o se corta a la fuerza a los **7 s** para no
    pasarse de la meta de latencia;
  - se descartan frases de menos de **0.3 s**.
- **Razón**: Silero distingue voz de música y ruido mucho mejor que un umbral de energía. Al venir
  dentro de faster-whisper, no hace falta instalar PyTorch.
- **Alternativas consideradas**:
  - `webrtcvad`: más ligero, pero confunde música con voz con frecuencia.
  - `silero-vad` en PyTorch: requiere `torch` (más de 1 GB).

## R-04. Voz a texto sin internet (RF-007, RF-015, CA-001, CA-002, CA-011)

- **Decisión**: **faster-whisper** con el modelo multilingüe **`small`** en `int8` sobre CPU
  (`beam_size=1`, `condition_on_previous_text=False`, `cpu_threads=4`). **Modelo de reserva:
  `base`**, si la medición de latencia (R-12) muestra que `small` no cumple los 3 s.
- **Razón**:
  - El modelo **multilingüe** detecta el idioma (`info.language`, `info.language_probability`). Si
    no es `en`, o la probabilidad es menor que 0.6, la frase se descarta. Así se cubre el caso
    límite de audio en otro idioma. Los modelos `.en` no detectan idioma.
  - Para reducir alucinaciones (por ejemplo, "Thank you." sobre música), se descartan los segmentos
    con `no_speech_prob > 0.6` o `avg_logprob < -1.0` (RF-012).
  - `int8` en CPU con AVX2 es la combinación más rápida disponible en el equipo de referencia, que
    no tiene GPU compatible.
- **Alternativas consideradas**:
  - `openai-whisper` (PyTorch): de 3 a 4 veces más lento en CPU y mucho más pesado.
  - `whisper.cpp`: rendimiento parecido, pero su integración con Python está menos madura.
  - `distil-whisper`: solo inglés y sin detección de idioma.
  - Vosk: más ligero, pero con menor precisión en habla natural.

## R-05. Traducción inglés → español sin internet (RF-007, RF-015)

- **Decisión**: modelo **OPUS-MT `Helsinki-NLP/opus-mt-en-es`** convertido a formato CTranslate2
  (`int8`), con tokenización `sentencepiece` (`source.spm` / `target.spm`). No usa PyTorch al
  ejecutarse.
- **Razón**: traducción neuronal de buena calidad, unos 80 MB en int8 y menos de 300 ms por frase
  en CPU. La conversión del modelo (`ct2-transformers-converter`) se hace **una sola vez** con un
  script de desarrollo; `transformers` y `torch` solo se usan ahí y no viajan en el instalador.
- **Alternativas consideradas**:
  - *Argos Translate*: usa los mismos modelos, pero arrastra `stanza` y PyTorch.
  - *NLLB-200 distilled 600M*: admite variantes de español, pero es unas 4 veces más lento y pesado.
  - *M2M100*: más pesado y de menor calidad en en→es.

## R-06. Español de México (Principio II, RF-007)

- **Decisión**: después de traducir, se aplica un **glosario es-MX**: un archivo de datos
  `glosario_es_mx.tsv` con reemplazos por palabra completa que respetan mayúsculas. Ejemplos:
  ordenador→computadora, móvil→celular, coche→carro, conducir→manejar, zumo→jugo, gafas→lentes,
  vale→está bien, vosotros→ustedes.
- **Razón**: ningún modelo sin internet traduce específicamente a es-MX, y OPUS-MT mezcla corpus de
  España y de América. El glosario es determinista, se prueba por completo y se amplía sin tocar
  código. Se aplica en los dos modos de procesamiento, porque el servicio en línea también entrega
  español genérico (`es`).
- **Limitación aceptada**: el glosario no corrige conjugaciones con *vosotros* ("tenéis"). Esos
  casos se registran en el glosario conforme aparezcan en las pruebas de CA-001.
- **Alternativas consideradas**: un modelo afinado a es-MX (no existe uno libre y ligero) o reglas
  gramaticales (complejidad desproporcionada para la v0).

## R-07. Interfaz, franja de subtítulos y barra de tareas (RF-001, RF-005, RF-008, RF-009, RF-014)

- **Decisión**: **PySide6 (Qt 6)**.
  - **Ventana principal**: pequeña, con el botón de activar o desactivar, el atajo visible, el
    indicador de estado, el interruptor del modo en línea y el botón **"Mover subtítulos"**. Ver
    [contracts/interfaz-usuario.md](contracts/interfaz-usuario.md).
  - **Franja de subtítulos**: `QWidget` con `FramelessWindowHint | WindowStaysOnTopHint | Tool`,
    fondo semitransparente y `WA_ShowWithoutActivating`, para que **no le quite el foco** a la
    llamada o al video. Cada 2 s se vuelve a fijar como `HWND_TOPMOST` con `SetWindowPos`, para
    seguir encima de reproductores en pantalla completa sin bordes (RF-008, CA-006).
  - **Mover la franja (RF-009)**, de dos formas:
    - **Mouse**: se arrastra con el botón izquierdo (`mousePressEvent` / `mouseMoveEvent`).
    - **Teclado**: el botón "Mover subtítulos" activa un *modo de mover*. Solo en ese modo la franja
      acepta el foco: se activa, se resalta con un borde y muestra una instrucción. Las flechas la
      mueven 20 px y Mayús + flecha 100 px. Enter o Esc terminan, la franja deja de aceptar el foco
      y el foco vuelve al botón. La franja nunca sale de los límites de la pantalla.
  - **Ícono en el área de notificación** de la barra de tareas (`QSystemTrayIcon`), con un menú para
    activar o desactivar, abrir la ventana y salir (RF-016a).
  - **Mouse y teclado a la vez (RF-014, CA-010, CA-016)**: todos los controles son widgets estándar
    de Qt. Responden al clic y también a Tab, Espacio y Enter, y ningún camino desactiva al otro.
    Los tests de interfaz recorren cada control **dos veces**: una solo con `qtbot.mouseClick` y
    otra solo con `qtbot.keyClick`.
  - **Accesibilidad**: cada control tiene `accessibleName` en español y un orden de tabulación
    definido. Contraste mínimo de 7:1 y letra de 28 px en los subtítulos.
  - **Cerrar y minimizar (RF-004a, CA-015)**: el `closeEvent` de la ventana principal detiene la
    traducción, cierra la captura, oculta la franja y el ícono, y termina la app
    (`QApplication.quit`). Minimizar no toca el estado.
- **Razón**: Qt da ventanas siempre encima, transparencia, ícono de notificación y accesibilidad
  (UI Automation) listos para usar, y `pytest-qt` permite probar la interfaz automáticamente.
- **Limitación conocida**: la franja no se ve sobre programas en **pantalla completa exclusiva**
  (algunos juegos con DirectX). Los videos en pantalla completa del navegador y de reproductores
  comunes usan ventana sin bordes y sí la muestran. La spec no menciona juegos.
- **Alternativas consideradas**: *Tkinter* (sin transparencia real por píxel ni buena
  accesibilidad) y *Electron / Tauri* (sumarían una segunda tecnología y más peso).

## R-08. Atajo global Ctrl+Alt+T (RF-016, RF-016a, CA-014)

- **Decisión**: la API de Win32 **`RegisterHotKey`** vía `ctypes`, con
  `MOD_CONTROL | MOD_ALT | MOD_NOREPEAT` y la tecla `T`, asociada a la ventana principal. El mensaje
  `WM_HOTKEY` se recibe con un `QAbstractNativeEventFilter`.
- **Razón**: funciona desde cualquier ventana, incluida una en pantalla completa, sin cambiar de
  ventana. Si otra aplicación ya registró el atajo, la función devuelve un error
  (`ERROR_HOTKEY_ALREADY_REGISTERED`, 1409), que es justo lo que necesita RF-016a para avisar. No
  requiere permisos de administrador ni ganchos de teclado de bajo nivel.
- **Alternativas consideradas**: la librería `keyboard` (gancho global de bajo nivel, a veces la
  bloquean los antivirus y no detecta que el atajo ya está ocupado) y `pynput` (mismo problema).

## R-09. Modo en línea (RF-015a, RF-015b, CA-012, CA-013)

- **Decisión**: **Azure AI Speech – Speech Translation** con `azure-cognitiveservices-speech`:
  `SpeechTranslationConfig`, `speech_recognition_language="en-US"`,
  `add_target_language("es")`. El audio entra por un `PushAudioInputStream` (PCM de 16 kHz, mono,
  16 bits) que se alimenta con la misma captura de R-02. Después se aplica el glosario es-MX (R-06).
- **Razón**: un solo servicio hace la voz a texto y la traducción en tiempo real (la spec pide un
  solo servicio) y tiene nivel gratuito (5 h de audio al mes).
- **Respaldo sin internet (RF-015b)**: el motor local se queda **cargado en memoria** aunque el modo
  en línea esté activo. Ante un evento `canceled` con error de red, una desconexión de la sesión o
  10 s sin respuesta, el selector de motores (ver
  [contracts/motor-traduccion.md](contracts/motor-traduccion.md)) cambia al motor local en la
  siguiente frase, muestra el aviso en español y pone el modo en *sin internet*. La traducción no
  se detiene.
- **Cuenta del servicio (RF-015a, RF-015c)**: la persona la captura en el cuadro de la app y se
  guarda cifrada (ver R-14). Nunca va en el instalador ni en el repositorio.
- **Alternativas consideradas**: Google Cloud Speech + Translation (son dos servicios), Deepgram +
  DeepL (dos servicios; DeepL sí distingue `ES-419`) y OpenAI Realtime (más caro y sin una
  traducción dedicada).

## R-10. Pruebas y trazabilidad (Principio IV)

- **Decisión**: `pytest` + `pytest-qt`. Cada test lleva una marca **`@pytest.mark.spec("RF-012",
  "CA-007")`** con los identificadores que cubre. El test **`tests/test_trazabilidad.py`** lee
  `spec.md`, extrae todos los `RF-xxx` y `CA-xxx`, y **falla** si alguno no tiene test, salvo que
  aparezca en `tests/solo_manuales.toml` con su justificación escrita (por ejemplo, CA-003 es una
  prueba con personas).
- **Niveles**:
  - **Unitarias** (rápidas, sin modelos): máquina de estados, segmentador con audio sintético,
    glosario, formato y tiempos de los subtítulos, selector y respaldo de motores (motores falsos),
    textos de la interfaz.
  - **Integración** (marca `modelos`, necesitan los modelos descargados): el flujo completo sin
    internet con WAV de prueba en inglés, en español, de música y de silencio.
  - **Interfaz** (pytest-qt): banderas de la franja, nombres accesibles, cada control solo con
    mouse y solo con teclado, modo de mover, cerrar y minimizar, cuadro de la cuenta (con la
    validación simulada) y reacción al atajo ocupado (con `RegisterHotKey` simulado).
- **Audios de prueba**: frases de *LibriSpeech test-clean* (CC BY 4.0) y clips libres de música y de
  habla en español, en `tests/fixtures/audio/`, con su atribución.
- **Alternativas consideradas**: `unittest` (más verboso y sin un equivalente cómodo de pytest-qt).

## R-11. Empaquetado e instalador (RF-001, RF-004)

- **Decisión**: **PyInstaller** en modo *onedir* + **Inno Setup 6**.
  - *onedir* arranca más rápido que *onefile* (no descomprime en cada inicio), lo que ayuda a
    CA-003.
  - Los modelos viajan en `modelos/` junto al ejecutable. El instalador pesa unos 700 MB con
    `small`.
  - Inno Setup crea el **acceso directo en el escritorio** y la entrada del menú Inicio. **No**
    registra arranque automático con Windows (RF-004).
- **Barra de tareas**: Windows 10 no permite que un instalador ancle programas a la barra de tareas.
  Con la app abierta, su botón y su ícono de notificación quedan en la barra. Para abrirla desde la
  barra estando cerrada, la persona la ancla con clic derecho → "Anclar a la barra de tareas". Ver
  la **Pendiente P-04**.
- **Alternativas consideradas**: *Nuitka* (compilación más lenta y frágil con PySide6) y *MSIX*
  (requiere firma de código).

## R-12. Meta de latencia (CA-002 ≤ 3 s) y medición previa

- **Presupuesto por frase** (desde que la persona termina de hablar):

  | Etapa | Presupuesto |
  |---|---|
  | Detectar el fin de la frase (silencio) | 0.6 s |
  | Voz a texto (`small` int8, frase de 3 a 5 s) | ≤ 1.6 s |
  | Traducción OPUS-MT + glosario | ≤ 0.3 s |
  | Mostrar en pantalla | ≤ 0.1 s |
  | **Total** | **≤ 2.6 s** (0.4 s de margen) |

- **Decisión**: la **primera tarea técnica** es un script `scripts/medir_latencia.py` que mide cada
  etapa en el equipo de referencia con los WAV de prueba. Si el percentil 90 del total pasa de
  3 s con `small`, se usa `base` y se repite la medición de calidad de CA-001.
- **Carga de modelos**: se cargan en segundo plano **al abrir la app**. Eso no es escuchar audio,
  así que no contradice RF-004. Si la persona activa la traducción antes de que terminen de cargar,
  la ventana muestra "Preparando la traducción…" y empieza a traducir en cuanto terminan.

## R-13. Ajustes guardados en el equipo

- **Decisión**: se guardan solo dos cosas, en `%APPDATA%\TraductorIngles\`:
  - `ajustes.json`, con **un único dato**: `aviso_en_linea_aceptado` (bool). Así el aviso de RF-015a
    sale **una sola vez por instalación** y, si la persona no lo acepta, vuelve a salir la siguiente
    vez.
  - `cuenta_en_linea.bin`: la cuenta del modo en línea, cifrada (R-14).
- **Desinstalar**: Inno Setup borra la carpeta `%APPDATA%\TraductorIngles\`. Así, una instalación
  nueva vuelve a mostrar el aviso, como pide "una vez por instalación".
- **No se guarda**: la posición de la franja (la spec no pide recordarla; Principio III), el estado
  de traducción ni el modo de procesamiento (ambos empiezan siempre en desactivada y sin internet).
  Tampoco ningún texto ni audio: los subtítulos no se guardan.
- **Bitácora técnica**: errores en `%LOCALAPPDATA%\TraductorIngles\errores.log`, **sin contenido**
  (ni audio ni texto traducido; nunca la clave). Solo tipo de error, componente y hora, para
  diagnóstico.

## R-14. Guardar y validar la cuenta del modo en línea (RF-015a, RF-015c, CA-012)

- **Decisión, guardado**: **DPAPI de Windows** (`CryptProtectData` / `CryptUnprotectData` vía
  `ctypes`, con alcance del usuario actual) sobre un JSON `{"clave": …, "region": …}`, escrito en
  `%APPDATA%\TraductorIngles\cuenta_en_linea.bin`.
- **Razón**: DPAPI viene en Windows y no agrega dependencias. Solo el mismo usuario en el mismo
  equipo puede descifrar el archivo, y si se copia a otra computadora no sirve. Así se cumple
  "guardarlas cifradas en el equipo".
- **Decisión, validación**: antes de guardar, la app pide un token a
  `https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken` con el encabezado
  `Ocp-Apim-Subscription-Key`, usando `urllib` de la librería estándar y un tiempo límite de 5 s.
  - **200**: la cuenta es válida; se guarda y el modo pasa a *en línea*.
  - **401 / 403**, o región inexistente: es inválida. **No se guarda**, se muestra M-08 y el modo
    sigue *sin internet* (RF-015c).
  - **Sin conexión o tiempo agotado**: no se guarda, se muestra M-09 y el modo sigue *sin internet*.
  - **Cancelar el cuadro**: no se guarda y el modo sigue *sin internet*, sin mensaje de error.
    Como la cuenta no se guardó, se vuelve a pedir la siguiente vez (RF-015c).
- **Cuenta guardada que el servicio rechaza después** (clave revocada): se borra
  `cuenta_en_linea.bin`, se muestra M-08 y la app vuelve a *sin internet*. La siguiente vez que se
  encienda el modo, vuelve a pedir la cuenta.
- **El cuadro**: el campo de la clave usa `QLineEdit.Password`, así que la clave nunca se muestra
  completa. La región es una lista desplegable de regiones de Azure Speech con texto editable, lo
  que evita errores de escritura.
- **Alternativas consideradas**: *Windows Credential Manager* con la librería `keyring` (agrega una
  dependencia y su ventaja es mínima para un solo dato) y `pywin32` (`win32crypt`, que agrega una
  dependencia grande por dos funciones).

---

## Huecos de la spec detectados al planear

| ID | Hueco | Estado |
|---|---|---|
| P-01 | **Estado de la spec**: dice "Borrador". La constitución exige aprobación antes de planear o implementar. | **Resuelto** (2026-11-08): el propietario aprobó la spec; el estado es "Aprobada" en `spec.md` y en `specs/MAPA.md`. |
| P-02 | Mover la franja con teclado. | **Resuelto** (aclaración del 2026-11-08): botón "Mover subtítulos" + flechas; también con mouse (RF-009, RF-014). |
| P-03 | Cómo se configura la cuenta del modo en línea. | **Resuelto**: cuadro en la app y guardado cifrado (RF-015a, RF-015c, R-14). |
| P-04 | **"Abrir desde la barra de tareas"** con la app cerrada: Windows 10 no deja que un instalador ancle programas. | **Documentado como limitación** (R-11): acceso directo en el escritorio y en el menú Inicio; botón e ícono en la barra mientras está abierta; anclar es manual. No requiere cambiar la spec. |
| P-05 | Qué pasa al cerrar la ventana principal. | **Resuelto**: cerrar sale de la app y minimizar no detiene nada (RF-004a, CA-015). |
| P-06 | "La primera vez" del aviso del modo en línea. | **Resuelto**: una vez por instalación (RF-015a, R-13). |
| P-07 | "Unos segundos" sin habla antes de borrar el subtítulo. | **Resuelto**: 4 s (RF-012). |
