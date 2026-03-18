from __future__ import annotations
import pm4py
from pandas import Timestamp, DataFrame
from pandas.core.groupby import DataFrameGroupBy
import pandas
from decimal import Decimal
from collections import defaultdict
from copy import deepcopy
from pm4py.objects.ocel.obj import OCEL
from typing import Union
import json
from pprint import pprint
import datetime
import sys
import uuid
from graphviz import Digraph
import tempfile
from pm4py.visualization.common import gview
import random
import time
import warnings

from .waste import *
from .labels import *
from .algorithm import *
from .conformance import *


warnings.filterwarnings("ignore", module="pm4py.*")
warnings.filterwarnings("ignore", module="pandas.*")


if __name__ == "__main__":
    point0 = time.perf_counter()

    ocel = pm4py.read_ocel2(sys.argv[1])

    point1 = time.perf_counter()

    # =====
    # Here, you can enter object types that will be filtered out.
    # =====
    ocel = pm4py.filtering.filter_ocel_object_attribute(
        ocel,
        "ocel:type",
        [
            "Forklift",
            "Truck",
            "Vehicle",
            "employees",
            "customers",
            "products",
            "Machine",
            "Worker",
            "Workstation",
        ],
        False,
    )

    labels = find_event_labels(
        ocel, {"SplitWaste": "final output", "SteelSheet": "inner"}
    )["labels"]

    point2 = time.perf_counter()

    # =====
    # If MFA shall be run, uncomment this lines.
    # It will edit the labels automatically.
    # Note that this throws an error if the mass attribute is not universally available on every object.
    # =====
    # labels = calculate_masses(ocel, labels, True)["labels"]

    point3 = time.perf_counter()

    by_object_id = ocel.objects.set_index("ocel:oid")

    agg, object_instances = aggregate(labels)

    # =====
    # Redefine `agg` here as the output of filtering if desired.
    # The lambda can be used to set the level.
    # =====
    # Alpha on configurations
    # agg2 = filter_aggregation_by_variants(agg, lambda total, i: i > total * 0.10)
    # Beta on preceding and succeeding activities
    # agg2 = filter_aggregation_by_associations(agg2, lambda total, i: i > total * 0.10)
    agg2 = agg

    # =====
    # Waste annotation is implemented here.
    # It changes `agg2` in place and computes waste annotations that are automatically rendered later.
    # See `waste.py` for the available mechanisms.
    # =====
    # calculate_object_type_count(agg2, ocel, by_object_id, labels, "Product")
    # calculate_object_type_mass(agg2, ocel, by_object_id, labels, "Resin")
    # calculate_object_type_mass(agg2, ocel, by_object_id, labels, "Fiber")
    # calculate_object_type_mass(agg2, ocel, by_object_id, labels, "Waste")
    # calculate_object_type_mass(agg2, ocel, by_object_id, labels, "Product")
    # calculate_implicit_waste_mass(agg2, ocel, by_object_id, labels, "Inject")
    # calculate_implicit_waste_mass(agg2, ocel, by_object_id, labels, "Pack")
    # calculate_implicit_waste_mass(agg2, ocel, by_object_id, labels, "Collect")
    # calculate_implicit_waste_mass(agg2, ocel, by_object_id, labels, "Collect")
    # calculate_explicit_waste(agg2, ocel, by_object_id, labels, "Inject", "mass")

    # calculate_implicit_waste_mass_for_hinge(
    #     agg2, ocel, by_object_id, labels, "SplitSteelSheet"
    # )
    # calculate_object_type_mass(agg2, ocel, by_object_id, labels, "SplitWaste")
    # calculate_object_type_mass(agg2, ocel, by_object_id, labels, "CutWaste")
    # calculate_object_type_count(agg2, ocel, by_object_id, labels, "FormedPart")
    # calculate_object_type_count(agg2, ocel, by_object_id, labels, "FemalePart")
    # calculate_object_type_count(agg2, ocel, by_object_id, labels, "MalePart")
    # calculate_object_type_mass(agg2, ocel, by_object_id, labels, "SteelPin")
    # calculate_object_type_mass(agg2, ocel, by_object_id, labels, "SteelCoil")

    # =====
    # If only variants with the bigger multiplicity should be kept, use this line.
    # This is only introduced as a future work suggestion in the thesis.
    # =====
    # agg2 = keep_general_variants(agg2)

    places, transitions = discover(
        agg2,
        ocel,
        by_object_id,
        labels,
        # =====
        # Set whether information should be shown on the places and transitions.
        # In addition, use weighted arcs if `False`, and variable arcs otherwise.
        # Set direction to `TB` for a top-to-bottom graph, and to `LR` for left-to-right.
        # =====
        {
            "DRAW_PLACE_INFORMATION": False,
            "DRAW_TRANSITION_INFORMATION": False,
            "USE_ARC_WEIGHTS": False,
            "DRAW_ARC_WEIGHTS": False,
            "DIRECTION": "TB",
        },
        object_instances,
    )

    point4 = time.perf_counter()

    # =====
    # Can be enabled to do conformance checking using the presented framework.
    # =====
    # calculate_conformance(ocel, places, transitions, object_instances)

    point5 = time.perf_counter()

    print("Reading took", point1 - point0, "s")
    print("Finding labels took", point2 - point1, "s")
    print("Mass took", point3 - point2, "s")
    print("Algorithm took", point4 - point3, "s")
    print("Conformance took", point5 - point4, "s")
