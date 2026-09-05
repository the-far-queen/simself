"""Minimal StateVector stub for ResilientSelfModel + WisdomLibrary.

This is a minimal implementation that satisfies the interface expected by
resilient_self_model.py. The full StateVector would have many more fields;
this stub provides just what ResilientSelfModel and WisdomLibrary need.

Fields:
- swedenborgian_axes: dict of axis_name -> float [0, 1]
- resource_pools: dict of resource_name -> {'current': float, 'max': float}
- core_metrics: dict of metric_name -> float
- recent_events: list of event dicts with timestamp_ns, type, module, details
"""


class StateVector:
    def __init__(self):
        self.swedenborgian_axes = {}
        self.resource_pools = {}
        self.core_metrics = {}
        self.recent_events = []


# SwedenborgianAxes is a type alias for dict[str, float]
SwedenborgianAxes = dict

# CoreMetrics is a type alias for dict[str, float]
CoreMetrics = dict