# Atribución de los audios de prueba

Todos los archivos están en WAV PCM de 16 bits, 16 kHz y mono.

| Archivo | Fuente | Licencia |
|---|---|---|
| `en_frase_01.wav` a `en_frase_10.wav` | LibriSpeech *test-clean* (Panayotov et al., 2015), lector 6930; los identificadores están en `en_frases.tsv` | CC BY 4.0 |
| `en_frases.tsv` | Transcripciones oficiales de LibriSpeech de esas frases | CC BY 4.0 |
| `en_pausa.wav` | `en_frase_01` + 10 s de silencio + `en_frase_02` (LibriSpeech 6930-75918-0000 y 6930-75918-0007) | CC BY 4.0 |
| `en_continuo.wav` | LibriSpeech *test-clean* 6930-75918-0003 (23.3 s de habla seguida) | CC BY 4.0 |
| `es_habla.wav` | Generado para este proyecto con la voz es-MX "Microsoft Sabina" de Windows (texto propio) | Creado por el proyecto |
| `musica.wav` | Acordes sintetizados para este proyecto (sin voz) | Creado por el proyecto |
| `silencio.wav` | 10 s de silencio digital | Creado por el proyecto |

LibriSpeech: V. Panayotov, G. Chen, D. Povey y S. Khudanpur, "Librispeech: an ASR corpus based on
public domain audio books", ICASSP 2015. Descarga: <https://www.openslr.org/12>.

Las frases en inglés se tomaron de `test-clean.tar.gz` leyéndolo en streaming y cortando en
cuanto hubo 10 frases de entre 2 y 5 s y una de más de 10 s.
