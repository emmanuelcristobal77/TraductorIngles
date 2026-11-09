# Contrato de interfaz de usuario: TraductorIngles v0

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)

Este contrato fija **todo** lo que la persona usuaria ve y opera. Cualquier elemento que no esté
aquí no se implementa (Principio III). Todos los textos están en español de México (Principio II).
Los tests de interfaz comprueban estos textos, nombres accesibles y comportamientos.

**Regla general (RF-014, CA-010, CA-016)**: cada control se puede usar **con el mouse y con el
teclado**. Ningún camino reemplaza ni desactiva al otro, y los tests recorren cada control de las
dos formas.

---

## 1. Ventana principal "TraductorIngles"

| ID | Elemento | Texto visible | Nombre accesible | Mouse | Teclado | Requisito |
|---|---|---|---|---|---|---|
| UI-01 | Botón de traducción (desactivada) | **Activar traducción** · *Ctrl+Alt+T* | "Activar traducción, atajo Control Alt T" | Clic | Tab hasta el botón, Espacio o Enter | RF-002, RF-016 |
| UI-01 | Botón de traducción (activa) | **Desactivar traducción** · *Ctrl+Alt+T* | "Desactivar traducción, atajo Control Alt T" | Clic | igual | RF-003 |
| UI-02 | Indicador de estado | "Traducción desactivada" / "Preparando la traducción…" / "Traducción activa" | igual que el texto | — | solo lectura (lo anuncia el lector de pantalla) | RF-005 |
| UI-03 | Indicador de modo | "Sin internet" / "En línea: el audio sale del equipo" | igual que el texto | — | solo lectura | RF-015a, CA-012 |
| UI-04 | Interruptor del modo en línea | "Modo en línea" (casilla, apagada al abrir) | "Modo en línea, apagado" / "Modo en línea, encendido" | Clic | Tab, Espacio | RF-015a |
| UI-06 | Botón de mover la franja | **Mover subtítulos** | "Mover subtítulos con las flechas" | Clic | Tab, Espacio o Enter | RF-009, RF-014 |
| UI-05 | Zona de mensajes | Texto del catálogo §6; vacía si no hay mensaje | "Mensaje" | — | solo lectura | RF-013, RF-016a |

**Reglas**:

- Orden de tabulación: UI-01 → UI-04 → UI-06. El foco inicial queda en UI-01, así que basta abrir
  la app y presionar Enter para activar la traducción (CA-003, CA-010).
- Diferencias visibles por estado: con la traducción activa, UI-01 y UI-02 cambian de texto **y**
  de color (no solo de color). Con el modo en línea encendido, UI-03 usa un color de aviso
  distinto del de "Sin internet".
- Letra de 16 px o más; contraste de 4.5:1 o más (Principio VI).
- **Cerrar** la ventana (con la X o con Alt+F4) **cierra la app**: se detiene la traducción y
  desaparecen la franja y el ícono en menos de 1 s (RF-004a, CA-015).
- **Minimizar** la ventana no cambia nada: la traducción y la franja siguen igual (RF-004a).

## 2. Franja de subtítulos

| Propiedad | Valor | Requisito |
|---|---|---|
| Visible | Con la traducción activa y un subtítulo vigente, o durante el modo de mover (§2.1) | RF-005, RF-012 |
| Posición inicial | Centrada horizontalmente, a 10 % del borde inferior de la pantalla principal | RF-008 |
| Siempre encima | Sí, incluido un video en pantalla completa sin bordes | RF-008, CA-006 |
| Toma el foco | **Nunca**, salvo durante el modo de mover (no interrumpe la llamada ni el video) | Historia 1, escenario 3 |
| Texto | Blanco sobre fondo negro al 75 % de opacidad, letra de 28 px, máximo 2 líneas | RF-008 |
| Mover con mouse | Se arrastra con el botón izquierdo a cualquier parte de la pantalla, en cualquier momento | RF-009 |
| Mover con teclado | Con el modo de mover (§2.1) | RF-009 |
| Límites | Nunca sale por completo de la pantalla | RF-009 |
| Recordar la posición | **No** (vuelve a la posición inicial al abrir la app) | Principio III |
| Desaparece | Con 4 s sin habla, o en menos de 1 s al desactivar la traducción | RF-012, CA-004 |

### 2.1 Modo de mover

| Paso | Qué pasa |
|---|---|
| Entrar | Clic o Enter en UI-06. La franja se muestra (aunque no haya subtítulo o la traducción esté desactivada), recibe el foco, se resalta con un borde amarillo de 3 px y muestra el texto **"Usa las flechas para mover los subtítulos. Enter o Esc para terminar."** |
| Mover | Las flechas la mueven 20 px y Mayús + flecha, 100 px. También se puede arrastrar con el mouse. |
| Terminar | Enter o Esc. La franja se queda donde está, pierde el resaltado, deja de aceptar el foco y el foco vuelve a UI-06. Si no hay subtítulo vigente, se oculta. |
| Fuera de foco | Si la persona cambia a otra ventana durante el modo, este termina igual que con Esc. |

## 3. Cuadros de diálogo

### D-01. Aviso del modo en línea (una vez por instalación; RF-015a)

- Sale al encender UI-04 si `aviso_en_linea_aceptado` es falso.
- Texto: el mensaje M-01.
- Botones: **Sí, usar en línea** / **No, seguir sin internet**. El foco empieza en "No".
- "Sí" guarda que se aceptó el aviso y sigue con D-02 (si no hay cuenta) o enciende el modo.
- "No", Esc o cerrar el cuadro: el modo sigue *sin internet* y el aviso volverá a salir la
  siguiente vez.

### D-02. Cuenta del modo en línea (solo si no hay cuenta guardada; RF-015a, RF-015c)

| Elemento | Texto | Nombre accesible | Detalle |
|---|---|---|---|
| Explicación | "Escribe la clave y la región de tu servicio de traducción en internet. Se guardan cifradas solo en esta computadora." | igual que el texto | — |
| Campo de la clave | Etiqueta "Clave" | "Clave del servicio" | Oculta con puntos; nunca se muestra completa |
| Campo de la región | Etiqueta "Región" | "Región del servicio" | Lista desplegable editable de regiones (por ejemplo, `southcentralus`) |
| Botón | **Guardar y activar** | igual que el texto | Solo se habilita con los dos campos llenos; mientras valida, muestra "Comprobando…" |
| Botón | **Cancelar** | igual que el texto | También con Esc |

**Resultados**:

- Cuenta válida: se guarda cifrada, se cierra el cuadro y UI-03 dice "En línea: el audio sale del
  equipo".
- Cuenta inválida: no se guarda, se cierra el cuadro, se muestra M-08 y el modo sigue *sin
  internet*.
- Sin conexión al comprobar: no se guarda, se muestra M-09 y el modo sigue *sin internet*.
- Cancelar: no se guarda, sin mensaje, y el modo sigue *sin internet*.

## 4. Ícono en el área de notificación de la barra de tareas

| Elemento | Texto | Mouse | Teclado | Requisito |
|---|---|---|---|---|
| Ícono | Información al pasar el mouse: "TraductorIngles: traducción desactivada" / "…activa" | Clic izquierdo: muestra la ventana principal. Clic derecho: abre el menú | Win+B, flechas hasta el ícono; Enter muestra la ventana y la tecla Menú o Mayús+F10 abre el menú | RF-001, RF-005 |
| Menú → opción 1 | "Activar traducción" / "Desactivar traducción" | Clic | Flechas + Enter | RF-002, RF-003, RF-016a |
| Menú → opción 2 | "Abrir TraductorIngles" | Clic | Flechas + Enter | RF-001 |
| Menú → opción 3 | "Salir" | Clic | Flechas + Enter | RF-004a |

## 5. Atajo global

| Atajo | Efecto | Alcance | Requisito |
|---|---|---|---|
| **Ctrl+Alt+T** | Activa la traducción si está desactivada y la desactiva si está activa | Desde cualquier ventana, mientras la app esté abierta; no cambia de ventana | RF-016, CA-014 |

- Mantener la tecla presionada no repite la acción (`MOD_NOREPEAT`).
- Si el atajo está ocupado al abrir la app, se muestra M-06 en UI-05, y UI-01 y el menú del ícono
  siguen funcionando (RF-016a).

## 6. Catálogo de mensajes

Cada mensaje es breve, está en español de México, no tiene códigos técnicos y dice qué puede hacer
la persona (RF-013).

| ID | Cuándo | Texto |
|---|---|---|
| M-01 | Aviso del modo en línea (D-01) | "En el modo en línea, el audio que suena en tu computadora se envía por internet a un servicio de traducción. ¿Quieres activarlo?" |
| M-02 | No se encontró una salida de audio | "No encontramos bocinas ni audífonos. Conecta uno y vuelve a activar la traducción." |
| M-03 | La captura de audio falló | "No pudimos escuchar el audio de la computadora. Desactiva y vuelve a activar la traducción." |
| M-04 | El motor local falló al traducir | "No pudimos traducir lo último que se dijo. Si se repite, desactiva y vuelve a activar la traducción." |
| M-05 | Los modelos no se pudieron cargar | "No se pudo preparar la traducción. Cierra la app y vuelve a abrirla; si sigue pasando, reinstálala." |
| M-06 | Ctrl+Alt+T está ocupado por otra app | "Otra aplicación ya usa Ctrl+Alt+T. Usa el botón o el ícono de la barra de tareas para activar la traducción." |
| M-07 | Se perdió la conexión en el modo en línea | "Se perdió la conexión a internet. Seguimos traduciendo sin internet." |
| M-08 | El servicio rechazó la clave o la región (al capturarlas o después) | "No se pudo activar el modo en línea: revisa la clave y la región. Seguimos traduciendo sin internet." |
| M-09 | No hay conexión al comprobar la cuenta | "No se pudo activar el modo en línea porque no hay conexión a internet. Seguimos traduciendo sin internet." |

- Los mensajes M-02 a M-09 se borran solos al cabo de 10 s o cuando cambia el estado.
- Ningún mensaje tapa la franja de subtítulos ni le quita el foco a otra ventana.

## 7. Instalación y accesos

| Acceso | Lo crea | Requisito |
|---|---|---|
| Acceso directo en el escritorio "TraductorIngles" | Instalador | RF-001 |
| Entrada en el menú Inicio "TraductorIngles" | Instalador | RF-001 |
| Botón en la barra de tareas mientras la app está abierta | Windows (ventana principal) | RF-001 |
| Ícono en el área de notificación mientras la app está abierta | La app (§4) | RF-001 |
| Arranque automático con Windows | **Nunca** | RF-004 |
| Al desinstalar | Se borran los ajustes y la cuenta guardada | RF-015a ("una vez por instalación") |
