from argparse import ArgumentParser
import time
import warnings

import napari
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from qtpy.QtCore import QTimer
from qtpy.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget
from tifffile import imread

from get_cell_activity import estimate_spikes, get_cell_activity


warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")


FRAMES_PATH = "frames.tif"
LABELS_PATH = "labels.tif"
FRAME_RATE_HZ = 60.0
SAMPLE_RATE_HZ = 44100
CLICK_DURATION_SECONDS = 0.001
CLICK_FREQUENCY_HZ = 1200.0


TEXT = {
    "en": {
        "instructions": "Label cells, then extract their fluorescence.",
        "extract_button": "Extract Fluorescence",
        "estimate_button": "Estimate Spikes",
        "play_button": "Play Click Train",
        "stop_button": "Stop",
        "fluorescence_extracted": "Fluorescence extracted.",
        "extract_first": "Extract fluorescence first.",
        "spikes_estimated": "Spikes estimated.",
        "estimate_first": "Estimate spikes first.",
        "audio_unavailable": "Audio is not available",
        "no_spikes": "No spikes to play.",
        "audio_failed": "Could not play audio",
        "x_label": "Frame",
        "y_label": "Mean fluorescence",
        "empty_plot": "Label cells, then click Extract Fluorescence.",
        "cell_label": "Cell",
        "controls_dock": "Cell Activity",
        "plot_dock": "Cell Activity Plot",
    },
    "de": {
        "instructions": "Zellen markieren und dann die Fluoreszenz extrahieren.",
        "extract_button": "Fluoreszenz extrahieren",
        "estimate_button": "Aktionspotentiale ermitteln",
        "play_button": "Audio abspielen",
        "stop_button": "Stopp",
        "fluorescence_extracted": "Fluoreszenz extrahiert.",
        "extract_first": "Zuerst Fluoreszenz extrahieren.",
        "spikes_estimated": "Aktionspotentiale ermittelt.",
        "estimate_first": "Zuerst Aktionspotentiale ernmitteln.",
        "audio_unavailable": "Audio ist nicht verfügbar",
        "no_spikes": "Keine Spikes zum Abspielen.",
        "audio_failed": "Audio konnte nicht abgespielt werden",
        "x_label": "Bild",
        "y_label": "Mittlere Fluoreszenz",
        "empty_plot": "Zellen markieren und dann Fluoreszenz extrahieren.",
        "cell_label": "Zelle",
        "controls_dock": "Zellaktivität",
        "plot_dock": "Zellaktivitäts-Plot",
    },
}


def make_click_train(spikes):
    n_frames = max(len(cell_spikes) for cell_spikes in spikes.values())
    duration_seconds = n_frames / FRAME_RATE_HZ
    audio = np.zeros(int(duration_seconds * SAMPLE_RATE_HZ), dtype=np.float32)

    click_samples = max(1, int(CLICK_DURATION_SECONDS * SAMPLE_RATE_HZ))
    click_time = np.arange(click_samples) / SAMPLE_RATE_HZ
    envelope = np.exp(-click_time / CLICK_DURATION_SECONDS)
    click = np.sin(2 * np.pi * CLICK_FREQUENCY_HZ * click_time) * envelope

    for cell_spikes in spikes.values():
        for frame in np.flatnonzero(cell_spikes):
            start = int(frame / FRAME_RATE_HZ * SAMPLE_RATE_HZ)
            end = min(start + click_samples, len(audio))
            audio[start:end] += click[: end - start]

    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = 0.4 * audio / peak

    return audio, n_frames


class CellActivityControls(QWidget):
    def __init__(self, viewer, frames_layer, labels_layer, plot_widget, text):
        super().__init__()
        self.viewer = viewer
        self.frames_layer = frames_layer
        self.labels_layer = labels_layer
        self.plot_widget = plot_widget
        self.text = text
        self.playback_start = None
        self.playback_frames = 0
        self.playback_timer = QTimer(self)
        self.playback_timer.setInterval(30)

        self.extract_button = QPushButton(text["extract_button"])
        self.estimate_spikes_button = QPushButton(text["estimate_button"])
        self.play_button = QPushButton(text["play_button"])
        self.stop_button = QPushButton(text["stop_button"])

        layout = QVBoxLayout()
        layout.addWidget(QLabel(text["instructions"]))
        layout.addWidget(self.extract_button)
        layout.addWidget(self.estimate_spikes_button)
        layout.addWidget(self.play_button)
        layout.addWidget(self.stop_button)
        layout.addStretch()
        self.setLayout(layout)

        self.extract_button.clicked.connect(self.extract_fluorescence)
        self.estimate_spikes_button.clicked.connect(self.estimate_spikes)
        self.play_button.clicked.connect(self.play_click_train)
        self.stop_button.clicked.connect(self.stop_playback)
        self.playback_timer.timeout.connect(self.update_playback_cursor)

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
        napari.utils.notifications.show_info(self.text["fluorescence_extracted"])

    def estimate_spikes(self):
        if self.plot_widget.cell_activity is None:
            napari.utils.notifications.show_warning(self.text["extract_first"])
            return

        spikes = estimate_spikes(self.plot_widget.cell_activity)
        self.plot_widget.plot_spikes(spikes)
        napari.utils.notifications.show_info(self.text["spikes_estimated"])

    def play_click_train(self):
        if self.plot_widget.spikes is None:
            napari.utils.notifications.show_warning(self.text["estimate_first"])
            return

        try:
            import sounddevice as sd
        except OSError as error:
            napari.utils.notifications.show_error(f"{self.text['audio_unavailable']}: {error}")
            return

        audio, self.playback_frames = make_click_train(self.plot_widget.spikes)
        if not np.any(audio):
            napari.utils.notifications.show_warning(self.text["no_spikes"])
            return

        self.stop_playback()
        try:
            sd.play(audio, SAMPLE_RATE_HZ)
        except Exception as error:
            napari.utils.notifications.show_error(f"{self.text['audio_failed']}: {error}")
            return

        self.playback_start = time.monotonic()
        self.playback_timer.start()

    def stop_playback(self):
        self.playback_timer.stop()
        try:
            import sounddevice as sd

            sd.stop()
        except OSError:
            pass

    def update_playback_cursor(self):
        elapsed = time.monotonic() - self.playback_start
        frame = min(int(elapsed * FRAME_RATE_HZ), self.playback_frames - 1)
        self.viewer.dims.set_current_step(0, frame)

        if frame >= self.playback_frames - 1:
            self.stop_playback()


class CellActivityPlot(QWidget):
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.figure = Figure(figsize=(8, 3))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.subplots()
        self.current_frame = 0
        self.frame_marker = None
        self.cell_activity = None
        self.colors = None
        self.spikes = None

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self._show_empty_plot()

    def _show_empty_plot(self):
        self.ax.clear()
        self.ax.set_xlabel(self.text["x_label"])
        self.ax.set_ylabel(self.text["y_label"])
        self.ax.text(
            0.5,
            0.5,
            self.text["empty_plot"],
            ha="center",
            va="center",
            transform=self.ax.transAxes,
        )
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def plot_traces(self, cell_activity, colors):
        self.cell_activity = cell_activity
        self.colors = colors
        self.spikes = None
        self._redraw_plot()

    def plot_spikes(self, spikes):
        self.spikes = spikes
        self._redraw_plot()

    def _redraw_plot(self):
        self.ax.clear()

        if self.cell_activity is None:
            self._show_empty_plot()
            return

        n_frames = max(len(trace) for trace in self.cell_activity.values())
        for label_id, trace in self.cell_activity.items():
            self.ax.plot(
                trace,
                color=self.colors[label_id],
                linewidth=2,
                label=f"{self.text['cell_label']} {label_id}",
            )
            if self.spikes is not None:
                spike_frames = np.flatnonzero(self.spikes[label_id])
                self.ax.scatter(
                    spike_frames,
                    trace[spike_frames],
                    color=self.colors[label_id],
                    marker="o",
                    edgecolors="black",
                    linewidths=0.8,
                    s=45,
                    zorder=3,
                )

        self.frame_marker = self.ax.axvline(
            self.current_frame,
            color="black",
            linestyle="--",
            linewidth=2,
            alpha=0.8,
        )
        self.ax.set_xlabel(self.text["x_label"])
        self.ax.set_ylabel(self.text["y_label"])
        self.ax.set_xlim(0, n_frames - 1)
        self.ax.margins(x=0)
        self.ax.grid(True, axis="y", color="0.9", linewidth=1)
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)
        self.ax.legend(loc="upper right", frameon=False)
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def update_current_frame(self, frame):
        self.current_frame = frame
        if self.frame_marker is None:
            return

        self.frame_marker.set_xdata([frame, frame])
        self.canvas.draw_idle()


def main():
    parser = ArgumentParser()
    parser.add_argument("--language", choices=TEXT, default="en")
    args = parser.parse_args()
    text = TEXT[args.language]

    viewer = napari.Viewer()
    frames_layer = viewer.add_image(imread(FRAMES_PATH), name="frames")
    labels_layer = viewer.add_labels(imread(LABELS_PATH), name="labels")

    plot_widget = CellActivityPlot(text)
    controls = CellActivityControls(viewer, frames_layer, labels_layer, plot_widget, text)

    def update_plot_frame(event=None):
        plot_widget.update_current_frame(viewer.dims.current_step[0])

    viewer.dims.events.current_step.connect(update_plot_frame)
    update_plot_frame()

    viewer.window.add_dock_widget(controls, area="right", name=text["controls_dock"])
    viewer.window.add_dock_widget(plot_widget, area="bottom", name=text["plot_dock"])

    napari.run()


if __name__ == "__main__":
    main()
