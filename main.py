from src.core.data_loading import DataLoader
from src.core.decision_tree import DecisionTreeBuilder
from src.core.prediction import Predictor
from src.core.preprocessing import DataPreprocessor


def main():
    loader = DataLoader()
    preprocessor = DataPreprocessor()
    builder = DecisionTreeBuilder()
    predictor = Predictor()

    dataset = loader.load("data/iris.csv")
    processed = preprocessor.preprocess(dataset, target_column="species")
    model = builder.build(processed)

    prediction_result = predictor.predict(model, processed, on="test")

    print(prediction_result.predicted_values.head())
    print(prediction_result.predicted_probabilities.head())


if __name__ == "__main__":
    main()
