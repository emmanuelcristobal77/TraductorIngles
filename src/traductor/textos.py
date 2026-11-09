"""Todos los textos visibles de TraductorIngles, en español de México (Principio II).

Cada texto se copia tal cual de ``specs/001-traductor-subtitulos-v0/contracts/interfaz-usuario.md``.
Ningún otro módulo escribe texto visible directamente.
"""

NOMBRE_APP = "TraductorIngles"

# §1 Ventana principal
UI01_ACTIVAR = "Activar traducción"
UI01_DESACTIVAR = "Desactivar traducción"
UI01_ATAJO = "Ctrl+Alt+T"
UI01_NOMBRE_ACTIVAR = "Activar traducción, atajo Control Alt T"
UI01_NOMBRE_DESACTIVAR = "Desactivar traducción, atajo Control Alt T"

UI02_DESACTIVADA = "Traducción desactivada"
UI02_PREPARANDO = "Preparando la traducción…"
UI02_ACTIVA = "Traducción activa"

UI03_SIN_INTERNET = "Sin internet"
UI03_EN_LINEA = "En línea: el audio sale del equipo"

UI04_TEXTO = "Modo en línea"
UI04_NOMBRE_APAGADO = "Modo en línea, apagado"
UI04_NOMBRE_ENCENDIDO = "Modo en línea, encendido"

UI05_NOMBRE = "Mensaje"

UI06_TEXTO = "Mover subtítulos"
UI06_NOMBRE = "Mover subtítulos con las flechas"

# §2.1 Modo de mover
INSTRUCCION_MOVER = "Usa las flechas para mover los subtítulos. Enter o Esc para terminar."

# §3 Cuadros de diálogo
D01_SI = "Sí, usar en línea"
D01_NO = "No, seguir sin internet"

D02_EXPLICACION = (
    "Escribe la clave y la región de tu servicio de traducción en internet. "
    "Se guardan cifradas solo en esta computadora."
)
D02_ETIQUETA_CLAVE = "Clave"
D02_NOMBRE_CLAVE = "Clave del servicio"
D02_ETIQUETA_REGION = "Región"
D02_NOMBRE_REGION = "Región del servicio"
D02_GUARDAR = "Guardar y activar"
D02_COMPROBANDO = "Comprobando…"
D02_CANCELAR = "Cancelar"

# §4 Ícono del área de notificación
TOOLTIP_DESACTIVADA = "TraductorIngles: traducción desactivada"
TOOLTIP_PREPARANDO = "TraductorIngles: preparando la traducción"
TOOLTIP_ACTIVA = "TraductorIngles: traducción activa"
MENU_ACTIVAR = "Activar traducción"
MENU_DESACTIVAR = "Desactivar traducción"
MENU_ABRIR = "Abrir TraductorIngles"
MENU_SALIR = "Salir"
AVISO_TITULO = "TraductorIngles"

# §6 Catálogo de mensajes
MENSAJES = {
    "M-01": (
        "En el modo en línea, el audio que suena en tu computadora se envía por internet a un "
        "servicio de traducción. ¿Quieres activarlo?"
    ),
    "M-02": "No encontramos bocinas ni audífonos. Conecta uno y vuelve a activar la traducción.",
    "M-03": (
        "No pudimos escuchar el audio de la computadora. "
        "Desactiva y vuelve a activar la traducción."
    ),
    "M-04": (
        "No pudimos traducir lo último que se dijo. "
        "Si se repite, desactiva y vuelve a activar la traducción."
    ),
    "M-05": (
        "No se pudo preparar la traducción. "
        "Cierra la app y vuelve a abrirla; si sigue pasando, reinstálala."
    ),
    "M-06": (
        "Otra aplicación ya usa Ctrl+Alt+T. "
        "Usa el botón o el ícono de la barra de tareas para activar la traducción."
    ),
    "M-07": "Se perdió la conexión a internet. Seguimos traduciendo sin internet.",
    "M-08": (
        "No se pudo activar el modo en línea: revisa la clave y la región. "
        "Seguimos traduciendo sin internet."
    ),
    "M-09": (
        "No se pudo activar el modo en línea porque no hay conexión a internet. "
        "Seguimos traduciendo sin internet."
    ),
}

# Nombres accesibles de cada control (RF-014): ninguno puede quedar vacío.
NOMBRES_ACCESIBLES = {
    "UI-01 desactivada": UI01_NOMBRE_ACTIVAR,
    "UI-01 preparando o activa": UI01_NOMBRE_DESACTIVAR,
    "UI-02": UI02_DESACTIVADA,
    "UI-03": UI03_SIN_INTERNET,
    "UI-04 apagado": UI04_NOMBRE_APAGADO,
    "UI-04 encendido": UI04_NOMBRE_ENCENDIDO,
    "UI-05": UI05_NOMBRE,
    "UI-06": UI06_NOMBRE,
    "D-02 clave": D02_NOMBRE_CLAVE,
    "D-02 región": D02_NOMBRE_REGION,
    "D-02 guardar": D02_GUARDAR,
    "D-02 cancelar": D02_CANCELAR,
}
