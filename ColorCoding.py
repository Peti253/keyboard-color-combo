# https://github.com/mhammond/pywin32
import win32com.client
import asyncio
import sys, os
from win32gui import GetWindowText, GetForegroundWindow, GetClassName
import win32process
import wmi
from pynput import keyboard

state = {}
importstate = {}
blockstate = {}
cache = open (".tmp","w")
current = "standard"
keystate = 0 #Shift(s), Ctrl(c), Meta(m), Alt(x)
lockfilename = "/tmp/keyboardlock"
terminatorfilename = "/tmp/keyboardexit"

if os.path.exists(lockfilename):
    terminator = open(terminatorfilename,"a")
    terminator.write("astala vista baby")
    terminator.close()
    sys.exit()
else:
    lockfile = open(lockfilename,"a")
    lockfile.write ("wer das liest ist dumm")
    lockfile.close()

c = wmi.WMI()

auraSdk = win32com.client.Dispatch("aura.sdk.1")
auraSdk.SwitchMode()
devices = auraSdk.Enumerate(0)

def decodecolor (rgb):
    bgr = rgb[4:6] + rgb[2:4] + rgb[0:2]
    return int(bgr, 16)

keycodes = {
    "escape": 0x0001 ,
    "1": 0x0002 ,
    "2": 0x0003 ,
    "3": 0x0004 ,
    "4": 0x0005 ,
    "5": 0x0006 ,
    "6": 0x0007 ,
    "7": 0x0008 ,
    "8": 0x0009 ,
    "9": 0x000a ,
    "0": 0x000b ,
    "minus": 0x000c ,
    "equals": 0x000d ,
    "back": 0x000e ,
    "tab": 0x000f ,
    "q": 0x0010 ,
    "w": 0x0011 ,
    "e": 0x0012 ,
    "r": 0x0013 ,
    "t": 0x0014 ,
    "y": 0x0015 ,
    "u": 0x0016 ,
    "i": 0x0017 ,
    "o": 0x0018 ,
    "p": 0x0019 ,
    "lbracket": 0x001a ,
    "rbracket": 0x001b ,
    "return": 0x001c ,
    "lcontrol": 0x001d ,
    "a": 0x001e ,
    "s": 0x001f ,
    "d": 0x0020 ,
    "f": 0x0021 ,
    "g": 0x0022 ,
    "h": 0x0023 ,
    "j": 0x0024 ,
    "k": 0x0025 ,
    "l": 0x0026 ,
    "semicolon": 0x0027 ,
    "apostrophe": 0x0028 ,
    "grave": 0x0029 ,
    "lshift": 0x002a ,
    "backslash": 0x002b ,
    "z": 0x002c ,
    "x": 0x002d ,
    "c": 0x002e ,
    "v": 0x002f ,
    "b": 0x0030 ,
    "n": 0x0031 ,
    "m": 0x0032 ,
    "comma": 0x0033 ,
    "period": 0x0034 ,
    "slash": 0x0035 ,
    "rshift": 0x0036 ,
    "multiply": 0x0037 ,
    "lmenu": 0x0038 ,
    "space": 0x0039 ,
    "capital": 0x003a ,
    "f1": 0x003b ,
    "f2": 0x003c ,
    "f3": 0x003d ,
    "f4": 0x003e ,
    "f5": 0x003f ,
    "f6": 0x0040 ,
    "f7": 0x0041 ,
    "f8": 0x0042 ,
    "f9": 0x0043 ,
    "f10": 0x0044 ,
    "numlock": 0x0045 ,
    "scroll": 0x0046 ,
    "numpad7": 0x0047 ,
    "numpad8": 0x0048 ,
    "numpad9": 0x0049 ,
    "subtract": 0x004a ,
    "numpad4": 0x004b ,
    "numpad5": 0x004c ,
    "numpad6": 0x004d ,
    "add": 0x004e ,
    "numpad1": 0x004f ,
    "numpad2": 0x0050 ,
    "numpad3": 0x0051 ,
    "numpad0": 0x0052 ,
    "decimal": 0x0053 ,
    "f11": 0x0057 ,
    "f12": 0x0058 ,
    "numpadenter": 0x009c ,
    "rcontrol": 0x009d ,
    "divide": 0x00b5 ,
    "sysrq": 0x00b7 ,
    "rmenu": 0x00b8 ,
    "pause": 0x00c5 ,
    "home": 0x00c7 ,
    "up": 0x00c8 ,
    "prior": 0x00c9 ,
    "left": 0x00cb ,
    "right": 0x00cd ,
    "end": 0x00cf ,
    "down": 0x00d0 ,
    "next": 0x00d1 ,
    "insert": 0x00d2 ,
    "delete": 0x00d3 ,
    "lwin": 0x00db ,
    "apps": 0x00dd ,
    "fn": 0x0100
}

def changekey (keyx, rgb):
    bgr = decodecolor(rgb)
    for dev in devices:
        keycode = keycodes[keyx]
        if dev.Type in [0x80000, 0x00081000]:
            dev.Keys(keycode - 1).color = bgr

def changeall (rgb):
    bgr = decodecolor(rgb)
    for dev in devices:
        for i in range(dev.Lights.Count):
            dev.Lights(i).color = bgr

def commit():
    for dev in devices:
        dev.Apply()

def findactivewindow():
    """Get applicatin filename given hwnd."""
    exe = None
    _, pid = win32process.GetWindowThreadProcessId(GetForegroundWindow())
    for p in c.query('SELECT Name FROM Win32_Process WHERE ProcessId = %s' % str(pid)):
        exe = p.Name
        break
    if exe is not None:
        if exe.endswith(".exe"):
            exe = exe[:-4]
        exe = exe.lower()
    return exe

def encoding(x):
    enc = 0
    if "s" in x:
        enc = enc | 0b1000
    if "c" in x:
        enc = enc | 0b0100
    if "m" in x:
        enc = enc | 0b0010
    if "x" in x:
        enc = enc | 0b0001
    return enc

def loadfile(filename):
    cfgfile = open (filename)
    lines = (cfgfile.readlines())
    strippedlines = map (lambda line: line.strip ("\t\n "), lines)
    filteredlines = filter (lambda line: line != "", strippedlines)
    splitlines = map (lambda line: line.split(), filteredlines)
    currentprogram = "standard"
    for line in splitlines:
        if line[0].startswith("["):
            currentprogram = line[0].strip("[]")
            state[currentprogram] = []
            importstate[currentprogram] = []
            blockstate[currentprogram] = []
        else:
            if line[0] == "i":
                importstate[currentprogram].append(line[1])
                continue
            if line[0] == "b":
                b = encoding(line[1])
                blockstate[currentprogram].append(b)
            if line[0][0] in "scmx":
                line[0] = encoding(line[0])
            state[currentprogram].append(line)
    for program,modulelist in importstate.items():
        modules = []
        while len(modulelist) > 0:
            module = modulelist.pop()
            if module in modules:
                continue
            modules.append(module)
            modulelist.extend(importstate[module])
        importstate[program] = modules
    for program,modulelist in importstate.items():
        blocked2d = map(lambda module: blockstate[module],modulelist)
        blockstate[program].extend(list(set(i for innerlist in blocked2d for i in innerlist)))

def onpress (key):
    global keystate
    lastkeystate = keystate
    key=str(key).strip("'")
    if key == "Key.shift" or key == "Key.shift_r":
        keystate = keystate | 0b1000
    if key == "Key.ctrl" or key == "Key.ctrl_r" or key == "Key.ctrl_l":
        keystate = keystate | 0b0100
    if key == "Key.cmd" or key == "Key.cmd_l":
        keystate = keystate | 0b0010
    if key == "Key.alt" or key == "Key.alt_l":
        keystate = keystate | 0b0001
    if lastkeystate != keystate:
        render()

def onrelease (key):
    global keystate
    lastkeystate = keystate
    key=str(key).strip("'")
    if key == "Key.shift" or key == "Key.shift_r":
        keystate = keystate & 0b0111
    if key == "Key.ctrl" or key == "Key.ctrl_r" or key == "Key.ctrl_l":
        keystate = keystate & 0b1011
    if key == "Key.cmd" or key == "Key.cmd_l":
        keystate = keystate & 0b1101
    if key == "Key.alt" or key == "Key.alt_l":
        keystate = keystate & 0b1110
    if lastkeystate != keystate:
        render()

listener=keyboard.Listener (on_press=onpress,on_release=onrelease)
listener.start()

loadfile ("Keyboard.yaml" if len(sys.argv) == 1 else sys.argv[1])

onrelease (None)

def render():
    keylist = state[current]
    for module in importstate[current]:
        keylist = state[module] + keylist
    if keystate == 0:
        changeall("000000")
        for k in keylist:
            if str(k[0]) == "a":
                changeall(k[1])
            elif str(k[0]) == "k":
                changekey(k[1],k[2])
        commit()
    elif keystate not in blockstate[current]:
        changeall("000000")
        for k in filter (lambda k:k[0] == keystate,keylist):
            print(k)
            changekey(k[1],k[2])
        commit()

async def mainloop():
    global current
    dev = list(devices)[1]
    while True:
        await asyncio.sleep(0.1)
        if os.path.exists(terminatorfilename):
            os.remove(terminatorfilename)
            os.remove(lockfilename)
            break
        oldwindowname = current
        windowname = findactivewindow()
        print(bin(keystate))
        if oldwindowname != windowname and windowname in state.keys():
            current = windowname
            render()
        elif windowname in state.keys():
            render()
        else:
            current = "standard"
            render()
asyncio.run(mainloop())
