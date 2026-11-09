# Contrato interno: motores de traducción

**Spec**: [../spec.md](../spec.md) | **Plan**: [../plan.md](../plan.md)

Es la interfaz entre el flujo de audio y los dos modos de procesamiento. Gracias a ella se puede
probar el respaldo sin internet (RF-015b) con motores falsos, sin modelos ni red.

---

## 1. Protocolo `MotorTraduccion`

```python
class MotorTraduccion(Protocol):
    nombre: Literal["LOCAL", "EN_LINEA"]

    def preparar(self) -> None:
        """Carga modelos o abre la conexión. Puede tardar; se llama fuera del hilo de la interfaz.
        Lanza ErrorPreparacion si no se puede."""

    def traducir(self, frase: Frase) -> ResultadoMotor:
        """Convierte una frase de audio en inglés a texto en español (sin el glosario).
        Devuelve texto_es=None si la frase se descarta.
        Lanza ErrorConexion o ErrorAutenticacion (solo EN_LINEA), o ErrorMotor."""

    def cerrar(self) -> None:
        """Libera los recursos. Se puede llamar más de una vez."""
```

`Frase` y `ResultadoMotor` están definidos en [../data-model.md](../data-model.md).

## 2. `MotorLocal`

| Garantía | Detalle | Requisito |
|---|---|---|
| Sin red | No abre ningún socket. Un test lo verifica bloqueando `socket.socket` durante `traducir`. | RF-015, CA-011 |
| Idioma | Descarta si `language != "en"` o `language_probability < 0.6` (`OTRO_IDIOMA`). | Caso límite: otro idioma |
| Sin voz | Descarta si `no_speech_prob > 0.6` (`SIN_VOZ`) o `avg_logprob < -1.0` (`BAJA_CONFIANZA`). | RF-012 |
| Latencia | Percentil 90 ≤ 2.0 s por frase de hasta 5 s en el equipo de referencia (voz a texto + traducción). | CA-002 |

## 3. `MotorEnLinea`

| Garantía | Detalle | Requisito |
|---|---|---|
| Solo con permiso | Solo se crea si `ModoProcesamiento == EN_LINEA`, que exige el aviso aceptado y una `CuentaEnLinea` validada ([../data-model.md](../data-model.md)). | RF-015a |
| Errores de red | Un `canceled` con error de red, una desconexión o 10 s sin respuesta lanzan `ErrorConexion`. | RF-015b |
| Cuenta rechazada | Un `canceled` con error de autenticación (clave revocada o región incorrecta) lanza `ErrorAutenticacion`. | RF-015c |
| Datos enviados | Solo el audio de las frases de la sesión activa; nunca audio con la traducción desactivada. | RF-004, RF-015a |

## 4. `SelectorMotor`

```python
class SelectorMotor:
    def __init__(self, local: MotorTraduccion, en_linea_factory: Callable[[], MotorTraduccion]): ...
    def usar_en_linea(self) -> None: ...      # lanza ErrorPreparacion → el modo sigue SIN_INTERNET
    def usar_local(self) -> None: ...
    def traducir(self, frase: Frase) -> ResultadoMotor: ...
```

**Comportamiento obligatorio** (con tests unitarios marcados `RF-015b`, `RF-015c` y `CA-013`):

1. Con el modo `EN_LINEA`, si `traducir` recibe `ErrorConexion`:
   - cierra el motor en línea;
   - traduce **la misma frase** con el `MotorLocal`, para no perderla;
   - emite el evento `conexion_perdida`, con el que la interfaz muestra M-07 y cambia UI-03 y UI-04
     a "Sin internet";
   - **no** cambia el `EstadoTraduccion`.
2. Con el modo `EN_LINEA`, si `traducir` recibe `ErrorAutenticacion`, hace lo mismo que en el punto
   1, pero emite `cuenta_rechazada` en vez de `conexion_perdida`: la interfaz muestra M-08 y se
   borra la cuenta guardada (RF-015c).
3. Con el modo `SIN_INTERNET`, nunca llama al motor en línea.
4. Un `ErrorMotor` del motor local emite `error_motor` (la interfaz muestra M-04) y el flujo sigue
   con la siguiente frase.

## 5. Postproceso común

Después de cualquier motor: `texto_es` → `Glosario.aplicar()` → `Subtitulo`. El glosario es
idempotente: aplicarlo dos veces da el mismo resultado.
