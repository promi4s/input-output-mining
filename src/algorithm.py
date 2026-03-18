from __future__ import annotations
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

from .waste import *


DRAW_PLACE_INFORMATION = False
DRAW_TRANSITION_INFORMATION = False
USE_ARC_WEIGHTS = False
DRAW_ARC_WEIGHTS = True


# Collapse occurrences greater than 1 to simplify the log,
# and where a count of `2` means the object occurs more than once
def collapse(
    input: list[tuple[str, str | None]], has_associated_activity: bool
) -> list[list[str | int | list[str | int]]]:
    result = []
    current_object = None
    current_count = 0

    f = 0
    for i, value in enumerate(input):
        if i < f:
            # Skip the elements that we collapsed
            continue

        if current_object is None:
            current_object = [
                value[0],
                [[value[1], 1]] if has_associated_activity else [],
            ]
            current_count = 1

        # This works because the log is sorted
        while f + 1 < len(input) and input[f + 1][0] == current_object[0]:
            if USE_ARC_WEIGHTS:
                current_count += 1
            elif current_count < 2:
                # Ceil the count at 2 since 2 means "any number greater 1" here
                current_count += 1

            # Add the following activity to the list
            if has_associated_activity:
                for i in current_object[1]:
                    if i[0] == input[f + 1][1]:  # if it is the same activity
                        i[1] += 1  # simply increase its count by 1
                        break
                else:  # otherwise create a new entry
                    current_object[1].append([input[f + 1][1], 1])

            f += 1
        f += 1

        result.append((current_object[0], current_count, current_object[1]))
        current_object = None
        current_count = 0

    return result


# Compare the arrays but do not compare the sets of next activities
# as these are separate from the variants
def compare(
    a: list[list[str | int | list[str | int]]],
    b: list[list[str | int | list[str | int]]],
) -> bool:
    return [[i[0], i[1]] for i in a] == [[i[0], i[1]] for i in b]


# Merges the activities in the list `source` into the list `into`
# by adding the count in `source` to the count in `into` if the
# activity already exists in `into`, and otherwise creating
# a new entry with the count from `source`.
def merge_activities(
    into: list[list[str | int]], source: list[list[str | int]]
) -> list[list[str | int]]:
    into_dict = {activity: count for activity, count in into}

    for activity, count in source:
        if activity in into_dict:
            into_dict[activity] += count
        else:
            into_dict[activity] = count

    into[:] = [[activity, into_dict[activity]] for activity in into_dict]


def aggregate(labels: dict[str, Union[str, list[tuple[str, str]], int]]):
    aggregation = defaultdict(list)
    object_instances = defaultdict(dict)

    for event_id, event in labels.items():
        types_of_input = [(i[0], i[2]) for i in event["input"]]
        types_of_output = [(i[0], i[2]) for i in event["output"]]
        types_of_initial_input = [(i[0],) for i in event["initial input"]]
        types_of_final_output = [(i[0],) for i in event["final output"]]
        types_of_unknown = [(i[0],) for i in event["unknown"]]

        # It is possible that the order of associations varies,
        # so to guarantee detecting the same set, we sort the lists
        types_of_input.sort()
        types_of_output.sort()
        types_of_initial_input.sort()
        types_of_final_output.sort()
        types_of_unknown.sort()

        types_of_input = collapse(types_of_input, True)
        types_of_output = collapse(types_of_output, True)
        types_of_initial_input = collapse(types_of_initial_input, False)
        types_of_final_output = collapse(types_of_final_output, False)
        types_of_unknown = collapse(types_of_unknown, False)

        for variant in aggregation[event["activity"]]:
            if (
                compare(variant["input"], types_of_input)
                and compare(variant["output"], types_of_output)
                and compare(variant["initial input"], types_of_initial_input)
                and compare(variant["final output"], types_of_final_output)
                and compare(variant["unknown"], types_of_unknown)
            ):
                variant["count"] += 1

                # Since the set of next activities can be different,
                # add the next activities found in the current variant
                # to the already stored next activities
                for i, _ in enumerate(variant["input"]):
                    merge_activities(variant["input"][i][2], types_of_input[i][2])

                for i, _ in enumerate(variant["output"]):
                    merge_activities(variant["output"][i][2], types_of_output[i][2])

                # Also add the current event to the variant that was found
                variant["initial input instances"] += [
                    i[1] for i in event["initial input"]
                ]
                variant["final output instances"] += [
                    i[1] for i in event["final output"]
                ]

                # For each object type that is an initial input,
                # increase its initial input count
                for i in event["initial input"]:
                    variant["initial input count"][i[0]] += 1

                for i in event["final output"]:
                    variant["final output count"][i[0]] += 1

                variant["event instances"].append(event_id)

                # Save that an object is an initial input here in the map
                for i in event["initial input"]:
                    object_instances[i[1]]["object type"] = i[0]

                    if "initial input variant" in object_instances[i[1]]:
                        # raise Exception("There already is an initial input variant")
                        pass

                    object_instances[i[1]]["initial input variant"] = variant

                # Save that an object is an initial input here in the map
                for i in event["final output"]:
                    object_instances[i[1]]["object type"] = i[0]

                    if "final output variant" in object_instances[i[1]]:
                        raise Exception("There already is an final output variant")

                    object_instances[i[1]]["final output variant"] = variant

                break
        else:
            initial_input_count = {i[0]: 0 for i in event["initial input"]}
            for i in event["initial input"]:
                initial_input_count[i[0]] += 1

            final_output_count = {i[0]: 0 for i in event["final output"]}
            for i in event["final output"]:
                final_output_count[i[0]] += 1

            variant = {
                "count": 1,
                "input": types_of_input,
                "output": types_of_output,
                "initial input": types_of_initial_input,
                "final output": types_of_final_output,
                "unknown": types_of_unknown,
                "initial input instances": [i[1] for i in event["initial input"]],
                "final output instances": [i[1] for i in event["final output"]],
                "initial input count": initial_input_count,
                "final output count": final_output_count,
                "object instances": [
                    i[1]
                    for i in (
                        event["initial input"]
                        + event["input"]
                        + event["output"]
                        + event["final output"]
                        + event["unknown"]
                    )
                ],
                "event instances": [event_id],
            }

            # Insert it since since we have not aborted during the loop
            aggregation[event["activity"]].append(variant)

            for i in event["initial input"]:
                object_instances[i[1]]["object type"] = i[0]

                if "initial input variant" in object_instances[i[1]]:
                    # raise Exception("There already is an initial input variant")
                    pass

                object_instances[i[1]]["initial input variant"] = variant

            for i in event["final output"]:
                object_instances[i[1]]["object type"] = i[0]

                if "final output variant" in object_instances[i[1]]:
                    raise Exception("There already is an final output variant")

                object_instances[i[1]]["final output variant"] = variant

    return aggregation, object_instances


class ObjectType:
    name: str
    color: str

    def __init__(self, name: str, color: str = "white"):
        self.name = name
        self.color = color

    def __repr__(self) -> str:
        return (
            f"ObjectType(name='{self.name}', color='{self.color}') at {hex(id(self))}"
        )

    def __eq__(self, other: object) -> bool:
        return self.name == other.name

    def rgb(self) -> list[int]:
        hex_color = self.color.lstrip("#")
        return [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)]


class Activity:
    name: str

    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:
        return f"Activity(name='{self.name}') at {hex(id(self))}"

    def __lt__(self, other: Activity) -> bool:
        return self.name < other.name

    def __eq__(self, other: object) -> bool:
        return self.name == other.name


def sublist(a: list[Activity], b: list[Activity]) -> bool:
    if len(a) == 0:
        return True

    i = 0
    j = 0

    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            i += 1
        j += 1  # Always move to next element in b
        # If we matched all elements in a, it is a sublist
        if i == len(a):
            return True
    return False


# A place of a specific object type, with some activities preceding
# it and some following it. The transitions are also stored.
class Place:
    _uuid: str
    _color: ObjectType = None
    _input: list[Activity] = []
    _output: list[Activity] = []
    _source: list[Transition] = []
    _target: list[Transition] = []
    _is_initial: bool
    _is_final: bool
    _is_unknown: bool
    _waste: Decimal | None
    _count: int

    def __init__(
        self,
        color: ObjectType,
        input: list[Activity],
        output: list[Activity],
        source: list[Transition],
        target: list[Transition],
        is_initial: bool = False,
        is_final: bool = False,
        is_unknown: bool = False,
        count: int = 0,
    ):
        self._uuid = str(uuid.uuid4())
        self._color = color
        self._input = sorted(input)
        self._output = sorted(output)
        self._source = source
        self._target = target
        self._is_initial = is_initial
        self._is_final = is_final
        self._is_unknown = is_unknown
        self._waste = None
        self._count = count

    def __repr__(self) -> str:
        return (
            f"Place(color='{self._color.name}', "
            f"input={[i.name for i in self._input]}, "
            f"output={[i.name for i in self._output]}"
            f"{", initial" if self._is_initial else ""}"
            f"{", final" if self._is_final else ""}"
            f") at {hex(id(self))}"
        )

    @property
    def uuid(self) -> str:
        return self._uuid

    @property
    def color(self) -> ObjectType:
        return self._color

    @color.setter
    def color(self, value: ObjectType) -> None:
        self._color = value

    @property
    def input(self) -> list[Activity]:
        return self._input

    @input.setter
    def input(self, value: list[Activity]) -> None:
        self._input = value

    @property
    def output(self) -> list[Activity]:
        return self._output

    @output.setter
    def output(self, value: list[Activity]) -> None:
        self._output = value

    @property
    def source(self) -> list[Transition]:
        return self._source

    @source.setter
    def source(self, value: list[Transition]) -> None:
        self._source = value

    @property
    def target(self) -> list[Transition]:
        return self._target

    @target.setter
    def target(self, value: list[Transition]) -> None:
        self._target = value

    @property
    def is_initial(self) -> bool:
        return self._is_initial

    @is_initial.setter
    def is_initial(self, value: bool) -> None:
        self._is_initial = value

    @property
    def is_final(self) -> bool:
        return self._is_final

    @is_final.setter
    def is_final(self, value: bool) -> None:
        self._is_final = value

    @property
    def is_unknown(self) -> bool:
        return self._is_unknown

    @is_unknown.setter
    def is_unknown(self, value: bool) -> None:
        self._is_unknown = value

    @property
    def waste(self) -> Decimal | None:
        return self._waste

    @waste.setter
    def waste(self, value: Decimal | None) -> None:
        self._waste = value

    @property
    def count(self) -> int | None:
        return self._count

    @count.setter
    def count(self, value: int) -> None:
        self._count = value

    def same_function_as(self, other: Place) -> bool:
        return (
            self.color == other.color
            and self.input == other.input
            and self.output == other.output
            and self.is_initial == other.is_initial
            and self.is_final == other.is_final
        )

    def subplace_of(self, other: Place) -> bool:
        return (
            self.color == other.color
            and sublist(self.input, other.input)
            and sublist(self.output, other.output)
            and self.is_initial == other.is_initial
            and self.is_final == other.is_final
            and self.is_unknown == other.is_unknown
        )


# A transition consisting of the activity associated with it,
# and two lists of the source and target places and its multiplicities
class Transition:
    _uuid: str
    _silent: bool
    # For silent transitions, these are the activities that we are connecting
    _silent_activity: Activity | None
    _activity: Activity | None
    _source: list[list[Place | int]]
    _target: list[list[Place | int]]
    _explicit_waste: Decimal | None
    _implicit_waste: Decimal | None
    # The original variant that created this transition, or None if silent
    _variant: Any | None

    def __init__(
        self,
        source: list[list[Place | int]],
        target: list[list[Place | int]],
        variant: Any | None = None,
        activity: Activity | None = None,
        silent: bool = False,
        silent_activity: Activity | None = None,
    ):
        self._uuid = str(uuid.uuid4())
        self._silent = silent
        self._silent_activity = silent_activity
        self._activity = activity
        self._source = source
        self._target = target
        self._variant = variant
        self._explicit_waste = None
        self._implicit_waste = None

    def __repr__(self) -> str:
        return (
            f"Transition("
            + (
                "silent, "
                if self.activity is None
                else f"activity='{self.activity.name}', "
            )
            + f"source={[(f"{i[0]._color.name} at {hex(id(i[0]))}", i[1]) for i in self._source]}, "
            f"target={[(f"{i[0]._color.name} at {hex(id(i[0]))}", i[1]) for i in self._target]}') "
            f"at {hex(id(self))}"
        )

    @property
    def uuid(self) -> str:
        return self._uuid

    @property
    def silent(self) -> bool:
        return self._silent

    @silent.setter
    def silent(self, value: bool) -> None:
        self._silent = value

    @property
    def silent_activity(self) -> tuple[Activity, Activity] | None:
        return self._silent_activity

    @silent_activity.setter
    def silent_activities(self, value: tuple[Activity, Activity] | None) -> None:
        self._silent_activity = value

    @property
    def activity(self) -> Activity | None:
        return self._activity

    @activity.setter
    def activity(self, value: Activity | None) -> None:
        self._activity = value

    @property
    def source(self) -> list[list[Place | int]]:
        return self._source

    @source.setter
    def source(self, value: list[list[Place | int]]) -> None:
        self._source = value

    @property
    def target(self) -> list[list[Place | int]]:
        return self._target

    @target.setter
    def target(self, value: list[list[Place | int]]) -> None:
        self._target = value

    @property
    def explicit_waste(self) -> Decimal | None:
        return self._explicit_waste

    @explicit_waste.setter
    def explicit_waste(self, value: Decimal | None) -> None:
        self._explicit_waste = value

    @property
    def implicit_waste(self) -> Decimal | None:
        return self._implicit_waste

    @implicit_waste.setter
    def implicit_waste(self, value: Decimal | None) -> None:
        self._implicit_waste = value

    @property
    def variant(self) -> Any:
        return self._variant


# Creates a transition for each variant in the aggregation,
# together with input and output places for each transition and object type
def generate_transitions_and_places(
    aggregation, object_instances, ocel, by_object_id, labels
):
    # First, create object types to be reused
    object_types = dict()
    # Also the activities
    activities = dict()

    color_i = 0
    predefined_colors = [
        # "#605d6e",
        "#ffa500",
        "#7b68ee",
        "#eec900",
        "#00bfff",
        "#32cd32",
        "#ff0000",
        "#ff1493",
        "#605D6E",
        "#132845",
        "#9ED020",
    ]

    # objects = []
    for activity, variants in aggregation.items():
        activities[activity] = Activity(name=activity)

        for variant in variants:
            for object in (
                variant["input"]
                + variant["output"]
                + variant["initial input"]
                + variant["final output"]
                + variant["unknown"]
            ):
                if object[0] in object_types:
                    continue

                if object[0] == "Container":
                    color = "#00bfff"
                    print("Container")
                elif object[0] == "Handling Unit":
                    color = "#32cd32"
                    print("Handling Unit")
                elif object[0] == "Transport Document":
                    color = "#7b68ee"
                    print("Transport Document")
                elif object[0] == "Customer Order":
                    color = "#ffa500"
                    print("Customer Order")
                elif object[0] == "Truck":
                    color = "#ff0000"
                    print("Truck")
                elif object[0] == "Forklift":
                    color = "#ff1493"
                    print("Forklift")
                elif object[0] == "Workstation":
                    color = "#e18ceb"
                    print("Vehicle")
                elif object[0] == "Worker":
                    color = "#1f3721"
                    print("Vehicle")
                elif object[0] == "Machine":
                    color = "#3B3B3B"
                    print("Vehicle")
                elif color_i < len(predefined_colors):
                    # if color_i < len(predefined_colors):
                    color = predefined_colors[color_i]
                    color_i += 1
                else:
                    color = "#{:02X}{:02X}{:02X}".format(
                        random.randint(0, 255),
                        random.randint(0, 255),
                        random.randint(0, 255),
                    )
                object_types[object[0]] = ObjectType(name=object[0], color=color)

    pprint(object_types)
    places = []
    transitions = []

    for activity, variants in aggregation.items():
        for variant in variants:
            # Create a transition and expand the source and target with
            # references to the newly created places afterwards
            transition = Transition(
                activity=activities[activity], source=[], target=[], variant=variant
            )

            if "explicit waste" in variant:
                transition.explicit_waste = variant["explicit waste"]

            if "implicit waste" in variant:
                transition.implicit_waste = variant["implicit waste"]

            transitions.append(transition)

            # Create the corresponding places

            for object_type, multiplicity, previous in variant["input"]:
                place = Place(
                    color=object_types[object_type],
                    # By using the if, we catch the case where
                    # an activity was filtered out completely
                    input=[activities[i[0]] for i in previous if i[0] in activities],
                    output=[activities[activity]],
                    source=[],
                    target=[transition],
                )

                places.append(place)

                # Add a backlink to the transition
                transition.source.append([place, multiplicity])

            for object_type, multiplicity, next in variant["output"]:
                place = Place(
                    color=object_types[object_type],
                    input=[activities[activity]],
                    output=[activities[i[0]] for i in next if i[0] in activities],
                    source=[transition],
                    target=[],
                )
                places.append(place)
                transition.target.append([place, multiplicity])

            for object_type, multiplicity, previous in variant["initial input"]:
                place = Place(
                    color=object_types[object_type],
                    input=[],
                    output=[activities[activity]],
                    source=[],
                    target=[transition],
                    is_initial=True,
                    count=variant["initial input count"][object_type],
                )

                if "object waste" in variant and object_type in variant["object waste"]:
                    place.waste = variant["object waste"][object_type]

                places.append(place)
                transition.source.append([place, multiplicity])

            for object_type, multiplicity, next in variant["final output"]:
                place = Place(
                    color=object_types[object_type],
                    input=[activities[activity]],
                    output=[],
                    source=[transition],
                    target=[],
                    is_final=True,
                    count=variant["final output count"][object_type],
                )

                if "object waste" in variant and object_type in variant["object waste"]:
                    place.waste = variant["object waste"][object_type]

                places.append(place)
                transition.target.append([place, multiplicity])

            for object_type, multiplicity, _ in variant["unknown"]:
                place = Place(
                    color=object_types[object_type],
                    input=[activities[activity]],
                    output=[activities[activity]],
                    source=[transition],
                    target=[transition],
                    is_unknown=True,
                )
                places.append(place)
                transition.target.append([place, multiplicity])

    return [transitions, places]


def detect_self_loops(transitions: list[Transition], places: list[Place]):
    for transition in transitions:
        activity = transition.activity

        for source in transition.source:
            if activity in source[0].input:
                # Find the corresponding output place
                for target in transition.target:
                    if (
                        target[0].color == source[0].color
                        and activity in target[0].output
                    ):
                        new_place = Place(
                            color=target[0].color,
                            input=source[0].input,
                            output=target[0].output,
                            source=[transition],
                            target=[transition],
                        )

                        # Remove the old places
                        places[:] = [
                            p
                            for p in places
                            if p is not source[0] and p is not target[0]
                        ]
                        places.append(new_place)

                        # Replace the old places with the new one
                        for s in transition.source:
                            if s[0] is source[0]:
                                # Keep the multiplicity
                                s[0] = new_place

                        for t in transition.target:
                            if t[0] is target[0]:
                                t[0] = new_place


# If two places refer to the exact same inputs and outputs, combine them
def combine_same_places(places: list[Place]):
    unique_places = []
    for place in places:
        for unique_place in unique_places:
            if place.same_function_as(unique_place):
                # Replace the place by the found unique place

                for transition in place.source:
                    # Replace the references
                    for p in transition.target:
                        if p[0] is place:
                            p[0] = unique_place
                            break
                    else:
                        raise Exception("Reference in transition not found")

                for transition in place.target:
                    for p in transition.source:
                        if p[0] is place:
                            p[0] = unique_place
                            break
                    else:
                        raise Exception("Reference in transition not found")
                break
        else:
            unique_places.append(place)

    return unique_places


# Merge the places if one is a subset of the other
def combine_subsets(places: list[Place]):
    changed = True
    while changed:
        changed = False
        unique_places = []
        for skip, place in enumerate(places):
            for unique_place in places:
                if place is unique_place:
                    continue

                if place.subplace_of(unique_place):
                    # Replace the place by the found unique place

                    for transition in place.source:
                        # Replace the references
                        unique_place.source.append(transition)

                        for p in transition.target:
                            if p[0] is place:
                                p[0] = unique_place
                                break
                        else:
                            raise Exception("Reference in transition not found")

                    for transition in place.target:
                        unique_place.target.append(transition)

                        if place.is_unknown:
                            continue

                        for p in transition.source:
                            if p[0] is place:
                                p[0] = unique_place
                                break
                        else:
                            raise Exception("Reference in transition not found")

                    changed = True
                    break
            else:
                unique_places.append(place)
                continue

            # We `break`ed before, and there is only one change per iteration,
            # so copy all the remaining places so we do not lose them
            for unique_place in places[skip + 1 :]:
                unique_places.append(unique_place)

            break

        places = unique_places

    return unique_places


def has_matching_transition(activity: Activity, transitions: list[Transition]) -> bool:
    for transition in transitions:
        if transition.activity is activity:
            return True
    return False


def get_transitions_of_activity(
    transitions: list[Transition], activity: Activity
) -> list[Transition]:
    result = []

    for t in transitions:
        if t.activity is activity:
            result.append(t)

    return result


def fill_missing_transitions(transitions: list[Transition], places: list[Place]):
    for place in places:
        # Check whether every output is matched by a transition
        for activity in place.output:
            if not has_matching_transition(activity, place.target):
                # Create silent transition

                # Find all the input places with the same object type of the target activity
                input_places = []
                for t in get_transitions_of_activity(transitions, activity):
                    for s, _ in t.source:
                        # Do not add duplicates
                        # Also, only create transitions to places that are not initial
                        if (
                            s.color is place.color
                            and not s in input_places
                            and not s.is_initial
                        ):
                            input_places.append(s)

                for i in input_places:
                    transition = Transition(
                        silent=True,
                        silent_activity=activity,
                        source=[[place, 1]],
                        # To all target places with multiplicity 1
                        target=[[i, 1]],
                    )
                    transitions.append(transition)

                    # Add the references to the new transitions on the targets
                    i.source.append(transition)


# Only keep those variants in the aggregation where `filter` returns `True`
def filter_aggregation_by_variants(aggregation, filter):
    result = dict()

    for activity, variants in aggregation.items():
        total = 0

        for variant in variants:
            total += variant["count"]

        kept = []
        for variant in variants:
            if filter(total, variant["count"]):
                kept.append(variant)

        if len(kept) > 0:
            result[activity] = kept

    return result


# Only keep those associated activites in the aggregation where `filter` returns `True`
def filter_aggregation_by_associations(aggregation, filter):
    result = deepcopy(aggregation)

    def handle_object(object):
        total = 0

        for associated in object[2]:
            total += associated[1]

        kept = []
        for associated in object[2]:
            if filter(total, associated[1]):
                kept.append([associated[0], associated[1]])

        return kept

    for variants in result.values():
        for variant in variants:
            kept_input = []
            kept_output = []

            for object in variant["input"]:
                kept = handle_object(object)
                if len(kept) > 0:
                    kept_input.append((object[0], object[1], kept))
                else:
                    raise Exception("No previous activity remaining after filtering")

            for object in variant["output"]:
                kept = handle_object(object)
                if len(kept) > 0:
                    kept_output.append((object[0], object[1], kept))
                else:
                    raise Exception("No next remaining after filtering")

            variant["input"] = kept_input
            variant["output"] = kept_output

    return result


def has_lower_multiplicites(
    a: list[list[Activity | int]], b: list[list[Activity | int]]
) -> bool:
    if len(a) != len(b):
        return False

    for i in a:
        for f in b:
            if i[0] == f[0] and i[1] <= f[1]:
                break
        else:
            # No matching element found in `b`
            return False

    return True


def is_more_general(subvariant, variant):
    return (
        has_lower_multiplicites(subvariant["input"], variant["input"])
        and has_lower_multiplicites(subvariant["output"], variant["output"])
        and has_lower_multiplicites(
            subvariant["initial input"], variant["initial input"]
        )
        and has_lower_multiplicites(subvariant["final output"], variant["final output"])
    )


# Removes variants if a more general variant exists for the same activity,
# meaning they are equal except an association has a higher multiplicity
def keep_general_variants(aggregation):
    result = dict()

    for activity, variants in aggregation.items():
        changed = True
        while changed:
            changed = False
            unique_variants = []
            for skip, variant in enumerate(variants):
                for unique_variant in variants:
                    if variant is unique_variant:
                        continue

                    if is_more_general(variant, unique_variant):
                        unique_variant["count"] += variant["count"]

                        changed = True
                        break
                else:
                    unique_variants.append(variant)
                    continue

                for unique_variant in variants[skip + 1 :]:
                    unique_variants.append(unique_variant)

                break

            variants = unique_variants

        result[activity] = variants

    return result


def contrast_color(rgb: list[int]) -> str:
    r, g, b = rgb
    if (
        (
            0.2126 * ((r / 255) ** 2.4 if r / 255 > 0.03928 else r / 255 / 12.92)
            + 0.7152 * ((g / 255) ** 2.4 if g / 255 > 0.03928 else g / 255 / 12.92)
            + 0.0722 * ((b / 255) ** 2.4 if b / 255 > 0.03928 else b / 255 / 12.92)
            + 0.05
        )
        / 0.05
    ) > (
        (1.0 + 0.05)
        / (
            0.2126 * ((r / 255) ** 2.4 if r / 255 > 0.03928 else r / 255 / 12.92)
            + 0.7152 * ((g / 255) ** 2.4 if g / 255 > 0.03928 else g / 255 / 12.92)
            + 0.0722 * ((b / 255) ** 2.4 if b / 255 > 0.03928 else b / 255 / 12.92)
            + 0.05
        )
    ):
        return "black"
    else:
        return "white"


# Taken and modified from
# https://github.com/process-intelligence-solutions/pm4py/blob/release/pm4py/visualization/ocel/ocpn/variants/wo_decoration.py
def apply(
    transitions: list[Transition],
    places: list[Place],
    rankdir: str = "TB",
) -> Digraph:
    filename = tempfile.NamedTemporaryFile(suffix=".gv")
    filename.close()

    viz = Digraph(
        "ofn",
        filename=filename.name,
        engine="dot",
        graph_attr={"bgcolor": "white"},
    )
    viz.attr("node", shape="ellipse", fixedsize="false")

    for place in places:
        label = (
            '<<FONT><TABLE BORDER="0" CELLSPACING="0">'
            + (
                (
                    (
                        f'<TR><TD COLSPAN="3"><I>{place.color.name}</I></TD></TR>'
                        + '<TR><TD BGCOLOR="black" COLSPAN="3" HEIGHT="1" CELLPADDING="0"></TD></TR>'  # Border
                    )
                    + (
                        "<TR><TD>&rarr;</TD><TD>"
                        + ", ".join(
                            map(
                                lambda i: i.name,
                                place.input,
                            )
                        )
                        + "</TD><TD></TD></TR>"
                        if len(place.input) > 0
                        else ""
                    )
                    + (
                        "<TR><TD></TD><TD>"
                        + ", ".join(
                            map(
                                lambda i: i.name,
                                place.output,
                            )
                        )
                        + "</TD><TD>&rarr;</TD></TR>"
                        if len(place.output) > 0
                        else ""
                    )
                )
                if DRAW_PLACE_INFORMATION
                else (
                    '<TR><TD COLSPAN="3">'
                    + (place.color.name if place.is_initial or place.is_final else "")
                    + "</TD></TR>"
                )
            )
            + (
                '<TR><TD BGCOLOR="black" COLSPAN="3" HEIGHT="1" CELLPADDING="0"></TD></TR>'  # Border
                f'<TR><TD COLSPAN="3">{place.waste}</TD></TR>'
                if place.waste is not None
                else ""
            )
            + "</TABLE></FONT>>"
        )

        viz.node(
            name=place.uuid,
            label=label,
            shape=(
                "doubleoctagon"
                if place.is_final
                else (
                    "octagon"
                    if place.is_initial
                    else ("ellipse" if DRAW_PLACE_INFORMATION else "circle")
                )
            ),
            style="filled",
            fillcolor=place.color.color,
            fontcolor=(contrast_color(place.color.rgb())),
        )

    for transition in transitions:
        label = (
            '<<FONT><TABLE BORDER="0" CELLSPACING="0">'
            + (
                (
                    '<TR><TD COLSPAN="3">'
                    + (
                        f"<I>\U0001d70f&#160;&#40;{transition.silent_activity.name}&#41;</I>"
                        if transition.silent
                        else f"<I>{transition.activity.name}</I>"
                    )
                    + "</TD></TR>"
                    + '<TR><TD BGCOLOR="black" COLSPAN="3" HEIGHT="1" CELLPADDING="0"></TD></TR>'  # Border
                    + "<TR><TD>&rarr;</TD><TD>"
                    + (
                        ", ".join(
                            map(
                                lambda i: f'<FONT COLOR="{i[0].color.color}">{i[1] if DRAW_ARC_WEIGHTS else ("&gt;1" if i[1] == 2 else "1")}</FONT>',
                                transition.source,
                            )
                        )
                    )
                    + "</TD><TD></TD></TR><TR><TD></TD><TD>"
                    + (
                        ", ".join(
                            map(
                                lambda i: f'<FONT COLOR="{i[0].color.color}">{i[1] if DRAW_ARC_WEIGHTS else ("&gt;1" if i[1] == 2 else "1")}</FONT>',
                                transition.target,
                            )
                        )
                    )
                    + "</TD><TD>&rarr;</TD></TR>"
                )
                if DRAW_TRANSITION_INFORMATION
                else (
                    '<TR><TD COLSPAN="3">'
                    + ("\U0001d70f" if transition.silent else transition.activity.name)
                    + "</TD></TR>"
                )
            )
            + (
                '<TR><TD BGCOLOR="black" COLSPAN="3" HEIGHT="1" CELLPADDING="0"></TD></TR>'
                if transition.explicit_waste is not None
                or transition.implicit_waste is not None
                else ""
            )
            + (
                '<TR><TD COLSPAN="3">' + f"{transition.explicit_waste}" + "</TD></TR>"
                if transition.explicit_waste is not None
                else ""
            )
            + (
                '<TR><TD COLSPAN="3">' + f"{transition.implicit_waste}" + "</TD></TR>"
                if transition.implicit_waste is not None
                else ""
            )
            + "</TABLE></FONT>>"
        )

        viz.node(
            name=transition.uuid,
            label=label,
            shape="box",
            style="solid",
        )

    for transition in transitions:

        def arc(place, multiplicity):
            if DRAW_ARC_WEIGHTS:
                return [
                    "1.0",
                    f'<<FONT COLOR="{place.color.color}">{multiplicity}</FONT>>',
                ]
            else:
                return ["4.0" if multiplicity == 2 else "1.0", None]

        for place, multiplicity in transition.source:
            pendwidth, label = arc(place, multiplicity)
            viz.edge(
                place.uuid,
                transition.uuid,
                color=place.color.color,
                penwidth=pendwidth,
                label=label,
            )

        for place, multiplicity in transition.target:
            penwidth, label = arc(place, multiplicity)

            if place.is_unknown:
                viz.edge(
                    transition.uuid,
                    place.uuid,
                    style="dashed",
                    dir="both",
                    arrowhead="empty",
                    arrowtail="empty",
                    color=place.color.color,
                    penwidth=penwidth,
                    label=label,
                )
            else:
                viz.edge(
                    transition.uuid,
                    place.uuid,
                    color=place.color.color,
                    penwidth=penwidth,
                    label=label,
                )

    viz.attr(rankdir=rankdir)
    viz.format = "svg"

    return viz


def discover_dot_string(
    aggregation, ocel, by_object_id, labels, config, object_instances
) -> Digraph:
    global DRAW_PLACE_INFORMATION
    global DRAW_TRANSITION_INFORMATION
    global USE_ARC_WEIGHTS
    global DRAW_ARC_WEIGHTS

    DRAW_PLACE_INFORMATION = config["DRAW_PLACE_INFORMATION"]
    DRAW_TRANSITION_INFORMATION = config["DRAW_TRANSITION_INFORMATION"]
    USE_ARC_WEIGHTS = config["USE_ARC_WEIGHTS"]
    DRAW_ARC_WEIGHTS = config["DRAW_ARC_WEIGHTS"]

    transitions, places = generate_transitions_and_places(
        aggregation, object_instances, ocel, by_object_id, labels
    )
    detect_self_loops(transitions, places)
    places = combine_subsets(places)
    fill_missing_transitions(transitions, places)
    viz = apply(transitions, places, config["DIRECTION"])

    return viz


def discover(aggregation, ocel, by_object_id, labels, config, object_instances):
    global DRAW_PLACE_INFORMATION
    global DRAW_TRANSITION_INFORMATION
    global USE_ARC_WEIGHTS
    global DRAW_ARC_WEIGHTS

    DRAW_PLACE_INFORMATION = config["DRAW_PLACE_INFORMATION"]
    DRAW_TRANSITION_INFORMATION = config["DRAW_TRANSITION_INFORMATION"]
    USE_ARC_WEIGHTS = config["USE_ARC_WEIGHTS"]
    DRAW_ARC_WEIGHTS = config["DRAW_ARC_WEIGHTS"]

    transitions, places = generate_transitions_and_places(
        aggregation, object_instances, ocel, by_object_id, labels
    )
    detect_self_loops(transitions, places)
    places = combine_subsets(places)
    fill_missing_transitions(transitions, places)
    viz = apply(transitions, places, config["DIRECTION"])

    gview.view(viz)

    # Check correctness: every transition target must be a place
    for t in transitions:
        for a, _ in t.source + t.target:
            for p in places:
                if a is p:
                    break
            else:
                print("Unlisted place", a)
                print("Transition", t)
                raise Exception("Target of a transition is not a place")

    # every place must be in some transition
    t_ = list(map(lambda i: i.source, transitions))
    t_ = t_ + list(map(lambda i: i.target, transitions))
    t_ = [i for ii in t_ for i in ii]
    t_ = list(map(lambda i: i[0], t_))
    for p in places:
        for a in t_:
            if a is p:
                break
        else:
            print("Unmentioned place", p)
            raise Exception("Place is not in any transition")

    # f = open("log", "w")
    # print("\n")
    # pprint(transitions, stream=f)
    # pprint(transitions)
    # print("\n")
    # pprint(places, stream=f)
    # pprint(places)

    return places, transitions
