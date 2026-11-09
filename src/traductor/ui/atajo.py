"""Atajo global fijo Ctrl+Alt+T con RegisterHotKey (RF-016, RF-016a, contrato §5)."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Callable

from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication, QObject, Signal

ID_ATAJO = 0x5444  # "TD"
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_NOREPEAT = 0x4000
VK_T = 0x54
WM_HOTKEY = 0x0312
ERROR_HOTKEY_ALREADY_REGISTERED = 1409


class _User32:
    """Envoltura de las funciones de user32 que usa el atajo."""

    def __init__(self) -> None:
        self._dll = ctypes.WinDLL("user32", use_last_error=True)
        self._dll.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
        self._dll.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]

    def RegisterHotKey(self, hwnd, ident, mods, vk):  # noqa: N802
        return self._dll.RegisterHotKey(hwnd, ident, mods, vk)

    def UnregisterHotKey(self, hwnd, ident):  # noqa: N802
        return self._dll.UnregisterHotKey(hwnd, ident)

    def GetLastError(self):  # noqa: N802
        return ctypes.get_last_error()


class _Filtro(QAbstractNativeEventFilter):
    def __init__(self, al_presionar: Callable[[], None]) -> None:
        super().__init__()
        self._al_presionar = al_presionar

    def nativeEventFilter(self, tipo, mensaje):  # noqa: N802
        if tipo in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            msg = wintypes.MSG.from_address(int(mensaje))
            if msg.message == WM_HOTKEY and msg.wParam == ID_ATAJO:
                self._al_presionar()
                return True, 0
        return False, 0


class AtajoGlobal(QObject):
    presionado = Signal()

    def __init__(self, obtener_hwnd: Callable[[], int], user32=None) -> None:
        super().__init__()
        self._obtener_hwnd = obtener_hwnd
        self.user32 = user32 or _User32()
        self.filtro = _Filtro(self.presionado.emit)
        self._hwnd = None

    def registrar(self) -> bool:
        """Registra Ctrl+Alt+T. Devuelve False si no se puede (otra app ya lo usa)."""
        app = QCoreApplication.instance()
        if app is not None:
            app.installNativeEventFilter(self.filtro)
        hwnd = self._obtener_hwnd()
        if self.user32.RegisterHotKey(hwnd, ID_ATAJO, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, VK_T):
            self._hwnd = hwnd
            return True
        return False

    def liberar(self) -> None:
        if self._hwnd is not None:
            self.user32.UnregisterHotKey(self._hwnd, ID_ATAJO)
            self._hwnd = None
        app = QCoreApplication.instance()
        if app is not None:
            app.removeNativeEventFilter(self.filtro)
