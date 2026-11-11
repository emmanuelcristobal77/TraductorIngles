# Validación de uso: TraductorIngles v0

**Spec**: [../spec.md](../spec.md) | **Pasos**: [../quickstart.md](../quickstart.md), parte B

La llena una persona con la app **instalada** (T078). En cada paso anota **Cumple** o **No
cumple** y una observación breve.

**Fecha**: 2026-11-10 | **Equipo**: equipo de referencia (HP ZBook 15 G1) | **Versión del instalador**: ____ | **Quién prueba**: ____

## Parte B

| Paso | Criterio | Resultado | Observación |
|---|---|---|---|
| B1 | RF-001, CA-012 | Cumple | Automático (2026-11-10): cumple; ver [validacion-automatica.md](validacion-automatica.md). |
| B2 | CA-007 | Cumple | Automático (2026-11-10): cumple; ver [validacion-automatica.md](validacion-automatica.md). |
| B3 | RF-002, RF-005 | Cumple | Automático (2026-11-10): cumple; ver [validacion-automatica.md](validacion-automatica.md). |
| B4 | CA-001 | Cumple | 8 / 10 frases entendidas con un video de habla clara. Con videos de música no traduce bien (fuera de alcance: el paso pide habla clara). |
| B5 | CA-002 | Cumple | 10 / 10 en 3 s o menos, medido por el script (latencias de 1.5 a 2.5 s). A mano también se vio a tiempo. |
| B6 | CA-006 | Cumple (con límite) | Primera prueba con el Reproductor multimedia en pantalla completa (F11): la franja quedó detrás. Causa: es una app de la Microsoft Store y Windows la pone por encima de toda ventana "siempre encima". Con Chrome en pantalla completa (F11) la franja sí se ve encima (comprobado con captura de pantalla). Se documenta como fuera de alcance (spec, enmienda 2026-11-10). Automático (2026-11-10): cumple; ver [validacion-automatica.md](validacion-automatica.md). |
| B7 | Historia 2 | Cumple | En la pausa el último subtítulo se queda unos segundos y después desaparece (la spec pide 4 s sin habla); al reanudar vuelven. Automático (2026-11-10): cumple; ver [validacion-automatica.md](validacion-automatica.md). |
| B8 | RF-009 | Cumple | Automático (2026-11-10): cumple; ver [validacion-automatica.md](validacion-automatica.md). |
| B9 | CA-005 | Pendiente | Falta la llamada. |
| B10 | CA-009 | Pendiente | Necesita una llamada. |
| B11 | Caso límite (cambio de dispositivo) | | |
| B11a | Caso límite (salida en silencio) | Cumple | Automático (2026-11-10): cumple; ver [validacion-automatica.md](validacion-automatica.md). |
| B12 | CA-014 | Parcial | Con el video en pantalla completa: cumple (automático, 2026-11-10). Falta repetirlo con la ventana de una llamada al frente. |
| B13 | CA-004, CA-008 | Cumple | Automático (2026-11-10): cumple; ver [validacion-automatica.md](validacion-automatica.md). |
| B13a | CA-015 | Cumple | Automático (2026-11-10): cumple; ver [validacion-automatica.md](validacion-automatica.md). |
| B14 | CA-010, RF-014 | Cumple | Todo se hizo solo con el teclado. |
| B14a | CA-016 | Cumple | Todo se hizo solo con el mouse. |
| B15 | CA-011 | Cumple | Todas las pruebas se hicieron en modo sin internet (el predeterminado). |
| B16 | CA-012 | Cumple | Apareció el aviso de que el audio saldrá del equipo y después el cuadro de la clave y la región. |
| B16a | CA-012, RF-015c | Cumple | Con una clave inventada salió "No se pudo activar el modo en línea: revisa la clave y la región…" y el indicador siguió en "Sin internet". La bitácora solo registró el tipo de error (HTTPError), sin la clave. |
| B16b | CA-012 | | |
| B16c | Supuestos (CA-001, CA-002 en línea) | | |
| B17 | CA-013 | | |
| B18 | CA-012 | | |
| B19 | CA-012 | | |

## Prueba con personas nuevas (CA-003)

| Persona | ¿Abrió y activó en menos de 10 s al primer intento? | Observación |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |
| 6 | | |
| 7 | | |
| 8 | | |
| 9 | | |
| 10 | | |

**Resultado**: omitida por decisión del propietario (2026-11-10): la app es de uso personal y solo la usa una persona. Es **obligatoria** antes de darla a otras personas. La parte medible (abrir y quedar lista en menos de 10 s) sí se comprobó: 6.5 s en frío (T077).

## Revisión final contra la constitución (T079)

- [ ] **Principio III**: todo comportamiento se rastrea a la spec.
- [ ] **Principio II**: todos los textos visibles salen de `textos.py` y están en es-MX.
- [ ] **R-13**: no hay escrituras de audio, texto ni clave en disco ni en la bitácora.
- [ ] **Principio IV**: la suite completa está en verde.
