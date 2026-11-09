# Plan de implementación: TraductorIngles v0 — subtítulos en español del audio en inglés

**Rama**: `001-traductor-subtitulos-v0` | **Fecha**: 2026-11-08 (actualizado tras la aclaración del
2026-11-08) | **Spec**: [spec.md](spec.md)

**Entrada**: especificación de la funcionalidad en `specs/001-traductor-subtitulos-v0/spec.md`

## Resumen

App de escritorio para Windows que, solo cuando la persona la activa (botón, ícono de la barra de
tareas o Ctrl+Alt+T), capta el audio que suena por las bocinas o audífonos y muestra su traducción
al español de México en una franja de subtítulos siempre visible. La franja se mueve con el mouse
o con el teclado, y todos los controles se usan de las dos formas.

El enfoque técnico es Python 3.12 con este flujo:

1. Captura con **WASAPI loopback**, que no altera el audio ni usa el micrófono.
2. Corte en frases con **Silero VAD**.
3. Voz a texto con **faster-whisper** (`small` int8 en CPU).
4. Traducción con **OPUS-MT en-es sobre CTranslate2**.
5. **Glosario es-MX** para ajustar el vocabulario a México.
6. Franja y ventana en **PySide6**.

Todo funciona sin internet. Hay un **modo en línea opcional** con Azure AI Speech Translation:

- empieza apagado;
- pide confirmación una vez por instalación;
- pide la cuenta en un cuadro sencillo y la guarda cifrada con DPAPI;
- vuelve solo al motor local si se pierde la conexión.

Detalle de cada decisión: [research.md](research.md).

## Contexto técnico

**Lenguaje/versión**: Python 3.12 (64 bits)

**Dependencias principales** (versiones mínimas; las exactas se fijan con `pip freeze` en
`requirements.txt` al implementar):

| Uso | Paquete |
|---|---|
| Captura WASAPI loopback | `PyAudioWPatch>=0.2.12` |
| Remuestreo a 16 kHz | `soxr>=0.5` |
| Leer (sin cambiar) el volumen y el silencio de la salida | `pycaw>=20240210` (R-02) |
| Audio | `numpy>=2.0` |
| Voz a texto + Silero VAD (ONNX) | `faster-whisper>=1.1` |
| Traducción sin internet | `ctranslate2>=4.5`, `sentencepiece>=0.2` |
| Interfaz, franja, ícono de notificación, cuadros | `PySide6>=6.8` |
| Modo en línea | `azure-cognitiveservices-speech>=1.41` |
| Cifrado de la cuenta (DPAPI) y atajo global (`RegisterHotKey`) | `ctypes` (librería estándar; sin dependencia nueva) |
| Validación de la cuenta | `urllib` (librería estándar) |
| Desarrollo (no viajan en el instalador) | `pytest>=8`, `pytest-qt>=4.4`, `pyinstaller>=6.11`, `transformers` + `torch` (solo para convertir OPUS-MT, una vez) |

**Almacenamiento** (todo en `%APPDATA%\TraductorIngles\`, que se borra al desinstalar):

- `ajustes.json`: un solo dato, `aviso_en_linea_aceptado` (R-13).
- `cuenta_en_linea.bin`: clave y región cifradas con DPAPI (R-14).
- Bitácora de errores sin contenido en `%LOCALAPPDATA%` (R-13).
- Nada de audio ni de texto se guarda.

**Pruebas**: `pytest` + `pytest-qt`. Cada test lleva la marca `@pytest.mark.spec(...)` con los
identificadores que cubre, y un test de trazabilidad verifica que cada RF y CA esté cubierto
(R-10). Los tests de interfaz recorren cada control solo con mouse y solo con teclado.

**Plataforma objetivo**: Windows 10 o posterior, 64 bits, en portátil sin GPU dedicada compatible.
Equipo de referencia: HP ZBook 15 G1 (i7 Haswell, 4 núcleos, AVX2).

**Tipo de proyecto**: app de escritorio, un solo proyecto.

**Metas de rendimiento**:

- Subtítulo en ≤ 3 s desde el fin de la frase en al menos 9 de cada 10 frases (percentil 90,
  CA-002); presupuesto de 2.6 s (R-12).
- Desactivar o cerrar la app → franja oculta en < 1 s (CA-004, CA-014, CA-015).
- La app abre y queda lista para activar en < 10 s (CA-003).
- Comprobar la cuenta del modo en línea: ≤ 5 s (R-14).

**Restricciones**:

- Sin internet por defecto (RF-015).
- Sin tocar el audio del sistema (RF-010).
- Sin micrófono (RF-011).
- Sin escuchar nada antes de activar (RF-004).
- Nada sigue corriendo al cerrar la ventana (RF-004a).
- Sin arranque automático.
- Memoria total ≤ 1.5 GB con `small`.
- Uso de CPU acotado para no trabar la llamada: voz a texto y traducción corren una después de la
  otra en el mismo hilo del selector, cada una con 4 hilos como máximo (`cpu_threads=4`,
  `intra_threads=4`), así que el cálculo pesado nunca usa más de 4 hilos a la vez. El VAD usa 1
  hilo.

**Escala/alcance**: 1 persona usuaria por equipo; 2 ventanas (principal y franja), 1 ícono de
notificación, 2 cuadros (aviso y cuenta) y 9 mensajes
([contracts/interfaz-usuario.md](contracts/interfaz-usuario.md)).

**NEEDS CLARIFICATION**: ninguno. Los huecos P-02, P-03, P-05, P-06 y P-07 quedaron resueltos por
la aclaración del 2026-11-08. P-04 es una limitación documentada de Windows. P-01 (aprobación formal de la spec) quedó resuelto
el 2026-11-08 ([research.md](research.md#huecos-de-la-spec-detectados-al-planear)).

## Revisión contra la constitución (v1.0.1)

*PUERTA: debe pasar antes de la fase 0. Se revisó de nuevo después del diseño de la fase 1.*

| Principio | Verificación | Resultado |
|---|---|---|
| **I. Spec primero** | Todo lo diseñado se rastrea a RF o CA de la spec 001, incluidos RF-004a, RF-015c, CA-015 y CA-016, que son nuevos. `specs/MAPA.md` tiene un solo propietario y la spec está "Aprobada" (2026-11-08). | ✅ Cumple (P-01 resuelto). |
| **II. Español de México** | Toda la interfaz, los cuadros y los mensajes M-01 a M-09 están en es-MX ([contrato](contracts/interfaz-usuario.md)); la traducción pasa por el glosario es-MX (R-06); se usa "mouse" y no "ratón"; la documentación está en español. | ✅ Cumple. Riesgo de calidad con *vosotros*, cubierto por las pruebas de CA-001. |
| **III. Cero alcance fantasma** | El contrato de interfaz enumera cada elemento con su requisito: UI-06 se basa en RF-009, D-02 en RF-015a y RF-015c, y "Salir" en RF-004a. No se recuerda la posición de la franja ni hay historial. | ✅ Cumple. |
| **IV. Los tests acompañan a la spec** | Marca `spec(...)` en cada test + `test_trazabilidad.py`, que falla si un RF o CA queda sin test; los criterios solo manuales se justifican por escrito en `solo_manuales.toml`. | ✅ Cumple. |
| **V. Verificable por una persona no técnica** | [quickstart.md](quickstart.md), parte B: pasos observables para cada CA, sin terminal. La cuenta del modo en línea se captura en la app, sin editar archivos (B16 a B16b). | ✅ Cumple. |
| **VI. Interfaz sencilla y accesible** | Un botón principal con foco inicial y el atajo visible; **todo se opera con mouse y con teclado**, incluido mover la franja (UI-06 y el modo de mover); nombres accesibles, orden de tabulación y contraste definidos; funciona en CPU sin hardware especial. | ✅ Cumple (la excepción P-02 del plan anterior quedó resuelta). |
| **Ejecución local** | Motor local por defecto, sin red (un test bloquea `socket`); modo en línea apagado al abrir, con aviso, cuenta cifrada solo en el equipo y regreso automático. | ✅ Cumple. |
| **Activación bajo demanda / plataforma** | El loopback se abre solo con la traducción activa y se cierra al cerrar la app; Windows 10 o posterior. | ✅ Cumple. |

**Resultado de la puerta**: el diseño puede continuar y `/speckit-tasks` ya no tiene bloqueos
(P-01 resuelto el 2026-11-08).

**Revisión después de la fase 1**: el modelo de datos (`CuentaEnLinea`, `ModoMoverFranja`, cierre
de la app) y los contratos (UI-06, D-01, D-02, M-08, M-09, `ErrorAutenticacion`) no agregaron
comportamiento fuera de la spec. No quedan huecos abiertos.

## Estructura del proyecto

### Documentación (esta funcionalidad)

```text
specs/001-traductor-subtitulos-v0/
├── spec.md
├── plan.md                    # este archivo
├── research.md                # fase 0
├── data-model.md              # fase 1
├── quickstart.md              # fase 1
├── contracts/
│   ├── interfaz-usuario.md    # fase 1: todo lo visible y operable
│   └── motor-traduccion.md    # fase 1: contrato interno de los motores y el respaldo
├── checklists/requirements.md
└── tasks.md                   # fase 2 (/speckit-tasks; no lo crea este comando)
```

### Código fuente (raíz del repositorio)

```text
src/traductor/
├── __main__.py               # python -m traductor
├── app.py                    # arranque, cableado, carga de modelos en segundo plano, cierre ordenado (RF-004a)
├── estado.py                 # EstadoTraduccion, ModoProcesamiento y sus transiciones
├── textos.py                 # todos los textos visibles (UI-xx, D-xx, M-xx) en es-MX
├── ajustes.py                # ajustes.json
├── cuenta.py                 # CuentaEnLinea: cifrado DPAPI, validación con el servicio
├── bitacora.py               # errores sin contenido en %LOCALAPPDATA% (R-13)
├── canal.py                  # flujo captura → segmentador → selector → glosario → Subtitulo, con colas e hilos
├── audio/
│   ├── captura.py            # WASAPI loopback, remuestreo, cambio de dispositivo
│   └── segmentador.py        # Silero VAD → Frase
├── motores/
│   ├── base.py               # protocolo MotorTraduccion y errores (Conexion, Autenticacion, Motor)
│   ├── local.py              # faster-whisper + CTranslate2 OPUS-MT
│   ├── en_linea.py           # Azure Speech Translation
│   └── selector.py           # SelectorMotor y respaldo sin internet
├── traduccion/
│   └── glosario.py           # postproceso es-MX
├── ui/
│   ├── ventana.py            # ventana principal (UI-01 a UI-06), cerrar y minimizar
│   ├── subtitulos.py         # franja siempre encima, sin foco, arrastre y modo de mover
│   ├── dialogos.py           # D-01 aviso, D-02 cuenta
│   ├── bandeja.py            # ícono del área de notificación y su menú
│   └── atajo.py              # RegisterHotKey Ctrl+Alt+T
└── recursos/
    ├── glosario_es_mx.tsv
    ├── regiones_azure.txt    # lista de la región en D-02
    └── icono.ico

tests/
├── conftest.py               # marca spec(...), fixtures de audio, motores falsos, validación de cuenta simulada
├── test_trazabilidad.py      # RF y CA de spec.md ↔ tests
├── solo_manuales.toml        # CA que solo se validan a mano, con su justificación
├── unit/                     # estado, segmentador, glosario, subtítulos, selector, cuenta, textos
├── integration/              # flujo completo sin internet con WAV (marca "modelos")
├── ui/                       # pytest-qt: ventana, franja y modo de mover, diálogos, bandeja, atajo, cierre; mouse y teclado
└── fixtures/audio/           # WAV en inglés, español, música, silencio + ATRIBUCION.md

scripts/
├── preparar_modelos.py       # descarga y conversión de modelos (desarrollo)
└── medir_latencia.py         # medición de R-12

instalador/
├── traductor.spec            # PyInstaller onedir
└── traductor.iss             # Inno Setup: escritorio + menú Inicio, sin arranque automático, borra %APPDATA% al desinstalar

modelos/                      # no se versiona (.gitignore); lo genera preparar_modelos.py
pyproject.toml
requirements.txt
requirements-dev.txt
```

**Decisión de estructura**: un solo proyecto Python con el código en `src/traductor/`, separado por
responsabilidad: audio, motores, cuenta, traducción e interfaz. Así cada parte se prueba por
separado con motores, audio y servicio falsos. Los modelos no se guardan en git y se generan con
un script.

## Orden sugerido para `/speckit-tasks`

1. **Medición previa**: `preparar_modelos.py` + `medir_latencia.py`; decidir entre `small` y `base`
   (R-12).
2. Esqueleto, `textos.py`, `estado.py` y la trazabilidad de tests.
3. **Historia 4 (P1)**: ventana, bandeja, atajo, cerrar y minimizar, con un motor falso.
4. **Historia 1 (P1)**: captura, segmentador, motor local, glosario y franja, con arrastre y modo de
   mover.
5. **Historias 2 y 3**: validación con video y audio (sin código nuevo esperado; pruebas de
   integración).
6. Modo en línea: D-01, D-02, `cuenta.py`, motor en línea y respaldo (RF-015a, RF-015b, RF-015c).
7. Instalador y validación de la parte B del quickstart.

## Seguimiento de complejidad

| Excepción | Por qué se necesita | Alternativa más simple descartada porque |
|---|---|---|
| Dos motores (local y en línea) con selector | La spec exige el modo en línea con regreso automático sin interrumpir (RF-015a, RF-015b). | Un solo motor no cumple RF-015a; cambiar de motor sin la interfaz común obligaría a reiniciar la traducción. |
| Glosario es-MX como postproceso | Ningún modelo sin internet da es-MX (Principio II). | Aceptar español genérico viola el Principio II. |
| Cifrado DPAPI + validación previa de la cuenta | RF-015a pide guardarla cifrada; RF-015c pide no quedarse con una cuenta inválida. | Guardar en texto plano viola RF-015a; guardar sin validar obligaría a descubrir el error a mitad de una llamada. |
