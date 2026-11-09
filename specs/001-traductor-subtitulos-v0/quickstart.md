# Guía de validación (quickstart): TraductorIngles v0

**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

Explica cómo preparar el entorno, correr las pruebas automáticas y validar a mano los criterios de
éxito de la spec. La parte B está pensada para que la siga una persona no técnica (Principio V).

---

## Parte A: Desarrollo (persona técnica)

### A1. Requisitos previos (una sola vez)

```powershell
winget install Python.Python.3.12
winget install Microsoft.VCRedist.2015+.x64
winget install JRSoftware.InnoSetup        # solo para generar el instalador
```

Después, desactiva el alias de la Microsoft Store para `python` en *Configuración > Aplicaciones >
Alias de ejecución de aplicaciones* y vuelve a abrir la terminal.

### A2. Entorno del proyecto

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
```

### A3. Modelos (una sola vez, necesita internet)

```powershell
python scripts\preparar_modelos.py      # descarga Whisper small/base y convierte OPUS-MT en-es a CTranslate2
```

Resultado esperado: carpeta `modelos\` con `whisper-small\`, `whisper-base\` y `opus-mt-en-es-ct2\`.

### A4. Medición de latencia (la primera tarea técnica; research R-12)

```powershell
python scripts\medir_latencia.py --modelo small
```

Resultado esperado: una tabla con los tiempos por etapa y el percentil 90 del total. **Si pasa de
3.0 s**, repítela con `--modelo base` y registra la decisión en `research.md`.

### A5. Pruebas automáticas

```powershell
pytest -m "not modelos"        # unitarias + interfaz: rápidas, sin modelos
pytest                         # suite completa (requiere A3); obligatoria en verde para el merge
```

`tests/test_trazabilidad.py` falla si algún `RF-xxx` o `CA-xxx` de la spec no tiene test o
justificación manual en `tests/solo_manuales.toml` (Principio IV).

### A6. Correr la app sin instalar

```powershell
python -m traductor
```

### A7. Generar el instalador

```powershell
pyinstaller instalador\traductor.spec
iscc instalador\traductor.iss          # genera dist\TraductorIngles-Setup.exe
```

---

## Parte B: Validación de uso (cualquier persona, con la app instalada)

Prepara antes: un video en inglés con habla clara en el navegador (10 frases conocidas), un podcast
o nota de voz en inglés en un reproductor de escritorio, y una llamada de prueba con otra persona
que hable en inglés.

| Paso | Qué hacer | Qué debe pasar | Criterio |
|---|---|---|---|
| B1 | Busca "TraductorIngles" en el escritorio y ábrelo. | Se abre la ventana. Dice "Traducción desactivada" y "Sin internet". | RF-001, CA-012 |
| B2 | Con la app abierta, sin activar nada, reproduce el video 1 minuto. | No aparece ningún subtítulo. | CA-007 |
| B3 | Presiona **Activar traducción**. | El botón cambia a "Desactivar traducción" y el estado a "Traducción activa". | RF-002, RF-005 |
| B4 | Reproduce las 10 frases del video. | Aparecen subtítulos en español, de 2 líneas como máximo; entiendes al menos 8 de 10 frases. | CA-001 |
| B5 | Cuenta mentalmente desde que termina cada frase. | El subtítulo sale en 3 segundos o menos. | CA-002 |
| B6 | Pon el video en pantalla completa. | Los subtítulos siguen encima. | CA-006 |
| B7 | Pausa el video 10 s y luego reanúdalo. | En la pausa el subtítulo desaparece y no salen nuevos; al reanudar vuelven. | Historia 2 |
| B8 | Arrastra la franja con el mouse a la parte de arriba. Luego presiona **Mover subtítulos**, muévela con las flechas a la izquierda y presiona Enter. | Las dos veces la franja se queda donde la dejaste; durante el modo de mover se ve resaltada con la instrucción. | RF-009 |
| B9 | Repite B4 con el podcast y con la llamada. | Funciona igual con las tres fuentes. | CA-005 |
| B10 | En la llamada, habla tú por el micrófono. | Lo que dices no aparece en los subtítulos. | CA-009 |
| B11 | Durante la llamada, cambia de bocinas a audífonos. | Los subtítulos siguen sin reactivar nada. | Caso límite |
| B12 | Con la ventana de la llamada al frente, presiona **Ctrl+Alt+T** dos veces. | La primera vez se desactiva y la segunda se activa; el cambio se ve en menos de 1 s y no cambias de ventana. | CA-014 |
| B13 | Presiona **Desactivar traducción**. | Los subtítulos desaparecen en menos de 1 s; el audio no se corta ni cambia de volumen. | CA-004, CA-008 |
| B13a | Activa otra vez la traducción y, con el video sonando, minimiza la ventana de TraductorIngles. Después ábrela desde la barra de tareas y ciérrala con la X. | Al minimizar, los subtítulos siguen saliendo; al cerrar, desaparecen la franja y el ícono en menos de 1 s. | CA-015 |
| B14 | Abre la app y úsala **solo con el teclado** (Win, escribe "Traductor", Enter, Enter, Tab…): activa, desactiva y mueve la franja con **Mover subtítulos** y las flechas. | Puedes hacer todo sin tocar el mouse. | CA-010 |
| B14a | Cierra la app. Ábrela y úsala **solo con el mouse** (doble clic en el acceso del escritorio): activa, desactiva, arrastra la franja, enciende y apaga **Modo en línea**. | Puedes hacer todo sin tocar el teclado (salvo escribir la clave la primera vez). | CA-016 |
| B15 | Apaga el wifi y desconecta el cable de red. Repite B3 a B5. | Funciona igual que con internet. | CA-011 |
| B16 | Enciende **Modo en línea** (primera vez en esta instalación). | Aparece un aviso de que el audio saldrá del equipo. Al aceptarlo, la app pide la clave y la región. | CA-012 |
| B16a | Escribe una clave **inventada** y presiona **Guardar y activar**. | Aparece "No se pudo activar el modo en línea: revisa la clave y la región…" y el indicador sigue en "Sin internet". | CA-012, RF-015c |
| B16b | Enciende otra vez **Modo en línea** y escribe la clave y la región correctas. | Ya no sale el aviso, solo el cuadro de la cuenta. Al guardar, el indicador dice "En línea: el audio sale del equipo". | CA-012 |
| B17 | Con el modo en línea y el video sonando, apaga el wifi. | Aparece "Se perdió la conexión a internet. Seguimos traduciendo sin internet." y los subtítulos siguen saliendo. | CA-013 |
| B18 | Prende el wifi y apaga **Modo en línea**. | El indicador vuelve a "Sin internet". | CA-012 |
| B19 | Cierra la app, ábrela otra vez y enciende **Modo en línea**. | Al abrir dice "Sin internet". Al encenderlo, ya no sale ni el aviso ni el cuadro de la cuenta: pasa directo a "En línea". | CA-012 |

**Prueba con personas nuevas (CA-003)**: 10 personas que nunca hayan usado la app, sin
instrucciones, con la app instalada y un video en inglés sonando. Se mide si logran abrirla y
activar la traducción en menos de 10 s al primer intento. Meta: 9 de 10.
