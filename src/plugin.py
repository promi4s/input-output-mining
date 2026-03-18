from typing import Annotated
from pydantic import BaseModel, Field

from .discover import *


from ocelescope import *
from ocelescope.visualization.default.dot import DotVis


class ObjectFlowNet(Resource):
    label = "Object Flow Net"
    description = "A Petri net mined on the object flow"

    # The dot string of this graph
    dot_str: str

    def visualize(self):
        return DotVis(dot_str=self.dot_str, layout_engine="dot")


class Input(PluginInput, frozen=True):
    remove_object_types: list[str] = OCEL_FIELD(
        field_type="object_type",
        ocel_id="ocel",
        title="Filter out object types",
    )

    hint_initial_input: list[str] = OCEL_FIELD(
        field_type="object_type",
        ocel_id="ocel",
        title="Always consider as initial input",
    )

    hint_final_output: list[str] = OCEL_FIELD(
        field_type="object_type",
        ocel_id="ocel",
        title="Always consider as final output",
    )

    calculate_masses: bool = Field(
        default=False,
        title="Use MFA to determine initial inputs and final outputs",
    )

    filter_configurations: float = Field(
        ge=0.0,
        le=1.0,
        default=0.0,
        title="Configurations threshold α",
    )

    filter_arcs: float = Field(
        ge=0.0,
        le=1.0,
        default=0.0,
        title="Arcs threshold β",
    )

    show_helper_text: bool = Field(
        default=False,
        title="Show place and transition information",
    )


class AnnotatedInput(Input, frozen=True):
    annotate_objects_count: list[str] = OCEL_FIELD(
        field_type="object_type",
        ocel_id="ocel",
        title="Annotate object types with count",
    )

    annotate_objects_mass: list[str] = OCEL_FIELD(
        field_type="object_type",
        ocel_id="ocel",
        title="Annotate object types with mass",
    )

    annotate_explicit: list[str] = OCEL_FIELD(
        field_type="event_type",
        ocel_id="ocel",
        title="Annotate activities with explicit mass",
    )

    annotate_implicit_count: list[str] = OCEL_FIELD(
        field_type="event_type",
        ocel_id="ocel",
        title="Annotate activities with implicit count",
    )

    annotate_implicit_mass: list[str] = OCEL_FIELD(
        field_type="event_type",
        ocel_id="ocel",
        title="Annotate activities with implicit mass",
    )


class ObjectFlowMiner(Plugin):
    label = "Object Flow Miner"
    description = "Mine the object flow based on inputs and outputs."
    version = "0.1.0"

    @plugin_method(label="Weighted arcs")
    def weighted_arcs_discovery(
        self,
        ocel: Annotated[OCEL, OCELAnnotation(label="Event Log")],
        input: Input,
    ) -> ObjectFlowNet:
        return discovery_unannotated(ocel, input, True)

    @plugin_method(label="Variable arcs")
    def variable_arcs_discovery(
        self,
        ocel: Annotated[OCEL, OCELAnnotation(label="Event Log")],
        input: Input,
    ) -> ObjectFlowNet:
        return discovery_unannotated(ocel, input, False)

    @plugin_method(label="Weighted arcs with annotations")
    def weighted_arcs_discovery_annotated(
        self,
        ocel: Annotated[OCEL, OCELAnnotation(label="Event Log")],
        input: AnnotatedInput,
    ) -> ObjectFlowNet:
        return discovery_annotated(ocel, input, True)

    @plugin_method(label="Variable arcs with annotations")
    def variable_arcs_discovery_annotated(
        self,
        ocel: Annotated[OCEL, OCELAnnotation(label="Event Log")],
        input: AnnotatedInput,
    ) -> ObjectFlowNet:
        return discovery_annotated(ocel, input, False)


def discovery_unannotated(ocel, input: Input, weighted: bool) -> ObjectFlowNet:
    ocel = pm4py.filtering.filter_ocel_object_attribute(
        ocel.ocel,
        "ocel:type",
        input.remove_object_types,
        False,
    )

    hints = dict()
    for i in input.hint_initial_input:
        hints[i] = "initial input"
    for i in input.hint_final_output:
        hints[i] = "final output"

    labels = find_event_labels(ocel, hints)["labels"]

    if input.calculate_masses:
        labels = calculate_masses(ocel, labels, True)["labels"]

    by_object_id = ocel.objects.set_index("ocel:oid")

    agg, object_instances = aggregate(labels)

    agg2 = filter_aggregation_by_variants(
        agg, lambda total, i: i > total * input.filter_configurations
    )
    agg3 = filter_aggregation_by_associations(
        agg2, lambda total, i: i > total * input.filter_arcs
    )

    viz = discover_dot_string(
        agg3,
        ocel,
        by_object_id,
        labels,
        {
            "DRAW_PLACE_INFORMATION": input.show_helper_text,
            "DRAW_TRANSITION_INFORMATION": input.show_helper_text,
            "USE_ARC_WEIGHTS": weighted,
            "DRAW_ARC_WEIGHTS": weighted,
        },
        object_instances,
    )

    return ObjectFlowNet(dot_str=viz.source)


def discovery_annotated(ocel, input: AnnotatedInput, weighted: bool) -> ObjectFlowNet:
    ocel = pm4py.filtering.filter_ocel_object_attribute(
        ocel.ocel,
        "ocel:type",
        input.remove_object_types,
        False,
    )

    hints = dict()
    for i in input.hint_initial_input:
        hints[i] = "initial input"
    for i in input.hint_final_output:
        hints[i] = "final output"

    labels = find_event_labels(ocel, hints)["labels"]

    if input.calculate_masses:
        labels = calculate_masses(ocel, labels, True)["labels"]

    by_object_id = ocel.objects.set_index("ocel:oid")

    agg, object_instances = aggregate(labels)

    agg2 = filter_aggregation_by_variants(
        agg, lambda total, i: i > total * input.filter_configurations
    )
    agg3 = filter_aggregation_by_associations(
        agg2, lambda total, i: i > total * input.filter_arcs
    )

    for i in input.annotate_objects_count:
        calculate_object_type_count(agg3, ocel, by_object_id, labels, i)

    for i in input.annotate_objects_mass:
        calculate_object_type_mass(agg3, ocel, by_object_id, labels, i)

    for i in input.annotate_explicit:
        calculate_explicit_waste(agg3, ocel, by_object_id, labels, i, "mass")

    for i in input.annotate_implicit_count:
        calculate_implicit_waste_count(agg3, ocel, by_object_id, labels, i)

    for i in input.annotate_implicit_mass:
        calculate_implicit_waste_mass(agg3, ocel, by_object_id, labels, i)

    viz = discover_dot_string(
        agg3,
        ocel,
        by_object_id,
        labels,
        {
            "DRAW_PLACE_INFORMATION": input.show_helper_text,
            "DRAW_TRANSITION_INFORMATION": input.show_helper_text,
            "USE_ARC_WEIGHTS": weighted,
            "DRAW_ARC_WEIGHTS": weighted,
        },
        object_instances,
    )

    return ObjectFlowNet(dot_str=viz.source)
