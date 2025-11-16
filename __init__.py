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
import os
import site

# Blender's Python executable
pybin = sys.executable

def add_user_site():
    """Add user site-packages to sys.path"""
    try:
        user_site = subprocess.check_output([pybin, "-m", "site", "--user-site"], stderr=subprocess.DEVNULL)
        
        try:
            user_site = user_site.decode("utf-8").strip()
        except UnicodeDecodeError:
            user_site = user_site.decode("latin1").strip()
        
        # Create directory if it doesn't exist
        if not os.path.exists(user_site):
            os.makedirs(user_site, exist_ok=True)
        
        # Add to sys.path if not already there
        if user_site not in sys.path:
            sys.path.insert(0, user_site)
            print(f"AMV TOOLS: Added user site-packages: {user_site}")
        
        return True
    except Exception as e:
        print(f"AMV TOOLS: Error adding user site: {e}")
        return False

def enable_pip():
    """Ensure pip is installed"""
    try:
        if importlib.util.find_spec("pip") is None:
            print("AMV TOOLS: Installing pip...")
            subprocess.check_call([pybin, "-m", "ensurepip", "--user"], stderr=subprocess.DEVNULL)
            subprocess.check_call([pybin, "-m", "pip", "install", "--upgrade", "pip", "--user"], stderr=subprocess.DEVNULL)
            print("AMV TOOLS: pip installed successfully")
    except Exception as e:
        print(f"AMV TOOLS: Error enabling pip: {e}")
    
def install_module(module : str):
    """Install a Python module if not already installed"""
    try:
        if importlib.util.find_spec(module) is None:
            print(f"AMV TOOLS: Installing {module}...")
            subprocess.check_call([pybin, "-m", "pip", "install", module, "--user", "--no-warn-script-location"], stderr=subprocess.DEVNULL)
            print(f"AMV TOOLS: {module} installed successfully")
            # Refresh sys.path and reload site packages
            importlib.invalidate_caches()
            site.main()
        else:
            print(f"AMV TOOLS: {module} already installed")
    except Exception as e:
        print(f"AMV TOOLS: Error installing {module}: {e}")

# Setup user site and install dependencies
add_user_site()
enable_pip()
modules = ["tifffile"] 
for module in modules:
    install_module(module)
# Refresh user site after installations
add_user_site()
importlib.invalidate_caches()

from . import main
from . import probes
from . import bake
from . import light
from . import gizmo
from . import reflectionProbes

def register():
    main.register()
    probes.register()
    bake.register()
    light.register()
    gizmo.register()
    reflectionProbes.register()

def unregister():
    main.unregister()
    probes.unregister()
    bake.unregister()
    light.unregister()
    gizmo.unregister()
    reflectionProbes.unregister()

if __name__ == "__main__":
    register()
