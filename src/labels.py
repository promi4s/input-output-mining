from decimal import Decimal
import json
from pandas import Timestamp, DataFrame
from pandas.core.groupby import DataFrameGroupBy
import numpy as np
from collections import defaultdict
from pprint import pprint
from pm4py.objects.ocel.obj import OCEL
from typing import Union
from copy import deepcopy


# Given that `logistical_all_before_and_after()` returned `True`, find the labels
def label_logistical_all_before_and_after(
    associations: dict[str, (bool, bool, bool)],
    grouped_by_oid: DataFrameGroupBy,
    event_id: str,
) -> dict[str, list[str]]:
    return {
        "type": "logistics0",
        "input": [
            (
                value[2],
                object_id,
                previous_activity(grouped_by_oid, event_id, object_id),
            )
            for object_id, value in associations.items()
        ],
        "output": [
            (
                value[2],
                object_id,
                next_activity(grouped_by_oid, event_id, object_id),
            )
            for object_id, value in associations.items()
        ],
        "initial input": [],
        "final output": [],
        "unknown": [],
    }


# Given that `logistical_all_before()` returned `True`, find the labels
def label_logistical_all_before(
    associations: dict[str, (bool, bool, bool)],
    grouped_by_oid: DataFrameGroupBy,
    event_id: str,
) -> dict[str, list[str]]:
    outputs = []
    final_outputs = []

    for object_id, value in associations.items():
        # Still used afterwards
        if value[1]:
            outputs.append(
                (
                    value[2],
                    object_id,
                    next_activity(grouped_by_oid, event_id, object_id),
                )
            )
        else:
            final_outputs.append((value[2], object_id, None))

    return {
        "type": "logistics1",
        "input": [
            (
                value[2],
                object_id,
                previous_activity(grouped_by_oid, event_id, object_id),
            )
            for object_id, value in associations.items()
        ],
        "output": outputs,
        "initial input": [],
        "final output": final_outputs,
        "unknown": [],
    }


# Given that `logistical_all_after()` returned `True`, find the labels
def label_logistical_all_after(
    associations: dict[str, (bool, bool, bool)],
    grouped_by_oid: DataFrameGroupBy,
    event_id: str,
) -> dict[str, list[str]]:
    inputs = []
    initials_inputs = []

    for object_id, value in associations.items():
        # Just moved logistically
        if value[0]:
            inputs.append(
                (
                    value[2],
                    object_id,
                    previous_activity(grouped_by_oid, event_id, object_id),
                )
            )
        else:
            initials_inputs.append((value[2], object_id, None))

    return {
        "type": "logistics2",
        "input": inputs,
        "output": [
            (
                value[2],
                object_id,
                next_activity(grouped_by_oid, event_id, object_id),
            )
            for object_id, value in associations.items()
        ],
        "initial input": initials_inputs,
        "final output": [],
        "unknown": [],
    }


def label_logistical_all_unknown(
    associations: dict[str, (bool, bool, bool)],
    grouped_by_oid: DataFrameGroupBy,
    event_id: str,
) -> dict[str, list[str]]:
    return {
        "type": "logistics3",
        "input": [],
        "output": [],
        "initial input": [
            (
                value[2],
                object_id,
                None,
            )
            for object_id, value in associations.items()
        ],
        "final output": [
            (
                value[2],
                object_id,
                None,
            )
            for object_id, value in associations.items()
        ],
        "unknown": [],
    }


# Given that `transformation_final()` returned `True`, find the labels
def label_transformation_final(
    associations: dict[str, (bool, bool, bool)],
    grouped_by_oid: DataFrameGroupBy,
    event_id: str,
) -> dict[str, list[str]]:
    inputs = []
    final_outputs = []

    for object_id, value in associations.items():
        # Just moved logistically
        if not value[0] and not value[1]:
            final_outputs.append((value[2], object_id, None))
        else:
            inputs.append(
                (
                    value[2],
                    object_id,
                    previous_activity(grouped_by_oid, event_id, object_id),
                )
            )

    return {
        "type": "transformation4",
        "input": inputs,
        "output": [],
        "initial input": [],
        "final output": final_outputs,
        "unknown": [],
    }


# Given that `transformation_initial()` returned `True`, find the labels
def label_transformation_initial(
    associations: dict[str, (bool, bool, bool)],
    grouped_by_oid: DataFrameGroupBy,
    event_id: str,
) -> dict[str, list[str]]:
    outputs = []
    initial_inputs = []

    for object_id, value in associations.items():
        # Just moved logistically
        if not value[0] and not value[1]:
            initial_inputs.append((value[2], object_id, None))
        else:
            outputs.append(
                (
                    value[2],
                    object_id,
                    next_activity(grouped_by_oid, event_id, object_id),
                )
            )

    return {
        "type": "transformation5",
        "input": [],
        "output": outputs,
        "initial input": initial_inputs,
        "final output": [],
        "unknown": [],
    }


# We do not need to check another function because this finds the fallthrough labels.
def label_transformation_fallthrough(
    associations: dict[str, (bool, bool, bool)],
    grouped_by_oid: DataFrameGroupBy,
    event_id: str,
) -> dict[str, list[str]]:
    inputs = []
    outputs = []
    unknown = []

    for object_id, value in associations.items():
        if value[0]:
            inputs.append(
                (
                    value[2],
                    object_id,
                    previous_activity(grouped_by_oid, event_id, object_id),
                )
            )

        if value[1]:
            outputs.append(
                (
                    value[2],
                    object_id,
                    next_activity(grouped_by_oid, event_id, object_id),
                )
            )

        if not value[0] and not value[1]:
            unknown.append((value[2], object_id, None))

    return {
        "type": "transformation6",
        "input": inputs,
        "output": outputs,
        "initial input": [],
        "final output": [],
        "unknown": unknown,
    }


activity_column = 1


def next_activity(grouped_by_oid, event_id: str, object_id: str):
    global activity_column

    # Fetch the group of the object that we are inspecting,
    group = grouped_by_oid[object_id]
    # By using the relative index, fetch the next event in the group
    # This works because the grouping frame is sorted by timestamp
    row_index = np.argmax(group[:, 0] == event_id)
    if row_index + 1 < group.shape[0]:
        return group[row_index + 1][activity_column]
    else:
        print("next_activity does not have next event")
        raise Exception()


def previous_activity(grouped_by_oid, event_id: str, object_id: str):
    global activity_column

    group = grouped_by_oid[object_id]
    row_index = np.argmax(group[:, 0] == event_id)
    if row_index > 0:
        return group[row_index - 1][activity_column]
    else:
        # Should not happen
        print("previous_activity does not have previous event")
        raise Exception()


# Find the labeling of each event in the log.
# The resources must be filtered out of the log when calling this function.
def find_event_labels(
    ocel: OCEL, hints: dict[str, str] = dict()
) -> dict[str, Union[str, list[tuple[str, str]], int]]:
    global activity_column

    # Stores two entries
    # [0] is the timestamp of the first occurrence
    # [1] is the timestamp of the last occurrence
    object_first_last = dict()
    sorted = ocel.relations.sort_values(by=["ocel:timestamp"])
    grouped = sorted.groupby("ocel:oid")

    grouped_by_oid = {group: data.to_numpy() for group, data in grouped}

    def determine_use(object_id: str, timestamp: Timestamp) -> tuple[bool, bool, bool]:
        cached = object_first_last[object_id]
        before = cached[0] < timestamp
        after = timestamp < cached[1]

        return (before, after)

    # Grouping ocel.relations does not change the order later
    activity_column = ocel.relations.columns.get_loc("ocel:activity")
    timestamp_column = ocel.relations.columns.get_loc("ocel:timestamp")
    oid_column = ocel.relations.columns.get_loc("ocel:oid")
    type_column = ocel.relations.columns.get_loc("ocel:type")

    for object_id, rows in grouped_by_oid.items():
        object_first_last[object_id] = (
            rows[0][timestamp_column],
            rows[-1][timestamp_column],
        )

    labels = dict()

    act = defaultdict(lambda: [0, 0, 0, 0, 0, 0, 0])

    grouped = {
        group: data.to_numpy()
        for group, data in ocel.relations.groupby("ocel:eid", sort=False)
    }

    for event_id, rows in grouped.items():
        associations = dict()

        activity = rows[0][activity_column]
        timestamp = rows[0][timestamp_column]

        for object in rows:
            # Set the hints manually
            if object[type_column] in hints and hints[object[type_column]] != "inner":
                continue

            a, b = determine_use(object[oid_column], timestamp)
            associations[object[oid_column]] = (a, b, object[type_column])

        if all([before and after for before, after, _ in associations.values()]):
            act[activity][0] += 1
            labels[event_id] = label_logistical_all_before_and_after(
                associations, grouped_by_oid, event_id
            )
        elif all([before for before, _, _ in associations.values()]):
            act[activity][1] += 1
            labels[event_id] = label_logistical_all_before(
                associations, grouped_by_oid, event_id
            )
        elif all([after for _, after, _ in associations.values()]):
            act[activity][2] += 1
            labels[event_id] = label_logistical_all_after(
                associations, grouped_by_oid, event_id
            )
        elif all(
            not before and not after for before, after, _ in associations.values()
        ):
            act[activity][3] += 1
            labels[event_id] = label_logistical_all_unknown(
                associations, grouped_by_oid, event_id
            )
        elif all([not after for _, after, _ in associations.values()]):
            act[activity][4] += 1
            labels[event_id] = label_transformation_final(
                associations, grouped_by_oid, event_id
            )
        elif all([not before for before, _, _ in associations.values()]):
            act[activity][5] += 1
            labels[event_id] = label_transformation_initial(
                associations, grouped_by_oid, event_id
            )
        else:
            act[activity][6] += 1
            labels[event_id] = label_transformation_fallthrough(
                associations, grouped_by_oid, event_id
            )

        # Also add the event activity type to each label
        labels[event_id]["activity"] = activity
        # Also add the event timestamp, as an `int`, to each label
        labels[event_id]["timestamp"] = int(timestamp.timestamp())

        # Set the hints by object type
        for object in rows:
            if object[type_column] in hints:
                if hints[object[type_column]] == "inner":
                    # Remove mentions in initial inputs and final outputs
                    labels[event_id]["initial input"] = [
                        (object_type, object_id, activity)
                        for (object_type, object_id, activity) in labels[event_id][
                            "initial input"
                        ]
                        if object_type != object[type_column]
                    ]
                    labels[event_id]["final output"] = [
                        (object_type, object_id, activity)
                        for (object_type, object_id, activity) in labels[event_id][
                            "final output"
                        ]
                        if object_type != object[type_column]
                    ]
                else:
                    labels[event_id][hints[object[type_column]]].append(
                        (object[type_column], object[oid_column], None)
                    )

    for a, b in act.items():
        print(a)
        print(b)

    return {"labels": labels}


# Try to resolve the "unknown" inputs or outputs by comparing masses.
# Returns the updated labels with the determined roles, as well as the
# fields `input_mass` and `output_mass` for the total masses.
def resolve_unknown(
    by_object_id: DataFrame,
    labels: dict[str, Union[str, list[tuple[str, str]], int]],
    input_mass: Decimal,
    output_mass: Decimal,
) -> dict[str, Union[Decimal, dict[str, Union[str, int]]]]:
    object_types = defaultdict(Decimal)

    # Find which activities in general are unknown
    for value in labels.values():
        for object_type, object_id, _ in value["unknown"]:
            mass = by_object_id.loc[object_id]

            object_types[object_type] += Decimal(mass["mass"])

    print("Unknown object types", object_types)

    # Build all possible combinations of an unknown being input or output
    events = list(object_types.keys())
    n = len(events)
    combinations = []

    def build_combinations(source):
        if len(source) == n:
            return combinations.append(source)

        source1 = deepcopy(source)
        source2 = deepcopy(source)
        source1.append(0)
        source2.append(1)

        build_combinations(source1)
        build_combinations(source2)

    build_combinations([])

    current_winner = Decimal("Infinity")
    current_combination = None
    current_input_mass = Decimal("0")
    current_output_mass = Decimal("0")

    for combination in combinations:
        input_mass_simulated = input_mass
        output_mass_simulated = output_mass

        for i, value in enumerate(combination):
            if value == 0:
                # Assume input
                input_mass_simulated += object_types[events[i]]
            else:
                # Assume output
                output_mass_simulated += object_types[events[i]]

        difference = abs(input_mass_simulated - output_mass_simulated)
        # Heuristically find the smallest absolute difference between the
        # input masses and output masses
        print("CHECK input", input_mass_simulated, "output", output_mass_simulated)
        if difference < current_winner:
            print("Found new winner", combination, difference)
            current_winner = difference
            current_combination = combination
            current_input_mass = input_mass_simulated
            current_output_mass = output_mass_simulated

    # Visually show the result as well
    verdict = dict()
    for i, value in enumerate(current_combination):
        if value == 0:
            verdict[events[i]] = "initial input"
        else:
            verdict[events[i]] = "final output"
    print("Final verdict", verdict)

    for value in labels.values():
        for object_type, object_id, _ in value["unknown"]:
            value[verdict[object_type]].append((object_type, object_id, None))

        for i, [object_type, object_id, _] in enumerate(value["initial input"]):
            # mass = by_object_id.loc[object_id]
            # Todo: Respect object_changes
            value["initial input"][i] = (
                object_type,
                object_id,
                None,
            )

        for i, [object_type, object_id, _] in enumerate(value["final output"]):
            # mass = by_object_id.loc[object_id]
            value["final output"][i] = (
                object_type,
                object_id,
                None,
            )

        # We resolved all unknowns
        value["unknown"] = []

    # Return the updated labels without unkowns
    return {
        "input_mass": current_input_mass,
        "output_mass": current_output_mass,
        "labels": labels,
        "verdict": verdict,
    }


# Calculate the total input and output mass. Resolve before if desired.
def calculate_masses(
    ocel: OCEL, labels: dict[str, Union[str, list[tuple[str, str]], int]], resolve: bool
) -> dict[str, Union[Decimal, dict[str, Union[str, int]]]]:
    by_object_id = ocel.objects.set_index("ocel:oid")

    input_mass = Decimal("0")
    output_mass = Decimal("0")

    # First, calculate the total input and output mass
    for value in labels.values():
        for _, object_id, _ in value["initial input"]:
            input_mass += Decimal(by_object_id.loc[object_id]["mass"])

        for i in value["unknown"]:
            if len(i) < 3:
                print("\n\n\n")
                print(value)
                exit()
        for _, object_id, _ in value["final output"]:
            output_mass += Decimal(by_object_id.loc[object_id]["mass"])

    # Try to resolve
    if resolve:
        resolved = resolve_unknown(by_object_id, labels, input_mass, output_mass)

        print("Input", resolved["input_mass"])
        print("Output", resolved["output_mass"])
        return resolved
    else:
        print("Input", input_mass)
        print("Output", output_mass)
        return {
            "input_mass": input_mass,
            "output_mass": output_mass,
            "labels": labels,
        }


# Export the labels to the file
def export_labels(labels: dict[str, Union[str, float]], file_name: str):
    json.dump(labels, open(file_name, "w"))
