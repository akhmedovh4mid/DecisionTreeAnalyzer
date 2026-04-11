from src.core.data_loading import DataLoader


def main():
    loader = DataLoader()

    datasets = [
        loader.load("data/iris.csv"),
        loader.load("data/iris.json"),
        loader.load("data/iris.tsv"),
        loader.load("data/iris.xlsx"),
    ]

    for dataset in datasets:
        print(f"{dataset.name=}")
        print(f"{dataset.file_format=}")
        print(f"{dataset.row_count=}")
        print(f"{dataset.column_count=}")
        print(f"{dataset.columns=}")
        print(f"{dataset.data.head()=}")
        print()


if __name__ == "__main__":
    main()
