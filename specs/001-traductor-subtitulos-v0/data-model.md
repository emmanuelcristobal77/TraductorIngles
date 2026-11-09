# Modelo de datos: TraductorIngles v0

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Fecha**: 2026-11-08

La app no tiene base de datos. Todo vive en memoria mientras la app está abierta. Lo único que se
guarda en disco es un ajuste y la cuenta cifrada del modo en línea (ver `Ajustes` y `CuentaEnLinea`). Los nombres de las entidades están en español; los
identificadores de código pueden quedar en inglés o en español sin acentos.

---

## 1. EstadoTraduccion *(entidad clave de la spec)*

| Campo | Tipo | Regla |
|---|---|---|
| `valor` | enum `DESACTIVADA` \| `PREPARANDO` \| `ACTIVA` | Al abrir la app siempre vale `DESACTIVADA` (RF-004). |
| `sesion` | int | Sube en 1 cada vez que la traducción se activa. Los resultados de una sesión anterior se descartan (CA-004). |

`PREPARANDO` solo existe si la persona activa la traducción antes de que terminen de cargar los
modelos (research R-12). Para la persona sigue contando como "activada": no tiene que hacer nada
más.

**Transiciones**:

```text
                 activar (botón, menú o Ctrl+Alt+T)
DESACTIVADA ────────────────────────────────────────► PREPARANDO ──(modelos listos)──► ACTIVA
     ▲                                                     │                             │
     │                 desactivar (botón, menú o Ctrl+Alt+T)                             │
     └─────────────────────────────────────────────────────┴─────────────────────────────┘
(si los modelos ya están listos, activar va directo de DESACTIVADA a ACTIVA)
```

**Reglas**:

- En `DESACTIVADA` el *stream* de loopback está **cerrado**: no se lee audio (RF-004, CA-007).
- Al pasar a `DESACTIVADA`: se cierra la captura, se vacían las colas, se oculta la franja
  **de inmediato** (menos de 1 s, CA-004) y cualquier resultado que llegue después con la `sesion`
  anterior se ignora.
- Ninguna transición toca el volumen ni la reproducción del sistema (RF-010, CA-008).
- Un error del motor **no** cambia el estado. Muestra un mensaje (RF-013) y la persona puede
  desactivar y volver a activar.
- Si la preparación de los modelos falla (`ErrorPreparacion`), queda marcada como fallida hasta que
  se cierra la app: se muestra M-05 sin que se borre solo, `PREPARANDO` pasa a `DESACTIVADA` y, a
  partir de ahí, `activar()` no cambia el estado y vuelve a mostrar M-05 (RF-005, RF-013).

## 2. ModoProcesamiento *(entidad clave de la spec)*

| Campo | Tipo | Regla |
|---|---|---|
| `valor` | enum `SIN_INTERNET` \| `EN_LINEA` | Al abrir la app siempre vale `SIN_INTERNET` (RF-015, RF-015a). |

**Transiciones**:

```text
encender UI-04
   │
   ├─ ¿aviso_en_linea_aceptado? ── no ──► D-01 ── "No"/Esc ──► SIN_INTERNET (el aviso volverá a salir)
   │                                         └── "Sí" ──► guarda aviso_en_linea_aceptado = true ─┐
   │ sí                                                                                           │
   ▼◄─────────────────────────────────────────────────────────────────────────────────────────────┘
   ├─ ¿hay CuentaEnLinea guardada? ── no ──► D-02 ── Cancelar ──► SIN_INTERNET (sin mensaje)
   │                                           ├── inválida ──► SIN_INTERNET + M-08 (no se guarda)
   │                                           ├── sin red ───► SIN_INTERNET + M-09 (no se guarda)
   │                                           └── válida ────► guarda la cuenta ─┐
   │ sí                                                                             │
   ▼◄───────────────────────────────────────────────────────────────────────────────┘
EN_LINEA
EN_LINEA ──(apagar UI-04, una sola acción)──► SIN_INTERNET
EN_LINEA ──(se pierde la conexión; M-07)──► SIN_INTERNET   (la traducción sigue, RF-015b)
EN_LINEA ──(el servicio rechaza la cuenta guardada; M-08)──► SIN_INTERNET + se borra la cuenta
```

**Reglas**:

- El aviso D-01 sale **una sola vez por instalación**. Si la persona no lo acepta, vuelve a salir la
  siguiente vez (RF-015a).
- La cuenta solo se guarda **después** de que el servicio la acepta; si no, se vuelve a pedir la
  siguiente vez (RF-015c).
- El modo es independiente del `EstadoTraduccion`: se puede cambiar con la traducción activa o
  desactivada.
- El motor local siempre está cargado, para que la vuelta a `SIN_INTERNET` sea inmediata.

## 3. Subtitulo *(entidad clave de la spec)*

| Campo | Tipo | Regla |
|---|---|---|
| `texto` | str | Español de México, ya con el glosario aplicado. No vacío. |
| `sesion` | int | Debe ser igual a `EstadoTraduccion.sesion` para mostrarse. |
| `mostrado_en` | instante monotónico | Cuándo apareció en la franja. |

**Reglas**:

- Se muestran **como máximo 2 líneas** (RF-008). Si el texto no cabe en 2 líneas al ancho de la
  franja, se divide en bloques de hasta 2 líneas que se muestran uno tras otro, y el último bloque
  es el que se queda.
- Un subtítulo nuevo **reemplaza** al anterior, así que siempre se ve lo más reciente (Historia 1,
  escenario 2).
- Si pasan **4 s** sin un subtítulo nuevo, la franja se vacía (RF-012).
- **No se guarda** en disco ni en ninguna bitácora (spec: "No se guarda").

---

## Entidades internas (no visibles para la persona usuaria)

### 4. FragmentoAudio

| Campo | Tipo | Regla |
|---|---|---|
| `muestras` | `numpy.ndarray[float32]` | 16 kHz, mono, valores entre -1.0 y 1.0. |
| `t_inicio` | instante monotónico | Para medir la latencia. |

Lo produce la captura (research R-02) y lo consume el segmentador.

### 5. Frase

| Campo | Tipo | Regla |
|---|---|---|
| `audio` | `numpy.ndarray[float32]` | Entre 0.3 s y 7 s de duración (research R-03). |
| `t_fin_habla` | instante monotónico | Desde aquí se cuentan los 3 s de CA-002. |
| `sesion` | int | La sesión en la que se capturó. |

### 6. ResultadoMotor

| Campo | Tipo | Regla |
|---|---|---|
| `texto_es` | str \| None | `None` si la frase se descartó (no es inglés, música o alucinación). |
| `motivo_descarte` | enum `NINGUNO` \| `OTRO_IDIOMA` \| `SIN_VOZ` \| `BAJA_CONFIANZA` | Solo para pruebas y diagnóstico. |
| `motor` | enum `LOCAL` \| `EN_LINEA` | Qué motor lo produjo. |

### 7. Ajustes

| Campo | Tipo | Default | Regla |
|---|---|---|---|
| `aviso_en_linea_aceptado` | bool | `false` | Pasa a `true` cuando la persona acepta el aviso de RF-015a. |

- **Archivo**: `%APPDATA%\TraductorIngles\ajustes.json`.
- Si el archivo no existe o está dañado, se usan los valores por defecto sin mostrar ningún error.

### 8. CuentaEnLinea *(entidad clave de la spec: "Cuenta del modo en línea")*

| Campo | Tipo | Regla |
|---|---|---|
| `clave` | str | No vacía. Se captura en D-02 y nunca se muestra completa. |
| `region` | str | No vacía, en minúsculas y sin espacios (por ejemplo, `southcentralus`). |

- **Archivo**: `%APPDATA%\TraductorIngles\cuenta_en_linea.bin`, cifrado con DPAPI para el usuario
  actual (research R-14).
- **Ciclo de vida**: no existe → se valida en D-02 → se guarda → se usa con el modo en línea → se
  borra si el servicio la rechaza después, o al desinstalar.
- Nunca se escribe en la bitácora ni sale del equipo, salvo hacia el propio servicio.

### 9. ModoMoverFranja *(interno de la interfaz)*

| Campo | Tipo | Regla |
|---|---|---|
| `activo` | bool | Empieza en `false` y se enciende con UI-06. |

Transiciones: `false ──(UI-06)──► true ──(Enter, Esc o perder el foco)──► false`. Mientras está en
`true`, la franja acepta el foco y las flechas la mueven. Arrastrarla con el mouse funciona siempre,
sin importar este estado (RF-009). Ver [contracts/interfaz-usuario.md](contracts/interfaz-usuario.md#21-modo-de-mover).

### 10. Cierre de la app (RF-004a)

Cerrar la ventana principal, o elegir "Salir" en el menú del ícono, ejecuta en este orden:
`EstadoTraduccion → DESACTIVADA` (se cierra la captura) → se ocultan la franja y el ícono → se libera
el atajo (`UnregisterHotKey`) → se cierran los motores → termina el proceso. Todo en menos de 1 s
(CA-015). Minimizar no ejecuta nada de esto.

---

## Flujo de datos

```text
WASAPI loopback ─► FragmentoAudio ─► Segmentador (Silero VAD) ─► Frase
     ─► SelectorMotor ─► (MotorLocal | MotorEnLinea) ─► ResultadoMotor
     ─► Glosario es-MX ─► Subtitulo ─► Franja de subtítulos
```

Cada flecha entre hilos es una `queue.Queue` con tamaño límite. Si se llena, se descarta la frase
más vieja, para mantener la latencia y mostrar siempre lo más reciente.
