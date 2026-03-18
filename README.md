# Input Output Mining


This repository contains the data for the thesis `Determining Material Waste in Object-Centric Event Logs using Input and Output Mining`.
In particular, it contains example logs, and how the methods presented, the heuristic discovery of role functions and the object flow miner with or without waste annotations, are applied to them.


There are two ways to use this tool.
The first is running it directly as a script, and the second is using the Ocelescope plugin.


## Script Installation


Make sure Python 3.13 is installed.
Also, install [`uv`](https://docs.astral.sh/uv/getting-started/installation/).
For example by

```bash
$ pip install uv
```

Afterward, in this directory, run

```bash
$ uv sync
```

This installs all required libraries.
The tool can now be run on an OCEL in `./path_to_log` with

```bash
$ uv run python -m src.discover ./path_to_log
```

We describe some OCELs that are ready to use below in the project structure.
For example, use `data/evaluation/publicocels/procure-to-pay.xml`.


## Ocelescope Installation

Run [Ocelescope](https://www.ocelescope.org/) using Docker.
Make sure to upload an OCEL from one of the folders `data/evaluation/` or choose one that comes with Ocelescope.
Then, open the Drag and Drop Uploader and paste the `ocelescope-plugin.zip` file found in this folder into the dialog.
The plugin appears at the bottom.
By clicking `View Plugin`, the four approaches can be selected and run.


Please note that Ocelescope does not currently support a way to output errors.
Thus, if a success popup appears but there is no output, an error might have occurred.
This can happen particularly if MFA or waste annotations with an attribute are selected, but the `mass` attribute does not always exist.


## Project Structure

The main contribution of the thesis is a tool that discovers object flow nets from OCEL2.0 event logs, and annotates them with information about waste.
The algorithm for that is in `src/`.
In `src/discover.py`, the algorithm is set up using parameters and the individual parts are called.
How the settings are changed is described in comments in that file.
This is the pathway to reproducing the nets from the thesis.


The first part of our algorithm is in `src/labels.py`, which heuristically discovers roles of each object related to an event.
The output is then fed into `src/algorithm.py`, which contains the aggregation, filtering and model discovery logic.
For the waste detection, methods are provided in `src/waste.py`.

In addition, `src/conformance.py` contains the code we used for our quantitative evaluation.
To generate our custom OCELs used for our evaluation, run `uv run python -m src.generate_nets` after setting the desired output logs at the bottom.
The code that integrates our tool into Ocelescope is in `src/plugin.py`.

The data used is in `data/`.
This has the subfolder `data/evaluation/` with the data sets we used in our evaluation.
