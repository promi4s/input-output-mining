from __future__ import annotations
import pm4py
from pandas import Timestamp, DataFrame
from pandas.core.groupby import DataFrameGroupBy
from decimal import Decimal
from collections import defaultdict
from copy import deepcopy
from pm4py.objects.ocel.obj import OCEL
import sys
import uuid
from graphviz import Digraph
import tempfile
from pm4py.visualization.common import gview
from tqdm.auto import tqdm
import pm4py
from pandas import Timestamp, DataFrame
from pandas.core.groupby import DataFrameGroupBy
import pandas
from decimal import Decimal
from collections import defaultdict
from copy import deepcopy
from pm4py.objects.ocel.obj import OCEL
from typing import Union, Any
import json
from pprint import pprint
import datetime
import sys
import networkx as nx
import uuid
from graphviz import Digraph
import tempfile
from pm4py.visualization.common import gview
import random
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils
from pm4py.algo.evaluation.simplicity import algorithm as simplicity_evaluator
from pm4py.algo.evaluation.generalization import algorithm as generalization_evaluator

from .algorithm import Place, Transition


MAX_TOKENS_PER_PLACE = 50


def calculate_conformance(ocel, places, transitions, object_instances):
    # Create Petri net unflattened, so the full one
    petri_net, _ = create_flattened_petri_net(places, transitions, object_instances)

    pm4py.view_petri_net(petri_net, format="svg")
    print("Simplicity:", simplicity_evaluator.apply(petri_net))

    print(size_statistics(places, transitions))

    # Alignments for accuracy
    conformance_alignments(ocel, places, transitions, object_instances)


def size_statistics(places: list[Place], transitions: list[Transition]):
    total_size = len(places) + len(transitions)
    silent_transitions = 0
    maximum_degree = 0
    duplicates = defaultdict(lambda: 0)

    for transition in transitions:
        # Also add the number of arcs to the total size
        total_size += len(transition.source) + len(transition.target)

        # For silent ratio
        if transition.silent:
            silent_transitions += 1
        else:
            # Add this to the number of same activities
            duplicates[transition.activity.name] += 1

        # Only the consider the maximum degree of transitions,
        # as these are the active part of the Petri net
        maximum_degree = max(maximum_degree, len(transition.source))
        maximum_degree = max(maximum_degree, len(transition.target))

    return {
        "total nodes": len(places) + len(transitions),
        "total size": total_size,
        "maximum degree": maximum_degree,
        "silent ratio": silent_transitions / len(transitions),
        "highest duplicate": max(duplicates.items(), key=lambda item: item[1]),
    }


def conformance_alignments(
    ocel: OCEL,
    places: list[Place],
    transitions: list[Transition],
    object_instances: Any,
):
    for place in places:
        if place.is_unknown:
            raise Exception(
                "Cannot run conformance when there are unknown places such as",
                repr(place),
            )

    all_fitnesses = []

    for flatten_object_type in tqdm(pm4py.ocel_get_object_types(ocel)):
        petri_net, markings = create_flattened_petri_net(
            places, transitions, object_instances, flatten_object_type
        )
        flattened = pm4py.ocel_flattening(ocel, flatten_object_type)

        # Get the connected components
        related_object_ids = determine_related_objects(ocel, flatten_object_type)
        related_object_ids = split_large_groups(related_object_ids)
        # Group the flattened log into the same case IDs
        flattened = group_flattened_log(flattened, related_object_ids)
        # Group the markings as well
        related_markings = group_by_related(markings, related_object_ids)

        fitnesses = []
        with tqdm(related_object_ids, desc=f"Processing {flatten_object_type}") as pbar:
            for group in pbar:
                group_id = "-".join(sorted(group))

                pbar.set_postfix({"current_id": group_id})

                trace_fitness = alignment_trace(
                    petri_net, related_markings, flattened, group
                )

                # Show failed traces
                if trace_fitness != 1.0 and False:
                    print("Not 1.0:", group_id)

                fitnesses.append(trace_fitness)

        print(
            f"Fitness average for {flatten_object_type}",
            sum(fitnesses) / len(fitnesses),
        )
        all_fitnesses.append(sum(fitnesses) / len(fitnesses))

    print(
        "Fitness average over all:",
        sum(all_fitnesses) / len(pm4py.ocel_get_object_types(ocel)),
    )


def alignment_trace(petri_net, related_markings, flattened, group):
    group_id = "-".join(sorted(group))

    flattened_filtered = flattened[flattened["case:concept:name"] == group_id]

    if False:
        print(
            flattened_filtered[
                ["ocel:eid", "time:timestamp", "case:concept:name"]
            ].to_string()
        )
        print(related_markings[group_id])
        pm4py.view_petri_net(
            petri_net,
            related_markings[group_id]["initial"],
            related_markings[group_id]["final"],
            format="svg",
        )

    try:
        replayed_traces = pm4py.conformance_diagnostics_alignments(
            flattened_filtered,
            petri_net,
            related_markings[group_id]["initial"],
            related_markings[group_id]["final"],
        )
    except Exception as e:
        return 0
        print(e)

        print(
            flattened_filtered[
                ["ocel:eid", "time:timestamp", "case:concept:name"]
            ].to_string()
        )
        print(related_markings[group_id])
        pm4py.view_petri_net(
            petri_net,
            related_markings[group_id]["initial"],
            related_markings[group_id]["final"],
            format="svg",
        )

    return replayed_traces[0]["fitness"]


def create_flattened_petri_net(
    places: list[Place],
    transitions: list[Transition],
    object_instances: dict[str, dict[str, Any]],
    object_type: str | None = None,
) -> tuple[PetriNet, dict[str, dict[str, Place | None]]]:
    net = PetriNet("PetriNet")
    petri_net_places = {}

    markings = defaultdict(lambda: {"initial": None, "final": None})

    for place in places:
        if object_type is not None and place.color.name != object_type:
            continue

        petri_net_place = PetriNet.Place(place.uuid)
        petri_net_places[place.uuid] = petri_net_place
        net.places.add(petri_net_place)

        continue
        if place.is_initial:
            initial_marking[petri_net_place] = place.count
        if place.is_final:
            final_marking[petri_net_place] = place.count

    petri_net_transitions = {}
    for transition in transitions:
        # Skip if this transition is not related to the place at all,
        # whether by being input or output
        if (
            object_type is not None
            and all(
                map(
                    lambda place: place[0].color.name != object_type,
                    transition.source,
                )
            )
            and all(
                map(
                    lambda place: place[0].color.name != object_type,
                    transition.target,
                )
            )
        ):
            continue

        petri_net_transition = PetriNet.Transition(
            transition.uuid, transition.activity.name if transition.activity else None
        )
        petri_net_transitions[transition.uuid] = petri_net_transition
        net.transitions.add(petri_net_transition)

        if object_type is None:
            continue

        for place, multiplicity in transition.source:
            if place.is_initial:
                # For the initial place,
                # find all objects
                if place.color.name != object_type:
                    # This place is of a different type the one we are flattening
                    continue

                for object_id, object_map in object_instances.items():
                    if object_map["object type"] == object_type:
                        if (
                            "initial input variant" in object_map
                            and object_map["initial input variant"]
                            is transition.variant
                        ):
                            # We now have a place of the type that we are flattening,
                            # and an object ID which is an initial input in the transition
                            # where that place is an initial input
                            markings[object_id]["initial"] = petri_net_places[
                                place.uuid
                            ]

        for place, multiplicity in transition.target:
            if place.is_final:
                if place.color.name != object_type:
                    continue

                for object_id, object_map in object_instances.items():
                    if object_map["object type"] == object_type:
                        if (
                            "final output variant" in object_map
                            and object_map["final output variant"] is transition.variant
                        ):
                            markings[object_id]["final"] = petri_net_places[place.uuid]

    for transition in transitions:
        for place, multiplicity in transition.source:
            if object_type is not None and place.color.name != object_type:
                continue

            petri_utils.add_arc_from_to(
                petri_net_places[place.uuid],
                petri_net_transitions[transition.uuid],
                net,
                # Assume weights are 1
                # multiplicity,
            )

        for place, multiplicity in transition.target:
            if object_type is not None and place.color.name != object_type:
                continue
            petri_utils.add_arc_from_to(
                petri_net_transitions[transition.uuid],
                petri_net_places[place.uuid],
                net,
                # multiplicity,
            )

    return (net, markings)


# Calculate the related objects which are connected through some events
def determine_related_objects(ocel: OCEL, object_type: str) -> list[list[str]]:
    # 1. Extract the E2O relations DataFrame
    # In pm4py OCEL objects, relations are typically stored in the 'relations' attribute
    relations = ocel.relations.copy()

    # 2. Extract Objects DataFrame to validate types
    objects_df = ocel.objects

    # 3. Apply Object Type Filter (if requested)
    if object_type:
        # Get set of valid OIDs for this type
        valid_oids = set(objects_df[objects_df["ocel:type"] == object_type]["ocel:oid"])

        # Filter the relations table to only include these objects
        relations = relations[relations["ocel:oid"].isin(valid_oids)]
    else:
        # If no filter, all OIDs in the object table are valid nodes
        valid_oids = set(objects_df["ocel:oid"])

    # 4. Initialize the Graph
    G = nx.Graph()

    # Add all valid objects as nodes immediately.
    # This ensures isolated objects (those that don't share events with others
    # or have no events) are still returned as single-item groups.
    G.add_nodes_from(valid_oids)

    # 5. Group relations by Event ID to find co-occurring objects
    # We group by 'ocel:eid' and get a list of 'ocel:oid's for each event
    events_grouping = relations.groupby("ocel:eid")["ocel:oid"].apply(list)

    # 6. Build the edges
    # For every event, all objects involved are related.
    for oids in events_grouping:
        if len(oids) > 1:
            # Optimization: Instead of adding edges between EVERY pair (N^2),
            # we simply connect the first object to all other objects in the list.
            # This creates a "star" shape for that event, which is sufficient
            # to establish connectivity for the component calculation.
            center_node = oids[0]
            other_nodes = oids[1:]

            edges = [(center_node, other) for other in other_nodes]
            G.add_edges_from(edges)

    # 7. Calculate Connected Components
    # This finds all disjoint sets of objects connected directly or transitively
    connected_components = list(nx.connected_components(G))

    # Convert sets to lists for the final output
    return [list(component) for component in connected_components]


def split_large_groups(groups: list[list[str]]) -> list[list[str]]:
    processed_list = []

    for sublist in groups:
        # Check if the sublist needs splitting
        if len(sublist) > MAX_TOKENS_PER_PLACE:
            # Create chunks of the sublist
            for i in range(0, len(sublist), MAX_TOKENS_PER_PLACE):
                processed_list.append(sublist[i : i + MAX_TOKENS_PER_PLACE])
        else:
            # Keep the sublist as it is
            processed_list.append(sublist)

    return processed_list


def group_flattened_log(flattened: DataFrame, related: list[list[str]]) -> DataFrame:
    # 1. Create a mapping dictionary: {object_id -> case_id}
    oid_to_case = {}

    for i, group in enumerate(related):
        # You can name the case whatever you want.
        # Here we use 'case_0', 'case_1', etc.
        sorted_group = sorted(group)
        case_name = "-".join(sorted_group)

        for oid in group:
            oid_to_case[oid] = case_name

    # 2. Apply the mapping to the DataFrame
    # If an object in the DF was not in the groups, it gets NaN (or you can handle fillna)
    flattened["case:concept:name"] = flattened["case:concept:name"].map(oid_to_case)

    return flattened


def group_by_related(
    markings: dict[str, dict[str, Place | None]], related: dict[str, dict[str, Marking]]
) -> dict[str, dict[str, Marking]]:
    result = {}

    for group in related:
        initial_marking = Marking()
        final_marking = Marking()

        for object_id in group:
            if markings[object_id]["initial"] is not None:
                initial_marking[markings[object_id]["initial"]] += 1

            if markings[object_id]["final"] is not None:
                final_marking[markings[object_id]["final"]] += 1

        #  # Same ID as in group_flattened_log
        result["-".join(sorted(group))] = {
            "initial": initial_marking,
            "final": final_marking,
        }

    return result
