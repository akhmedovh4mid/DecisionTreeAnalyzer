from __future__ import annotations

from pathlib import Path

from src.core.analysis import DataAnalyzer
from src.core.data_loading import DataLoader
from src.core.decision_tree import DecisionTreeBuilder
from src.core.evaluation import QualityEvaluator
from src.core.prediction import Predictor
from src.core.preprocessing import DataPreprocessor
from src.core.visualization import Visualizer


def test_prepare_visualization_for_iris_dataset() -> None:
    data_dir = Path("data")
    dataset = DataLoader().load(data_dir / "iris.csv")

    analyzer = DataAnalyzer()
    preprocessor = DataPreprocessor()
    builder = DecisionTreeBuilder()
    predictor = Predictor()
    evaluator = QualityEvaluator()
    visualizer = Visualizer()

    dataset_info = analyzer.analyze(dataset, "species")
    processed = preprocessor.preprocess(dataset, "species")
    model = builder.build(processed)
    prediction = predictor.predict(model, processed, on="test")
    metrics = evaluator.evaluate(prediction, average="weighted", zero_division=0)

    visualization = visualizer.prepare(dataset_info, model, metrics)

    assert visualization.source_dataset_name == "iris"
    assert visualization.target_column == "species"
    assert visualization.has_tree_text is True
    assert "class:" in visualization.tree_text
    assert "depth" in visualization.model_summary
    assert "accuracy" in visualization.metrics_summary
    assert isinstance(visualization.feature_importances, dict)
