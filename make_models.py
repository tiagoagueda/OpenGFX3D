#!/usr/bin/env python3
"""Make all models of the OpenGFX3D package, and its index opengfx3d.json.

    python3 make_models.py

Each file models_*.py makes a group of models: its build() writes the .glb files into the current
folder and returns the entries for the index, as {"vehicles": [...], "buildings": [...]}.
The shapes are made with the Model class of gfx3d.py.
"""

import glob
import importlib
import json
import os
import sys


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    sys.path.insert(0, here)
    index = {
        "name": "OpenGFX3D",
        "description": "3D models for the experimental 3D view. Vehicles and buildings that are not listed keep the sprites of the 2D game.",
        "vehicles": [],
        "buildings": [],
    }
    for path in sorted(glob.glob("models_*.py")):
        name = os.path.splitext(path)[0]
        module = importlib.import_module(name)
        entries = module.build()
        for key in ("vehicles", "buildings"):
            index[key].extend(entries.get(key, []))
    with open("opengfx3d.json", "w") as f:
        json.dump(index, f, indent="\t")
        f.write("\n")


if __name__ == "__main__":
    main()
