import pm4py
from decimal import Decimal

ocel = pm4py.read_ocel2_xml("socel_hinge.xml")

# Fill the formed part weight
# Just copy the weight which is given in the update table
for index, part in ocel.objects[ocel.objects["ocel:type"] == "FormedPart"].iterrows():
    print(index, "at", part["ocel:oid"])

    weight = ocel.object_changes[
        (ocel.object_changes["ocel:oid"] == part["ocel:oid"])
        & (ocel.object_changes["ocel:field"] == "p_mass[kg]")
    ]
    if len(weight) != 1:
        raise Exception()

    ocel.objects.loc[index, "p_mass[kg]"] = weight.iloc[0]["p_mass[kg]"]
    ocel.object_changes = ocel.object_changes.drop(index=weight.index[0]).reset_index(
        drop=True
    )

# Calculate the new female formed weight
# Subtract the waste given in the cut event
for index, part in ocel.objects[ocel.objects["ocel:type"] == "FemalePart"].iterrows():
    print(index, "at", part["ocel:oid"])

    cutRelation = ocel.relations[
        (ocel.relations["ocel:oid"] == part["ocel:oid"])
        & (ocel.relations["ocel:activity"] == "CuttFemalePart")
    ].iloc[0]["ocel:eid"]

    cutEvent = ocel.events[ocel.events["ocel:eid"] == cutRelation].iloc[0]

    formedPart = ocel.relations[
        (ocel.relations["ocel:type"] == "FormedPart")
        & (ocel.relations["ocel:activity"] == "CuttFemalePart")
    ].iloc[0]["ocel:oid"]

    weight = ocel.objects[ocel.objects["ocel:oid"] == formedPart]["p_mass[kg]"].iloc[0]

    ocel.objects.loc[index, "p_mass[kg]"] = Decimal(weight) - Decimal(
        cutEvent["i_steel-waste[kg]"]
    )

# Fill in the CuttMalePart waste
# This is based on the 0.76 of the being waste as defined in
# https://github.com/marcoheinisch/thesis-sOCEL/blob/main/cpn/cpn-sim-util.sml line 207
for index, cut in ocel.events[
    ocel.events["ocel:activity"] == "CuttMalePart"
].iterrows():
    print(index, "at", cut["ocel:eid"])

    formedPart = ocel.relations[
        (ocel.relations["ocel:eid"] == cut["ocel:eid"])
        & (ocel.relations["ocel:type"] == "FormedPart")
    ]
    if len(formedPart) != 1:
        raise Exception()
    formedPart = formedPart.iloc[0]["ocel:oid"]

    formedPart = ocel.objects[ocel.objects["ocel:oid"] == formedPart].iloc[0]

    waste = Decimal(formedPart["p_mass[kg]"]) * Decimal("0.12") * Decimal("2")
    ocel.events.loc[index, "i_steel-waste[kg]"] = waste

    malePart = ocel.relations[
        (ocel.relations["ocel:eid"] == cut["ocel:eid"])
        & (ocel.relations["ocel:type"] == "MalePart")
    ]
    if len(malePart) != 1:
        raise Exception()
    malePart = malePart.iloc[0]["ocel:oid"]

    malePart = ocel.objects[ocel.objects["ocel:oid"] == malePart].iloc[0]

    ocel.objects.loc[malePart.name, "p_mass[kg]"] = (
        Decimal(formedPart["p_mass[kg]"]) - waste
    )

    index = ocel.object_changes[
        ocel.object_changes["ocel:oid"] == malePart["ocel:oid"]
    ].index[0]
    ocel.object_changes = ocel.object_changes.drop(index=index).reset_index(drop=True)

# Fix a bug in the hinge assembly
# The weights used were not the actual cut parts and there was also a bug in the equation
for index, event in ocel.events[
    ocel.events["ocel:activity"] == "AssembleHinge"
].iterrows():
    print(index, "at", event["ocel:eid"])

    inputs = ocel.relations[
        (ocel.relations["ocel:eid"] == event["ocel:eid"])
        & (ocel.relations["ocel:qualifier"] == "input")
    ]["ocel:oid"]

    objects = ocel.objects[ocel.objects["ocel:oid"].isin(inputs)]
    weight = Decimal("0.1")

    for _, i in objects.iterrows():
        weight += Decimal(i["p_mass[kg]"])

    hinge = ocel.relations[
        (ocel.relations["ocel:eid"] == event["ocel:eid"])
        & (ocel.relations["ocel:type"] == "Hinge")
    ].iloc[0]
    hinge = ocel.objects[(ocel.objects["ocel:oid"] == hinge["ocel:oid"])].iloc[0]

    ocel.objects.loc[hinge.name, "p_mass[kg]"] = weight

pm4py.write_ocel2_xml(ocel, "socel_data.xml")
