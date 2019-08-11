import sys
from cx_Freeze import setup, Executable
import os

os.environ['TCL_LIBRARY'] = r'C:\Users\Stephen\OneDrive\Work\PF-PDF-images\env-desktop\Lib\tcl8.6'
os.environ['TK_LIBRARY'] = r'C:\Users\Stephen\OneDrive\Work\PF-PDF-images\env-desktop\Lib\tcl8.6'

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os"], "include_files": ["tcl86t.dll", "tk86t.dll"]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "PF-Image-Extractor",
        version = "0.1",
        description = "Extract images from Paizo PDFs.",
        options = {"build_exe": build_exe_options},
        executables = [Executable("main.py", base=base)])
