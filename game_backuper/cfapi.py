from ctypes import HRESULT, POINTER, Structure, Union, byref, c_uint, sizeof, windll  # noqa: E501
from ctypes.wintypes import BYTE, DWORD, HANDLE, LARGE_INTEGER, LPCWSTR, LPVOID, PDWORD, PHANDLE, ULONG, WPARAM  # noqa: E501


ULONG_PTR = WPARAM
PVOID = LPVOID
dll = windll.CldApi
CF_HYDRATE_FLAG_NONE = 0
CF_IN_SYNC_STATE_NOT_IN_SYNC = 0
CF_IN_SYNC_STATE_IN_SYNC = 1
CF_OPEN_FILE_FLAG_NONE = 0
CF_OPEN_FILE_FLAG_EXCLUSIVE = 1
CF_OPEN_FILE_FLAG_WRITE_ACCESS = 2
CF_OPEN_FILE_FLAG_DELETE_ACCESS = 3
CF_OPEN_FILE_FLAG_FOREGROUND = 4
CF_PIN_STATE_UNSPECIFIED = 0
CF_PIN_STATE_PINNED = 1
CF_PIN_STATE_UNPINNED = 2
CF_PIN_STATE_EXCLUDED = 3
CF_PIN_STATE_INHERIT = 4
CF_PLACEHOLDER_INFO_BASIC = 0
CF_PLACEHOLDER_INFO_STANDARD = 1
CF_SET_PIN_FLAG_NONE = 0x00000000
CF_SET_PIN_FLAG_RECURSE = 0x00000001
CF_SET_PIN_FLAG_RECURSE_ONLY = 0x00000002
CF_SET_PIN_FLAG_RECURSE_STOP_ON_ERROR = 0x00000004


class CF_PLACEHOLDER_BASIC_INFO(Structure):
    _fields_ = [("PinState", c_uint),
                ("InSyncState", c_uint),
                ("FileId", LARGE_INTEGER),
                ("SyncRootFileId", LARGE_INTEGER),
                ("FileIdentityLength", ULONG),
                ("FileIdentity", BYTE)]


class CF_PLACEHOLDER_STANDARD_INFO(Structure):
    _fields_ = [("OnDiskDataSize", LARGE_INTEGER),
                ("ValidatedDataSize", LARGE_INTEGER),
                ("ModifiedDataSize", LARGE_INTEGER),
                ("PropertiesSize", LARGE_INTEGER),
                ("PinState", c_uint),
                ("InSyncState", c_uint),
                ("FileId", LARGE_INTEGER),
                ("SyncRootFileId", LARGE_INTEGER),
                ("FileIdentityLength", ULONG),
                ("FileIdentity", BYTE)]


class DUMMYSTRUCTNAME(Structure):
    _fields_ = [("Offset", DWORD), ("OffsetHigh", DWORD)]


class DUMMYUNIONNAME(Union):
    _fields_ = [("DUMMYSTRUCTNAME", DUMMYSTRUCTNAME), ("Pointer", PVOID)]


class OVERLAPPED(Structure):
    _fields_ = [("Internal", ULONG_PTR),
                ("InternalHigh", ULONG_PTR),
                ("DUMMYUNIONNAME", DUMMYUNIONNAME),
                ("hEvent", HANDLE)]


LPOVERLAPPED = POINTER(OVERLAPPED)
CfOpenFileWithOplock = dll.CfOpenFileWithOplock
CfOpenFileWithOplock.argtypes = [LPCWSTR, c_uint, PHANDLE]
CfOpenFileWithOplock.restype = HRESULT
CfHydratePlaceholder = dll.CfHydratePlaceholder
CfHydratePlaceholder.argtypes = [HANDLE, LARGE_INTEGER, LARGE_INTEGER, c_uint, LPVOID]  # noqa: E501
CfHydratePlaceholder.restype = HRESULT
CfCloseHandle = dll.CfCloseHandle
CfCloseHandle.argtypes = [HANDLE]
CfGetPlaceholderInfo = dll.CfGetPlaceholderInfo
CfGetPlaceholderInfo.argtypes = [HANDLE, c_uint, PVOID, DWORD, PDWORD]  # noqa: E501
CfGetPlaceholderInfo.restype = HRESULT
CfSetPinState = dll.CfSetPinState
CfSetPinState.argtypes = [HANDLE, c_uint, c_uint, LPOVERLAPPED]
CfSetPinState.restype = HRESULT
ERROR_INVALID_FUNCTION = 1
ERROR_MORE_DATA = 234
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


def get_info(s: str, standard: bool = False):
    h = HANDLE()
    i = CF_PLACEHOLDER_STANDARD_INFO() if standard else CF_PLACEHOLDER_BASIC_INFO()  # noqa: E501
    t = CF_PLACEHOLDER_INFO_STANDARD if standard else CF_PLACEHOLDER_INFO_BASIC
    le = DWORD()
    si = DWORD(sizeof(i))
    try:
        CfOpenFileWithOplock(s, CF_OPEN_FILE_FLAG_FOREGROUND, byref(h))
        CfGetPlaceholderInfo(h, t, byref(i), si, byref(le))
    except OSError as e:
        ee = GetLastError()
        if ee == ERROR_MORE_DATA:
            CfCloseHandle(h)
            return i
        if ee != ERROR_INVALID_FUNCTION:
            CfCloseHandle(h)
            raise e
    CfCloseHandle(h)
    return i


def unpin_file(s: str):
    h = HANDLE()
    try:
        CfOpenFileWithOplock(s, CF_OPEN_FILE_FLAG_FOREGROUND, byref(h))
        CfSetPinState(h, CF_PIN_STATE_UNPINNED, CF_SET_PIN_FLAG_NONE, None)
    except OSError as e:
        if GetLastError() != ERROR_INVALID_FUNCTION:
            CfCloseHandle(h)
            raise e
    CfCloseHandle(h)
