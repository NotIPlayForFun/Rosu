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
from enum import IntEnum, IntFlag
import time


# TODO: consider whether this should be a class, f.e. Keyboard, since then we don't have
# to load user32 in a .py import, rather just in the instance of a class. Could make it singleton? probably overkill

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
  
class MOUSEINPUT(ctypes.Structure):
    """
```c
typedef struct tagMOUSEINPUT {
    LONG      dx;
    LONG      dy;
    DWORD     mouseData;
    DWORD     dwFlags;
    DWORD     time;
    ULONG_PTR dwExtraInfo;
} MOUSEINPUT, *PMOUSEINPUT, *LPMOUSEINPUT;
```
'_PTR' means an integer wide enough to hold a pointer on the current platform
    """
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

class DUMMYUNIONNAME(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]
class INPUT(ctypes.Structure):
    """
    ```c
    typedef struct tagINPUT {
    DWORD type;
    union {
        MOUSEINPUT    mi;
        KEYBDINPUT    ki;
        HARDWAREINPUT hi;
    } DUMMYUNIONNAME;
    } INPUT, *PINPUT, *LPINPUT;
    ```
    """
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

# TODO: decide whether enums should go into separate file
# TODO: decide whether the ctypes definitions (structures) should go into a separate file
class KEYBDINPUT_FLAGS(IntFlag):
    """
    dwFlags for KEYBDINPUT. 
    See https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-keybdinput
    """
    KEYEVENTF_EXTENDEDKEY = 0x0001
    """
    KEYEVENTF_EXTENDEDKEY: If specified, the wScan scan code consists of a 
    sequence of two bytes, where the first byte has a value of 0xE0. 
    See Extended-Key Flag for more info.
    """
    KEYEVENTF_KEYUP = 0x0002
    """
    KEYEVENTF_KEYUP: If specified, the key is being released. 
    If not specified, the key is being pressed.
    """
    KEYEVENTF_SCANCODE = 0x0008
    """KEYEVENTF_SCANCODE: If specified, wScan identifies the key and wVk is ignored."""
    KEYEVENTF_UNICODE = 0x0004
    """
    KEYEVENTF_UNICODE: If specified, the system synthesizes a VK_PACKET keystroke. 
    The wVk parameter must be zero. This flag can only be combined with the 
    KEYEVENTF_KEYUP flag. For more information, see the Remarks section.
    """

class INPUT_TYPES(IntEnum):
    MOUSE = 0
    KEYBOARD = 1
    HARDWARE = 2

class HW_SCAN_CODES(IntEnum):
    F2 = 0x003C

# VK_F2 = 0x71
# hw scan codes:
# see https://learn.microsoft.com/en-us/windows/win32/inputdev/about-keyboard-input#scan-codes

def send_key(hw_scan_code, keyup):
    
    flags = KEYBDINPUT_FLAGS.KEYEVENTF_SCANCODE | (keyup * KEYBDINPUT_FLAGS.KEYEVENTF_KEYUP)
    # debug: test flags-setting
    # print(f"Keyup: {keyup}")
    # print(f"Flags: {flags.name}")
    # Create INPUT structure for the event
    # see https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-input 
    _input = INPUT(
        type=INPUT_TYPES.KEYBOARD, # DWORD type: The type of the input event. 0=mouse, 1=keyboard, 2=hardware
        ki=KEYBDINPUT(
            wVk=0, # virtual key code. windows intuits it from the scan code
            wScan=hw_scan_code, # code identifying the physical key 
                                # (regardless of current keyboard layout)
                                # used instead of wVk if KEYEVENTF_SCANCODE flag is set
            dwFlags=flags,
            time=0, # if 0, the system will provide the timestamp
            dwExtraInfo=0,
        )
        # mi and hi = 0
    )

    result = user32.SendInput(
        1,  # UINT cInputs: The number of structures in the pInputs array.
        ctypes.byref(_input),
        ctypes.sizeof(INPUT)
    )
    """
    SendInput returns the number of events successfully inserted
    into the keyboard or mouse input stream.
    """
    
    # debug
    # print(f"SendInput result: {result}")
    
    if result != 1:
        # Get the windows error code through ctypes 
        # This works if dlllib=ctypes.WinDLL("<dlllibname>"..., use_last_error=True)
        error_code = ctypes.get_last_error()
        error = ctypes.WinError(error_code)
        error.add_note(
            f"SendInput failed to insert a key-{'up' if keyup else 'down'}"
            f" event for key with hardware scan code {hw_scan_code:#06X} into the"
            f" forground application's keyboard input stream."
        )
        raise error

# # test
# send_key(hw_scan_code=HW_SCAN_CODES.F2, keyup=False)  # send F2 key release
# send_key(hw_scan_code=HW_SCAN_CODES.F2, keyup=True )  # send F2 key press

def press_F2(hold_time_s: float) -> None:
    send_key(hw_scan_code=HW_SCAN_CODES.F2, keyup=False)
    time.sleep(hold_time_s)
    send_key(hw_scan_code=HW_SCAN_CODES.F2, keyup=True)

# debug
if __name__ == "__main__":
    time.sleep(2)
    press_F2(hold_time_s=5)