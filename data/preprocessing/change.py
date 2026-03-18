import pm4py
import pandas as pd
from decimal import Decimal

ocel = pm4py.read_ocel2("socel_data.xml")
waste_oid = []
waste_type = []
waste_mass = []
waster_eid = []
waster_activity = []
waster_timestamp = []
waster_oid = []
waster_type = []
waster_qualifier = []
wasteo_oid = []
wasteo_oid2 = []
wasteo_qualifier = []


# Rename columns
ocel.events = ocel.events.rename(columns={"p_duration[s]": "duration"})
ocel.objects = ocel.objects.rename(columns={"p_mass[kg]": "mass"})


# Filter out useless events and objects
ocel = pm4py.filtering.filter_ocel_event_attribute(
    ocel, "ocel:activity", ["MoveParts"], False
)
ocel = pm4py.filtering.filter_ocel_object_attribute(
    ocel, "ocel:type", ["Facility"], False
)


# Drop useless attributes
ocel.events = ocel.events.drop(
    columns=[
        "s_co2e[kg]",
        "i_compressed-air[m3]",
        "i_electric-from-grid-de[kWh]",
        "i_coating-material[kg]",
        "i_coating-material-waste[kg]",
        "i_gas-n2-used[m3]",
        "i_gas-n2-emiited-to-air[m3]",
        "i_gas_input[Wh]",
        "i_emission-of-burn[Wh]",
        "i_cardboard-box[kg]",
        "i_steel-waste-to-recycle[kg]",
    ]
)
ocel.objects = ocel.objects.drop(
    columns=[
        "p_material[EN10130:2006]",
        "s_co2e[kg]",
        "i_steel-waste[kg]",
        "P_electric-from-grid-de[kWh]",
        "P_gas-from-grid-de[m3]",
        "i_material-cold-rolled-steel[kg]",
        "i_steel-waste-to-recycle[kg]",
        "P_electric-from-grid-de[kWh]",
        "i_material-steel-pin[kg]",
        "P_compressed-air[m3]",
        "p_init-len[cm]",
        "p_width[cm]",
    ]
)


# Rename the Cutt* events
ocel.events.loc[ocel.events["ocel:activity"] == "CuttFemalePart", "ocel:activity"] = (
    "CutFemalePart"
)
ocel.events.loc[ocel.events["ocel:activity"] == "CuttMalePart", "ocel:activity"] = (
    "CutMalePart"
)


# Mass equation for AssembleHinge
for _, event in ocel.events[ocel.events["ocel:activity"] == "AssembleHinge"].iterrows():
    print(event["ocel:eid"])
    inputs = ocel.relations[
        (ocel.relations["ocel:eid"] == event["ocel:eid"])
        & (ocel.relations["ocel:qualifier"] == "input")
    ]
    mass = Decimal(0)
    for _, i in inputs.iterrows():
        obj = ocel.objects[ocel.objects["ocel:oid"] == i["ocel:oid"]]
        if obj.shape[0] != 1:
            raise Exception()
        mass += Decimal(obj.iloc[0]["mass"])
    output = ocel.relations[
        (ocel.relations["ocel:eid"] == event["ocel:eid"])
        & (ocel.relations["ocel:qualifier"] == "output")
    ]
    if output.shape[0] != 1:
        raise Exception()

    ocel.objects.loc[ocel.objects["ocel:oid"] == output.iloc[0]["ocel:oid"], "mass"] = (
        mass
    )


# Mass equation for PackHinges
for _, event in ocel.events[ocel.events["ocel:activity"] == "PackHinges"].iterrows():
    print(event["ocel:eid"])
    inputs = ocel.relations[
        (ocel.relations["ocel:eid"] == event["ocel:eid"])
        & (ocel.relations["ocel:qualifier"] == "input")
    ]
    mass = Decimal(0)
    for _, i in inputs.iterrows():
        obj = ocel.objects[ocel.objects["ocel:oid"] == i["ocel:oid"]]
        if obj.shape[0] != 1:
            raise Exception()
        mass += Decimal(obj.iloc[0]["mass"])
    output = ocel.relations[
        (ocel.relations["ocel:eid"] == event["ocel:eid"])
        & (ocel.relations["ocel:qualifier"] == "output")
    ]
    if output.shape[0] != 1:
        raise Exception()

    ocel.objects.loc[ocel.objects["ocel:oid"] == output.iloc[0]["ocel:oid"], "mass"] = (
        mass
    )


# Create steel coil waste
for _, f in ocel.objects[ocel.objects["ocel:type"] == "SteelCoil"].iterrows():
    current_weight = Decimal(f["mass"])

    ocel.object_changes = ocel.object_changes[
        ~(ocel.object_changes["ocel:oid"] == f["ocel:oid"])
    ].reset_index(drop=True)

    for _, i in ocel.relations[ocel.relations["ocel:oid"] == f["ocel:oid"]].iterrows():
        event = i["ocel:eid"]
        print(event)
        relation = ocel.relations[
            (ocel.relations["ocel:eid"] == event)
            & (ocel.relations["ocel:type"] == "SteelSheet")
        ]
        if relation.shape[0] != 1:
            raise Exception()
        weight = Decimal(
            ocel.objects[ocel.objects["ocel:oid"] == relation.iloc[0]["ocel:oid"]].iloc[
                0
            ]["mass"]
        )

        current_weight = current_weight - weight - weight * Decimal("0.02")

        duration = ocel.events[ocel.events["ocel:eid"] == event].iloc[0]["duration"]

        new_row = pd.DataFrame(
            [
                {
                    "ocel:oid": f["ocel:oid"],
                    "ocel:type": "SteelCoil",
                    "ocel:timestamp": i["ocel:timestamp"]
                    + pd.Timedelta(seconds=float(duration)),
                    "ocel:field": "mass",
                    "mass": current_weight,
                }
            ]
        )
        ocel.object_changes = pd.concat(
            [ocel.object_changes, new_row], ignore_index=True
        )

        name = "o_splitwaste_" + event.split("_")[-1]

        waste_oid.append(name)
        waste_type.append("SplitWaste")
        waste_mass.append(weight * Decimal("0.02"))

        waster_eid.append(event)
        waster_activity.append(i["ocel:activity"])
        waster_timestamp.append(i["ocel:timestamp"])
        waster_oid.append(name)
        waster_type.append("SplitWaste")
        waster_qualifier.append("output")

        wasteo_oid.append(name)
        wasteo_oid2.append(f["ocel:oid"])
        wasteo_qualifier.append("created from")

    print(current_weight)
    if current_weight < 0:
        raise Exception()


# Create waste objects for the cut events
for _, event in ocel.events[
    ocel.events["ocel:activity"].isin(["CutFemalePart", "CutMalePart"])
].iterrows():
    print(event["ocel:eid"])

    name = "o_cutwaste_" + (event["ocel:eid"].split("_"))[-1]

    waste_oid.append(name)
    waste_type.append("CutWaste")
    waste_mass.append(event["i_steel-waste[kg]"])

    waster_eid.append(event["ocel:eid"])
    waster_activity.append(event["ocel:activity"])
    waster_timestamp.append(event["ocel:timestamp"])
    waster_oid.append(name)
    waster_type.append("CutWaste")
    waster_qualifier.append("output")

    input = ocel.relations[
        (ocel.relations["ocel:eid"] == event["ocel:eid"])
        & (ocel.relations["ocel:qualifier"] == "input")
    ]
    if input.shape[0] != 1:
        raise Exception()
    wasteo_oid.append(name)
    wasteo_oid2.append(input.iloc[0]["ocel:oid"])
    wasteo_qualifier.append("created from")

new_object = pd.DataFrame(
    {
        "ocel:oid": waste_oid,  # Unique object ID
        "ocel:type": waste_type,  # e.g., 'Order'
        "mass": waste_mass,  # e.g., 'Order'
    }
)
ocel.objects = pd.concat([ocel.objects, new_object], ignore_index=True)

new_object = pd.DataFrame(
    {
        "ocel:eid": waster_eid,  # Unique object ID
        "ocel:activity": waster_activity,  # Unique object ID
        "ocel:timestamp": waster_timestamp,  # Unique object ID
        "ocel:oid": waster_oid,  # Unique object ID
        "ocel:type": waster_type,  # e.g., 'Order'
        "ocel:qualifier": waster_qualifier,  # e.g., 'Order'
    }
)
ocel.relations = pd.concat([ocel.relations, new_object], ignore_index=True)

new_object = pd.DataFrame(
    {
        "ocel:oid": wasteo_oid,  # Unique object ID
        "ocel:oid_2": wasteo_oid2,  # Unique object ID
        "ocel:qualifier": wasteo_qualifier,  # e.g., 'Order'
    }
)
ocel.o2o = pd.concat([ocel.o2o, new_object], ignore_index=True)
ocel.events = ocel.events.drop(columns=["i_steel-waste[kg]"])


pm4py.write_ocel2_xml(ocel, "hinge-mass.xml")
