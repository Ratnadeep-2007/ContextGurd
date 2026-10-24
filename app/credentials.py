"""Windows-current-user protection for optional OAuth tokens; never log token contents."""
import base64
import ctypes
import os
from ctypes import wintypes


class Blob(ctypes.Structure):
    _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_byte))]


def transform(value, decrypt=False):
    if os.name != 'nt':
        raise RuntimeError('OAuth token persistence requires Windows DPAPI; configure a scoped token through environment variables instead.')
    content = base64.b64decode(value) if decrypt else value.encode()
    buffer = ctypes.create_string_buffer(content)
    original = Blob(len(content), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    output = Blob()
    crypt = ctypes.windll.crypt32
    crypt.CryptProtectData.argtypes = [ctypes.POINTER(Blob), wintypes.LPCWSTR, ctypes.POINTER(Blob), ctypes.c_void_p,
                                       ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    crypt.CryptUnprotectData.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob), ctypes.c_void_p,
                                         ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    ctypes.windll.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    ctypes.windll.kernel32.LocalFree.restype = ctypes.c_void_p
    if decrypt:
        ok = crypt.CryptUnprotectData(ctypes.byref(original), None, None, None, None, 1, ctypes.byref(output))
    else:
        ok = crypt.CryptProtectData(ctypes.byref(original), 'ContextGuard OAuth', None, None, None, 1, ctypes.byref(output))
    if not ok:
        raise RuntimeError('Windows credential protection failed; token was not saved.')
    try:
        result = ctypes.string_at(output.data, output.size)
        return result.decode() if decrypt else base64.b64encode(result).decode()
    finally:
        ctypes.windll.kernel32.LocalFree(output.data)
