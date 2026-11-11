# Validación automática con la app instalada

Generado por `scripts/validar_instalada.py`. Cubre la parte mecánica de los pasos del
[quickstart](../quickstart.md) (parte B); lo que necesita a una persona está al final.

**Fecha**: 2026-11-10 13:11 | **Ejecutable**: `C:\Users\HP ZBook 15 G1\AppData\Local\Programs\TraductorIngles\TraductorIngles.exe`

## Resultados

| Paso | Criterio | Resultado | Observación |
|---|---|---|---|
| Arranque | CA-003 (parte medible) | Cumple | Lista para activar en 1.4 s (meta < 10 s; no es arranque en frío). |
| B1 | RF-001, CA-012 | Cumple | Dice «Traducción desactivada» y «Sin internet». |
| B2 | CA-007 | Cumple | 60 s de habla en inglés sin activar: no apareció ningún subtítulo. |
| B3 | RF-002, RF-005 | Cumple | Botón «Desactivar traducción» y estado «Traducción activa» a los 0.7 s. |
| B4 | CA-001 | A juicio de una persona | Salieron subtítulos en 10 de 10 frases; la tabla de abajo es para juzgar si se entienden 8 de 10. |
| B5 | CA-002 | Cumple | 10 de 10 subtítulos salieron en 3 s o menos tras el fin de la frase (meta: 9 de 10). Latencias: 2.1, 1.5, 1.8, 1.8, 2.2, 1.9, 2.5, 2.3, 2.0, 2.2. |
| B6 | CA-006 | Cumple | chrome en pantalla completa (sí); franja visible (sí) y encima del navegador (sí). Con apps de la Microsoft Store no aplica (fuera de alcance). |
| B7 | Historia 2 | Cumple | Frase, 10 s de pausa (de 3.5 a 13.5 s) y otra frase. Eventos: 5.8 s aparece, 9.8 s desaparece, 18.5 s aparece, 22.5 s desaparece. En la pausa el subtítulo se va tras 4 s sin habla y no salen nuevos. |
| B8 | RF-009 | Cumple | Arrastre con el mouse: de y=788 a y=20 (se quedó arriba). Mover subtítulos: instrucción visible (sí); 5 flechas a la izquierda la movieron de x=246 a x=121; Enter terminó el modo (sí). |
| B11a | Caso límite (salida en silencio) | Cumple | Con el sonido de Windows en silencio, el subtítulo se fue a los 4.4 s y no salieron nuevos en 12 s; la traducción siguió activa (sí) y la bitácora no registró errores (0 nuevos). Al quitar el silencio volvieron a los 9.1 s. |
| B13 | CA-004, CA-008 | Cumple | Al presionar «Desactivar traducción» la franja se fue en 218 ms (meta < 1 s). El volumen y el silencio de Windows no cambiaron (sí); el audio siguió sonando (pico 0.46). |
| B12 (video) | CA-014 | Cumple | Con chrome en pantalla completa al frente: Ctrl+Alt+T activó la traducción (sí); latencias de las frases: 2.3 s. Ctrl+Alt+T otra vez: la franja se fue en 106 ms. El navegador siguió al frente (sí). |
| B13a | CA-015 | Cumple | Minimizada, los subtítulos siguieron saliendo (sí). Al cerrar con la X: la franja se fue en 129 ms y la app (con su ícono) terminó en 394 ms (meta < 1 s). |

## Subtítulos de las 10 frases (para juzgar B4)

Juzga si el subtítulo transmite el sentido de la frase en inglés. Meta: 8 de 10.

| Frase | En inglés | Subtítulo | Latencia |
|---|---|---|---|
| en_frase_01.wav | CONCORD RETURNED TO ITS PLACE AMIDST THE TENTS | El acorde de peón volvió a su lugar en medio de las tiendas. | 2.1 s |
| en_frase_02.wav | YOU WILL BE FRANK WITH ME I ALWAYS AM | Siempre lo soy. | 1.5 s |
| en_frase_03.wav | CAN YOU IMAGINE WHY BUCKINGHAM HAS BEEN SO VIOLENT I SUSPECT | ¿Se imagina por qué Buckingham ha sido tan violento? | 1.8 s |
| en_frase_04.wav | I CAN PERCEIVE LOVE CLEARLY ENOUGH | Puedo percibir el amor con suficiente claridad. | 1.8 s |
| en_frase_05.wav | I AM CONVINCED OF WHAT I SAY SAID THE COUNT | convencido de lo que digo, dijo el conde. | 2.2 s |
| en_frase_06.wav | IN THOSE VERY TERMS I EVEN ADDED MORE | en esos mismos términos, incluso añadí más. | 1.9 s |
| en_frase_07.wav | NOW WHAT WAS THE SENSE OF IT TWO INNOCENT BABIES LIKE THAT | ¿Qué sentido tiene? | 2.5 s |
| en_frase_08.wav | HERS HAPPENED TO BE IN THE SAME FRAME TOO BUT SHE EVIDENTLY DIDN'T CARE ABOUT THAT | Heres estaba en el mismo cuadro 2, pero evidentemente no le importaba. | 2.3 s |
| en_frase_09.wav | NOW WHAT HAVE YOU TO SAY CYNTHIA SPRAGUE | ¿Qué tienes que decir, Cynthia Sprague? | 2.0 s |
| en_frase_10.wav | IT CAN'T HURT ANYTHING I'M SURE FOR WE WON'T DISTURB THINGS AT ALL | Estoy seguro de que no vamos a molestar nada. | 2.2 s |

## Capturas

- `C:\Users\HPZBOO~1\AppData\Local\Temp\TraductorIngles-validacion-20261110-131102\b6_pantalla_completa.png`

## Quedan a mano

| Paso | Por qué |
|---|---|
| B4 | Leer la tabla de subtítulos de este reporte (o ver un video real) y juzgar si se entienden al menos 8 de 10 frases. |
| B9 | Necesita una llamada real con otra persona y un podcast en un reproductor de escritorio. |
| B10 | Necesita hablar por el micrófono durante una llamada real. |
| B11 | Necesita conectar y desconectar audífonos durante una llamada. |
| B12 (llamada) | La parte con la ventana de una llamada al frente necesita una llamada real. |
| B14 | Se trata de que una persona pueda usarla solo con el teclado. |
| B14a | Se trata de que una persona pueda usarla solo con el mouse. |
| B15 | Necesita apagar el wifi y desconectar el cable de red. |
| B16 a B19 | Modo en línea: necesita la clave real, apagar el wifi y la primera vez de la instalación (el script no la gasta). |
| Personas nuevas (CA-003) | 10 personas que nunca hayan usado la app. |
