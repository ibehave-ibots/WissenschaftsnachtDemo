import napari
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from qtpy.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget
from tifffile import imread

from get_cell_activity import get_cell_activity


FRAMES_PATH = "frames.tif"
LABELS_PATH = "labels.tif"


class CellActivityControls(QWidget):
    def __init__(self, frames_layer, labels_layer, plot_widget):
        super().__init__()
        self.frames_layer = frames_layer
        self.labels_layer = labels_layer
        self.plot_widget = plot_widget

        self.extract_button = QPushButton("Extract Fluorescence")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Label cells, then extract their fluorescence."))
        layout.addWidget(self.extract_button)
        layout.addStretch()
        self.setLayout(layout)

        self.extract_button.clicked.connect(self.extract_fluorescence)

    def extract_fluorescence(self):
        frames = np.asarray(self.frames_layer.data)
        labels = np.asarray(self.labels_layer.data)

        try:
            cell_activity = get_cell_activity(frames, labels)
        except ValueError as error:
            napari.utils.notifications.show_warning(str(error))
            return

        colors = {
            label_id: self.labels_layer.get_color(label_id)
            for label_id in cell_activity
        }
        self.plot_widget.plot_traces(cell_activity, colors)
        napari.utils.notifications.show_info("Fluorescence extracted.")


class CellActivityPlot(QWidget):
    def __init__(self):
        super().__init__()
        self.figure = Figure(figsize=(8, 3))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.subplots()

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self._show_empty_plot()

    def _show_empty_plot(self):
        self.ax.clear()
        self.ax.set_title("Mean Cell Activity")
        self.ax.set_xlabel("Frame")
        self.ax.set_ylabel("Mean fluorescence")
        self.ax.text(
            0.5,
            0.5,
            "Label cells, then click Extract Fluorescence.",
            ha="center",
            va="center",
            transform=self.ax.transAxes,
        )
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def plot_traces(self, cell_activity, colors):
        self.ax.clear()
        for label_id, trace in cell_activity.items():
            self.ax.plot(
                trace,
                color=colors[label_id],
                linewidth=2,
                label=f"Cell {label_id}",
            )
        self.ax.set_title("Mean Cell Activity")
        self.ax.set_xlabel("Frame")
        self.ax.set_ylabel("Mean fluorescence")
        self.ax.legend(loc="best")
        self.figure.tight_layout()
        self.canvas.draw_idle()


def main():
    viewer = napari.Viewer()
    frames_layer = viewer.add_image(imread(FRAMES_PATH), name="frames")
    labels_layer = viewer.add_labels(imread(LABELS_PATH), name="labels")

    plot_widget = CellActivityPlot()
    controls = CellActivityControls(frames_layer, labels_layer, plot_widget)

    viewer.window.add_dock_widget(controls, area="right", name="Cell Activity")
    viewer.window.add_dock_widget(plot_widget, area="bottom", name="Cell Activity Plot")

    napari.run()


if __name__ == "__main__":
    main()
