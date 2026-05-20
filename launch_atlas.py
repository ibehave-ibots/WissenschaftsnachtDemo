from argparse import ArgumentParser
from pathlib import Path

import napari
from brainglobe_atlasapi.bg_atlas import BrainGlobeAtlas
from tifffile import imread, imwrite


ATLAS_PATH = Path("mouse_atlas.tif")
ATLAS_NAME = "allen_mouse_25um"


def ensure_atlas_exists():
    if ATLAS_PATH.exists():
        return

    print(f"Downloading {ATLAS_NAME} atlas...")
    atlas = BrainGlobeAtlas(ATLAS_NAME)
    imwrite(ATLAS_PATH, atlas.reference)
    print(f"Created {ATLAS_PATH}")


def main():
    parser = ArgumentParser(description="Launch napari with the mouse atlas.")
    parser.parse_args()

    ensure_atlas_exists()

    viewer = napari.Viewer(ndisplay=3)
    viewer.add_image(imread(ATLAS_PATH), name="Mouse Atlas")
    napari.run()


if __name__ == "__main__":
    main()
