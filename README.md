# Wissenschaftsnacht Demo

This project contains two napari-based demos.

## Mouse Atlas GUI

Launch the atlas viewer with:

```bash
pixi run launch_atlas
```

The launcher automatically downloads `mouse_atlas.tif` if it is not already present, then opens it in napari.

In the GUI:

1. Explore the mouse brain in 2D or 3D.
2. Find the left barrel cortex.

Useful references:

[Barrel Cortex Image](https://upload.wikimedia.org/wikipedia/commons/1/1d/RatBarrelFieldCOstain.jpg)

[Barrel Cortex Diagram](https://www.cell.com/cms/10.1016/j.neuron.2007.09.017/asset/16329b95-3e79-4732-9e54-3a63ecae4f3c/main.assets/gr1_lrg.jpg)

## Cell Activity GUI

Launch the cell activity viewer with:

```bash
pixi run launch_napari
```

To show the custom demo controls in German, use:

```bash
pixi run launch_napari --language de
```

The launcher automatically opens `frames.tif` and `labels.tif` in napari.

In the GUI:

1. Label one or more cells in the labels layer.
2. Click `Extract Fluorescence` to plot the mean fluorescence trace for each labeled cell.
3. Click `Estimate Spikes` to mark likely activity events using OASIS deconvolution.
4. Click `Play Click Train` to hear the estimated spikes as short clicks.
5. Use `Stop` to stop playback.

The vertical marker in the plot follows the currently selected napari frame and moves during audio playback.

Useful reference:

[Calcium Imaging Video](https://www.youtube.com/shorts/DyFPv_aKQkI)
