import numpy as np
import matplotlib.pyplot as plt
from tifffile import imread


def get_cell_activity(frames: np.ndarray, labels: np.ndarray) -> dict[int, np.ndarray]:
    label_ids = np.unique(labels)
    label_ids = label_ids[label_ids != 0]

    if len(label_ids) == 0:
        raise ValueError("No labeled cells found.")

    return {
        int(label_id): frames[:, labels == label_id].mean(axis=1)
        for label_id in label_ids
    }


def plot_cell_activity(cell_activity: dict[int, np.ndarray], fname="results.png"):
    fig, ax = plt.subplots()
    for label_id, trace in cell_activity.items():
        ax.plot(trace, label=f"Cell {label_id}")
    ax.set_title("Mean Cell Activity")
    ax.set_xlabel("Frame")
    ax.set_ylabel("Mean fluorescence")
    ax.legend()
    fig.tight_layout()
    fig.savefig(fname)
    plt.close(fig)

def main():

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('frames')
    parser.add_argument('labels')
    args = parser.parse_args()

    frames = imread(args.frames)
    labels = imread(args.labels)

    cell_activity = get_cell_activity(frames, labels)
    plot_cell_activity(cell_activity)

if __name__ == "__main__":
    main()
