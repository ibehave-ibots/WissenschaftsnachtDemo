from argparse import ArgumentParser
from pathlib import Path

import napari
from brainglobe_atlasapi.bg_atlas import BrainGlobeAtlas
from tifffile import imread, imwrite


BASE_DIR = Path(__file__).resolve().parent
ATLAS_PATH = BASE_DIR / "mouse_atlas.tif"
ANNOTATION_PATH = BASE_DIR / "mouse_atlas_annotations.tif"
ATLAS_NAME = "allen_mouse_25um"


def ensure_atlas_exists():
    if ATLAS_PATH.exists() and ANNOTATION_PATH.exists():
        return

    print(f"Preparing {ATLAS_NAME} atlas...")
    atlas = BrainGlobeAtlas(ATLAS_NAME)
    if not ATLAS_PATH.exists():
        imwrite(ATLAS_PATH, atlas.reference)
        print(f"Created {ATLAS_PATH}")
    if not ANNOTATION_PATH.exists():
        imwrite(ANNOTATION_PATH, atlas.annotation)
        print(f"Created {ANNOTATION_PATH}")


def main():
    parser = ArgumentParser(description="Launch napari with the mouse atlas.")
    parser.parse_args()

    ensure_atlas_exists()

    viewer = napari.Viewer(ndisplay=3)
    viewer.add_image(imread(ATLAS_PATH), name="Mouse Atlas")
    viewer.add_labels(
        imread(ANNOTATION_PATH),
        name="Brain Region Annotations",
        opacity=0.35,
    )
    napari.run()


if __name__ == "__main__":
    main()
