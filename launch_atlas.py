from argparse import ArgumentParser
from pathlib import Path

import napari
import numpy as np
from brainglobe_atlasapi.bg_atlas import BrainGlobeAtlas
from qtpy.QtWidgets import QLabel, QVBoxLayout, QWidget
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


class BrainRegionInfo(QWidget):
    def __init__(self, annotation_layer, structures):
        super().__init__()
        self.annotation_layer = annotation_layer
        self.structures = structures

        self.label = QLabel("Move the mouse over the atlas annotations.")
        self.label.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addStretch()
        self.setLayout(layout)

    def update_from_position(self, position):
        coords = np.round(position).astype(int)
        annotation = self.annotation_layer.data

        if len(coords) != annotation.ndim:
            return

        if np.any(coords < 0) or np.any(coords >= annotation.shape):
            return

        region_id = int(annotation[tuple(coords)])
        if region_id == 0:
            self.label.setText("No annotated brain region here.")
            return

        structure = self.structures.get(region_id)
        if structure is None:
            self.label.setText(f"Unknown region\nID: {region_id}")
            return

        self.label.setText(
            f"{structure['name']}\n"
            f"Acronym: {structure['acronym']}\n"
            f"ID: {region_id}"
        )


def main():
    parser = ArgumentParser(description="Launch napari with the mouse atlas.")
    parser.parse_args()

    ensure_atlas_exists()
    atlas = BrainGlobeAtlas(ATLAS_NAME)

    viewer = napari.Viewer(ndisplay=3)
    viewer.add_image(imread(ATLAS_PATH), name="Mouse Atlas")
    annotation_layer = viewer.add_labels(
        imread(ANNOTATION_PATH),
        name="Brain Region Annotations",
        opacity=0.35,
    )
    region_info = BrainRegionInfo(annotation_layer, atlas.structures)

    def update_region_info(viewer, event):
        region_info.update_from_position(event.position)

    viewer.mouse_move_callbacks.append(update_region_info)
    viewer.window.add_dock_widget(region_info, area="right", name="Brain Region")

    napari.run()


if __name__ == "__main__":
    main()
