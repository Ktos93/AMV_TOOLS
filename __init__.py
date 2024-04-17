bl_info = {
    "name": "AMV TOOLS",
    "author": "ktos93",
    "version": (0, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Tools",
    "description": "",
    "warning": "",
    "wiki_url": "",
    "category": "Object",
}

import bpy
import sys
import importlib
import subprocess

# Blender's Python executable
pybin = sys.executable

def add_user_site():
    # Locate users site-packages (writable)
    user_site = subprocess.check_output([pybin, "-m", "site", "--user-site"])
    
    try:
        user_site = user_site.decode("utf-8").rstrip("\n")   # Convert to string and remove line-break
    except UnicodeDecodeError:
    # If decoding with utf-8 fails, try with latin1
        user_site = user_site.decode("latin1").rstrip("\n")

    # Add user packages to sys.path (if it exits)
    user_site_exists = user_site is not None
    if user_site not in sys.path and user_site_exists:
        sys.path.append(user_site)
    return user_site_exists

def enable_pip():
    if importlib.util.find_spec("pip") is None:
        subprocess.check_call([pybin, "-m", "ensurepip", "--user"])
        subprocess.check_call([pybin, "-m", "pip", "install", "--upgrade", "pip", "--user"])
    
def install_module(module : str):
    if importlib.util.find_spec(module) is None:
        subprocess.check_call([pybin, "-m", "pip", "install", module, "--user"])

user_site_added = add_user_site()
enable_pip()
modules = ["tifffile"] 
for module in modules:
    install_module(module)
# If there was no user-site before...
if not user_site_added:
    add_user_site()

from . import main
from . import probes
from . import bake
from . import light
from . import gizmo

def register():
    main.register()
    probes.register()
    bake.register()
    light.register()
    gizmo.register()

def unregister():
    main.unregister()
    probes.unregister()
    bake.unregister()
    light.unregister()
    gizmo.unregister()

if __name__ == "__main__":
    register()
