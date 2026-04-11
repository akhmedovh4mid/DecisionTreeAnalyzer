from src.app.controller import ApplicationController


def main():
    controller = ApplicationController()

    result = controller.run_pipeline(
        file_path="data/iris.csv",
        target_column="species",
    )

    print(result.evaluation_metrics.score_summary)
    print(result.model.depth)
    print(result.prediction_result.predicted_values.head())


if __name__ == "__main__":
    main()
