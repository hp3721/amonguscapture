from ctypes import *
from ctypes.wintypes import *
import psutil, platform, win32api, win32process, struct, sys

class ProcessMemory():
    def __init__(self):
        self.WinAPI = self.WinAPI()

        self.processPid = -1
        self.processHandler = None
        self.modules = []
        self.IsHooked = False

    def getpid(self, nameprocess: str):
        for process in psutil.process_iter():
            try:
                if nameprocess in process.name():
                    return process.pid
            except (PermissionError, psutil.AccessDenied):
                continue
        return -1

    def HookProcess(self, name: str):
        self.IsHooked = self.processHandler != None and psutil.pid_exists(self.processPid)
        if not self.IsHooked:
            self.processPid = self.getpid(name)
            if self.processPid != -1:
                self.processHandler = win32api.OpenProcess(0x410, 0, self.processPid)
                if self.processHandler != None and psutil.pid_exists(self.processPid):
                    moduleIds = win32process.EnumProcessModulesEx(self.processHandler, 0x3)
                    if len(moduleIds) > 0:
                        for moduleId in moduleIds:
                            moduleName = self.WinAPI.GetModuleBaseName(self.processHandler, c_void_p(moduleId))
                            moduleInfo = self.WinAPI.GetModuleInformation(self.processHandler, c_void_p(moduleId))
                            m = self.Module()
                            m.BaseAddress = moduleInfo.BaseAddress
                            m.Name = moduleName
                            self.modules.append(m)
                    self.IsHooked = True
        return self.IsHooked

    def ReadPointer(self, address: int, offsets: list, numBytes: int):
        if self.processHandler == None or address == 0:
            return 0
        
        for ofs in offsets[:-1]:
            buffer = self.Read(address + ofs, 4)
            address = struct.unpack('<L', buffer)[0]
            if address == 0:
                break
        last = offsets[-1] if len(offsets) > 0 else 0
        b = self.Read(address + last, numBytes)
        return b

    def ReadString(self, address: int):
        if self.processHandler == None or address == 0:
            return 0

        stringLength = struct.unpack('<L', self.Read(address + 0x8, 4))[0]
        rawString = bytes(self.Read(address + 0xC, stringLength << 1))
        return rawString.decode("utf16")

    def Read(self, address: int, numBytes: int):
        if self.processHandler == None or address == 0:
            return 0

        data = self.WinAPI.ReadProcessMemory(self.processHandler, address, numBytes)
        return data

    class WinAPI():
        @staticmethod
        def GetModuleBaseName(processHandle, moduleId):
            _GetModuleBaseNameW = WinDLL("psapi").GetModuleBaseNameW
            _GetModuleBaseNameW.argtypes = [HANDLE, HMODULE, LPWSTR, DWORD]
            _GetModuleBaseNameW.restype = ctypes.c_ulong
            moduleBaseName = ctypes.create_unicode_buffer(260)
            _GetModuleBaseNameW(processHandle.handle, moduleId, moduleBaseName, 260)
            return moduleBaseName.value

        @staticmethod
        def GetModuleInformation(processHandle, moduleId):
            _GetModuleInformation = WinDLL("psapi").GetModuleInformation
            _GetModuleInformation.argtypes = [HANDLE, HMODULE, POINTER(ProcessMemory.ModuleInfo), DWORD]
            _GetModuleInformation.restype = BOOL
            moduleInfo = ProcessMemory.ModuleInfo()
            _GetModuleInformation(processHandle.handle, moduleId, byref(moduleInfo), sizeof(moduleInfo))
            return moduleInfo

        @staticmethod
        def ReadProcessMemory(processHandle, address, numBytes):
            _ReadProcessMemory = WinDLL("kernel32").ReadProcessMemory
            _ReadProcessMemory.argtypes = [HANDLE, LPCVOID, LPVOID, c_size_t, POINTER(c_size_t)]
            _ReadProcessMemory.restype = BOOL
            data = (c_uint8*numBytes)()
            bytesRead = c_ulonglong() if sys.maxsize > 2**32 else c_ulong()
            _ReadProcessMemory(processHandle.handle, address, byref(data), sizeof(data), byref(bytesRead))
            return data

    class Module(Structure):
        _fields_ = [
            ("BaseAddress", LPVOID),    # remote pointer
            ("Name", LPWSTR),
        ]

    class ModuleInfo(Structure):
        _fields_ = [
            ("BaseAddress", c_void_p),    # remote pointer
            ("ModuleSize", DWORD),
            ("EntryPoint", c_void_p),    # remote pointer
        ]