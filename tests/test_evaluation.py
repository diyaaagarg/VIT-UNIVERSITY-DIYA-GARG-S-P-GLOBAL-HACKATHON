from src.evaluation.metrics import classification_report


def test_classification_report() -> None:
    result = classification_report(["positive", "negative", "neutral"], ["positive", "negative", "negative"])
    assert result["accuracy"] == 0.667
    assert result["labels"]["positive"]["f1"] == 1.0
