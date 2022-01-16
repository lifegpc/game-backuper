from ctypes import HRESULT, byref, c_uint, windll
from ctypes.wintypes import (
    DWORD, HANDLE, LARGE_INTEGER, LPCWSTR, LPVOID, PHANDLE
)


dll = windll.CldApi
CF_OPEN_FILE_FLAG_NONE = 0
CF_OPEN_FILE_FLAG_EXCLUSIVE = 1
CF_OPEN_FILE_FLAG_WRITE_ACCESS = 2
CF_OPEN_FILE_FLAG_DELETE_ACCESS = 3
CF_OPEN_FILE_FLAG_FOREGROUND = 4
CfOpenFileWithOplock = dll.CfOpenFileWithOplock
CfOpenFileWithOplock.argtypes = [LPCWSTR, c_uint, PHANDLE]
CfOpenFileWithOplock.restype = HRESULT
CfHydratePlaceholder = dll.CfHydratePlaceholder
CfHydratePlaceholder.argtypes = [HANDLE, LARGE_INTEGER, LARGE_INTEGER, c_uint, LPVOID]  # noqa: E501
CfHydratePlaceholder.restype = HRESULT
CfCloseHandle = dll.CfCloseHandle
CfCloseHandle.argtypes = [HANDLE]
ERROR_INVALID_FUNCTION = 1
GetLastError = windll.Kernel32.GetLastError
GetLastError.restype = DWORD


def hydrate_file(s: str):
    h = HANDLE()
    try:
        CfOpenFileWithOplock(s, CF_OPEN_FILE_FLAG_NONE, byref(h))
        CfHydratePlaceholder(h, 0, -1, 0, LPVOID())
    except OSError as e:
        if GetLastError() != ERROR_INVALID_FUNCTION:
            CfCloseHandle(h)
            raise e
    CfCloseHandle(h)
