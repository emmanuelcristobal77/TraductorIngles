---

description: "Lista de tareas para implementar TraductorIngles v0"
---

# Tareas: TraductorIngles v0 — subtítulos en español del audio en inglés

**Entrada**: documentos de diseño en `specs/001-traductor-subtitulos-v0/`

**Prerrequisitos**: [plan.md](plan.md), [spec.md](spec.md) (Aprobada), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: **obligatorios**. El Principio IV de la constitución exige al menos un test por cada RF y
CA, marcado con `@pytest.mark.spec("RF-xxx", "CA-xxx")`. En cada fase, los tests se escriben
**primero** y deben fallar antes de implementar.

**Organización**: las tareas van por historia de usuario, en el orden que sugiere el plan:
Historia 4 (P1) y luego Historia 1 (P1), que juntas forman el MVP; después las Historias 2 (P2) y
3 (P3). El modo en línea (RF-015a, RF-015b, RF-015c, CA-012, CA-013) no pertenece a una sola
historia, así que tiene su propia fase transversal, sin etiqueta de historia.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin depender de tareas pendientes).
- **[USn]**: historia de usuario de [spec.md](spec.md) a la que pertenece la tarea.
- Las rutas son relativas a la raíz del repositorio. El código vive en `src/traductor/` y los tests
  en `tests/`, como fija el plan.

## Reglas comunes a todas las tareas

- Todo texto visible sale de `src/traductor/textos.py` y se copia **tal cual** de
  [contracts/interfaz-usuario.md](contracts/interfaz-usuario.md) (Principio II). Ningún texto
  visible se escribe directo en otro módulo.
- No se agrega nada que no esté en la spec o en los contratos (Principio III). Por ejemplo: no se
  recuerda la posición de la franja, no hay historial y no se configuran colores.
- Nunca se escribe audio, texto traducido ni la clave en disco ni en la bitácora.
- Cada test lleva `@pytest.mark.spec(...)` con los identificadores que cubre.

---

## Fase 1: Preparación (infraestructura compartida)

**Propósito**: crear el proyecto, conseguir los modelos y medir la latencia antes de escribir la
app (research R-12).

- [X] T001 Crear la estructura de carpetas del plan con un `__init__.py` vacío en cada paquete: `src/traductor/`, `src/traductor/audio/`, `src/traductor/motores/`, `src/traductor/traduccion/`, `src/traductor/ui/`, `src/traductor/recursos/`, `tests/unit/`, `tests/integration/`, `tests/ui/`, `tests/fixtures/audio/`, `scripts/` e `instalador/`
- [X] T002 Crear `pyproject.toml`: paquete `traductor` con diseño `src/`, `requires-python = ">=3.12"` y configuración de pytest con `testpaths = ["tests"]`, `qt_api = "pyside6"` y los marcadores `spec(*ids): identificadores RF/CA de spec.md que cubre el test` y `modelos: necesita los modelos descargados en modelos/`
- [X] T003 [P] Crear `requirements.txt` con las versiones mínimas del plan (`PyAudioWPatch>=0.2.12`, `soxr>=0.5`, `pycaw>=20240210`, `numpy>=2.0`, `faster-whisper>=1.1`, `ctranslate2>=4.5`, `sentencepiece>=0.2`, `PySide6>=6.8`, `azure-cognitiveservices-speech>=1.41`) y `requirements-dev.txt` con `pytest>=8`, `pytest-qt>=4.4`, `pyinstaller>=6.11`, `transformers` y `torch` (estos dos solo para convertir OPUS-MT)
- [X] T004 [P] Crear `.gitignore` con `modelos/`, `.venv/`, `build/`, `dist/`, `__pycache__/` y `*.log`
- [X] T005 [P] Crear `src/traductor/recursos/icono.ico`, un ícono genérico propio (sin marcas) en 16, 32, 48 y 256 px, para la ventana, el área de notificación y el instalador
- [X] T006 Escribir `scripts/preparar_modelos.py`, que debe ser idempotente: si una carpeta ya existe, no la repite. Hace tres cosas:
  - descarga los modelos faster-whisper multilingües `small` y `base` (CTranslate2, `int8`) a `modelos/whisper-small/` y `modelos/whisper-base/`;
  - convierte `Helsinki-NLP/opus-mt-en-es` con `ct2-transformers-converter --quantization int8` a `modelos/opus-mt-en-es-ct2/`;
  - copia `source.spm` y `target.spm` a esa misma carpeta.
- [X] T007 [P] Poner en `tests/fixtures/audio/` los audios de prueba (16 kHz, mono) y su `ATRIBUCION.md` con la fuente y la licencia de cada archivo:
  - al menos 10 frases en inglés de *LibriSpeech test-clean* (CC BY 4.0), en archivos `en_frase_01.wav` a `en_frase_10.wav`, con su transcripción en `en_frases.tsv`;
  - `en_pausa.wav`: habla, 10 s de silencio y otra vez habla;
  - `en_continuo.wav`: más de 7 s de habla seguida;
  - `es_habla.wav`, `musica.wav` y `silencio.wav`, con licencia libre.
- [X] T008 Escribir `scripts/medir_latencia.py --modelo {small,base}` (depende de T006 y T007). Debe funcionar solo, sin importar `src/traductor`, y hacer lo siguiente:
  - por cada `en_frase_*.wav`, medir la voz a texto con faster-whisper (`beam_size=1`, `condition_on_previous_text=False`, `cpu_threads=4`, `compute_type="int8"`) y la traducción con `ctranslate2.Translator` y `sentencepiece`;
  - sumar 0.6 s fijos por la detección del fin de la frase;
  - imprimir una tabla por etapa y el percentil 90 del total;
  - salir con código 1 si el percentil 90 pasa de 3.0 s.
- [X] T009 Correr `scripts/medir_latencia.py --modelo small` en el equipo de referencia (HP ZBook 15 G1). Si el percentil 90 pasa de 3.0 s, repetir con `--modelo base`. Anotar el resultado y el modelo elegido en `specs/001-traductor-subtitulos-v0/research.md`, en una subsección nueva "Resultado de la medición" dentro de R-12

**Punto de control**: los modelos están en `modelos/` y ya se sabe si se usa `small` o `base`.

---

## Fase 2: Base (prerrequisitos que bloquean todo)

**Propósito**: textos, estados, el contrato de motores, la bitácora y la trazabilidad de tests.

**⚠️ CRÍTICO**: ninguna historia empieza hasta terminar esta fase.

### Tests de la base

- [X] T010 [P] Escribir `tests/conftest.py`. Debe registrar el marcador `spec` y dar estas *fixtures*:
  - `appdata_temporal`, que redirige `APPDATA` y `LOCALAPPDATA` a `tmp_path` con `monkeypatch`;
  - `bloquear_red`, que reemplaza `socket.socket` por una función que lanza `AssertionError("se intentó usar la red")`;
  - `motor_falso`, una implementación de `MotorTraduccion` que devuelve resultados programados o lanza los errores que se le indiquen;
  - `canal_falso`, que registra cuántas veces se inició y se detuvo;
  - `cargar_wav(nombre)`, que devuelve un `numpy.ndarray[float32]` de 16 kHz y mono desde `tests/fixtures/audio/`.
- [X] T011 [P] Escribir `tests/test_trazabilidad.py`. Lee `specs/001-traductor-subtitulos-v0/spec.md` y extrae los identificadores con la expresión `\b(RF-\d{3}[a-z]?|CA-\d{3})\b`. Después recorre con `ast` todos los `tests/**/*.py` y junta los argumentos literales de `pytest.mark.spec(...)`. Falla si pasa cualquiera de estas cosas, y su mensaje nombra los identificadores afectados:
  - un identificador de la spec no tiene test y tampoco está en `tests/solo_manuales.toml`;
  - una entrada de `solo_manuales.toml` no tiene `justificacion`;
  - una entrada de `solo_manuales.toml` nombra un identificador que no existe en la spec.
- [X] T012 [P] Crear `tests/solo_manuales.toml` con la tabla `[CA-003]` y `justificacion = "La parte con 10 personas nuevas, sin instrucciones (quickstart parte B), no se puede automatizar; el test automático de T020 solo comprueba el foco inicial y que la app responde antes de cargar los modelos."`, más `paso_quickstart = "Prueba con personas nuevas"`
- [X] T013 [P] Escribir `tests/unit/test_estado.py`, marcado `spec("RF-004", "RF-002", "RF-003", "RF-005", "RF-015")`. Comprueba lo siguiente:
  - `EstadoTraduccion` empieza en `DESACTIVADA` con `sesion = 0`;
  - activar con los modelos listos lleva a `ACTIVA` y sube `sesion` en 1;
  - activar con los modelos sin cargar lleva a `PREPARANDO`, y luego a `ACTIVA` en cuanto se avisa que los modelos están listos;
  - desactivar desde `PREPARANDO` o desde `ACTIVA` lleva a `DESACTIVADA`;
  - `preparacion_fallida()` desde `PREPARANDO` lleva a `DESACTIVADA`; después de eso, `activar()` deja el estado en `DESACTIVADA` y avisa a los observadores que la preparación falló (para mostrar M-05);
  - `ModoProcesamiento` empieza en `SIN_INTERNET`;
  - un error del motor no cambia el estado.
- [X] T014 [P] Escribir `tests/unit/test_textos.py`, marcado `spec("RF-013", "RF-014")`. Comprueba lo siguiente:
  - están todos los IDs UI-01 a UI-06, D-01, D-02 y M-01 a M-09, con el texto exacto del contrato;
  - ningún mensaje contiene números de error, las palabras "error", "exception", "code" ni "ratón", ni tiene más de 160 caracteres;
  - cada control tiene nombre accesible y no está vacío.
- [X] T014a [P] Escribir `tests/unit/test_bitacora.py`, marcado `spec("RF-013")` (supuesto de la spec sobre la bitácora de diagnóstico, R-13), con la *fixture* `appdata_temporal`. El docstring del módulo explica que la marca RF-013 es la más cercana y que el test cubre el supuesto de la spec sobre la bitácora de diagnóstico, que no tiene identificador propio. Comprueba lo siguiente:
  - `registrar_error("captura", ValueError("hola secreto clave-123"))` crea `%LOCALAPPDATA%\TraductorIngles\errores.log` con una línea que tiene la hora, `captura` y `ValueError`;
  - el archivo **no** contiene el texto de la excepción ("hola", "secreto" ni "clave-123");
  - si la carpeta no existe, se crea;
  - si escribir falla (por ejemplo, la ruta es un archivo de solo lectura o `open` simulado lanza `OSError`), `registrar_error` no lanza nada.

### Implementación de la base

- [X] T015 [P] Crear `src/traductor/textos.py` con los textos del contrato, copiados literalmente de [contracts/interfaz-usuario.md](contracts/interfaz-usuario.md):
  - constantes de texto visible y nombre accesible de UI-01 (sus dos textos: desactivada, y preparando o activa), UI-02 (sus tres textos), UI-03 (sus dos textos), UI-04 (sus dos nombres accesibles), UI-05 (nombre accesible "Mensaje") y UI-06;
  - los textos del menú y los tres del aviso emergente del ícono;
  - los textos de D-01 y D-02;
  - la instrucción del modo de mover: "Usa las flechas para mover los subtítulos. Enter o Esc para terminar.";
  - el diccionario `MENSAJES` con M-01 a M-09.
- [X] T016 [P] Crear `src/traductor/estado.py`, sin dependencias de Qt, con lo siguiente:
  - `class ValorEstado(Enum)` con `DESACTIVADA`, `PREPARANDO` y `ACTIVA`;
  - `class EstadoTraduccion`, con `valor`, `sesion` y los métodos `activar()`, `desactivar()`, `alternar()`, `modelos_listos()` y `preparacion_fallida()`, más la lista de observadores `al_cambiar`. Regla: "Al abrir la app siempre vale `DESACTIVADA`", `sesion` "sube en 1 cada vez que la traducción se activa", y tras `preparacion_fallida()` ya no se puede activar mientras la app siga abierta ([data-model.md §1](data-model.md));
  - `class ModoProcesamiento`, con `valor` (`SIN_INTERNET` o `EN_LINEA`), los métodos `encender_en_linea()` y `volver_sin_internet()` y observadores. Regla: "Al abrir la app siempre vale `SIN_INTERNET`".
- [X] T017 [P] Crear `src/traductor/motores/base.py` con lo siguiente:
  - el `Protocol` `MotorTraduccion`, con `nombre`, `preparar()`, `traducir(frase)` y `cerrar()`, como en [contracts/motor-traduccion.md](contracts/motor-traduccion.md);
  - `@dataclass(frozen=True) Frase`, con `audio: numpy.ndarray[float32]` ("Entre 0.3 s y 7 s de duración"), `t_fin_habla: float` (instante monotónico) y `sesion: int`;
  - `@dataclass(frozen=True) ResultadoMotor`, con `texto_es: str | None`, `motivo_descarte` (enum `NINGUNO`, `OTRO_IDIOMA`, `SIN_VOZ` o `BAJA_CONFIANZA`) y `motor` (enum `LOCAL` o `EN_LINEA`);
  - las excepciones `ErrorPreparacion`, `ErrorConexion`, `ErrorAutenticacion` y `ErrorMotor`.
- [X] T018 [P] Crear `src/traductor/bitacora.py` con `registrar_error(componente: str, exc: BaseException)`. Escribe en `%LOCALAPPDATA%\TraductorIngles\errores.log` solo la hora, el componente y `type(exc).__name__`, **nunca** `str(exc)`, ni audio, ni texto, ni la clave (R-13). Crea la carpeta si no existe y, si escribir falla, no lanza nada.
- [X] T019 Crear `src/traductor/app.py` y `src/traductor/__main__.py` (depende de T015 a T018). Deben dar lo siguiente:
  - `main()`, que crea el `QApplication` y el `EstadoTraduccion`;
  - la clase `Controlador`, que recibe una `fabrica_canal` (un objeto con `iniciar(sesion)` y `detener()`), la inicia al pasar a `ACTIVA` y la detiene al pasar a `DESACTIVADA`;
  - la carga en segundo plano con `QThreadPool` al abrir la app, que recibe una función de preparación. Al terminar, llama a `estado.modelos_listos()`; si recibe `ErrorPreparacion`, llama a `estado.preparacion_fallida()`, publica M-05 (fijo) y lo registra en la bitácora.
  - la clase `CanalNulo` en `app.py`, con `iniciar(sesion)` y `detener()` que no hacen nada. Es la `fabrica_canal` por defecto hasta T050, para que `python -m traductor` arranque en la fase 3 sin audio ni modelos; T050 la quita. En los tests se usa la *fixture* `canal_falso`, que se le pasa al `Controlador`.
  - Mientras `CanalNulo` sea el canal, la carga en segundo plano solo llama a `estado.modelos_listos()` (todavía no hay motores reales); T050 la cambia a `MotorLocal.preparar()`.

**Punto de control**: `pytest tests/unit/test_estado.py tests/unit/test_textos.py tests/unit/test_bitacora.py` pasa. `test_trazabilidad.py` falla y lista los RF y CA que todavía no tienen test, lo cual es lo esperado.

---

## Fase 3: Historia 4 — Activar y desactivar rápido, solo cuando la persona lo decide (P1) 🎯 MVP, parte 1

**Meta**: ventana principal, ícono del área de notificación, atajo Ctrl+Alt+T, cerrar y minimizar.
En esta fase se trabaja con `CanalNulo` (en la app) y `canal_falso` (en los tests), sin audio real.

**Prueba independiente**: abrir la app con `python -m traductor`, ver "Traducción desactivada",
activar y desactivar con clic, con Enter, desde el menú del ícono y con Ctrl+Alt+T desde otra
ventana, y cerrar con la X.

### Tests de la Historia 4 ⚠️ (escribir primero; deben fallar)

- [X] T020 [P] [US4] Escribir `tests/ui/test_ventana.py`, marcado `spec("RF-002", "RF-003", "RF-005", "RF-014", "RF-016", "CA-003", "CA-010", "CA-016")`. Comprueba lo siguiente:
  - UI-01 muestra "Activar traducción" con "Ctrl+Alt+T" visible y el nombre accesible del contrato, y al activar cambia a "Desactivar traducción", tanto en `PREPARANDO` como en `ACTIVA`;
  - UI-02 dice "Traducción desactivada", "Preparando la traducción…" o "Traducción activa" según el estado;
  - con la traducción activa, UI-01 y UI-02 cambian de texto **y** de color;
  - el foco inicial está en UI-01, y presionar Enter recién abierta la app la activa;
  - se activa y desactiva **solo con mouse** (`qtbot.mouseClick`) y **solo con teclado** (`qtbot.keyClick` con Espacio y con Enter);
  - la letra mide 16 px o más y el contraste del texto con el fondo es de 4.5:1 o más;
  - la ventana se muestra y acepta clics antes de que terminen de cargar los modelos (usar un motor falso que tarda 30 s en `preparar`).
- [X] T021 [P] [US4] Escribir `tests/ui/test_mensajes.py`, marcado `spec("RF-013", "RF-005")`. Comprueba lo siguiente:
  - UI-05 muestra el texto de `MENSAJES` y se vacía a los 10 s (con el reloj simulado) o cuando cambia el estado;
  - M-05 no se vacía ni a los 10 s ni al cambiar el estado: con un motor falso cuyo `preparar` lanza `ErrorPreparacion` y la traducción activada (en `PREPARANDO`), UI-02 pasa a "Traducción desactivada", UI-05 muestra M-05 y, al activar otra vez, UI-02 sigue en "Traducción desactivada" y M-05 sigue visible;
  - con M-05 visible, `mostrar_mensaje("M-08")` muestra M-08 en UI-05 (RF-015c), y a los 10 s (con el reloj simulado) UI-05 vuelve a mostrar M-05; un cambio de estado durante esos 10 s también regresa a M-05;
  - mostrar un mensaje no le quita el foco a otra ventana.
- [X] T022 [P] [US4] Escribir `tests/ui/test_bandeja.py`, marcado `spec("RF-001", "RF-002", "RF-003", "RF-005", "RF-004a", "RF-014")`. Comprueba lo siguiente:
  - el aviso emergente dice "TraductorIngles: traducción desactivada", "TraductorIngles: preparando la traducción" o "TraductorIngles: traducción activa" según el estado;
  - el menú tiene, en este orden, "Activar traducción" (desactivada) o "Desactivar traducción" (preparando o activa), "Abrir TraductorIngles" y "Salir";
  - en `PREPARANDO`, la opción 1 lleva a `DESACTIVADA`;
  - con `preparar` falso que lanza `ErrorPreparacion` y la ventana minimizada: al fallar, y luego al activar con la opción 1 del menú y con el atajo simulado, se llama a `showMessage` con el título "TraductorIngles" y el texto de M-05, y no se activa ninguna ventana; sin la falla, `showMessage` nunca se llama;
  - la opción 1 alterna el estado;
  - un clic izquierdo y "Abrir TraductorIngles" muestran la ventana;
  - "Salir" ejecuta el cierre ordenado;
  - con teclado (contrato §4), simulando las señales que manda Windows: `activated(QSystemTrayIcon.Trigger)` (Enter sobre el ícono) muestra la ventana, `activated(QSystemTrayIcon.Context)` (tecla Menú o Mayús+F10) abre el menú, y en el menú abierto las flechas y Enter eligen cada una de las 3 opciones.
- [X] T023 [P] [US4] Escribir `tests/ui/test_atajo.py`, marcado `spec("RF-016", "RF-016a", "CA-014")`, con `RegisterHotKey` y `UnregisterHotKey` simulados. Comprueba lo siguiente:
  - se registra con `MOD_CONTROL | MOD_ALT | MOD_NOREPEAT` (`0x0001 | 0x0002 | 0x4000`) y la tecla `0x54` (`T`);
  - cada `WM_HOTKEY` (`0x0312`) alterna el estado en menos de 1 s sin activar la ventana principal;
  - si `RegisterHotKey` devuelve 0 con `GetLastError() == 1409`, UI-05 muestra M-06 y UI-01 y el menú del ícono siguen alternando el estado.
- [X] T024 [P] [US4] Escribir `tests/ui/test_cierre.py`, marcado `spec("RF-004a", "CA-015")`. Comprueba lo siguiente:
  - con la traducción activa, `close()` de la ventana y Alt+F4 dejan el estado en `DESACTIVADA`, llaman a `canal.detener()`, ocultan el ícono, llaman a `UnregisterHotKey`, llaman a `cerrar()` de los motores y a `QApplication.quit`, en ese orden y en menos de 1 s;
  - minimizar (`showMinimized`) no cambia el estado ni detiene el canal.
- [X] T025 [P] [US4] Escribir `tests/unit/test_activacion_bajo_demanda.py`, marcado `spec("RF-004", "CA-007")`, con el `canal_falso`. Comprueba lo siguiente:
  - abrir la app y no activar nada durante 60 s simulados no inicia el canal;
  - activar lo inicia con la `sesion` nueva y desactivar lo detiene;
  - `main()` no registra ningún arranque automático: no escribe en la clave `Run` del registro ni en la carpeta Inicio.

### Implementación de la Historia 4

- [X] T026 [P] [US4] Crear `src/traductor/ui/ventana.py` con `VentanaPrincipal(QWidget)`, título "TraductorIngles" e ícono `recursos/icono.ico`:
  - UI-01 es un `QPushButton` con el texto y el atajo de `textos.py`, `setAccessibleName` y la señal `alternar_solicitado`;
  - UI-02 es un `QLabel` de solo lectura con el nombre accesible igual a su texto;
  - UI-05 es un `QLabel` con el nombre accesible "Mensaje" y el método `mostrar_mensaje(id)`, que borra el texto con un `QTimer` de 10 s o con el siguiente cambio de estado, salvo M-05, que se queda fijo: si otro mensaje sale mientras M-05 está fijo, se muestra su tiempo normal y al borrarse UI-05 vuelve a M-05 (contrato §6);
  - los colores por estado siguen la regla "cambian de texto **y** de color", con letra de 16 px o más y contraste de 4.5:1 o más;
  - el foco inicial está en UI-01;
  - `closeEvent` llama al cierre ordenado del `Controlador`, y minimizar no hace nada.
- [X] T027 [P] [US4] Crear `src/traductor/ui/bandeja.py` con `Bandeja(QSystemTrayIcon)`. Tiene el aviso emergente de `textos.py`, el menú de 3 opciones del contrato §4, el clic izquierdo (`QSystemTrayIcon.Trigger`) que muestra la ventana, la señal `salir_solicitado` y el método `avisar(id_mensaje)`, que llama a `showMessage("TraductorIngles", MENSAJES[id_mensaje])`; un clic en el aviso (`messageClicked`) muestra la ventana.
- [X] T028 [P] [US4] Crear `src/traductor/ui/atajo.py` con lo siguiente:
  - `AtajoGlobal(QAbstractNativeEventFilter)`, que llama a `RegisterHotKey(hwnd_ventana, ID_ATAJO, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, 0x54)` por `ctypes`;
  - `registrar() -> bool`, que devuelve `False` si `GetLastError() == 1409`;
  - `nativeEventFilter`, que emite `presionado` cuando llega `WM_HOTKEY` (`0x0312`) con `ID_ATAJO`;
  - `liberar()`, que llama a `UnregisterHotKey` y se puede llamar más de una vez.
- [X] T029 [US4] Conectar en `src/traductor/app.py` la ventana, la bandeja y el atajo con el `Controlador` (depende de T026 a T028):
  - UI-01, la opción 1 del menú y el atajo llaman a `estado.alternar()`;
  - los observadores del estado actualizan UI-01, UI-02 y el aviso emergente;
  - si `registrar()` devuelve `False`, se muestra M-06;
  - cada vez que se publica M-05 por una falla de preparación (al fallar y en cada intento de activar después), además de UI-05 se llama a `bandeja.avisar("M-05")` (RF-005, contrato §4);
  - `cerrar_app()` sigue el orden de [data-model.md §10](data-model.md): `EstadoTraduccion → DESACTIVADA` → ocultar el ícono → `liberar()` → cerrar los motores → `QApplication.quit` (la franja todavía no existe; T050 agrega ocultarla en este mismo paso);
  - "Salir" del menú llama a `cerrar_app()`.
- [X] T030 [US4] Correr `pytest tests/unit tests/ui -m "not modelos"` y corregir hasta que todos los tests de T020 a T025 pasen

**Punto de control**: la Historia 4 funciona con el canal falso: la app se activa, se desactiva y se cierra con mouse, con teclado y con el atajo.

---

## Fase 4: Historia 1 — Subtítulos en español durante una llamada en inglés (P1) 🎯 MVP, parte 2

**Meta**: captura WASAPI loopback, segmentador, motor local, glosario es-MX y franja de subtítulos,
que se mueve con el mouse y con el teclado. Todo funciona sin internet.

**Prueba independiente**: con una llamada o un video en inglés sonando, activar la app y ver
subtítulos en español de México encima de la ventana de la llamada (quickstart B3 a B5 y B8).

### Tests de la Historia 1 ⚠️ (escribir primero; deben fallar)

- [X] T031 [P] [US1] Escribir `tests/unit/test_captura.py`, marcado `spec("RF-004", "RF-006", "RF-010", "RF-011", "CA-008", "CA-009")`, con `pyaudiowpatch` simulado. Comprueba lo siguiente:
  - solo se abre el dispositivo *loopback* de la salida predeterminada, nunca un dispositivo de entrada o micrófono, y nunca en modo exclusivo;
  - no se abre nada antes de `iniciar()`, y `detener()` cierra el *stream*;
  - el audio de 48 kHz estéreo (int16 o float32) sale como `FragmentoAudio` de 16 kHz, mono, float32 y con valores entre -1.0 y 1.0;
  - una lectura sin datos dentro del tiempo límite se entrega como silencio, no como error;
  - si la salida predeterminada cambia (revisión cada 2 s, con el reloj simulado), se reabre el *loopback* del nuevo dispositivo sin cambiar el `EstadoTraduccion`;
  - sin dispositivo de salida se emite M-02, y una lectura que falla se emite como M-03;
  - con `pycaw` simulado: si la salida está silenciada (`GetMute() == 1`) o en 0 (`GetMasterVolumeLevelScalar() == 0.0`), los fragmentos salen como silencio y no se produce ninguna frase; al quitar el silencio o subir el volumen (revisión cada 0.5 s), vuelve a salir el audio; si leer el volumen lanza una excepción, el audio sale normal y no se muestra mensaje;
  - nunca se llama a un método que **cambie** el volumen o la reproducción (`SetMute`, `SetMasterVolumeLevel*` ni similares); solo se usan `GetMute` y `GetMasterVolumeLevelScalar`.
- [X] T032 [P] [US1] Escribir `tests/unit/test_segmentador.py`, marcado `spec("RF-012")`, con probabilidades de voz simuladas en ventanas de 512 muestras. Comprueba lo siguiente:
  - una frase empieza cuando la probabilidad pasa de 0.5;
  - la frase termina tras 0.6 s de silencio, con `t_fin_habla` al final de la voz;
  - se corta a la fuerza a los 7 s;
  - se descartan las frases de menos de 0.3 s;
  - el silencio y el ruido con probabilidad menor de 0.5 no producen frases;
  - cada `Frase` lleva la `sesion` con la que se creó;
  - `voz_detectada()` se llama mientras hay voz, como máximo una vez cada 0.5 s, y nunca con silencio o ruido de probabilidad menor de 0.5.
- [X] T033 [P] [US1] Escribir `tests/unit/test_glosario.py`, marcado `spec("RF-007")`. Comprueba lo siguiente:
  - los pares iniciales de R-06 se reemplazan por palabra o frase completa respetando mayúsculas: ordenador→computadora, coche→carro, coches→carros, zumo→jugo, gafas→lentes, vosotros→ustedes, teléfono móvil→celular y el móvil→el celular ("Ordenador" pasa a "Computadora");
  - las coincidencias dentro de otra palabra no se tocan ("cocheras" se queda igual);
  - las palabras con varios sentidos no se tocan: "vale la pena", "vale 10 pesos", "dispositivo móvil" y "conducir una reunión" se quedan igual;
  - si dos entradas coinciden, gana la más larga ("teléfono móvil" pasa a "celular", no a "teléfono celular");
  - aplicar el glosario dos veces da el mismo resultado (idempotente);
  - si `glosario_es_mx.tsv` trae una fila mal formada, esa fila se ignora.
- [X] T034 [P] [US1] Escribir `tests/unit/test_motor_local.py`, marcado `spec("RF-007", "RF-012", "RF-015", "CA-011")`, con `WhisperModel` y `ctranslate2.Translator` simulados. Comprueba lo siguiente:
  - si `language != "en"` o `language_probability < 0.6`, devuelve `texto_es=None` con `OTRO_IDIOMA`;
  - si `no_speech_prob > 0.6`, devuelve `SIN_VOZ`, y si `avg_logprob < -1.0`, devuelve `BAJA_CONFIANZA`;
  - si todo está bien, devuelve el texto traducido con `motor=LOCAL`;
  - con la *fixture* `bloquear_red` activa, `traducir` funciona sin intentar abrir un *socket*;
  - una excepción interna se convierte en `ErrorMotor`.
- [X] T035 [P] [US1] Escribir `tests/unit/test_selector_local.py`, marcado `spec("RF-013", "RF-015")`. Comprueba lo siguiente:
  - con el modo `SIN_INTERNET`, `SelectorMotor.traducir` nunca llama a `en_linea_factory`;
  - un `ErrorMotor` del motor local emite `error_motor` y la siguiente frase se traduce normalmente.
- [X] T036 [P] [US1] Escribir `tests/unit/test_canal.py`, marcado `spec("CA-004", "RF-013")`, con captura, segmentador y motor falsos. Comprueba lo siguiente:
  - las colas tienen tamaño límite y, si se llenan, se descarta la frase más vieja;
  - un resultado de una `sesion` anterior no se muestra;
  - `detener()` vacía las colas y regresa en menos de 1 s, aunque el motor esté a mitad de una frase;
  - un `ErrorMotor` no cambia el estado y emite M-04.
- [X] T037 [P] [US1] Escribir `tests/ui/test_franja.py`, marcado `spec("RF-008", "RF-009", "RF-012", "CA-004", "CA-006", "CA-016")`. Comprueba lo siguiente:
  - la franja tiene las banderas `FramelessWindowHint`, `WindowStaysOnTopHint` y `Tool`, más `WA_ShowWithoutActivating`, y mostrarla no le quita el foco a otra ventana;
  - la posición inicial está centrada horizontalmente, a 10 % del borde inferior de la pantalla principal;
  - el texto es blanco sobre negro al 75 % de opacidad, con letra de 28 px;
  - se ven como máximo 2 líneas; un texto más largo se divide en bloques de hasta 2 líneas que se muestran uno tras otro, y el último se queda;
  - con el reloj simulado, cada bloque que no es el último dura `clamp(caracteres / 15, 1.5, 4.0)` segundos (un bloque de 15 caracteres dura 1.5 s, uno de 45 dura 3 s y uno de 90 dura 4 s), y un subtítulo nuevo descarta los bloques que falten;
  - un subtítulo nuevo reemplaza al anterior;
  - la franja se vacía 4 s después de lo último que ocurra entre la aparición del último bloque y `marcar_voz()` (con el reloj simulado): sin voz, un subtítulo de un solo bloque se vacía a los 4 s de mostrarse; si `marcar_voz()` llega a los 3 s, se vacía a los 7 s; un subtítulo de 3 bloques cuyos dos primeros duran 4 s cada uno muestra los 3 bloques y se vacía a los 12 s (8 s de bloques + 4 s);
  - `ocultar_ya()` la oculta en menos de 1 s;
  - un `Subtitulo` con una `sesion` distinta de la actual se ignora;
  - se arrastra con el botón izquierdo del mouse (`qtbot.mousePress`, `mouseMove` y `mouseRelease`) y nunca sale por completo de la pantalla.
- [X] T038 [P] [US1] Escribir `tests/ui/test_mover_franja.py`, marcado `spec("RF-009", "RF-014", "CA-010", "CA-016")`. Comprueba lo siguiente:
  - UI-06 dice "Mover subtítulos", su nombre accesible es "Mover subtítulos con las flechas" y es el último control del orden de tabulación, después de UI-01 (la prueba no supone qué hay entre los dos, para que siga valiendo cuando T069 agregue UI-04);
  - un clic **o** Enter en UI-06 entra al modo de mover: la franja se muestra aunque no haya subtítulo o la traducción esté desactivada, recibe el foco, tiene un borde amarillo de 3 px y muestra la instrucción de `textos.py`;
  - las flechas la mueven 20 px y Mayús + flecha, 100 px;
  - con la franja junto a cada borde de la pantalla, seguir presionando la flecha (o Mayús + flecha) hacia ese borde no la saca por completo de la pantalla;
  - Enter o Esc terminan el modo: se quita el resaltado, la franja deja de aceptar el foco y el foco vuelve a UI-06; si no hay subtítulo vigente, la franja se oculta;
  - si la franja pierde el foco, el modo termina igual que con Esc;
  - durante el modo también se puede arrastrar con el mouse;
  - la posición no se guarda en disco.
- [X] T039 [P] [US1] Escribir `tests/integration/test_flujo_sin_internet.py`, con las marcas `modelos` y `spec("RF-006", "RF-007", "RF-012", "RF-015", "CA-001", "CA-002", "CA-011")`. Usa la *fixture* `bloquear_red` en toda la prueba y alimenta el canal real con `en_frase_*.wav` en lugar de la captura. Comprueba lo siguiente:
  - cada frase en inglés produce un subtítulo no vacío en español, ya con el glosario aplicado;
  - el percentil 90 del tiempo entre `t_fin_habla` y el momento en que se muestra es de 3.0 s o menos;
  - `es_habla.wav`, `musica.wav` y `silencio.wav` no producen subtítulos.

### Implementación de la Historia 1

- [X] T040 [P] [US1] Crear `src/traductor/audio/captura.py`. Tiene `@dataclass FragmentoAudio(muestras: numpy.ndarray[float32], t_inicio: float)` ("16 kHz, mono, valores entre -1.0 y 1.0") y la clase `CapturaLoopback`, con `iniciar(cola)` y `detener()`. Su comportamiento:
  - usa `pyaudiowpatch.PyAudio().get_default_wasapi_loopback()` en modo compartido;
  - remuestrea con `soxr.resample` a 16 kHz y convierte a mono;
  - lee con tiempo límite y trata la falta de datos como silencio;
  - revisa el dispositivo predeterminado cada 2 s, y también cuando una lectura falla, para reabrirlo si cambió;
  - emite M-02 si no hay salida y M-03 si la lectura falla;
  - cada 0.5 s, y al cambiar de dispositivo, **lee** con `pycaw` el silencio y el volumen maestro de la salida predeterminada; si está silenciada o en 0, entrega silencio; si la lectura falla, supone que suena (R-02);
  - nunca abre un dispositivo de entrada ni cambia el volumen.
- [X] T041 [P] [US1] Crear `src/traductor/audio/segmentador.py` con la clase `Segmentador`, que usa el Silero VAD (ONNX) incluido en `faster_whisper.vad`:
  - procesa ventanas de 512 muestras;
  - una frase empieza cuando la probabilidad pasa de 0.5;
  - la frase termina con 0.6 s de silencio, o a los 7 s como máximo;
  - descarta las frases de menos de 0.3 s;
  - produce `Frase(audio, t_fin_habla, sesion)`;
  - llama a un callback `voz_detectada()` como máximo una vez cada 0.5 s mientras la probabilidad pase de 0.5 (para la regla de 4 s sin habla de RF-012).
- [X] T042 [P] [US1] Crear `src/traductor/traduccion/glosario.py` y `src/traductor/recursos/glosario_es_mx.tsv`:
  - la clase `Glosario` carga el TSV (`origen<TAB>reemplazo`, una fila por par; `origen` puede ser una frase de varias palabras) y su método `aplicar(texto)` reemplaza por palabra o frase completa con `\b`, probando primero las entradas más largas, sin distinguir mayúsculas al buscar y conservando las del original;
  - el TSV empieza con los 8 pares iniciales de R-06 y sigue la regla de "un solo sentido" de R-06.
- [X] T043 [P] [US1] Crear `src/traductor/motores/local.py` con la clase `MotorLocal(MotorTraduccion)`, cuyo `nombre` es `"LOCAL"`:
  - `preparar()` carga `WhisperModel(modelos/whisper-<modelo elegido en T009>, device="cpu", compute_type="int8", cpu_threads=4)` y `ctranslate2.Translator(modelos/opus-mt-en-es-ct2, inter_threads=1, intra_threads=4)` con `sentencepiece`;
  - `traducir()` usa `beam_size=1` y aplica los descartes de la tabla del contrato §2. Por la medición de T009 (research R-12), Whisper se llama en **una sola pasada** del codificador (`encode`, `detect_language` y `generate` sobre la misma salida), con el modelo `base`;
  - `cerrar()` es idempotente;
  - la ruta de `modelos/` se resuelve junto al ejecutable cuando la app está empaquetada (`sys.frozen`) o en la raíz del repositorio durante el desarrollo.
- [X] T044 [US1] Crear `src/traductor/motores/selector.py` con la clase `SelectorMotor(local, en_linea_factory)` y los métodos `traducir(frase)` y `usar_local()`. Sus eventos son callbacks: `error_motor`, `conexion_perdida` y `cuenta_rechazada`. Por ahora solo se implementa el camino del modo `SIN_INTERNET` (contrato §4, puntos 3 y 4); el camino en línea llega en T067.
- [X] T045 [P] [US1] Crear `src/traductor/ui/subtitulos.py` con lo siguiente:
  - `@dataclass Subtitulo(texto: str, sesion: int, mostrado_en: float)`, donde `texto` "no [es] vacío";
  - la clase `FranjaSubtitulos(QWidget)`, con las banderas y el estilo de T037, división en bloques de hasta 2 líneas según el ancho, con la duración por bloque del contrato §2 ("Texto largo"), un temporizador de 4 s que arranca cuando aparece el último bloque, se reinicia con `marcar_voz()` y no corre mientras queden bloques por mostrar, y `ocultar_ya()`;
  - arrastre con `mousePressEvent` y `mouseMoveEvent`, limitado a la geometría de la pantalla;
  - un `QTimer` de 2 s que vuelve a fijar `HWND_TOPMOST` con `SetWindowPos(..., SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)` por `ctypes`.
- [X] T046 [US1] Agregar el modo de mover en `src/traductor/ui/subtitulos.py` (depende de T045):
  - `entrar_modo_mover()` quita temporalmente `WA_ShowWithoutActivating`, activa la franja, pone el borde amarillo de 3 px y la instrucción;
  - `keyPressEvent` mueve la franja con las flechas (20 px, o 100 px con Mayús), con el mismo límite a la geometría de la pantalla que el arrastre de T045, y termina con Enter o Esc;
  - `focusOutEvent` termina el modo;
  - al terminar, emite `modo_mover_terminado` y se oculta si no hay subtítulo vigente.
- [X] T047 [US1] Agregar UI-06 en `src/traductor/ui/ventana.py`: un `QPushButton` "Mover subtítulos" con su nombre accesible y la señal `mover_solicitado`. El orden de tabulación es UI-01 → UI-06, y al recibir `modo_mover_terminado` el foco vuelve a UI-06.
- [X] T048 [US1] **Antes de T049** (debe fallar mientras no exista `canal.py`): escribir `tests/unit/test_flujo_datos.py`, marcado `spec("RF-008")`. Con el `Canal` y motores falsos, un `ResultadoMotor` con el texto "Me gusta el coche" llega a la franja como "Me gusta el carro".
- [X] T049 [US1] Crear `src/traductor/canal.py` con la clase `Canal` (depende de T040 a T044 y de que T048 ya esté escrito). Arma el flujo de datos de [data-model.md](data-model.md). Su comportamiento:
  - `iniciar(sesion)` arranca hilos para la captura, el segmentador y el selector, unidos por `queue.Queue(maxsize=…)`; si una cola se llena, se descarta la frase más vieja;
  - cada `ResultadoMotor` con texto pasa por `Glosario.aplicar()` y se convierte en un `Subtitulo`, que se entrega al hilo de Qt con una señal;
  - el callback `voz_detectada()` del segmentador se entrega al hilo de Qt con la señal `voz`, que `app.py` conecta con `FranjaSubtitulos.marcar_voz()` (T050);
  - `detener()` cierra la captura, vacía las colas y regresa en menos de 1 s;
  - un error se publica como mensaje y se registra con `bitacora.registrar_error`, sin cambiar el estado.
- [X] T050 [US1] Conectar en `src/traductor/app.py` el `Canal` real en lugar de `CanalNulo`, y borrar `CanalNulo`:
  - la carga en segundo plano llama a `MotorLocal.preparar()`;
  - el `Subtitulo` va a `FranjaSubtitulos.mostrar` con la `sesion` actual, y la señal `voz` del `Canal` va a `FranjaSubtitulos.marcar_voz()`;
  - al pasar a `DESACTIVADA` se llama a `ocultar_ya()`;
  - UI-06 se conecta con `entrar_modo_mover()`;
  - los errores se convierten en M-02 a M-05 en UI-05;
  - `cerrar_app()` también oculta la franja, junto con el ícono (orden de [data-model.md §10](data-model.md)).
- [X] T051 [US1] Correr `pytest` (incluidos los tests con la marca `modelos`) y corregir hasta que pasen todos los tests de T031 a T039 y T048

**Punto de control**: el MVP (Historias 4 y 1) funciona sin internet. Se valida a mano con los pasos B1 a B8, B10 a B13a, B14 y B15 del [quickstart](quickstart.md).

---

## Fase 5: Historia 2 — Subtítulos en español de un video en inglés (P2)

**Meta**: confirmar que la pausa, la reanudación y la pantalla completa funcionan. No se espera
código nuevo.

**Prueba independiente**: reproducir un video en inglés en el navegador con la traducción activa,
pausarlo, reanudarlo y ponerlo en pantalla completa (quickstart B6 y B7).

- [X] T052 [P] [US2] Escribir `tests/integration/test_fuente_video.py`, con las marcas `modelos` y `spec("RF-012", "CA-005")`. Alimenta el canal con `en_pausa.wav` y el reloj real, y comprueba lo siguiente:
  - en la pausa de 10 s el último subtítulo desaparece 4 s después de que aparece su último bloque (no hay voz que reinicie el temporizador) y no sale ninguno nuevo;
  - al volver el habla, aparecen subtítulos otra vez.
- [X] T053 [P] [US2] Escribir `tests/ui/test_pantalla_completa.py`, marcado `spec("CA-006", "RF-008")`. Comprueba lo siguiente:
  - con una ventana de prueba sin bordes, a pantalla completa y con el foco, mostrar la franja no le quita el foco a esa ventana;
  - el temporizador de 2 s llama a `SetWindowPos` (simulado) con `HWND_TOPMOST` y `SWP_NOACTIVATE`.
- [X] T054 [US2] Si T052 o T053 fallan, corregir en `src/traductor/ui/subtitulos.py` o `src/traductor/audio/segmentador.py` sin agregar comportamiento nuevo, y volver a correrlos

**Punto de control**: las Historias 4, 1 y 2 funcionan. Se valida a mano con los pasos B6 y B7.

---

## Fase 6: Historia 3 — Subtítulos en español de un audio en inglés (P3)

**Meta**: confirmar que el audio largo y continuo, como un podcast, también se traduce.

**Prueba independiente**: reproducir un podcast en inglés en un reproductor de escritorio con la
traducción activa (quickstart B9).

- [X] T055 [P] [US3] Escribir `tests/integration/test_fuente_audio.py`, con las marcas `modelos` y `spec("CA-005", "RF-006")`. Alimenta el canal con `en_continuo.wav` (más de 7 s de habla) y comprueba que se producen al menos 2 subtítulos, gracias al corte a los 7 s, y que el percentil 90 del tiempo desde su `t_fin_habla` es de 3.0 s o menos (CA-002).
- [X] T056 [US3] Si T055 falla, corregir en `src/traductor/audio/segmentador.py` o `src/traductor/canal.py` sin agregar comportamiento nuevo, y volver a correrlo

**Punto de control**: las cuatro historias funcionan sin internet. Se valida a mano con el paso B9.

---

## Fase 7: Modo en línea opcional (transversal: RF-015a, RF-015b, RF-015c, CA-012, CA-013)

**Meta**: interruptor UI-04, indicador UI-03, aviso D-01, cuadro de la cuenta D-02, cuenta cifrada
con DPAPI, motor Azure y regreso automático al motor local.

**Prueba independiente**: pasos B16 a B19 del quickstart: encender el modo, aceptar el aviso,
probar una clave inválida y luego una válida, apagar el wifi y reiniciar la app.

### Tests del modo en línea ⚠️ (escribir primero; deben fallar)

- [X] T057 [P] Escribir `tests/unit/test_ajustes.py`, marcado `spec("RF-015a")`, con la *fixture* `appdata_temporal`. Comprueba lo siguiente:
  - sin archivo, `aviso_en_linea_aceptado` vale `false`;
  - guardar `true` y volver a cargar da `true`;
  - un `ajustes.json` dañado da los valores por defecto sin lanzar nada ni mostrar mensaje;
  - el archivo solo contiene la llave `aviso_en_linea_aceptado`.
- [X] T058 [P] Escribir `tests/unit/test_cuenta.py`, marcado `spec("RF-015a", "RF-015c")`, con `appdata_temporal` y `urllib.request.urlopen` simulado. Comprueba lo siguiente:
  - guardar y cargar con DPAPI real devuelve la misma clave y región;
  - `cuenta_en_linea.bin` no contiene la clave en texto plano;
  - la región se normaliza a minúsculas y sin espacios, y una clave o región vacía no se acepta;
  - la validación hace `POST https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken` con el encabezado `Ocp-Apim-Subscription-Key` y `timeout=5`;
  - una respuesta 200 da `VALIDA`; 401, 403 o una región inexistente dan `INVALIDA`; `URLError` o tiempo agotado dan `SIN_RED`;
  - `borrar()` elimina el archivo;
  - la clave nunca aparece en `errores.log`.
- [X] T059 [P] Escribir `tests/unit/test_motor_en_linea.py`, marcado `spec("RF-015a", "RF-015b", "RF-015c", "RF-004")`, con `azure.cognitiveservices.speech` simulado. Comprueba lo siguiente:
  - la configuración usa `speech_recognition_language="en-US"` y `add_target_language("es")`;
  - el audio entra por un `PushAudioInputStream` de 16 kHz, mono y 16 bits, y solo con frases de la sesión activa;
  - un `canceled` por error de red, una desconexión o 10 s sin respuesta lanzan `ErrorConexion`;
  - un `canceled` por autenticación lanza `ErrorAutenticacion`.
- [X] T060 [P] Escribir `tests/unit/test_selector_en_linea.py`, marcado `spec("RF-015b", "RF-015c", "CA-013")`. Comprueba lo siguiente:
  - con el modo `EN_LINEA`, un `ErrorConexion` cierra el motor en línea, traduce **la misma frase** con el motor local, emite `conexion_perdida` y no cambia el `EstadoTraduccion`;
  - un `ErrorAutenticacion` hace lo mismo pero emite `cuenta_rechazada`;
  - si `usar_en_linea()` recibe `ErrorPreparacion`, el modo sigue en `SIN_INTERNET`;
  - el motor local nunca se cierra mientras el modo en línea está activo.
- [X] T061 [P] Escribir `tests/ui/test_modo_en_linea.py`, marcado `spec("RF-015a", "RF-015c", "RF-014", "CA-010", "CA-012", "CA-016")`, con la validación de la cuenta simulada. Comprueba lo siguiente:
  - al abrir, UI-03 dice "Sin internet" y UI-04 está apagado con el nombre accesible "Modo en línea, apagado";
  - el orden de tabulación es UI-01 → UI-04 → UI-06;
  - D-01 sale al encender UI-04 con el foco en "No, seguir sin internet"; "No", Esc o cerrarlo dejan `SIN_INTERNET`, y el aviso sale otra vez la siguiente vez;
  - "Sí, usar en línea" guarda `aviso_en_linea_aceptado` y abre D-02;
  - en D-02, la clave usa `QLineEdit.Password`, "Guardar y activar" solo se habilita con los dos campos llenos y muestra "Comprobando…" mientras valida;
  - en D-02, Cancelar o Esc dejan `SIN_INTERNET` sin mensaje; una cuenta inválida muestra M-08 y no guarda; sin red se muestra M-09 y no se guarda; en los tres casos (y al decir "No" en D-01), UI-04 queda apagado con el nombre accesible "Modo en línea, apagado";
  - con una cuenta válida, UI-03 dice "En línea: el audio sale del equipo" con un color de aviso distinto;
  - apagar UI-04 regresa a "Sin internet" con una sola acción;
  - después de cancelar D-02 o de una cuenta inválida, al volver a encender UI-04 ya no sale D-01 pero sí sale D-02 otra vez;
  - al volver a encender, ya no sale D-01, y con la cuenta guardada tampoco sale D-02;
  - al simular que se reinicia la app, empieza otra vez en "Sin internet";
  - se puede recorrer todo **solo con mouse** y **solo con teclado** (Tab y Espacio en UI-04, Tab y Enter en los cuadros).
- [X] T062 [P] Escribir `tests/ui/test_respaldo_en_linea.py`, marcado `spec("RF-015b", "RF-015c", "CA-013")`, con motores falsos. Comprueba lo siguiente:
  - con el modo `EN_LINEA` y la traducción activa, `conexion_perdida` muestra M-07, cambia UI-03 y UI-04 a "Sin internet" y los subtítulos siguen saliendo sin reactivar nada;
  - `cuenta_rechazada` muestra M-08 y borra `cuenta_en_linea.bin`.

### Implementación del modo en línea

- [X] T063 [P] Crear `src/traductor/ajustes.py` con la clase `Ajustes`, que tiene un solo campo, `aviso_en_linea_aceptado: bool = False`, y los métodos `cargar()` y `guardar()`. Usa el archivo `%APPDATA%\TraductorIngles\ajustes.json`, con escritura atómica (archivo temporal y `os.replace`); "Si el archivo no existe o está dañado, se usan los valores por defecto sin mostrar ningún error".
- [X] T064 [P] Crear `src/traductor/cuenta.py` con lo siguiente:
  - `@dataclass CuentaEnLinea(clave: str, region: str)`, donde la clave es "No vacía" y la región "No vacía, en minúsculas y sin espacios";
  - `guardar()`, `cargar() -> CuentaEnLinea | None` y `borrar()`, que usan `CryptProtectData` y `CryptUnprotectData` por `ctypes` (alcance del usuario actual) sobre el JSON `{"clave": …, "region": …}` en `%APPDATA%\TraductorIngles\cuenta_en_linea.bin`;
  - `validar(cuenta) -> ResultadoValidacion` (`VALIDA`, `INVALIDA` o `SIN_RED`), según R-14, con `urllib` y `timeout=5`;
  - la clave nunca se registra en la bitácora.
- [X] T065 [P] Crear `src/traductor/recursos/regiones_azure.txt` con las regiones de Azure AI Speech que admiten Speech Translation, una por línea, en minúsculas (por ejemplo `southcentralus`, `eastus`, `westus2`, `westeurope`).
- [X] T066 [P] Crear `src/traductor/motores/en_linea.py` con la clase `MotorEnLinea(MotorTraduccion)`, cuyo `nombre` es `"EN_LINEA"`. Se construye con una `CuentaEnLinea`:
  - `preparar()` crea `SpeechTranslationConfig(subscription=clave, region=region)` y un `TranslationRecognizer` con `PushAudioInputStream` de 16 kHz, mono y 16 bits;
  - `traducir(frase)` convierte la frase a PCM int16, la empuja al *stream* y espera el resultado `es` con 10 s como máximo;
  - convierte los errores en `ErrorConexion` o `ErrorAutenticacion` según la tabla del contrato §3;
  - `cerrar()` es idempotente.
- [X] T067 Completar en `src/traductor/motores/selector.py` los métodos `usar_en_linea()` y `usar_local()` y los puntos 1 y 2 del contrato §4 (depende de T066): respaldo con la misma frase y los eventos `conexion_perdida` y `cuenta_rechazada`.
- [X] T068 [P] Crear `src/traductor/ui/dialogos.py` con lo siguiente:
  - `AvisoEnLinea(QMessageBox)` (D-01), con el texto M-01, los botones "Sí, usar en línea" y "No, seguir sin internet", y el foco inicial en "No";
  - `CuadroCuenta(QDialog)` (D-02), con la explicación, el campo "Clave" (`Password`, nombre accesible "Clave del servicio"), el `QComboBox` editable "Región" (nombre accesible "Región del servicio"), cargado desde `regiones_azure.txt`, y los botones "Guardar y activar" y "Cancelar". Esc cancela;
  - la validación de D-02 corre en un `QThreadPool` para no congelar la ventana, y el botón muestra "Comprobando…" mientras tanto.
- [X] T069 Agregar UI-03 y UI-04 en `src/traductor/ui/ventana.py`:
  - UI-03 es un `QLabel` con los textos de `textos.py` y un color de aviso distinto con el modo `EN_LINEA`;
  - UI-04 es un `QCheckBox` "Modo en línea", apagado al abrir, cuyo nombre accesible cambia entre "Modo en línea, apagado" y "Modo en línea, encendido";
  - el orden de tabulación final es UI-01 → UI-04 → UI-06;
  - volver a correr `tests/ui/test_mover_franja.py` (T038) y `tests/ui/test_ventana.py` (T020) para confirmar que siguen en verde con UI-04.
- [X] T070 Conectar en `src/traductor/app.py` el flujo de [data-model.md §2](data-model.md) (depende de T063 a T069):
  - al encender UI-04: D-01 si hace falta, luego D-02 si no hay cuenta, y luego `selector.usar_en_linea()` y `modo.encender_en_linea()`;
  - al apagar UI-04: `selector.usar_local()` y `modo.volver_sin_internet()`;
  - `conexion_perdida` muestra M-07 y pone el modo en `SIN_INTERNET`;
  - `cuenta_rechazada` muestra M-08, llama a `cuenta.borrar()` y pone el modo en `SIN_INTERNET`;
  - UI-04 vuelve a apagado (con su nombre accesible "Modo en línea, apagado") en cualquier salida que deje el modo en `SIN_INTERNET`: cancelar D-01 o D-02, M-08, M-09, `conexion_perdida` o `cuenta_rechazada`.
- [X] T071 Correr `pytest -m "not modelos"` y corregir hasta que todos los tests de T057 a T062 pasen

**Punto de control**: el modo en línea funciona con servicios simulados. Se valida a mano con los pasos B14a y B16 a B19, con una cuenta real de Azure.

---

## Fase 8: Instalador, trazabilidad y validación final

**Propósito**: instalador, cierre de la trazabilidad y validación de la parte B del quickstart.

- [ ] T072 [P] Crear `instalador/traductor.spec` (PyInstaller *onedir*): punto de entrada `src/traductor/__main__.py`, nombre `TraductorIngles`, ícono `src/traductor/recursos/icono.ico`, sin consola, con `src/traductor/recursos/` y las carpetas de `modelos/` necesarias (el modelo de Whisper elegido en T009 y `opus-mt-en-es-ct2`) como datos, y los binarios de `ctranslate2`, `PyAudioWPatch` y `azure-cognitiveservices-speech` (incluir `comtypes`, que usa `pycaw`, como *hidden import*)
- [ ] T073 [P] Crear `instalador/traductor.iss` (Inno Setup 6), que genera `dist\TraductorIngles-Setup.exe`:
  - crea el acceso directo "TraductorIngles" en el escritorio y en el menú Inicio;
  - **no** crea ninguna entrada de arranque automático (ni `Run` en el registro ni la carpeta Inicio);
  - borra `{userappdata}\TraductorIngles` y `{localappdata}\TraductorIngles` al desinstalar (`[UninstallDelete]`);
  - garantiza el Microsoft Visual C++ Redistributable (x64), que necesitan `ctranslate2`, `onnxruntime`, PySide6, `PyAudioWPatch` y el SDK de Azure: si `dist\TraductorIngles\` ya trae `msvcp140.dll`, `vcruntime140.dll` y `vcruntime140_1.dll`, basta con eso; si no, el instalador incluye `vc_redist.x64.exe` y lo ejecuta en silencio (`/install /quiet /norestart`) solo cuando falta (revisando `HKLM\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64`, valor `Installed`);
  - todos los textos del instalador están en español.
- [ ] T074 [P] Escribir `tests/unit/test_instalador.py`, marcado `spec("RF-001", "RF-004", "RF-015a")`. Lee `instalador/traductor.iss` e `instalador/traductor.spec` y comprueba lo siguiente:
  - ninguno de los dos incluye `cuenta_en_linea.bin`, `ajustes.json` ni ninguna clave del servicio (RF-015a: "nunca va en el instalador");
  - hay entradas `[Icons]` para `{autodesktop}` y `{autoprograms}` con el nombre "TraductorIngles";
  - no hay entradas `[Registry]` con `CurrentVersion\Run` ni íconos en `{autostartup}` o `{userstartup}`;
  - `[UninstallDelete]` incluye `{userappdata}\TraductorIngles` y `{localappdata}\TraductorIngles`.
- [ ] T075 Completar `tests/solo_manuales.toml` con los criterios que necesitan a una persona además de su test automático. `CA-001` va con la justificación "Entender el sentido de 8 de 10 frases lo juzga una persona (quickstart B4); el test automático solo comprueba que hay traducción". Agregar también, cada uno con su `justificacion` y su `paso_quickstart`, los CA cuyo test automático usa simulaciones o WAV y que se confirman a mano con fuentes reales: CA-002 (B5), CA-004 (B13), CA-005 (B9), CA-006 (B6), CA-007 (B2), CA-008 (B13), CA-009 (B10), CA-010 (B14), CA-011 (B15), CA-012 (B16 a B19), CA-013 (B17), CA-014 (B12), CA-015 (B13a) y CA-016 (B14a). Así, los 16 CA quedan con su paso manual documentado. (T011 ya acepta que un CA tenga test automático y además entrada en `solo_manuales.toml`; la entrada documenta la parte manual). Después, correr `pytest tests/test_trazabilidad.py` hasta que quede en verde sin ninguna entrada injustificada
- [ ] T076 Correr la suite completa `pytest` (con los modelos) en el equipo de referencia y dejarla en verde (Principio IV)
- [ ] T077 Generar el instalador con `pyinstaller instalador\traductor.spec` y `iscc instalador\traductor.iss`, instalarlo en el equipo de referencia y comprobar que la app abre y queda lista para activar en menos de 10 s (CA-003, meta del plan) y que usa 1.5 GB de memoria o menos con la traducción activa (Administrador de tareas). Además, instalarlo en un Windows limpio sin el Visual C++ Redistributable (por ejemplo, Windows Sandbox o una máquina virtual nueva) y comprobar que la app abre y activa la traducción sin errores de DLL (Principio VI, CA-003)
- [ ] T078 Seguir los pasos B1 a B19 de la parte B del [quickstart](quickstart.md) con la app instalada y la prueba con personas nuevas (CA-003). Anotar el resultado de cada paso (cumple / no cumple y una observación) en `specs/001-traductor-subtitulos-v0/checklists/validacion-uso.md`
- [ ] T079 Revisión final contra la constitución, escrita en `specs/001-traductor-subtitulos-v0/checklists/validacion-uso.md`:
  - todo comportamiento se rastrea a la spec (Principio III);
  - todos los textos visibles salen de `textos.py` y están en es-MX (Principio II);
  - no hay escrituras de audio, texto o clave en disco ni en la bitácora (R-13);
  - la suite está en verde (Principio IV).

---

## Dependencias y orden de ejecución

### Dependencias entre fases

- **Preparación (fase 1)**: sin dependencias. T009 (la medición) depende de T006 a T008 y decide el modelo que usa T043.
- **Base (fase 2)**: depende de la fase 1 y **bloquea todas las historias**.
- **Historia 4 (fase 3)**: depende de la fase 2. Usa el canal falso, así que no necesita audio ni modelos.
- **Historia 1 (fase 4)**: depende de la fase 2 y del modelo decidido en T009. Se integra con la ventana de la Historia 4 en T047 y T050; esas dos tareas van después de la fase 3.
- **Historias 2 y 3 (fases 5 y 6)**: dependen de la fase 4, porque validan el canal real. Son independientes entre sí.
- **Modo en línea (fase 7)**: depende de las fases 3 y 4 (ventana, selector y canal). Es independiente de las fases 5 y 6.
- **Fase 8**: depende de todas las anteriores.

```text
Fase 1 ─► Fase 2 ─► Fase 3 (US4) ─► Fase 4 (US1) ─┬─► Fase 5 (US2) ─┐
                                                   ├─► Fase 6 (US3) ─┼─► Fase 8
                                                   └─► Fase 7 (en línea) ┘
```

### Dentro de cada fase

- Los tests van primero y deben fallar antes de implementar.
- Los modelos de datos van antes que los servicios, y los servicios antes que la interfaz y el cableado en `app.py`.
- Las tareas que tocan el mismo archivo van en orden: T045 → T046 (`subtitulos.py`); T026 → T047 → T069 (`ventana.py`); T019 → T029 → T050 → T070 (`app.py`); T044 → T067 (`selector.py`).

### Oportunidades de trabajo en paralelo

- **Fase 1**: T003, T004, T005 y T007.
- **Fase 2**: T010 a T014a (tests) y luego T015 a T018 (implementación).
- **Fase 3**: T020 a T025 (tests) y T026 a T028 (implementación).
- **Fase 4**: T031 a T039 (tests) y T040 a T043 y T045 (implementación).
- **Fases 5, 6 y 7**: se pueden hacer en paralelo entre sí cuando termina la fase 4.
- **Fase 7**: T057 a T062 (tests) y T063 a T066 y T068 (implementación).
- **Fase 8**: T072 a T074.

---

## Ejemplo en paralelo: Historia 1

```text
# Todos los tests de la Historia 1 a la vez (archivos distintos):
Tarea: "T031 tests/unit/test_captura.py"
Tarea: "T032 tests/unit/test_segmentador.py"
Tarea: "T033 tests/unit/test_glosario.py"
Tarea: "T034 tests/unit/test_motor_local.py"
Tarea: "T037 tests/ui/test_franja.py"
Tarea: "T038 tests/ui/test_mover_franja.py"

# Después, los componentes independientes a la vez:
Tarea: "T040 src/traductor/audio/captura.py"
Tarea: "T041 src/traductor/audio/segmentador.py"
Tarea: "T042 src/traductor/traduccion/glosario.py"
Tarea: "T043 src/traductor/motores/local.py"
Tarea: "T045 src/traductor/ui/subtitulos.py"

# Al final, en orden: T044 → T046 → T047 → T048 (test) → T049 → T050 → T051
```

## Ejemplo en paralelo: Historia 4

```text
Tarea: "T020 tests/ui/test_ventana.py"
Tarea: "T022 tests/ui/test_bandeja.py"
Tarea: "T023 tests/ui/test_atajo.py"
Tarea: "T024 tests/ui/test_cierre.py"

Tarea: "T026 src/traductor/ui/ventana.py"
Tarea: "T027 src/traductor/ui/bandeja.py"
Tarea: "T028 src/traductor/ui/atajo.py"
# Luego: T029 → T030
```

---

## Estrategia de implementación

### MVP primero (Historias 4 y 1, las dos P1)

1. Fase 1, incluida la medición de latencia (T009). Si ni `base` cumple los 3 s, **detenerse** y revisar la spec con el propietario antes de seguir.
2. Fase 2.
3. Fase 3 (Historia 4): **detenerse y validar** la activación, el atajo y el cierre con el canal falso.
4. Fase 4 (Historia 1): **detenerse y validar** con una llamada real (pasos B1 a B8, B10 a B13a, B14 y B15 del quickstart; B9 es de la fase 6 y B14a necesita el modo en línea de la fase 7).
5. Con eso ya hay un MVP usable sin internet.

### Entrega incremental

1. MVP (Historias 4 y 1).
2. Historia 2 y luego Historia 3: solo pruebas, sin código nuevo esperado.
3. Modo en línea (fase 7).
4. Instalador y validación final (fase 8).

---

## Notas

- [P] = archivos distintos y sin dependencias pendientes.
- `src/traductor/bitacora.py` (R-13, supuesto de la spec sobre la bitácora de diagnóstico) y `src/traductor/canal.py` (flujo de datos de data-model) están en la estructura del plan. La bitácora se rastrea a ese supuesto y su regla de privacidad tiene test en T014a; `canal.py` solo separa responsabilidades y no agrega comportamiento.
- Cada RF y CA de la spec tiene al menos una tarea de test con su marca `spec(...)`. `test_trazabilidad.py` (T011) lo hace cumplir.
- Hacer un commit al terminar cada tarea o grupo lógico, con el mensaje en español.
