"""Dependency-light classification metrics for reproducible reports."""
from __future__ import annotations
from collections import Counter


def classification_report(truth: list[str], predicted: list[str]) -> dict[str, object]:
    labels = sorted(set(truth) | set(predicted))
    rows = {}
    for label in labels:
        tp = sum(a == b == label for a, b in zip(truth, predicted))
        fp = sum(a != label and b == label for a, b in zip(truth, predicted))
        fn = sum(a == label and b != label for a, b in zip(truth, predicted))
        precision, recall = tp / (tp + fp) if tp + fp else 0.0, tp / (tp + fn) if tp + fn else 0.0
        rows[label] = {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(2 * precision * recall / (precision + recall), 3) if precision + recall else 0.0, "support": truth.count(label)}
    macro_f1 = sum(row["f1"] for row in rows.values()) / len(rows) if rows else 0.0
    return {"accuracy": round(sum(a == b for a, b in zip(truth, predicted)) / len(truth), 3) if truth else 0.0, "macro_f1": round(macro_f1, 3), "labels": rows, "n": len(truth)}
