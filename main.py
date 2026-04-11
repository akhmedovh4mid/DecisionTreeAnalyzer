from src.core.data_loading import DataLoader
from src.core.decision_tree import DecisionTreeBuilder
from src.core.preprocessing import DataPreprocessor


def main():
    loader = DataLoader()
    preprocessor = DataPreprocessor()
    builder = DecisionTreeBuilder(max_depth=4, random_state=42)

    dataset = loader.load("data/iris.csv")
    processed = preprocessor.preprocess(dataset, target_column="species")
    model = builder.build(processed)

    print(model.depth)
    print(model.feature_importances)


if __name__ == "__main__":
    main()
