from copy import deepcopy
import pm4py
import pandas as pd
from pm4py.objects.ocel.obj import OCEL
from pprint import pprint


def new_ocel(objects_map):
    time = pd.Timestamp(0)
    i = 0

    events_eid = []
    events_activity = []
    events_timestamp = []

    objects_oid = []
    objects_type = []

    relations_eid = []
    relations_activity = []
    relations_timestamp = []
    relations_oid = []
    relations_type = []
    relations_qualifier = []

    def new_event(event_id, event_activity, objects):
        nonlocal i
        i += 1

        events_eid.append(event_id)
        events_activity.append(event_activity)
        events_timestamp.append(time + pd.Timedelta(seconds=i))

        for object_name in objects:
            if not object_name in objects_oid:
                objects_oid.append(object_name)
                objects_type.append(objects_map[object_name])

            relations_eid.append(event_id)
            relations_activity.append(event_activity)
            relations_timestamp.append(time + pd.Timedelta(minutes=i))
            relations_oid.append(object_name)
            relations_type.append(objects_map[object_name])
            relations_qualifier.append("placeholder")

    def build_ocel():
        print(events_eid)
        print(events_activity)
        print(events_timestamp)
        events = pd.DataFrame(
            {
                "ocel:eid": events_eid,
                "ocel:activity": events_activity,  # Unique object ID
                "ocel:timestamp": events_timestamp,  # Unique object ID
            }
        )

        objects = pd.DataFrame(
            {
                "ocel:oid": objects_oid,  # Unique object ID
                "ocel:type": objects_type,  # e.g., 'Order'
            }
        )

        relations = pd.DataFrame(
            {
                "ocel:eid": relations_eid,
                "ocel:activity": relations_activity,  # Unique object ID
                "ocel:timestamp": relations_timestamp,  # Unique object ID
                "ocel:oid": relations_oid,  # Unique object ID
                "ocel:type": relations_type,  # e.g., 'Order'
                "ocel:qualifier": relations_qualifier,  # e.g., 'Order'
            }
        )

        o2o = pd.DataFrame(
            {
                "ocel:oid": [],  # Unique object ID
                "ocel:oid_2": [],  # Unique object ID
                "ocel:qualifier": [],  # e.g., 'Order'
            }
        )

        return OCEL(events=events, objects=objects, relations=relations, o2o=o2o)

    def render(ocel):
        model = pm4py.discover_oc_petri_net(ocel)
        pm4py.view_ocpn(model, format="svg")

    return [new_event, build_ocel, render]


# OCELS


def simple_parallel():
    current = pd.Timestamp(0)
    timestamps = []
    for i in range(0, 8):
        timestamps.append(current + pd.Timedelta(minutes=i))
    print(timestamps)

    events = pd.DataFrame(
        {
            "ocel:eid": ["A1", "B1", "C1", "D1", "A2", "C2", "B2", "D2"],
            "ocel:activity": [
                "A",
                "B",
                "C",
                "D",
                "A",
                "C",
                "B",
                "D",
            ],  # Unique object ID
            "ocel:timestamp": timestamps,  # Unique object ID
        }
    )
    print(events["ocel:timestamp"])

    objects = pd.DataFrame(
        {
            "ocel:oid": ["o1", "o2"],  # Unique object ID
            "ocel:type": ["o", "o"],  # e.g., 'Order'
        }
    )

    relations = pd.DataFrame(
        {
            "ocel:eid": ["A1", "B1", "C1", "D1", "A2", "C2", "B2", "D2"],
            "ocel:activity": [
                "A",
                "B",
                "C",
                "D",
                "A",
                "C",
                "B",
                "D",
            ],  # Unique object ID
            "ocel:timestamp": timestamps,  # Unique object ID
            "ocel:oid": ["o1", "o1", "o1", "o1", "o2", "o2", "o2", "o2"],
            "ocel:type": ["o", "o", "o", "o", "o", "o", "o", "o"],  # e.g., 'Order'
            "ocel:qualifier": ["a", "a", "a", "a", "a", "a", "a", "a"],  # e.g., 'Order'
        }
    )

    ocel = OCEL(events=events, objects=objects, relations=relations)
    print(ocel.get_summary())

    pm4py.write_ocel2_xml(ocel, "simple_parallel.xml")

    model = pm4py.discover_oc_petri_net(ocel)
    pm4py.view_ocpn(model, format="svg")


def simple_condition():
    current = pd.Timestamp(0)
    timestamps = []
    for i in range(0, 6):
        timestamps.append(current + pd.Timedelta(minutes=i))
    print(timestamps)

    events = pd.DataFrame(
        {
            "ocel:eid": ["A1", "B1", "D1", "A2", "C2", "D2"],
            "ocel:activity": ["A", "B", "D", "A", "C", "D"],  # Unique object ID
            "ocel:timestamp": timestamps,  # Unique object ID
        }
    )

    objects = pd.DataFrame(
        {
            "ocel:oid": ["o1", "o2"],  # Unique object ID
            "ocel:type": ["o", "o"],  # e.g., 'Order'
        }
    )

    relations = pd.DataFrame(
        {
            "ocel:eid": ["A1", "B1", "D1", "A2", "C2", "D2"],
            "ocel:activity": ["A", "B", "D", "A", "C", "D"],
            "ocel:timestamp": timestamps,
            "ocel:oid": ["o1", "o1", "o1", "o2", "o2", "o2"],
            "ocel:type": ["o", "o", "o", "o", "o", "o"],
            "ocel:qualifier": ["a", "a", "a", "a", "a", "a"],
        }
    )

    ocel = OCEL(events=events, objects=objects, relations=relations)
    print(ocel.get_summary())

    pm4py.write_ocel2_xml(ocel, "simple_condition.xml")

    model = pm4py.discover_oc_petri_net(ocel)
    pm4py.view_ocpn(model, format="svg")


def simple_split_but_no_join():
    current = pd.Timestamp(0)
    timestamps = []
    for i in range(0, 3):
        timestamps.append(current + pd.Timedelta(minutes=i))
    print(timestamps)

    events = pd.DataFrame(
        {
            "ocel:eid": ["A1", "B1", "C1"],
            "ocel:activity": ["A", "B", "C"],  # Unique object ID
            "ocel:timestamp": timestamps,  # Unique object ID
        }
    )

    objects = pd.DataFrame(
        {
            "ocel:oid": ["o1", "o2"],  # Unique object ID
            "ocel:type": ["o", "o"],  # e.g., 'Order'
        }
    )

    timestamps.append(current + pd.Timedelta(minutes=i + 1))
    relations = pd.DataFrame(
        {
            "ocel:eid": ["A1", "A1", "B1", "C1"],
            "ocel:activity": ["A", "A", "B", "C"],
            "ocel:timestamp": timestamps,
            "ocel:oid": ["o1", "o2", "o1", "o2"],
            "ocel:type": ["o", "o", "o", "o"],
            "ocel:qualifier": ["a", "a", "a", "a"],
        }
    )

    ocel = OCEL(events=events, objects=objects, relations=relations)
    print(ocel.get_summary())

    pm4py.write_ocel2_xml(ocel, "simple_split_but_no_join.xml")

    model = pm4py.discover_oc_petri_net(ocel)
    pm4py.view_ocpn(model, format="svg")


def simple_length_2_loop():
    current = pd.Timestamp(0)
    timestamps = []
    for i in range(0, 5):
        timestamps.append(current + pd.Timedelta(minutes=i))
    print(timestamps)

    events = pd.DataFrame(
        {
            "ocel:eid": ["A1", "B1", "C1", "B2", "D1"],
            "ocel:activity": ["A", "B", "C", "B", "D"],
            "ocel:timestamp": timestamps,
        }
    )

    objects = pd.DataFrame(
        {
            "ocel:oid": ["o1", "o2"],
            "ocel:type": ["o", "o"],
        }
    )

    relations = pd.DataFrame(
        {
            "ocel:eid": ["A1", "B1", "C1", "B2", "D1"],
            "ocel:activity": ["A", "B", "C", "B", "D"],
            "ocel:timestamp": timestamps,
            "ocel:oid": ["o1", "o1", "o1", "o1", "o1"],
            "ocel:type": ["o", "o", "o", "o", "o"],
            "ocel:qualifier": ["a", "a", "a", "a", "a"],
        }
    )

    ocel = OCEL(events=events, objects=objects, relations=relations)
    print(ocel.get_summary())

    pm4py.write_ocel2_xml(ocel, "simple_length_2_loop.xml")

    model = pm4py.discover_oc_petri_net(ocel)
    pm4py.view_ocpn(model, format="svg")


def simple_length_3_loop():
    current = pd.Timestamp(0)
    timestamps = []
    for i in range(0, 8):
        timestamps.append(current + pd.Timedelta(minutes=i))
    print(timestamps)

    events = pd.DataFrame(
        {
            "ocel:eid": ["A1", "B1", "C1", "D1", "B2", "C2", "D2", "E1"],
            "ocel:activity": ["A", "B", "C", "D", "B", "C", "D", "E"],
            "ocel:timestamp": timestamps,
        }
    )

    objects = pd.DataFrame(
        {
            "ocel:oid": ["o1", "o2"],
            "ocel:type": ["o", "o"],
        }
    )

    relations = pd.DataFrame(
        {
            "ocel:eid": ["A1", "B1", "C1", "D1", "B2", "C2", "D2", "E1"],
            "ocel:activity": ["A", "B", "C", "D", "B", "C", "D", "E"],
            "ocel:timestamp": timestamps,
            "ocel:oid": ["o1", "o1", "o1", "o1", "o1", "o1", "o1", "o1"],
            "ocel:type": ["o", "o", "o", "o", "o", "o", "o", "o"],
            "ocel:qualifier": ["a", "a", "a", "a", "a", "a", "a", "a"],
        }
    )

    ocel = OCEL(events=events, objects=objects, relations=relations)
    print(ocel.get_summary())

    pm4py.write_ocel2_xml(ocel, "simple_length_3_loop.xml")

    model = pm4py.discover_oc_petri_net(ocel)
    pm4py.view_ocpn(model, format="svg")


def simple_length_3_other_loop():
    current = pd.Timestamp(0)
    timestamps = []
    for i in range(0, 9):
        timestamps.append(current + pd.Timedelta(minutes=i))
    print(timestamps)

    events = pd.DataFrame(
        {
            "ocel:eid": ["A1", "B1", "C1", "D1", "B2", "C2", "D2", "B3", "E1"],
            "ocel:activity": ["A", "B", "C", "D", "B", "C", "D", "B", "E"],
            "ocel:timestamp": timestamps,
        }
    )

    objects = pd.DataFrame(
        {
            "ocel:oid": ["o1", "o2"],
            "ocel:type": ["o", "o"],
        }
    )

    relations = pd.DataFrame(
        {
            "ocel:eid": ["A1", "B1", "C1", "D1", "B2", "C2", "D2", "B3", "E1"],
            "ocel:activity": ["A", "B", "C", "D", "B", "C", "D", "B", "E"],
            "ocel:timestamp": timestamps,
            "ocel:oid": ["o1", "o1", "o1", "o1", "o1", "o1", "o1", "o1", "o1"],
            "ocel:type": ["o", "o", "o", "o", "o", "o", "o", "o", "o"],
            "ocel:qualifier": ["a", "a", "a", "a", "a", "a", "a", "a", "a"],
        }
    )

    ocel = OCEL(events=events, objects=objects, relations=relations)
    print(ocel.get_summary())

    pm4py.write_ocel2_xml(ocel, "simple_length_3_other_loop.xml")

    model = pm4py.discover_oc_petri_net(ocel)
    pm4py.view_ocpn(model, format="svg")


def simple_nonlocal_dependencies():
    current = pd.Timestamp(0)
    timestamps = []
    for i in range(0, 6):
        timestamps.append(current + pd.Timedelta(minutes=i))
    print(timestamps)

    events = pd.DataFrame(
        {
            "ocel:eid": ["A1", "C1", "D1", "B2", "C2", "E2"],
            "ocel:activity": ["A", "C", "D", "B", "C", "E"],
            "ocel:timestamp": timestamps,
        }
    )

    objects = pd.DataFrame(
        {
            "ocel:oid": ["o1", "o2"],
            "ocel:type": ["o", "o"],
        }
    )

    relations = pd.DataFrame(
        {
            "ocel:eid": ["A1", "C1", "D1", "B2", "C2", "E2"],
            "ocel:activity": ["A", "C", "D", "B", "C", "E"],
            "ocel:timestamp": timestamps,
            "ocel:oid": ["o1", "o1", "o1", "o2", "o2", "o2"],
            "ocel:type": ["o", "o", "o", "o", "o", "o"],
            "ocel:qualifier": ["a", "a", "a", "a", "a", "a"],
        }
    )

    ocel = OCEL(events=events, objects=objects, relations=relations)
    print(ocel.get_summary())

    pm4py.write_ocel2_xml(ocel, "simple_nonlocal_dependencies.xml")

    model = pm4py.discover_oc_petri_net(ocel)
    pm4py.view_ocpn(model, format="svg")


def simple_non_free_choice():
    current = pd.Timestamp(0)
    timestamps = []
    for i in range(0, 11):
        timestamps.append(current + pd.Timedelta(minutes=i))
    print(timestamps)

    events = pd.DataFrame(
        {
            "ocel:eid": [
                "A1",
                "B1",
                "C1",
                "D1",
                "A2",
                "C2",
                "B2",
                "D2",
                "A3",
                "E3",
                "D3",
            ],
            "ocel:activity": ["A", "B", "C", "D", "A", "C", "B", "D", "A", "E", "D"],
            "ocel:timestamp": timestamps,
        }
    )

    objects = pd.DataFrame(
        {
            "ocel:oid": ["o1", "o2", "o3"],
            "ocel:type": ["o", "o", "o"],
        }
    )

    relations = pd.DataFrame(
        {
            "ocel:eid": [
                "A1",
                "B1",
                "C1",
                "D1",
                "A2",
                "C2",
                "B2",
                "D2",
                "A3",
                "E3",
                "D3",
            ],
            "ocel:activity": ["A", "B", "C", "D", "A", "C", "B", "D", "A", "E", "D"],
            "ocel:timestamp": timestamps,
            "ocel:oid": [
                "o1",
                "o1",
                "o1",
                "o1",
                "o2",
                "o2",
                "o2",
                "o2",
                "o3",
                "o3",
                "o3",
            ],
            "ocel:type": [
                "o",
                "o",
                "o",
                "o",
                "o",
                "o",
                "o",
                "o",
                "o",
                "o",
                "o",
            ],
            "ocel:qualifier": ["a", "a", "a", "a", "a", "a", "a", "a", "a", "a", "a"],
        }
    )

    ocel = OCEL(events=events, objects=objects, relations=relations)
    print(ocel.get_summary())

    pm4py.write_ocel2_xml(ocel, "simple_non_free_choice.xml")

    model = pm4py.discover_oc_petri_net(ocel)
    pm4py.view_ocpn(model, format="svg")


def complex_demonstration():
    current = pd.Timestamp(0)
    i = -1

    def next_timestamp():
        nonlocal i
        i += 1
        return current + pd.Timedelta(minutes=i)

    events = {
        "collect1": ["Collect Goods", next_timestamp()],
        "order1": ["Order Empty Containers", next_timestamp()],
        "pick1": ["Pick Up Empty Container", next_timestamp()],
        "load1": ["Load Truck", next_timestamp()],
        "collect2": ["Collect Goods", next_timestamp()],
        "load2": ["Load Truck", next_timestamp()],
        "drive1": ["Drive to Terminal", next_timestamp()],
        "collect3": ["Collect Goods", next_timestamp()],
        "load3": ["Load Truck", next_timestamp()],
        "drive2": ["Drive to Terminal", next_timestamp()],
        "ship1": ["Ship", next_timestamp()],
    }

    objects = {
        "hu1": "Handling Unit",
        "hu2": "Handling Unit",
        "hu3": "Handling Unit",
        "container1": "Container",
        "container2": "Container",
    }

    events_df = pd.DataFrame(
        {
            "ocel:eid": [key for key in events.keys()],
            "ocel:activity": [events[key][0] for key in events.keys()],
            "ocel:timestamp": [events[key][1] for key in events.keys()],
        }
    )

    objects_df = pd.DataFrame(
        {
            "ocel:oid": [key for key in objects.keys()],
            "ocel:type": [objects[key] for key in objects.keys()],
        }
    )

    relations_eid = [
        "collect1",
        "order1",
        "order1",
        "pick1",
        "load1",
        "load1",
        "collect2",
        "load2",
        "load2",
        "drive1",
        "collect3",
        "load3",
        "load3",
        "drive2",
        "ship1",
        "ship1",
    ]
    relations_oid = [
        "hu1",
        "container1",
        "container2",
        "container1",
        "hu1",
        "container1",
        "hu2",
        "hu2",
        "container1",
        "container1",
        "hu3",
        "hu3",
        "container2",
        "container2",
        "container1",
        "container2",
    ]
    relations_df = pd.DataFrame(
        {
            "ocel:eid": relations_eid,
            "ocel:activity": [events[key][0] for key in relations_eid],
            "ocel:timestamp": [events[key][1] for key in relations_eid],
            "ocel:oid": relations_oid,
            "ocel:type": [objects[key] for key in relations_oid],
            "ocel:qualifier": ["a" for _ in relations_eid],
        }
    )

    ocel = OCEL(events=events_df, objects=objects_df, relations=relations_df)
    print(ocel.get_summary())

    pm4py.write_ocel2_xml(ocel, "complex_demonstration.xml")

    model = pm4py.discover_oc_petri_net(ocel)
    pm4py.view_ocpn(model, format="svg")


def complex_demonstration_with_error():
    current = pd.Timestamp(0)
    i = -1

    def next_timestamp():
        nonlocal i
        i += 1
        return current + pd.Timedelta(minutes=i)

    events = {
        "collect1": ["Collect Goods", next_timestamp()],
        "order1": ["Order Empty Containers", next_timestamp()],
        "pick1": ["Pick Up Empty Container", next_timestamp()],
        "load1": ["Load Truck", next_timestamp()],
        "collect2": ["Collect Goods", next_timestamp()],
        "load2": ["Load Truck", next_timestamp()],
        "drive1": ["Drive to Terminal", next_timestamp()],
        "collect3": ["Collect Goods", next_timestamp()],
        "collect4": ["Collect Goods", next_timestamp()],
        "load3": ["Load Truck", next_timestamp()],
        "drive2": ["Drive to Terminal", next_timestamp()],
        "ship1": ["Ship", next_timestamp()],
    }

    objects = {
        "hu1": "Handling Unit",
        "hu2": "Handling Unit",
        "hu3": "Handling Unit",
        "hu4": "Handling Unit",
        "container1": "Container",
        "container2": "Container",
    }

    events_df = pd.DataFrame(
        {
            "ocel:eid": [key for key in events.keys()],
            "ocel:activity": [events[key][0] for key in events.keys()],
            "ocel:timestamp": [events[key][1] for key in events.keys()],
        }
    )

    objects_df = pd.DataFrame(
        {
            "ocel:oid": [key for key in objects.keys()],
            "ocel:type": [objects[key] for key in objects.keys()],
        }
    )

    relations_eid = [
        "collect1",
        "order1",
        "order1",
        "pick1",
        "load1",
        "load1",
        "collect2",
        "load2",
        "load2",
        "drive1",
        "collect3",
        "collect4",
        "load3",
        "load3",
        "drive2",
        "ship1",
        "ship1",
    ]
    relations_oid = [
        "hu1",
        "container1",
        "container2",
        "container1",
        "hu1",
        "container1",
        "hu2",
        "hu2",
        "container1",
        "container1",
        "hu3",
        "hu4",
        "hu3",
        "container2",
        "container2",
        "container1",
        "container2",
    ]
    relations_df = pd.DataFrame(
        {
            "ocel:eid": relations_eid,
            "ocel:activity": [events[key][0] for key in relations_eid],
            "ocel:timestamp": [events[key][1] for key in relations_eid],
            "ocel:oid": relations_oid,
            "ocel:type": [objects[key] for key in relations_oid],
            "ocel:qualifier": ["a" for _ in relations_eid],
        }
    )

    ocel = OCEL(events=events_df, objects=objects_df, relations=relations_df)
    print(ocel.get_summary())

    pm4py.write_ocel2_xml(ocel, "complex_demonstration_with_error.xml")

    model = pm4py.discover_oc_petri_net(ocel)
    pm4py.view_ocpn(model, format="svg")


def discussion_example_different_transitions():
    current = pd.Timestamp(0)
    i = -1

    def next_timestamp():
        nonlocal i
        i += 1
        return current + pd.Timedelta(minutes=i)

    events = {
        "generate1": ["Generate A", next_timestamp()],
        "use1": ["Use A", next_timestamp()],
        "use2": ["Use A", next_timestamp()],
    }

    objects = {
        "a1": "A",
        "a2": "A",
    }

    events_df = pd.DataFrame(
        {
            "ocel:eid": [key for key in events.keys()],
            "ocel:activity": [events[key][0] for key in events.keys()],
            "ocel:timestamp": [events[key][1] for key in events.keys()],
        }
    )

    objects_df = pd.DataFrame(
        {
            "ocel:oid": [key for key in objects.keys()],
            "ocel:type": [objects[key] for key in objects.keys()],
        }
    )

    relations_eid = [
        "generate1",
        "use1",
        "use2",
    ]
    relations_oid = ["a1", "a1", "a2"]
    relations_df = pd.DataFrame(
        {
            "ocel:eid": relations_eid,
            "ocel:activity": [events[key][0] for key in relations_eid],
            "ocel:timestamp": [events[key][1] for key in relations_eid],
            "ocel:oid": relations_oid,
            "ocel:type": [objects[key] for key in relations_oid],
            "ocel:qualifier": ["a" for _ in relations_eid],
        }
    )

    ocel = OCEL(events=events_df, objects=objects_df, relations=relations_df)
    print(ocel.get_summary())

    pm4py.write_ocel2_xml(ocel, "discussion_example_different_transitions.xml")

    model = pm4py.discover_oc_petri_net(ocel)
    pm4py.view_ocpn(model, format="svg")


def discussion_example_same_hierarchy():
    current = pd.Timestamp(0)
    i = -1

    def next_timestamp():
        nonlocal i
        i += 1
        return current + pd.Timedelta(minutes=i)

    events = {
        "generate1": ["Generate A", next_timestamp()],
        "use1_1": ["Use A", next_timestamp()],
        "use1_2": ["Use A", next_timestamp()],
        "consume1": ["Consume A", next_timestamp()],
    }

    objects = {
        "a1": "A",
    }

    events_df = pd.DataFrame(
        {
            "ocel:eid": [key for key in events.keys()],
            "ocel:activity": [events[key][0] for key in events.keys()],
            "ocel:timestamp": [events[key][1] for key in events.keys()],
        }
    )

    objects_df = pd.DataFrame(
        {
            "ocel:oid": [key for key in objects.keys()],
            "ocel:type": [objects[key] for key in objects.keys()],
        }
    )

    relations_eid = [
        "generate1",
        "use1_1",
        "use1_2",
        "consume1",
    ]
    relations_oid = [
        "a1",
        "a1",
        "a1",
        "a1",
    ]
    relations_df = pd.DataFrame(
        {
            "ocel:eid": relations_eid,
            "ocel:activity": [events[key][0] for key in relations_eid],
            "ocel:timestamp": [events[key][1] for key in relations_eid],
            "ocel:oid": relations_oid,
            "ocel:type": [objects[key] for key in relations_oid],
            "ocel:qualifier": ["a" for _ in relations_eid],
        }
    )

    ocel = OCEL(events=events_df, objects=objects_df, relations=relations_df)
    print(ocel.get_summary())

    pm4py.write_ocel2_xml(ocel, "discussion_example_same_hierarchy.xml")

    model = pm4py.discover_oc_petri_net(ocel)
    pm4py.view_ocpn(model, format="svg")


def motivation_example():
    current = pd.Timestamp(0)
    i = -1

    def next_timestamp():
        nonlocal i
        i += 1
        return current + pd.Timedelta(minutes=i)

    events = {
        # Case 1
        "s1_1": ["Inject", next_timestamp()],
        "s1_2": ["Degas", next_timestamp()],
        "s1_3_1": ["Trim", next_timestamp()],
        "s1_4": ["Pack", next_timestamp()],
        # Case 2
        "s2_1": ["Inject", next_timestamp()],
        # Skip "s2_2"
        "s2_3_1": ["Trim", next_timestamp()],
        "s2_3_2": ["Trim", next_timestamp()],
        "s2_3_3": ["Trim", next_timestamp()],
        "s2_4": ["Pack", next_timestamp()],
    }

    objects = {
        # Case 1
        "a1": "Fiber",
        "b1": "Resin",
        "c1": "Mold",
        "d1_1": "Waste",
        "e1": "Product",
        # Case 2
        "a2": "Fiber",
        "b2": "Resin",
        "c2": "Mold",
        "d2_1": "Waste",
        "d2_2": "Waste",
        "d2_3": "Waste",
        "e2": "Product",
    }

    objects_mass = {
        # Case 1
        "a1": 11,
        "b1": 12,
        "c1": 22,
        "d1_1": 2,
        "e1": 10 + 12 - 2,
        # Case 2
        "a2": 13,
        "b2": 14,
        "c2": 25,
        "d2_1": 3,
        "d2_2": 5,
        "d2_3": 2,
        "e2": (10 + 12 - 2) + (10 + 15 - 3 - 5 - 2),
    }

    events_df = pd.DataFrame(
        {
            "ocel:eid": [key for key in events.keys()],
            "ocel:activity": [events[key][0] for key in events.keys()],
            "ocel:timestamp": [events[key][1] for key in events.keys()],
            # Add explicit waste mass
            "mass": [
                3 if key == "s1_1" else (5 if key == "s2_1" else 0)
                for key in events.keys()
            ],
        }
    )

    objects_df = pd.DataFrame(
        {
            "ocel:oid": [key for key in objects.keys()],
            "ocel:type": [objects[key] for key in objects.keys()],
            "mass": [objects_mass[key] for key in objects.keys()],
        }
    )

    relations_eid = [
        # Case 1
        "s1_1",
        "s1_1",
        "s1_1",
        "s1_2",
        "s1_3_1",
        "s1_3_1",
        "s1_4",
        "s1_4",
        # Case 2
        "s2_1",
        "s2_1",
        "s2_1",
        # "s2_2",
        "s2_3_1",
        "s2_3_1",
        "s2_3_2",
        "s2_3_2",
        "s2_3_3",
        "s2_3_3",
        "s2_4",
        "s2_4",
        "s2_4",
    ]
    relations_oid = [
        # Case 1
        "a1",  # s1_1
        "b1",  # s1_1
        "c1",  # s1_1
        "c1",  # s1_2
        "c1",  # s1_3_1
        "d1_1",  # s1_3_1
        "c1",  # s1_4
        "e1",  # s1_4
        # Case 2
        "a2",  # s2_1
        "b2",  # s2_1
        "c2",  # s2_1
        # "c2",  # s2_2
        "c2",  # s2_3_1
        "d2_1",  # s2_3_1
        "c2",  # s1_3_2
        "d2_2",  # s1_3_2
        "c2",  # s1_3_3
        "d2_3",  # s1_3_3
        "c2",  # s2_4
        "e1",  # s2_4
        "e2",  # s2_4
    ]
    relations_df = pd.DataFrame(
        {
            "ocel:eid": relations_eid,
            "ocel:activity": [events[key][0] for key in relations_eid],
            "ocel:timestamp": [events[key][1] for key in relations_eid],
            "ocel:oid": relations_oid,
            "ocel:type": [objects[key] for key in relations_oid],
            "ocel:qualifier": ["a" for _ in relations_eid],
        }
    )

    ocel = OCEL(events=events_df, objects=objects_df, relations=relations_df)
    print(ocel.get_summary())

    pm4py.write_ocel2_xml(ocel, "motivation_example.xml")

    model = pm4py.discover_oc_petri_net(ocel)
    pm4py.view_ocpn(model, format="svg")


def variable_arcs_example():
    current = pd.Timestamp(0)
    i = -1

    def next_timestamp():
        nonlocal i
        i += 1
        return current + pd.Timedelta(minutes=i)

    events = {
        # Case 1
        "s1_1": ["Inject", next_timestamp()],
        "s1_2": ["Degas", next_timestamp()],
        "s1_3_1": ["Trim", next_timestamp()],
        "s1_4": ["Pack", next_timestamp()],
        # Case 2
        "s2_1": ["Inject", next_timestamp()],
        # Skip "s2_2"
        "s2_3_1": ["Trim", next_timestamp()],
        "s2_3_2": ["Trim", next_timestamp()],
        "s2_3_3": ["Trim", next_timestamp()],
        "s2_4": ["Pack", next_timestamp()],
    }

    objects = {
        # Case 1
        "a1_1": "Fiber",
        "a1_2": "Fiber",
        "a1_3": "Fiber",
        "a1_4": "Fiber",
        "a1_5": "Fiber",
        "b1_1": "Resin",
        "b1_2": "Resin",
        "b1_3": "Resin",
        "c1": "Mold",
        "d1_1": "Waste",
        "e1": "Product",
        # Case 2
        "a2_1": "Fiber",
        "a2_2": "Fiber",
        "a2_3": "Fiber",
        "a2_4": "Fiber",
        "a2_5": "Fiber",
        "b2_1": "Resin",
        "b2_2": "Resin",
        "b2_3": "Resin",
        "c2": "Mold",
        "d2_1": "Waste",
        "d2_2": "Waste",
        "d2_3": "Waste",
        "e2": "Product",
    }

    objects_mass = {
        # Case 1
        "a1_1": 10,
        "a1_2": 10,
        "a1_3": 10,
        "a1_4": 10,
        "a1_5": 10,
        "b1_1": 12,
        "b1_2": 12,
        "b1_3": 12,
        "c1": 22,
        "d1_1": 2,
        "e1": 31,
        # Case 2
        "a2_1": 10,
        "a2_2": 10,
        "a2_3": 10,
        "a2_4": 10,
        "a2_5": 10,
        "b2_1": 15,
        "b2_2": 15,
        "b2_3": 15,
        "c2": 25,
        "d2_1": 3,
        "d2_2": 5,
        "d2_3": 2,
        "e2": 31,
    }

    events_df = pd.DataFrame(
        {
            "ocel:eid": [key for key in events.keys()],
            "ocel:activity": [events[key][0] for key in events.keys()],
            "ocel:timestamp": [events[key][1] for key in events.keys()],
        }
    )

    objects_df = pd.DataFrame(
        {
            "ocel:oid": [key for key in objects.keys()],
            "ocel:type": [objects[key] for key in objects.keys()],
            "mass": [objects_mass[key] for key in objects.keys()],
        }
    )

    relations_eid = [
        # Case 1
        "s1_1",
        "s1_1",
        "s1_1",
        "s1_1",
        "s1_1",
        "s1_1",
        "s1_1",
        "s1_1",
        "s1_1",
        "s1_2",
        "s1_3_1",
        "s1_3_1",
        "s1_4",
        "s1_4",
        # Case 2
        "s2_1",
        "s2_1",
        "s2_1",
        "s2_1",
        "s2_1",
        "s2_1",
        "s2_1",
        "s2_1",
        "s2_1",
        # "s2_2",
        "s2_3_1",
        "s2_3_1",
        "s2_3_2",
        "s2_3_2",
        "s2_3_3",
        "s2_3_3",
        "s2_4",
        "s2_4",
    ]
    relations_oid = [
        # Case 1
        "a1_1",  # s1_1
        "a1_2",  # s1_1
        "a1_3",  # s1_1
        "a1_4",  # s1_1
        "a1_5",  # s1_1
        "b1_1",  # s1_1
        "b1_2",  # s1_1
        "b1_3",  # s1_1
        "c1",  # s1_1
        "c1",  # s1_2
        "c1",  # s1_3_1
        "d1_1",  # s1_3_1
        "c1",  # s1_4
        "e1",  # s1_4
        # Case 2
        "a2_1",  # s2_1
        "a2_2",  # s2_1
        "a2_3",  # s2_1
        "a2_4",  # s2_1
        "a2_5",  # s2_1
        "b2_1",  # s2_1
        "b2_2",  # s2_1
        "b2_3",  # s2_1
        "c2",  # s2_1
        # "c2",  # s2_2
        "c2",  # s2_3_1
        "d2_1",  # s2_3_1
        "c2",  # s1_3_2
        "d2_2",  # s1_3_2
        "c2",  # s1_3_3
        "d2_3",  # s1_3_3
        "c2",  # s2_4
        "e2",  # s2_4
    ]
    relations_df = pd.DataFrame(
        {
            "ocel:eid": relations_eid,
            "ocel:activity": [events[key][0] for key in relations_eid],
            "ocel:timestamp": [events[key][1] for key in relations_eid],
            "ocel:oid": relations_oid,
            "ocel:type": [objects[key] for key in relations_oid],
            "ocel:qualifier": ["a" for _ in relations_eid],
        }
    )

    ocel = OCEL(events=events_df, objects=objects_df, relations=relations_df)
    print(ocel.get_summary())

    pm4py.write_ocel2_xml(ocel, "variable_arcs_example.xml")

    model = pm4py.discover_oc_petri_net(ocel)
    pm4py.view_ocpn(model, format="svg")


def filtering_edges():
    current = pd.Timestamp(0)
    i = -1

    def next_timestamp():
        nonlocal i
        i += 1
        return current + pd.Timedelta(minutes=i)

    events = {
        # Case 2
        "s2_1": ["Inject", next_timestamp()],
        # Skip "s2_2"
        "s2_3_1": ["Trim", next_timestamp()],
        "s2_3_2": ["Trim", next_timestamp()],
        "s2_3_3": ["Trim", next_timestamp()],
        "s2_4": ["Pack", next_timestamp()],
        # Case 1.0
        "s10_1": ["Inject", next_timestamp()],
        "s10_2": ["Stir", next_timestamp()],
        "s10_3_1": ["Trim", next_timestamp()],
        "s10_3_2": ["Trim", next_timestamp()],
        "s10_4": ["Pack", next_timestamp()],
        # Case 1.1
        "s11_1": ["Inject", next_timestamp()],
        "s11_2": ["Stir", next_timestamp()],
        "s11_3_1": ["Trim", next_timestamp()],
        "s11_4": ["Pack", next_timestamp()],
        # Case 1.2
        "s12_1": ["Inject", next_timestamp()],
        "s12_2": ["Stir", next_timestamp()],
        "s12_3_1": ["Trim", next_timestamp()],
        "s12_4": ["Pack", next_timestamp()],
        # Case 1.3
        "s13_1": ["Inject", next_timestamp()],
        "s13_2": ["Stir", next_timestamp()],
        "s13_3_1": ["Trim", next_timestamp()],
        "s13_4": ["Pack", next_timestamp()],
        # Case 1.4
        "s14_1": ["Inject", next_timestamp()],
        "s14_2": ["Stir", next_timestamp()],
        "s14_3_1": ["Trim", next_timestamp()],
        "s14_4": ["Pack", next_timestamp()],
        # Case 1.5
        "s15_1": ["Inject", next_timestamp()],
        "s15_2": ["Stir", next_timestamp()],
        "s15_3_1": ["Trim", next_timestamp()],
        "s15_4": ["Pack", next_timestamp()],
        # Case 1.6
        "s16_1": ["Inject", next_timestamp()],
        "s16_2": ["Stir", next_timestamp()],
        "s16_3_1": ["Trim", next_timestamp()],
        "s16_4": ["Pack", next_timestamp()],
        # Case 1.7
        "s17_1": ["Inject", next_timestamp()],
        "s17_2": ["Stir", next_timestamp()],
        "s17_3_1": ["Trim", next_timestamp()],
        "s17_4": ["Pack", next_timestamp()],
        # Case 1.8
        "s18_1": ["Inject", next_timestamp()],
        "s18_2": ["Stir", next_timestamp()],
        "s18_3_1": ["Trim", next_timestamp()],
        "s18_4": ["Pack", next_timestamp()],
        # Case 1.9
        "s19_1": ["Inject", next_timestamp()],
        "s19_2": ["Stir", next_timestamp()],
        "s19_3_1": ["Trim", next_timestamp()],
        "s19_4": ["Pack", next_timestamp()],
    }

    objects = {
        # Case 2
        "a2": "Fiber",
        "b2": "Resin",
        "c2": "Substance",
        "d2_1": "Waste",
        "d2_2": "Waste",
        "d2_3": "Waste",
        "e2": "Product",
        # Case 1.0
        "a10": "Fiber",
        "b10": "Resin",
        "c10": "Substance",
        "d10_1": "Waste",
        "d10_2": "Waste",
        "e10": "Product",
        # Case 1.1
        "a11": "Fiber",
        "b11": "Resin",
        "c11": "Substance",
        "d11_1": "Waste",
        "e11": "Product",
        # Case 1.2
        "a12": "Fiber",
        "b12": "Resin",
        "c12": "Substance",
        "d12_1": "Waste",
        "e12": "Product",
        # Case 1.3
        "a13": "Fiber",
        "b13": "Resin",
        "c13": "Substance",
        "d13_1": "Waste",
        "e13": "Product",
        # Case 1.4
        "a14": "Fiber",
        "b14": "Resin",
        "c14": "Substance",
        "d14_1": "Waste",
        "e14": "Product",
        # Case 1.5
        "a15": "Fiber",
        "b15": "Resin",
        "c15": "Substance",
        "d15_1": "Waste",
        "e15": "Product",
        # Case 1.6
        "a16": "Fiber",
        "b16": "Resin",
        "c16": "Substance",
        "d16_1": "Waste",
        "e16": "Product",
        # Case 1.7
        "a17": "Fiber",
        "b17": "Resin",
        "c17": "Substance",
        "d17_1": "Waste",
        "e17": "Product",
        # Case 1.8
        "a18": "Fiber",
        "b18": "Resin",
        "c18": "Substance",
        "d18_1": "Waste",
        "e18": "Product",
        # Case 1.9
        "a19": "Fiber",
        "b19": "Resin",
        "c19": "Substance",
        "d19_1": "Waste",
        "e19": "Product",
    }

    objects_mass = {
        # Case 2
        "a2": 10,
        "b2": 15,
        "c2": 25,
        "d2_1": 3,
        "d2_2": 5,
        "d2_3": 2,
        "e2": 31,
        # Case 1.0
        "a10": 10,
        "b10": 12,
        "c10": 22,
        "d10_1": 2,
        "d10_2": 2,
        "e10": 31,
        # Case 1.1
        "a11": 10,
        "b11": 12,
        "c11": 22,
        "d11_1": 2,
        "e11": 31,
        # Case 1.2
        "a12": 10,
        "b12": 12,
        "c12": 22,
        "d12_1": 2,
        "e12": 31,
        # Case 1.3
        "a13": 10,
        "b13": 12,
        "c13": 22,
        "d13_1": 2,
        "e13": 31,
        # Case 1.4
        "a14": 10,
        "b14": 12,
        "c14": 22,
        "d14_1": 2,
        "e14": 31,
        # Case 1.5
        "a15": 10,
        "b15": 12,
        "c15": 22,
        "d15_1": 2,
        "e15": 31,
        # Case 1.6
        "a16": 10,
        "b16": 12,
        "c16": 22,
        "d16_1": 2,
        "e16": 31,
        # Case 1.7
        "a17": 300,
        "b17": 12,
        "c17": 22,
        "d17_1": 2,
        "e17": 31,
        # Case 1.8
        "a18": 10,
        "b18": 12,
        "c18": 22,
        "d18_1": 2,
        "e18": 31,
        # Case 1.9
        "a19": 10,
        "b19": 12,
        "c19": 22,
        "d19_1": 2,
        "e19": 31,
    }

    events_df = pd.DataFrame(
        {
            "ocel:eid": [key for key in events.keys()],
            "ocel:activity": [events[key][0] for key in events.keys()],
            "ocel:timestamp": [events[key][1] for key in events.keys()],
        }
    )

    objects_df = pd.DataFrame(
        {
            "ocel:oid": [key for key in objects.keys()],
            "ocel:type": [objects[key] for key in objects.keys()],
            "mass": [objects_mass[key] for key in objects.keys()],
        }
    )

    relations_eid = [
        # Case 2
        "s2_1",
        "s2_1",
        "s2_1",
        # "s2_2",
        "s2_3_1",
        "s2_3_1",
        "s2_3_2",
        "s2_3_2",
        "s2_3_3",
        "s2_3_3",
        "s2_4",
        "s2_4",
        # Case 1.0
        "s10_1",
        "s10_1",
        "s10_1",
        "s10_2",
        "s10_3_1",
        "s10_3_1",
        "s10_3_2",
        "s10_3_2",
        "s10_4",
        "s10_4",
        # Case 1.1
        "s11_1",
        "s11_1",
        "s11_1",
        "s11_2",
        "s11_3_1",
        "s11_3_1",
        "s11_4",
        "s11_4",
        # Case 1.2
        "s12_1",
        "s12_1",
        "s12_1",
        "s12_2",
        "s12_3_1",
        "s12_3_1",
        "s12_4",
        "s12_4",
        # Case 1.3
        "s13_1",
        "s13_1",
        "s13_1",
        "s13_2",
        "s13_3_1",
        "s13_3_1",
        "s13_4",
        "s13_4",
        # Case 1.4
        "s14_1",
        "s14_1",
        "s14_1",
        "s14_2",
        "s14_3_1",
        "s14_3_1",
        "s14_4",
        "s14_4",
        # Case 1.5
        "s15_1",
        "s15_1",
        "s15_1",
        "s15_2",
        "s15_3_1",
        "s15_3_1",
        "s15_4",
        "s15_4",
        # Case 1.6
        "s16_1",
        "s16_1",
        "s16_1",
        "s16_2",
        "s16_3_1",
        "s16_3_1",
        "s16_4",
        "s16_4",
        # Case 1.7
        "s17_1",
        "s17_1",
        "s17_1",
        "s17_2",
        "s17_3_1",
        "s17_3_1",
        "s17_4",
        "s17_4",
        # Case 1.8
        "s18_1",
        "s18_1",
        "s18_1",
        "s18_2",
        "s18_3_1",
        "s18_3_1",
        "s18_4",
        "s18_4",
        # Case 1.9
        "s19_1",
        "s19_1",
        "s19_1",
        "s19_2",
        "s19_3_1",
        "s19_3_1",
        "s19_4",
        "s19_4",
    ]
    relations_oid = [
        # Case 2
        "a2",  # s2_1
        "b2",  # s2_1
        "c2",  # s2_1
        # "c2",  # s2_2
        "c2",  # s2_3_1
        "d2_1",  # s2_3_1
        "c2",  # s1_3_2
        "d2_2",  # s1_3_2
        "c2",  # s1_3_3
        "d2_3",  # s1_3_3
        "c2",  # s2_4
        "e2",  # s2_4
        # Case 1.0
        "a10",  # s1_1
        "b10",  # s1_1
        "c10",  # s1_1
        "c10",  # s1_2
        "c10",  # s1_3_1
        "d10_1",  # s1_3_1
        "c10",  # s1_3_1
        "d10_2",  # s1_3_1
        "c10",  # s1_4
        "e10",  # s1_4
        # Case 1.1
        "a11",  # s1_1
        "b11",  # s1_1
        "c11",  # s1_1
        "c11",  # s1_2
        "c11",  # s1_3_1
        "d11_1",  # s1_3_1
        "c11",  # s1_4
        "e11",  # s1_4
        # Case 1.2
        "a12",  # s1_1
        "b12",  # s1_1
        "c12",  # s1_1
        "c12",  # s1_2
        "c12",  # s1_3_1
        "d12_1",  # s1_3_1
        "c12",  # s1_4
        "e12",  # s1_4
        # Case 1.3
        "a13",  # s1_1
        "b13",  # s1_1
        "c13",  # s1_1
        "c13",  # s1_2
        "c13",  # s1_3_1
        "d13_1",  # s1_3_1
        "c13",  # s1_4
        "e13",  # s1_4
        # Case 1.4
        "a14",  # s1_1
        "b14",  # s1_1
        "c14",  # s1_1
        "c14",  # s1_2
        "c14",  # s1_3_1
        "d14_1",  # s1_3_1
        "c14",  # s1_4
        "e14",  # s1_4
        # Case 1.5
        "a15",  # s1_1
        "b15",  # s1_1
        "c15",  # s1_1
        "c15",  # s1_2
        "c15",  # s1_3_1
        "d15_1",  # s1_3_1
        "c15",  # s1_4
        "e15",  # s1_4
        # Case 1.6
        "a16",  # s1_1
        "b16",  # s1_1
        "c16",  # s1_1
        "c16",  # s1_2
        "c16",  # s1_3_1
        "d16_1",  # s1_3_1
        "c16",  # s1_4
        "e16",  # s1_4
        # Case 1.7
        "a17",  # s1_1
        "b17",  # s1_1
        "c17",  # s1_1
        "c17",  # s1_2
        "c17",  # s1_3_1
        "d17_1",  # s1_3_1
        "c17",  # s1_4
        "e17",  # s1_4
        # Case 1.8
        "a18",  # s1_1
        "b18",  # s1_1
        "c18",  # s1_1
        "c18",  # s1_2
        "c18",  # s1_3_1
        "d18_1",  # s1_3_1
        "c18",  # s1_4
        "e18",  # s1_4
        # Case 1.9
        "a19",  # s1_1
        "b19",  # s1_1
        "c19",  # s1_1
        "c19",  # s1_2
        "c19",  # s1_3_1
        "d19_1",  # s1_3_1
        "c19",  # s1_4
        "e19",  # s1_4
    ]
    relations_df = pd.DataFrame(
        {
            "ocel:eid": relations_eid,
            "ocel:activity": [events[key][0] for key in relations_eid],
            "ocel:timestamp": [events[key][1] for key in relations_eid],
            "ocel:oid": relations_oid,
            "ocel:type": [objects[key] for key in relations_oid],
            "ocel:qualifier": ["a" for _ in relations_eid],
        }
    )

    ocel = OCEL(events=events_df, objects=objects_df, relations=relations_df)
    print(ocel.get_summary())

    pm4py.write_ocel2_xml(ocel, "filtering_edges.xml")

    model = pm4py.discover_oc_petri_net(ocel)
    pm4py.view_ocpn(model, format="svg")


def filtering_transitions():
    current = pd.Timestamp(0)
    i = -1

    def next_timestamp():
        nonlocal i
        i += 1
        return current + pd.Timedelta(minutes=i)

    events = {
        # Case 1.0
        "s10_1": ["Inject", next_timestamp()],
        "s10_2": ["Degas", next_timestamp()],
        "s10_3_1": ["Trim", next_timestamp()],
        "s10_3_2": ["Trim", next_timestamp()],
        "s10_4": ["Pack", next_timestamp()],
        # Case 1.1
        "s11_1": ["Inject", next_timestamp()],
        "s11_2": ["Degas", next_timestamp()],
        "s11_3_1": ["Trim", next_timestamp()],
        "s11_4": ["Pack", next_timestamp()],
        # Case 1.2
        "s12_1": ["Inject", next_timestamp()],
        "s12_2": ["Degas", next_timestamp()],
        "s12_3_1": ["Trim", next_timestamp()],
        "s12_4": ["Pack", next_timestamp()],
        # Case 1.3
        "s13_1": ["Inject", next_timestamp()],
        "s13_2": ["Degas", next_timestamp()],
        "s13_3_1": ["Trim", next_timestamp()],
        "s13_4": ["Pack", next_timestamp()],
        # Case 1.4
        "s14_1": ["Inject", next_timestamp()],
        "s14_2": ["Degas", next_timestamp()],
        "s14_3_1": ["Trim", next_timestamp()],
        "s14_4": ["Pack", next_timestamp()],
        # Case 1.5
        "s15_1": ["Inject", next_timestamp()],
        "s15_2": ["Degas", next_timestamp()],
        "s15_3_1": ["Trim", next_timestamp()],
        "s15_4": ["Pack", next_timestamp()],
        # Case 1.6
        "s16_1": ["Inject", next_timestamp()],
        "s16_2": ["Degas", next_timestamp()],
        "s16_3_1": ["Trim", next_timestamp()],
        "s16_4": ["Pack", next_timestamp()],
        # Case 1.7
        "s17_1": ["Inject", next_timestamp()],
        "s17_2": ["Degas", next_timestamp()],
        "s17_3_1": ["Trim", next_timestamp()],
        "s17_4": ["Pack", next_timestamp()],
        # Case 1.8
        "s18_1": ["Inject", next_timestamp()],
        "s18_2": ["Degas", next_timestamp()],
        "s18_3_1": ["Trim", next_timestamp()],
        "s18_4": ["Pack", next_timestamp()],
        # Case 1.9
        "s19_1": ["Inject", next_timestamp()],
        "s19_2": ["Degas", next_timestamp()],
        "s19_3_1": ["Trim", next_timestamp()],
        "s19_4": ["Pack", next_timestamp()],
    }

    objects = {
        # Case 1.0
        "a10_1": "Fiber",
        "a10_2": "Fiber",
        "b10": "Resin",
        "c10": "Mold",
        "d10_1": "Waste",
        "d10_2": "Waste",
        "e10": "Product",
        # Case 1.1
        "a11": "Fiber",
        "b11": "Resin",
        "c11": "Mold",
        "d11_1": "Waste",
        "e11": "Product",
        # Case 1.2
        "a12": "Fiber",
        "b12": "Resin",
        "c12": "Mold",
        "d12_1": "Waste",
        "e12": "Product",
        # Case 1.3
        "a13": "Fiber",
        "b13": "Resin",
        "c13": "Mold",
        "d13_1": "Waste",
        "e13": "Product",
        # Case 1.4
        "a14": "Fiber",
        "b14": "Resin",
        "c14": "Mold",
        "d14_1": "Waste",
        "e14": "Product",
        # Case 1.5
        "a15": "Fiber",
        "b15": "Resin",
        "c15": "Mold",
        "d15_1": "Waste",
        "e15": "Product",
        # Case 1.6
        "a16": "Fiber",
        "b16": "Resin",
        "c16": "Mold",
        "d16_1": "Waste",
        "e16": "Product",
        # Case 1.7
        "a17": "Fiber",
        "b17": "Resin",
        "c17": "Mold",
        "d17_1": "Waste",
        "e17": "Product",
        # Case 1.8
        "a18": "Fiber",
        "b18": "Resin",
        "c18": "Mold",
        "d18_1": "Waste",
        "e18": "Product",
        # Case 1.9
        "a19": "Fiber",
        "b19": "Resin",
        "c19": "Mold",
        "d19_1": "Waste",
        "e19": "Product",
    }

    objects_mass = {
        # Case 1.0
        "a10_1": 10,
        "a10_2": 10,
        "b10": 12,
        "c10": 22,
        "d10_1": 2,
        "d10_2": 2,
        "e10": 31,
        # Case 1.1
        "a11": 10,
        "b11": 12,
        "c11": 22,
        "d11_1": 2,
        "e11": 31,
        # Case 1.2
        "a12": 10,
        "b12": 12,
        "c12": 22,
        "d12_1": 2,
        "e12": 31,
        # Case 1.3
        "a13": 10,
        "b13": 12,
        "c13": 22,
        "d13_1": 2,
        "e13": 31,
        # Case 1.4
        "a14": 10,
        "b14": 12,
        "c14": 22,
        "d14_1": 2,
        "e14": 31,
        # Case 1.5
        "a15": 10,
        "b15": 12,
        "c15": 22,
        "d15_1": 2,
        "e15": 31,
        # Case 1.6
        "a16": 10,
        "b16": 12,
        "c16": 22,
        "d16_1": 2,
        "e16": 31,
        # Case 1.7
        "a17": 300,
        "b17": 12,
        "c17": 22,
        "d17_1": 2,
        "e17": 31,
        # Case 1.8
        "a18": 10,
        "b18": 12,
        "c18": 22,
        "d18_1": 2,
        "e18": 31,
        # Case 1.9
        "a19": 10,
        "b19": 12,
        "c19": 22,
        "d19_1": 2,
        "e19": 31,
    }

    events_df = pd.DataFrame(
        {
            "ocel:eid": [key for key in events.keys()],
            "ocel:activity": [events[key][0] for key in events.keys()],
            "ocel:timestamp": [events[key][1] for key in events.keys()],
        }
    )

    objects_df = pd.DataFrame(
        {
            "ocel:oid": [key for key in objects.keys()],
            "ocel:type": [objects[key] for key in objects.keys()],
            "mass": [objects_mass[key] for key in objects.keys()],
        }
    )

    relations_eid = [
        # Case 1.0
        "s10_1",
        "s10_1",
        "s10_1",
        "s10_1",
        "s10_2",
        "s10_3_1",
        "s10_3_1",
        "s10_3_2",
        "s10_3_2",
        "s10_4",
        "s10_4",
        # Case 1.1
        "s11_1",
        "s11_1",
        "s11_1",
        "s11_2",
        "s11_3_1",
        "s11_3_1",
        "s11_4",
        "s11_4",
        # Case 1.2
        "s12_1",
        "s12_1",
        "s12_1",
        "s12_2",
        "s12_3_1",
        "s12_3_1",
        "s12_4",
        "s12_4",
        # Case 1.3
        "s13_1",
        "s13_1",
        "s13_1",
        "s13_2",
        "s13_3_1",
        "s13_3_1",
        "s13_4",
        "s13_4",
        # Case 1.4
        "s14_1",
        "s14_1",
        "s14_1",
        "s14_2",
        "s14_3_1",
        "s14_3_1",
        "s14_4",
        "s14_4",
        # Case 1.5
        "s15_1",
        "s15_1",
        "s15_1",
        "s15_2",
        "s15_3_1",
        "s15_3_1",
        "s15_4",
        "s15_4",
        # Case 1.6
        "s16_1",
        "s16_1",
        "s16_1",
        "s16_2",
        "s16_3_1",
        "s16_3_1",
        "s16_4",
        "s16_4",
        # Case 1.7
        "s17_1",
        "s17_1",
        "s17_1",
        "s17_2",
        "s17_3_1",
        "s17_3_1",
        "s17_4",
        "s17_4",
        # Case 1.8
        "s18_1",
        "s18_1",
        "s18_1",
        "s18_2",
        "s18_3_1",
        "s18_3_1",
        "s18_4",
        "s18_4",
        # Case 1.9
        "s19_1",
        "s19_1",
        "s19_1",
        "s19_2",
        "s19_3_1",
        "s19_3_1",
        "s19_4",
        "s19_4",
    ]
    relations_oid = [
        # Case 1.0
        "a10_1",  # s1_1
        "a10_2",  # s1_1
        "b10",  # s1_1
        "c10",  # s1_1
        "c10",  # s1_2
        "c10",  # s1_3_1
        "d10_1",  # s1_3_1
        "c10",  # s1_3_1
        "d10_2",  # s1_3_1
        "c10",  # s1_4
        "e10",  # s1_4
        # Case 1.1
        "a11",  # s1_1
        "b11",  # s1_1
        "c11",  # s1_1
        "c11",  # s1_2
        "c11",  # s1_3_1
        "d11_1",  # s1_3_1
        "c11",  # s1_4
        "e11",  # s1_4
        # Case 1.2
        "a12",  # s1_1
        "b12",  # s1_1
        "c12",  # s1_1
        "c12",  # s1_2
        "c12",  # s1_3_1
        "d12_1",  # s1_3_1
        "c12",  # s1_4
        "e12",  # s1_4
        # Case 1.3
        "a13",  # s1_1
        "b13",  # s1_1
        "c13",  # s1_1
        "c13",  # s1_2
        "c13",  # s1_3_1
        "d13_1",  # s1_3_1
        "c13",  # s1_4
        "e13",  # s1_4
        # Case 1.4
        "a14",  # s1_1
        "b14",  # s1_1
        "c14",  # s1_1
        "c14",  # s1_2
        "c14",  # s1_3_1
        "d14_1",  # s1_3_1
        "c14",  # s1_4
        "e14",  # s1_4
        # Case 1.5
        "a15",  # s1_1
        "b15",  # s1_1
        "c15",  # s1_1
        "c15",  # s1_2
        "c15",  # s1_3_1
        "d15_1",  # s1_3_1
        "c15",  # s1_4
        "e15",  # s1_4
        # Case 1.6
        "a16",  # s1_1
        "b16",  # s1_1
        "c16",  # s1_1
        "c16",  # s1_2
        "c16",  # s1_3_1
        "d16_1",  # s1_3_1
        "c16",  # s1_4
        "e16",  # s1_4
        # Case 1.7
        "a17",  # s1_1
        "b17",  # s1_1
        "c17",  # s1_1
        "c17",  # s1_2
        "c17",  # s1_3_1
        "d17_1",  # s1_3_1
        "c17",  # s1_4
        "e17",  # s1_4
        # Case 1.8
        "a18",  # s1_1
        "b18",  # s1_1
        "c18",  # s1_1
        "c18",  # s1_2
        "c18",  # s1_3_1
        "d18_1",  # s1_3_1
        "c18",  # s1_4
        "e18",  # s1_4
        # Case 1.9
        "a19",  # s1_1
        "b19",  # s1_1
        "c19",  # s1_1
        "c19",  # s1_2
        "c19",  # s1_3_1
        "d19_1",  # s1_3_1
        "c19",  # s1_4
        "e19",  # s1_4
    ]
    relations_df = pd.DataFrame(
        {
            "ocel:eid": relations_eid,
            "ocel:activity": [events[key][0] for key in relations_eid],
            "ocel:timestamp": [events[key][1] for key in relations_eid],
            "ocel:oid": relations_oid,
            "ocel:type": [objects[key] for key in relations_oid],
            "ocel:qualifier": ["a" for _ in relations_eid],
        }
    )

    ocel = OCEL(events=events_df, objects=objects_df, relations=relations_df)
    print(ocel.get_summary())

    pm4py.write_ocel2_xml(ocel, "filtering_transitions.xml")

    model = pm4py.discover_oc_petri_net(ocel)
    pm4py.view_ocpn(model, format="svg")


# General OCEL for testing
def general_optional_input():
    objects_map = {
        "o11": "object1",
        "o12": "object2",
        "o13": "object3",
        "o14": "object4",
        "o21": "object1",
        "o22": "object2",
        "o23": "object3",
        "o24": "object4",
        "o25": "object5",
    }

    new_event, build_ocel, render = new_ocel(objects_map)

    new_event("start1", "Start", ["o11"])
    new_event("passthrough1", "Passthrough", ["o11"])
    new_event("transform1", "Transform", ["o11", "o12", "o13"])
    new_event("option1_1", "Option", ["o12", "o13", "o14"])
    new_event("end1", "End1", ["o14"])

    new_event("start2", "Start", ["o21"])
    new_event("passthrough2", "Passthrough", ["o21"])
    new_event("transform2", "Transform", ["o21", "o22", "o23"])
    new_event("option2_2", "Option", ["o22", "o24", "o25"])
    new_event("end2_1", "End1", ["o24"])
    new_event("end2_2", "End2", ["o23", "o25"])

    ocel = build_ocel()
    print(ocel.get_summary())

    pm4py.write_ocel2_sqlite(ocel, "general_optional_input.sqlite")

    render(ocel)


# Simple OCEL with multiple outputs which are then used one by one,
# by the same event activity
def simple_multiple_to_one():
    objects_map = {
        "o11": "object1",
        "o12": "object1",
        "o13": "object1",
        "o14": "object1",
        "o15": "object1",
        "o2": "object2",
        "o3": "object2",
        "o4": "object2",
        "o5": "object2",
        "o6": "object2",
    }

    new_event, build_ocel, render = new_ocel(objects_map)

    new_event("start1", "Start", ["o11", "o12", "o13"])

    new_event("consume1", "Consume", ["o11", "o2"])
    new_event("end1", "End", ["o2"])

    new_event("consume2", "Consume", ["o12", "o3"])
    new_event("end2", "End", ["o3"])

    new_event("consume3", "Consume", ["o13", "o4"])
    new_event("end3", "End", ["o4"])

    new_event("start2", "Start", ["o14", "o15"])

    new_event("consume4", "Consume", ["o14", "o5"])
    new_event("end4", "End", ["o5"])

    new_event("consume5", "Consume", ["o15", "o6"])
    new_event("end5", "End", ["o6"])

    ocel = build_ocel()
    print(ocel.get_summary())

    pm4py.write_ocel2_sqlite(ocel, "simple_multiple_to_one.sqlite")

    render(ocel)


# =====
# Just call the functions for which the log should be written into the current working directory.
# =====
motivation_example()
