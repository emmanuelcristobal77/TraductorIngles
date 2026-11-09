# Especificación de funcionalidad: TraductorIngles v0 — subtítulos en español del audio en inglés

**Rama**: `001-traductor-subtitulos-v0`

**Creada**: 2026-11-08

**Estado**: Aprobada (2026-11-08, por el propietario)

**Propietario**: ver [MAPA.md](../MAPA.md)

**Entrada**: Descripción del usuario: "TraductorIngles v0: traducir todo lo que se escucha en inglés por
las bocinas o audífonos (llamada en línea o de escritorio, video o audio) y mostrar la traducción
como subtítulos de película. Un solo usuario. Accesible desde el escritorio y/o la barra de tareas,
se activa solo cuando el usuario lo decide y se puede desactivar en cualquier momento."

## Aclaraciones

### Sesión 2026-11-08

- P: ¿El audio puede enviarse por internet a un servicio de traducción, o todo debe procesarse en la
  portátil sin conexión? → R: Sin internet por defecto; con internet solo si la persona lo activa a
  propósito (modo en línea opcional).
- P: ¿Debe haber un atajo de teclado que active o desactive la traducción desde cualquier ventana?
  → R: Sí, un atajo fijo (Ctrl+Alt+T), sin opción de cambiarlo en la v0.
- P: ¿Cómo mueve la franja de subtítulos una persona que solo usa teclado? → R: Con un botón
  "Mover subtítulos" en la ventana principal; al presionarlo, las flechas mueven la franja y Enter o
  Esc terminan.
- P: ¿Qué pasa al cerrar la ventana principal (X o Alt+F4)? → R: Se cierra la app: se detiene la
  traducción y desaparecen la franja y el ícono. Minimizar la ventana no detiene nada.
- P: ¿Cómo se configura la cuenta del servicio en internet del modo en línea? → R: La primera vez
  que se enciende el modo en línea, después del aviso, la app pide la clave y la región en un cuadro
  sencillo y las guarda cifradas en el equipo.
- P: ¿Cada cuánto sale el aviso de que el audio saldrá del equipo? → R: Una sola vez por
  instalación; después basta encender el interruptor.
- P: ¿Cuántos segundos sigue el último subtítulo cuando ya nadie habla? → R: 4 segundos.
- P: ¿Poder usar todo con teclado limita el uso del mouse? → R: No. Todo lo que se hace con
  teclado también se puede hacer con el mouse; los dos caminos conviven.

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — Subtítulos en español durante una llamada en inglés (Prioridad: P1)

La persona usuaria está en una llamada o reunión (por ejemplo, con un cliente o un entrevistador)
en la que le hablan en inglés. Activa TraductorIngles y, mientras la otra persona habla, ve en
pantalla la traducción al español de México como subtítulos de película, sin salir de la llamada.

**Por qué esta prioridad**: es el caso de uso principal y el de mayor valor: entender una
conversación en vivo donde no hay forma de pausar ni repetir.

**Prueba independiente**: con una llamada en inglés en curso en cualquier plataforma, activar la
app y comprobar que aparecen subtítulos en español de lo que dice la otra persona.

**Escenarios de aceptación**:

1. **Dado** que hay una llamada en curso donde la otra persona habla en inglés y la traducción está
   desactivada, **cuando** la persona usuaria activa la traducción, **entonces** aparecen subtítulos
   en español de México de lo que se dice a partir de ese momento.
2. **Dado** que la traducción está activa, **cuando** la otra persona sigue hablando, **entonces**
   los subtítulos se renuevan conforme avanza la conversación y siempre muestran lo más reciente.
3. **Dado** que la traducción está activa, **cuando** la persona usuaria cambia a otra ventana (por
   ejemplo, la de la llamada), **entonces** los subtítulos siguen visibles encima de esa ventana.
4. **Dado** que la traducción está activa, **cuando** la persona usuaria la desactiva, **entonces**
   los subtítulos dejan de aparecer y la llamada continúa sin interrupción.

---

### Historia 2 — Subtítulos en español de un video en inglés (Prioridad: P2)

La persona usuaria reproduce un video en inglés (en una página web o en un reproductor de
escritorio). Activa la app y ve la traducción como subtítulos mientras el video avanza.

**Por qué esta prioridad**: mismo mecanismo que la Historia 1, con un uso muy frecuente; confirma
que la app funciona con cualquier fuente de audio, no solo con llamadas.

**Prueba independiente**: reproducir un video en inglés con la traducción activa y comprobar que
aparecen subtítulos en español sincronizados con lo que se dice.

**Escenarios de aceptación**:

1. **Dado** que se reproduce un video en inglés, **cuando** la traducción está activa,
   **entonces** aparecen subtítulos en español de lo que se dice en el video.
2. **Dado** que la traducción está activa, **cuando** el video se pausa, **entonces** no aparecen
   subtítulos nuevos; **y cuando** se reanuda, **entonces** vuelven a aparecer.
3. **Dado** que el video está en pantalla completa, **cuando** la traducción está activa,
   **entonces** los subtítulos siguen visibles.

---

### Historia 3 — Subtítulos en español de un audio en inglés (Prioridad: P3)

La persona usuaria escucha un audio en inglés (podcast, nota de voz, grabación) en cualquier
aplicación. Activa la app y lee la traducción como subtítulos.

**Por qué esta prioridad**: amplía el mismo comportamiento a audio sin imagen; no requiere nada
distinto de las historias anteriores, solo confirma que la fuente puede ser cualquiera.

**Prueba independiente**: reproducir un audio en inglés con la traducción activa y comprobar que
aparecen subtítulos en español.

**Escenarios de aceptación**:

1. **Dado** que se reproduce un audio en inglés, **cuando** la traducción está activa,
   **entonces** aparecen subtítulos en español de lo que se dice.

---

### Historia 4 — Activar y desactivar rápido, solo cuando la persona lo decide (Prioridad: P1)

La persona usuaria encuentra la app en el escritorio y/o la barra de tareas, la activa con un solo
paso y la desactiva igual de fácil en cualquier momento. La traducción nunca empieza sola.

**Por qué esta prioridad**: sin un acceso rápido y confiable las Historias 1–3 no sirven, sobre todo
en una llamada ya iniciada.

**Prueba independiente**: sin manual, una persona que nunca usó la app la encuentra, activa la
traducción y la desactiva.

**Escenarios de aceptación**:

1. **Dado** que la app está instalada, **cuando** la persona usuaria busca cómo abrirla,
   **entonces** la encuentra en el escritorio y en la barra de tareas.
2. **Dado** que la app está abierta y la traducción desactivada, **cuando** la persona usuaria hace
   una sola acción de activar, **entonces** la traducción queda activa y la app lo indica de forma
   visible.
3. **Dado** que la traducción está activa, **cuando** la persona usuaria hace una sola acción de
   desactivar, **entonces** la traducción se detiene y la app indica que está desactivada.
4. **Dado** que la persona usuaria enciende la portátil o abre la app, **cuando** no ha activado la
   traducción, **entonces** la app no escucha ni traduce nada.
5. **Dado** que la traducción está activa, **cuando** la persona usuaria la activa o desactiva,
   **entonces** el audio que estaba escuchando no se corta, no se pausa ni cambia de volumen.
6. **Dado** que la app está abierta y la persona usuaria está en la ventana de una llamada,
   **cuando** presiona Ctrl+Alt+T, **entonces** la traducción cambia de desactivada a activa (o al
   revés) sin salir de la llamada.

---

### Casos límite

- **Silencio**: si no suena nada, no aparecen subtítulos y el último subtítulo desaparece tras 4
  segundos sin habla.
- **Audio en otro idioma**: si lo que suena no está en inglés (por ejemplo, ya está en español), la
  app no muestra traducciones inventadas.
- **Música o ruido de fondo**: la app traduce la voz en inglés que distinga; la música sola no
  genera subtítulos.
- **Varias personas hablando**: los subtítulos muestran la traducción de lo que se dice, sin
  identificar quién habla.
- **Sin sonido de salida** (volumen en cero o en silencio): no hay subtítulos; la app no muestra
  errores técnicos.
- **Cambio de bocinas a audífonos** con la traducción activa: la app sigue traduciendo lo que suena
  por el nuevo dispositivo sin que la persona tenga que volver a activarla.
- **Voz propia por micrófono**: lo que la persona usuaria dice por su micrófono no se traduce; solo
  lo que se escucha por bocinas o audífonos.
- **Sin internet**: en el modo por defecto la app funciona igual con o sin conexión. Si el modo en
  línea está activo y se cae la conexión, la app avisa y sigue en modo sin internet (RF-015b).
- **Atajo ocupado**: si otra aplicación ya usa Ctrl+Alt+T, la app lo avisa y se puede seguir
  activando con el botón o el ícono de la barra de tareas (RF-016a).
- **Error al traducir**: si la app no puede traducir, muestra un mensaje breve y claro en español
  (sin códigos técnicos) y la persona puede desactivar y volver a activar.

## Requisitos *(obligatorio)*

### Requisitos funcionales

- **RF-001** (RF1 del usuario): La app DEBE poder abrirse desde un acceso en el escritorio y desde
  la barra de tareas de Windows.
- **RF-002**: La persona usuaria DEBE poder activar la traducción con una sola acción desde la app.
- **RF-003** (RF2 del usuario): La persona usuaria DEBE poder desactivar la traducción en cualquier
  momento con una sola acción.
- **RF-004** (RF3 del usuario): La app NO DEBE escuchar ni traducir audio mientras la traducción no
  haya sido activada por la persona usuaria. La app no se abre sola al encender la portátil.
- **RF-004a**: Cerrar la ventana principal (con la X o con Alt+F4) DEBE cerrar la app por
  completo: se detiene la traducción y desaparecen la franja de subtítulos y el ícono de la barra
  de tareas. Minimizar la ventana NO DEBE detener la traducción.
- **RF-005**: La app DEBE indicar de forma visible si la traducción está activa o desactivada.
- **RF-006**: Con la traducción activa, la app DEBE captar el audio en inglés que se reproduce por
  las bocinas o audífonos de la computadora, sin importar qué aplicación o plataforma lo produce.
- **RF-007**: La app DEBE traducir ese audio al español de México.
- **RF-008**: La app DEBE mostrar la traducción como subtítulos: texto en una franja sobre las demás
  ventanas (incluido un video en pantalla completa), en letra grande, alto contraste y no más de dos
  líneas a la vez, renovándose conforme avanza lo que se dice.
- **RF-009**: La persona usuaria DEBE poder mover la franja de subtítulos a otra parte de la
  pantalla para que no tape lo que necesita ver, de dos formas:
  - arrastrándola con el mouse;
  - con el teclado: el botón "Mover subtítulos" de la ventana principal activa el modo de mover;
    las flechas desplazan la franja y Enter o Esc terminan el modo.
- **RF-010**: La app NO DEBE alterar el audio original: no lo silencia, no lo pausa ni cambia su
  volumen.
- **RF-011**: La app NO DEBE traducir lo que entra por el micrófono.
- **RF-012**: Cuando no hay voz en inglés, la app NO DEBE mostrar subtítulos inventados, y el último
  subtítulo DEBE desaparecer tras 4 segundos sin habla.
- **RF-013**: Si ocurre un error, la app DEBE mostrar un mensaje breve en español de México, sin
  códigos técnicos, que diga qué puede hacer la persona.
- **RF-014**: Todos los controles de la app (abrir, activar, desactivar, mover subtítulos, modo en
  línea) DEBEN poder usarse **tanto con el mouse como con el teclado**, y tener nombres claros en
  español. El soporte de teclado no reemplaza ni limita el uso del mouse.
- **RF-015**: Por defecto, el procesamiento del audio y la traducción DEBE ocurrir completamente en
  la computadora, sin conexión a internet y sin enviar audio ni texto fuera del equipo (modo sin
  internet).
- **RF-015a**: La persona usuaria PUEDE activar a propósito un modo en línea, en el que el audio se
  envía a un servicio de traducción en internet. Este modo DEBE:
  - estar desactivado al instalar la app y cada vez que se abre;
  - pedir confirmación una sola vez por instalación, con un aviso claro en español de que el audio
    saldrá del equipo. Si la persona no acepta, el aviso vuelve a salir la siguiente vez que
    encienda el modo; una vez aceptado, ya no se repite;
  - mostrarse de forma visible mientras esté en uso, distinguible del modo sin internet;
  - poder apagarse con una sola acción, volviendo al modo sin internet;
  - si todavía no hay cuenta configurada, pedir después del aviso la clave y la región del servicio
    en un cuadro sencillo y guardarlas cifradas en el equipo, con la protección de datos de Windows
    para el usuario actual. La clave nunca se muestra completa, nunca va en el instalador y nunca
    sale del equipo, salvo hacia el propio servicio.
- **RF-015c**: Si la persona cancela el cuadro de la cuenta, o el servicio rechaza la clave o la
  región, la app DEBE quedarse en modo sin internet y mostrar un mensaje breve en español que diga
  que el modo en línea no se pudo activar. En ese caso DEBE volver a pedir la cuenta la siguiente
  vez que se encienda el modo en línea.
- **RF-015b**: Si el modo en línea está activo y se pierde la conexión, la app DEBE avisar con un
  mensaje breve y seguir traduciendo en modo sin internet, sin que la persona tenga que reactivar la
  traducción.
- **RF-016**: Mientras la app esté abierta, el atajo de teclado fijo **Ctrl+Alt+T** DEBE activar la
  traducción si está desactivada y desactivarla si está activa, desde cualquier ventana (incluida
  la de una llamada o un video en pantalla completa), sin cambiar de ventana. La app DEBE mostrar
  ese atajo junto al botón de activar para que se descubra sin manual.
- **RF-016a**: Si el atajo no se puede usar porque otra aplicación ya lo ocupa, la app DEBE avisarlo
  con un mensaje breve en español, y el botón y el ícono de la barra de tareas DEBEN seguir
  funcionando.

### Fuera de alcance (v0)

- Guardar, exportar o consultar un historial de las traducciones.
- Traducir otros idiomas o traducir del español al inglés.
- Traducir la voz propia (micrófono) o hablar la traducción en voz alta.
- Identificar quién habla.
- Configuraciones adicionales (tamaño de letra, colores, idioma de la interfaz) más allá de mover
  la franja de subtítulos, encender o apagar el modo en línea y capturar la cuenta del modo en línea
  (RF-015a).
- Elegir entre varios servicios de traducción en internet; la v0 usa uno solo en el modo en línea.
- Cambiar las teclas del atajo; en la v0 es fijo (Ctrl+Alt+T).
- Varias cuentas o perfiles de usuario.

### Entidades clave

- **Estado de traducción**: activa o desactivada; empieza siempre desactivada.
- **Modo de procesamiento**: sin internet (por defecto) o en línea (opcional, elegido por la
  persona); al abrir la app siempre empieza en sin internet.
- **Cuenta del modo en línea**: la clave y la región del servicio de traducción en internet. Se
  capturan una vez y se guardan cifradas en el equipo; solo se usan con el modo en línea encendido.
- **Subtítulo**: un fragmento de texto en español de México que corresponde a lo último que se dijo
  en inglés; se muestra un tiempo y se reemplaza por el siguiente. No se guarda.

## Criterios de éxito *(obligatorio)*

Todos se comprueban usando la app, sin leer código (Principio V de la constitución).

### Resultados medibles

- **CA-001** (CA1 del usuario): Al reproducir un video de prueba en inglés con habla clara, con la
  traducción activa, aparecen subtítulos en español; en una muestra de 10 frases, la persona que
  prueba entiende correctamente el sentido de al menos 8.
- **CA-002**: El subtítulo de cada frase aparece a más tardar 3 segundos después de que se terminó
  de decir.
- **CA-003** (CA2 del usuario): Una persona que nunca ha usado la app, sin instrucciones, abre la
  app y activa la traducción en menos de 10 segundos; 9 de cada 10 personas lo logran al primer
  intento.
- **CA-004**: La traducción se desactiva con una sola acción, y los subtítulos dejan de aparecer en
  menos de 1 segundo.
- **CA-005**: Funciona igual con al menos tres fuentes distintas: una llamada en línea, un video en
  el navegador y un audio en un reproductor de escritorio.
- **CA-006**: Los subtítulos se ven encima de un video en pantalla completa y de la ventana de una
  llamada.
- **CA-007**: Al abrir la app y no activar nada, durante 1 minuto con un video en inglés sonando, no
  aparece ningún subtítulo.
- **CA-008**: Activar o desactivar la traducción no corta, no pausa ni cambia el volumen del audio
  que se está escuchando.
- **CA-009**: Lo que la persona dice por su micrófono durante una llamada no aparece en los
  subtítulos.
- **CA-010**: La app se puede abrir, activar, desactivar y mover la franja de subtítulos usando
  solo el teclado.
- **CA-011**: Con el wifi apagado y el cable de red desconectado, la app traduce un video en inglés
  igual que con conexión (cumple CA-001 y CA-002).
- **CA-012**: Al abrir la app, la pantalla indica "sin internet". Para encender el modo en línea hay
  que hacerlo a propósito y aceptar un aviso. La primera vez, la app pide la clave y la región del
  servicio; con una clave inválida aparece un aviso en español y la app sigue en "sin internet".
  Con una clave válida, el modo en línea se ve claramente encendido, y al apagarlo la app vuelve a
  indicar "sin internet". Al cerrar y volver a abrir la app, la pantalla indica otra vez "sin
  internet", y encender el modo en línea ya no muestra el aviso.
- **CA-013**: Con el modo en línea encendido, al apagar el wifi aparece un aviso en español y los
  subtítulos siguen saliendo sin tener que reactivar nada.
- **CA-014**: Con la app abierta y la ventana de una llamada o un video en pantalla completa al
  frente, presionar Ctrl+Alt+T activa la traducción; volver a presionarlo la desactiva. En ambos
  casos el cambio se ve en menos de 1 segundo y no hay que cambiar de ventana.
- **CA-015**: Con la traducción activa, minimizar la ventana principal deja los subtítulos
  saliendo; cerrarla con la X hace que los subtítulos y el ícono de la barra de tareas desaparezcan
  en menos de 1 segundo.
- **CA-016**: La app se puede abrir, activar, desactivar, mover la franja de subtítulos y encender o
  apagar el modo en línea usando solo el mouse.

## Supuestos

- Un solo usuario por computadora; no hay cuentas ni inicio de sesión.
- La computadora (portátil o de escritorio) usa Windows 10 o posterior, como fija la constitución.
- "Accesible desde el escritorio y/o barra de tareas" se cubre con un acceso directo en el
  escritorio y un ícono en la barra de tareas.
- "Solo se inicia si el usuario la activa" significa que la traducción siempre empieza desactivada y
  que la app no arranca sola con Windows.
- Se traduce únicamente lo que sale por bocinas o audífonos; el micrófono queda fuera.
- Los subtítulos muestran solo el texto en español (no el inglés original).
- Las metas de calidad y rapidez (CA-001, CA-002) aplican al modo sin internet; el modo en línea
  debe igualarlas o superarlas.
- El modo en línea es la dependencia externa declarada y aprobada en esta spec, como exige la
  sección "Restricciones del producto" de la constitución.
- La calidad de la traducción se mide con habla clara; con mucho ruido o acentos difíciles puede
  bajar, y eso no se considera falla de la v0.
