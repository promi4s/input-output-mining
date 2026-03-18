from decimal import Decimal, ROUND_HALF_UP
from pprint import pprint
import pandas
import math


def calculate_system_wide_count(aggregation, ocel, by_object_id, labels, object_types):
    input_count = 0
    output_count = 0

    for activity, variant in aggregation.items():
        for variant in aggregation[activity]:
            for event_id in variant["event instances"]:
                input_count += len(labels[event_id]["initial input"])
                output_count += len(labels[event_id]["final output"])

    return {"input": input_count, "output": output_count}


def calculate_system_wide_mass(aggregation, ocel, by_object_id, labels, object_types):
    input_mass = 0
    output_mass = 0

    for activity, variants in aggregation.items():
        for variant in variants:
            for event_id in variant["event instances"]:

                for i in labels[event_id]["initial input"]:
                    if i[0] in object_types:
                        input_mass += Decimal(
                            property_at(
                                ocel,
                                i[1],
                                "mass",
                                timestamp(labels[event_id]["timestamp"]),
                            )
                        )

                for i in labels[event_id]["final output"]:
                    if i[0] in object_types:
                        output_mass += Decimal(
                            property_at(
                                ocel,
                                i[1],
                                "mass",
                                timestamp(labels[event_id]["timestamp"]),
                            )
                        )

    return {"input": input_mass, "output": output_mass}


def calculate_explicit_waste(
    aggregation, ocel, by_object_id, labels, activity, attribute
):
    print(ocel.events)
    for variant in aggregation[activity]:
        waste = []

        # Calculate for each event
        for event_id in variant["event instances"]:
            waste.append(
                Decimal(
                    ocel.events[ocel.events["ocel:eid"] == event_id].iloc[0][attribute]
                )
            )

        total = sum(waste)
        avg = total / len(waste)
        avg = round_like(avg, total)
        variant["explicit waste"] = (
            f"Explicit: avg  {format(avg)} / total {format(total)}"
        )


def calculate_implicit_waste_count(aggregation, ocel, by_object_id, labels, activity):
    for variant in aggregation[activity]:
        input_count = 0
        output_count = 0

        # Calculate for each event
        for event_id in variant["event instances"]:
            label = labels[event_id]
            input_count += len(label["input"] + label["initial input"])
            output_count += len(label["output"] + label["final output"])

        variant["implicit waste"] = (
            f"Implicit count: total {input_count - output_count}"
        )


def calculate_implicit_waste_mass(aggregation, ocel, by_object_id, labels, activity):
    for variant in aggregation[activity]:
        differences = []

        for event_id in variant["event instances"]:
            input_mass = Decimal("0")
            output_mass = Decimal("0")

            label = labels[event_id]

            for i in label["input"] + label["initial input"]:
                input_mass += Decimal(
                    property_at(ocel, i[1], "mass", timestamp(label["timestamp"]))
                )

            for i in label["output"] + label["final output"]:
                output_mass += Decimal(
                    property_at(ocel, i[1], "mass", timestamp(label["timestamp"]))
                )

            differences.append(input_mass - output_mass)

        total = sum(differences)
        avg = total / len(differences)
        variant["implicit waste"] = (
            f"Implicit mass: avg {format(avg)} / total {format(total)}"
        )


def calculate_implicit_waste_mass_for_hinge(
    aggregation, ocel, by_object_id, labels, activity
):
    for variant in aggregation[activity]:
        differences = []
        for event_id in variant["event instances"]:
            input_mass = Decimal("0")
            output_mass = Decimal("0")

            label = labels[event_id]

            for i in label["initial input"]:
                mass = property_at(ocel, i[1], "mass", timestamp(label["timestamp"]))
                print(f"Input {i[1]} with {mass}")
                input_mass += Decimal(mass)

            # We need stupid tricks here to get the correct values
            # because the hinge production log has events where the
            # object change occurs after the event, but not only that,
            # but it also occurs after the next event. Thus, we need
            # to calculate the precise time of the change using the
            # duration, and cannot just take the next or previous value.

            for i in label["input"]:

                prev_event = ocel.events[
                    (ocel.events["ocel:activity"] == activity)
                    & (ocel.events["ocel:timestamp"] < timestamp(label["timestamp"]))
                ].iloc[-1]

                print(f"Prev event of {event_id} is", prev_event["ocel:eid"])

                timestamp2 = prev_event["ocel:timestamp"] + pandas.Timedelta(
                    seconds=float(prev_event["duration"])
                )
                mass = property_before_and_current(
                    ocel, i[1], "mass", timestamp(timestamp2)
                )
                print(f"Input {i[1]} with {mass}")
                input_mass += Decimal(mass)

            for i in label["output"] + label["final output"]:
                event = ocel.events[(ocel.events["ocel:eid"] == event_id)].iloc[0]
                if i[0] == "SteelCoil":
                    timestamp2 = event["ocel:timestamp"] + pandas.Timedelta(
                        seconds=float(event["duration"])
                    )

                    mass = property_before_and_current(
                        ocel, i[1], "mass", timestamp(timestamp2)
                    )
                    output_mass += Decimal(mass)
                else:
                    assert i[0] == "SteelSheet" or i[0] == "SplitWaste"
                    mass = property_at(
                        ocel, i[1], "mass", timestamp(label["timestamp"])
                    )
                    output_mass += Decimal(mass)
                print(f"Output: {i[1]} with {mass}")

            differences.append(input_mass - output_mass)

        total = sum(differences)
        avg = total / len(differences)
        variant["implicit waste"] = (
            f"Implicit mass: avg {format(avg)} / total {format(total)}"
        )


def calculate_object_type_count(aggregation, ocel, by_object_id, labels, object_type):
    for activity, variants in aggregation.items():
        for variant in variants:
            if not "object waste" in variant:
                variant["object waste"] = dict()

            initial_input_count = 0
            final_output_count = 0

            for event_id in variant["event instances"]:
                label = labels[event_id]

                for i in label["initial input"]:
                    if i[0] == object_type:
                        initial_input_count += 1

                for i in label["final output"]:
                    if i[0] == object_type:
                        final_output_count += 1

            # Assume it is always either initial input or final output

            if initial_input_count > 0 and final_output_count > 0:
                raise Exception("It is either one of them")

            if initial_input_count > 0:
                variant["object waste"][
                    object_type
                ] = f"Count: total {initial_input_count}"

            if final_output_count > 0:
                variant["object waste"][
                    object_type
                ] = f"Count: total {final_output_count}"


def calculate_object_type_mass(aggregation, ocel, by_object_id, labels, object_type):
    for activity, variants in aggregation.items():
        for variant in variants:
            if not "object waste" in variant:
                variant["object waste"] = dict()

            initial_input = []
            final_output = []

            for event_id in variant["event instances"]:
                label = labels[event_id]

                for i in label["initial input"]:
                    if i[0] == object_type:
                        initial_input.append(
                            Decimal(
                                property_at(
                                    ocel,
                                    i[1],
                                    "mass",
                                    timestamp(label["timestamp"]),
                                )
                            )
                        )

                for i in label["final output"]:
                    if i[0] == object_type:
                        final_output.append(
                            Decimal(
                                property_at(
                                    ocel,
                                    i[1],
                                    "mass",
                                    timestamp(label["timestamp"]),
                                )
                            )
                        )

            # Assume it is always either initial input or final output

            if len(initial_input) > 0 and len(final_output) > 0:
                raise Exception("It is either one of them")

            if len(initial_input) > 0:
                total = sum(initial_input)
                avg = total / len(initial_input)
                avg = round_like(avg, total)
                variant["object waste"][
                    object_type
                ] = f"Mass: avg {format(avg)} / total {format(total)}"

            if len(final_output) > 0:
                total = sum(final_output)
                avg = total / len(final_output)
                avg = round_like(avg, total)
                variant["object waste"][
                    object_type
                ] = f"Mass: avg {format(avg)} / total {format(total)}"


def property_at(ocel, object_id, attribute, timestamp):
    return ocel.objects[ocel.objects["ocel:oid"] == object_id].iloc[0][attribute]


def property_next(ocel, object_id, attribute, timestamp):
    changes = ocel.object_changes[ocel.object_changes["ocel:timestamp"] > timestamp]
    changes = ocel.object_changes[
        (ocel.object_changes["ocel:oid"] == object_id)
        & (ocel.object_changes["ocel:field"] == attribute)
        & (ocel.object_changes["ocel:timestamp"] > timestamp)
    ]

    if changes.shape[0] == 0:
        # There is no next timestamp
        # Pick the last timestamp or the default
        changes_all = ocel.object_changes[
            (ocel.object_changes["ocel:oid"] == object_id)
            & (ocel.object_changes["ocel:field"] == attribute)
        ]

        if changes_all.shape[0] == 0:
            # Pick the default
            return ocel.objects[ocel.objects["ocel:oid"] == object_id].iloc[0][
                attribute
            ]
        else:
            # Pick the last valid value
            return changes_all.iloc[-1][attribute]
    else:
        return changes.iloc[0][attribute]


def property_before(ocel, object_id, attribute, timestamp):
    changes = ocel.object_changes[
        (ocel.object_changes["ocel:oid"] == object_id)
        & (ocel.object_changes["ocel:field"] == attribute)
        & (ocel.object_changes["ocel:timestamp"] < timestamp)
    ]

    if changes.shape[0] == 0:
        # Use the default value set in the objects dataframe
        return ocel.objects[ocel.objects["ocel:oid"] == object_id].iloc[0][attribute]
    else:
        return changes.iloc[-1][attribute]


def property_before_and_current(ocel, object_id, attribute, timestamp):
    changes = ocel.object_changes[
        (ocel.object_changes["ocel:oid"] == object_id)
        & (ocel.object_changes["ocel:field"] == attribute)
        & (ocel.object_changes["ocel:timestamp"] <= timestamp)
    ]

    if changes.shape[0] == 0:
        # Use the default value set in the objects dataframe
        return ocel.objects[ocel.objects["ocel:oid"] == object_id].iloc[0][attribute]
    else:
        return changes.iloc[-1][attribute]


def timestamp(seconds):
    return pandas.to_datetime(seconds, unit="s", utc=True)


def format(decimal):
    return (
        '<FONT FACE="monospace" POINT-SIZE="13.0">'
        + str(
            decimal.quantize(Decimal(1))
            if decimal == decimal.to_integral()
            else decimal.normalize()
        )
        + "</FONT> "
    )


def round_like(a, b):
    return a.quantize(
        Decimal("1." + "0" * abs(b.as_tuple().exponent)), rounding=ROUND_HALF_UP
    )
