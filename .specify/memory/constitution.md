# Constitución de TraductorIngles

TraductorIngles es una herramienta de escritorio para portátil que traduce al español de México
todo el audio en inglés que suena por las bocinas o los audífonos: llamadas, reuniones, videos o
cualquier audio de una plataforma en línea o de escritorio. Se ejecuta de forma local y la persona
usuaria la puede activar en cualquier momento. El proyecto nace con Desarrollo Guiado por
Especificaciones (SDD).

## Principios fundamentales

### I. Spec primero

- Todo comportamiento observable de la aplicación DEBE nacer de una spec aprobada en `specs/`.
- Todo cambio de comportamiento DEBE empezar por corregir la spec existente o crear una nueva,
  antes de tocar código.
- `specs/MAPA.md` DEBE listar cada spec con exactamente un propietario. Una spec sin propietario,
  o con más de uno, no se considera aprobada.
- Si el código y la spec no coinciden, manda la spec: se corrige el código o se enmienda la spec
  por el flujo normal, nunca se deja la diferencia.

**Razón**: la spec es la única fuente de verdad sobre qué hace la app; un solo propietario por spec
deja claro quién decide.

### II. Idioma: español de México

- Toda traducción que produzca la app DEBE estar en español de México (es-MX): vocabulario,
  ortografía y expresiones de uso común en México.
- Todo texto de la interfaz (botones, mensajes, errores, ayuda) DEBE estar en español de México.
- Las specs, planes, tareas y documentación del proyecto DEBEN escribirse en español de México.
  Los identificadores de código y los nombres técnicos pueden quedarse en inglés.

**Razón**: la app existe para que una persona hispanohablante de México entienda lo que escucha; la
misma regla para el producto y el proyecto evita mezclas de idioma.

### III. Cero alcance fantasma

- NO se DEBE implementar ninguna funcionalidad, opción, pantalla o comportamiento que no esté
  escrito en una spec aprobada.
- Una idea nueva que surja durante el diseño, la implementación o las pruebas se registra como
  propuesta (spec nueva o enmienda) y se queda fuera del código hasta que se apruebe.
- En la revisión de código, cualquier comportamiento que no se pueda rastrear a una spec es motivo
  de rechazo.

**Razón**: lo que no está en la spec no tiene criterio de aceptación ni test, y por lo tanto nadie
puede garantizar que funcione.

### IV. Los tests acompañan a la spec

- Cada regla de negocio y cada criterio de aceptación relevante de una spec DEBE tener al menos un
  test automatizado que la referencia por su identificador (por ejemplo, `FR-003` o `CA-2`).
- La suite completa de tests en verde es condición obligatoria para hacer merge. No se hace merge
  con tests fallando, omitidos sin justificación escrita o desactivados.
- Cuando cambia una spec, sus tests DEBEN actualizarse en el mismo cambio.

**Razón**: el test es la prueba ejecutable de que la spec se cumple; sin él la spec es solo una
intención.

### V. Verificable por una persona no técnica

- Cada criterio de éxito de una spec DEBE poder comprobarse usando la app, sin leer código, sin
  abrir una terminal y sin herramientas de desarrollo.
- Cada criterio se escribe como pasos concretos y un resultado observable, por ejemplo: "Reproduce
  un video en inglés; en menos de N segundos aparece el texto en español en la ventana".
- Un criterio que solo se puede verificar con conocimientos técnicos DEBE reescribirse antes de
  aprobar la spec.

**Razón**: quien usa la app es quien decide si funciona; si no lo puede comprobar, el criterio no
sirve.

### VI. Interfaz sencilla y accesible

- Una persona que abre la app por primera vez DEBE poder activar la traducción sin manual ni
  instrucciones externas.
- La interfaz DEBE ser accesible: se puede operar completa con teclado, el texto es legible (tamaño
  y contraste suficientes) y los controles tienen nombres claros.
- La app DEBE funcionar en una portátil común con Windows, sin hardware especial.
- Cada elemento de interfaz nuevo DEBE justificarse en una spec; ante la duda, menos controles.

**Razón**: la app se usa en medio de una llamada o un video, cuando no hay tiempo de aprender a
usarla.

## Restricciones del producto

- **Fuente de audio**: la app traduce el audio que la portátil reproduce por sus bocinas o
  audífonos, sin importar qué aplicación o plataforma lo genera.
- **Idiomas**: entrada en inglés; salida en español de México. Otros pares de idiomas quedan fuera
  de alcance salvo que una spec aprobada los agregue.
- **Ejecución local**: la app se instala y se ejecuta en la portátil de la persona usuaria. Si
  alguna parte del procesamiento (por ejemplo, reconocimiento de voz o traducción) dependiera de un
  servicio externo o de conexión a internet, esa dependencia DEBE declararse en la spec y aprobarse
  explícitamente antes de implementarse.
  TODO(EJECUCION_LOCAL): confirmar si "local" significa procesar audio y traducción sin internet.
- **Activación bajo demanda**: la persona usuaria puede activar y desactivar la traducción en
  cualquier momento, sin reiniciar la app ni la llamada o el video en curso.
- **Plataforma objetivo**: Windows 10 o posterior en portátil.

## Flujo de trabajo y puertas de calidad

1. **Spec**: se crea o corrige la spec en `specs/` y se registra su propietario en
   `specs/MAPA.md`.
2. **Aprobación**: el propietario aprueba la spec. Sin aprobación no se planea ni se implementa.
3. **Plan y tareas**: el plan DEBE incluir una revisión explícita contra los seis principios; toda
   excepción se documenta con su justificación.
4. **Implementación con tests**: el código y los tests que referencian la spec se entregan juntos.
5. **Revisión**: antes del merge se confirma que:
   - todo comportamiento nuevo se rastrea a la spec (Principio III);
   - cada regla y criterio relevante tiene su test (Principio IV);
   - la suite completa está en verde (Principio IV);
   - los textos visibles están en español de México (Principio II).
6. **Validación de uso**: los criterios de éxito se comprueban usando la app, siguiendo los pasos
   escritos en la spec (Principio V).

## Gobernanza

- Esta constitución está por encima de cualquier otra práctica o guía del proyecto. Si hay
  conflicto, manda la constitución.
- **Enmiendas**: toda enmienda se propone por escrito, explica el motivo y su impacto en las specs
  existentes, y se aprueba antes de aplicarse. Las specs afectadas se actualizan después de la
  enmienda.
- **Versionado** (versionado semántico):
  - MAJOR: se elimina o redefine un principio de forma incompatible.
  - MINOR: se agrega un principio o sección, o se amplía de forma importante una guía.
  - PATCH: aclaraciones, redacción o correcciones sin cambio de significado.
- **Cumplimiento**: cada plan y cada revisión de código verifican el cumplimiento de esta
  constitución. Toda complejidad o excepción debe justificarse por escrito.

**Versión**: 1.0.0 | **Ratificada**: 2026-11-08 | **Última enmienda**: 2026-11-08
