## Structure

In `testocels/`, there are small generated OCELs using `src/generate_nets.py`.
These are used for our running example and for testing the capabilities of our algorithm.
Besides the running example, the models discovered on these OCELs are in the _Basic Constructs_ section of our evaluation.

In `publicocels/` we have saved copies of four public OCELs.
These are `container-logistics.xml`, `procure-to-pay.xml`, and `order-management.sqlite`.
In addition, there is the unmodified hinge production `socel_hinge.xml`, as well as `socel_data.xml` and `hinge-mass.xml` which are both created from our preprocessing described in `../preprocessing/README.md`.

For plotting the runtimes, `plot_runtimes.py` was used.
