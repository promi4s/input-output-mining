## Preprocessing the Hinge production log

The standard hinge production log contains invalid mass attributes as this is supposed to be readable from inferring the other attributes.
For our thesis, we therefore filled these attributes and dropped unnecessary information from the standard OCEL.

We use the modified `hinge-mass.xml` in `../evaluation/`.
To obtain this event log, put `socel_hinge.xml` in the current directory and run `uv run python fill-data.py` and then `uv run python change.py`.
