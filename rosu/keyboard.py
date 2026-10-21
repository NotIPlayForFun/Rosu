"""
Send key presses to the focused window (Requires Windows)

Load the required DLL containing the SendInput function: user32.dll

References:
    * SendInput function from the Windows API:
    https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput
    + sublinks from there
    * https://docs.python.org/3/library/ctypes.html#ctypes-tutorial

"""

import ctypes, ctypes.wintypes

# Load the user32.dll, which contains SendInput
user32 = ctypes.WinDLL("user32.dll", use_last_error=True)
# use_last_error:  
#   as per the ctypes documentation: "the ctypes private copy of the system errno variable is 
#   exchanged with the real errno value before and after the call; use_last_error does the same
#   for the Windows error code."
#   aka: Before the call to the DLL function, ctypes swaps its private copy
#   of the error code variable with the real windows error code value. Then the function
#   runs and may set a windows error code. After the call, ctypes swaps them again, so the private 
#   copy holds the functions value, if it set one. This can be useful if the function's return value 
#   indicates an error. Checking this by yourself at that point is too late since the error code
#   may have been overwritten by functions executed by f.e. the python interpreter. Instead,
#   we can then use ctypes.get_last_error() to retrieve the private copy.
#   See https://docs.python.org/3/library/ctypes.html#ctypes-tutorial, ctrl+f "use_last_error"

# Use ctypes to describe memory layout of the function's argument and return types
#   C doesn't contain type information at runtime, and it thus has to be specified.
#   See https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput
#   and https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-input etc.
#   for the field types and thus required sizes of the fields

"""
typedef struct tagHARDWAREINPUT {
  DWORD uMsg;
  WORD  wParamL;
  WORD  wParamH;
} HARDWAREINPUT, *PHARDWAREINPUT, *LPHARDWAREINPUT;
"""
class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.wintypes.DWORD),
        ("wParamL", ctypes.wintypes.WORD),
        ("wParamH", ctypes.wintypes.WORD),
    ]
    
"""
typedef struct tagKEYBDINPUT {
  WORD      wVk;
  WORD      wScan;
  DWORD     dwFlags;
  DWORD     time;
  ULONG_PTR dwExtraInfo; <-_PTR means an integer wide enough to hold a pointer on the current platform
} KEYBDINPUT, *PKEYBDINPUT, *LPKEYBDINPUT;
"""
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        # ULONG_PTR's size is dependent on whether the process is 
        # running in 32-bit python or 64-bit python
        # See "dwExtraInfo is a ULONG_PTR" comment for more details.
        # ctypes.wintypes.WPARAM: "An unsigned integer type with the same size as c_void_p." 
        # https://docs.python.org/3/library/ctypes.html#ctypes.wintypes.WPARAM
        ("dwExtraInfo", ctypes.wintypes.WPARAM),
    ]
  
# dwExtraInfo is a ULONG_PTR: 
#   not a pointer, but an unsigned integer exactly as wide
#   as a pointer (4 bytes on 32-bit Python, 8 on 64-bit). Free slot for app-defined
#   data attached to the event; we leave it 0. 
#   Goal: a ctypes type whose size follows the pointer width of the running Python
#   process (not the OS), so our struct layout matches what Windows expects. 
#   Fixed-width types like c_uint64 fail this (wrong size on 32-bit).
#   Options:
#       * ctypes.c_size_t: C's type for sizes of objects in memory. It must be able to
#           hold the size of the largest possible object, which generally works out to 
#           pointer-sized width. On Windows at least it's always pointer-sized.
#           But C standard doesn't technically promise this.
#       * wintypes.WPARAM: defined by ctypes docs as "unsigned int with the same size 
#           as c_void_p", meaning the size of a pointer (void*), which is literally the 
#           definition of ULONG_PTR. 
#           https://docs.python.org/3/library/ctypes.html#ctypes.wintypes.WPARAM
#       * ctypes.c_void_p: a pointer, so pointer-sized by definition. Works, but it's
#           semantically a pointer (0 reads back as None), odd for a number field.
  
"""
typedef struct tagMOUSEINPUT {
  LONG      dx;
  LONG      dy;
  DWORD     mouseData;
  DWORD     dwFlags;
  DWORD     time;
  ULONG_PTR dwExtraInfo; <-_PTR means an integer wide enough to hold a pointer on the current platform
} MOUSEINPUT, *PMOUSEINPUT, *LPMOUSEINPUT;
"""
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.wintypes.LONG),
        ("dy", ctypes.wintypes.LONG),
        ("mouseData", ctypes.wintypes.DWORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        # ULONG_PTR's size is dependent on whether the process is 
        # running in 32-bit python or 64-bit python.
        # See "dwExtraInfo is a ULONG_PTR" comment for more details.
        # ctypes.wintypes.WPARAM: "An unsigned integer type with the same size as c_void_p." 
        # https://docs.python.org/3/library/ctypes.html#ctypes.wintypes.WPARAM
        ("dwExtraInfo", ctypes.wintypes.WPARAM), 
    ]

"""
typedef struct tagINPUT {
  DWORD type;
  union {
    MOUSEINPUT    mi;
    KEYBDINPUT    ki;
    HARDWAREINPUT hi;
  } DUMMYUNIONNAME;
} INPUT, *PINPUT, *LPINPUT;
"""
class DUMMYUNIONNAME(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]
class INPUT(ctypes.Structure):
    _anonymous_ = ("DUMMYUNIONNAME",)
    _fields_ = [
        ("type", ctypes.wintypes.DWORD),
        ("DUMMYUNIONNAME", DUMMYUNIONNAME),
    ]

"""
UINT SendInput(
  [in] UINT    cInputs, 
  [in] LPINPUT pInputs, <- LP=Long Pointer (nowadays same as pointer) -> INPUT*
  [in] int     cbSize
);
"""
user32.SendInput.argtypes = (ctypes.wintypes.UINT, ctypes.POINTER(INPUT), ctypes.wintypes.INT)
user32.SendInput.restype = ctypes.wintypes.UINT

# # Create test input and set ki directly (anonymous), then read back through the DUMMYUNIONNAME
# # to confirm they are the same memory
# test_input = INPUT()
# test_input.ki.wVk = 0x41  # write through the short path

# # Values: both should print 65 (0x41)
# print(test_input.ki.wVk, test_input.DUMMYUNIONNAME.ki.wVk)

# # Real C addresses: first two should be equal, third should be 8
# a_short = ctypes.addressof(test_input.ki)
# a_long = ctypes.addressof(test_input.DUMMYUNIONNAME.ki)
# print(a_short, a_long, a_short - ctypes.addressof(test_input))

# should be 40
# print(ctypes.sizeof(INPUT))