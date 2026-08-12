#!/usr/bin/env python3
"""Stable JSON adapter for the KGCQual M_N/M_V/M formulas.

This file is a Semantier fork addition. It exposes the intrinsic formula
surface from Main.java without changing upstream's file-oriented CLI.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from typing import Any


ADAPTER_VERSION = "kgcqual-semantier-json.v1"
UPSTREAM_METRICS = (
    "kgcqual.noun_metric",
    "kgcqual.verb_metric_with_polarity",
    "kgcqual.combined_metric",
)


def _components(nodes: set[str], edges: list[dict[str, Any]]) -> int:
    if not nodes:
        return 0
    adjacent: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        subject, object_ = str(edge["subject"]), str(edge["object"])
        adjacent[subject].add(object_)
        adjacent[object_].add(subject)
    seen: set[str] = set()
    count = 0
    for node in sorted(nodes):
        if node in seen:
            continue
        count += 1
        stack = [node]
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(sorted(adjacent[current] - seen, reverse=True))
    return count


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    prediction = payload["prediction"]
    reference = payload["reference"]
    predicted_nodes = {str(node["id"]) for node in prediction.get("nodes", [])}
    reference_nodes = {str(node["id"]) for node in reference.get("nodes", [])}
    predicted_edges = list(prediction.get("edges", []))
    reference_edges = list(reference.get("edges", []))

    noun_denominator = max(len(reference_nodes), 1)
    missing_nodes = len(reference_nodes - predicted_nodes)
    surplus_nodes = len(predicted_nodes - reference_nodes)
    component_penalty = abs(
        _components(predicted_nodes, predicted_edges)
        - _components(reference_nodes, reference_edges)
    )
    noun_metric = min(
        1.0,
        (missing_nodes + surplus_nodes + component_penalty) / (2.0 * noun_denominator),
    )

    def relation_key(edge: dict[str, Any]) -> tuple[str, str, str]:
        return (str(edge["subject"]), str(edge["predicate"]), str(edge["object"]))

    reference_relations = {relation_key(edge): str(edge.get("polarity", "positive")) for edge in reference_edges}
    predicted_relations = {relation_key(edge): str(edge.get("polarity", "positive")) for edge in predicted_edges}
    predicate_denominator = max(len(reference_relations), 1)
    missing_relations = len(reference_relations.keys() - predicted_relations.keys())
    surplus_relations = len(predicted_relations.keys() - reference_relations.keys())
    polarity_mismatches = sum(
        predicted_relations[key] != polarity
        for key, polarity in reference_relations.items()
        if key in predicted_relations
    )
    verb_metric = min(
        1.0,
        (
            missing_relations
            + surplus_relations
            + float(payload.get("polarity_penalty", 0.1)) * polarity_mismatches
        )
        / (2.0 * predicate_denominator),
    )
    alpha = float(payload.get("alpha", 0.5))
    combined = alpha * noun_metric + (1.0 - alpha) * verb_metric
    return {
        "adapter_version": ADAPTER_VERSION,
        "metrics": [
            {"metric_name": UPSTREAM_METRICS[0], "value": noun_metric},
            {"metric_name": UPSTREAM_METRICS[1], "value": verb_metric},
            {"metric_name": UPSTREAM_METRICS[2], "value": combined},
        ],
        "parameters": {"alpha": alpha, "polarity_penalty": float(payload.get("polarity_penalty", 0.1))},
    }


def main() -> None:
    payload = json.load(sys.stdin)
    json.dump(evaluate(payload), sys.stdout, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
