"""Контроллер отображения эксперимента."""

from __future__ import annotations

from dataclasses import dataclass

from dt_analytics.application.dto import (
    CreateExperimentRequest,
    ExperimentDto,
    ModelConfigDto,
    PreprocessingConfigDto,
    RunExperimentRequest,
)
from dt_analytics.application.use_cases.experiments import (
    CreateExperimentUseCase,
    RunDecisionTreeExperimentUseCase,
)
from dt_analytics.presentation.dialogs import ErrorDialog
from dt_analytics.presentation.pages import ModelConfigPage, PreprocessingConfigPage


@dataclass(slots=True)
class ExperimentUiState:
    """Контроллер отображения эксперимента."""

    project_id: str | None = None
    dataset_id: str | None = None
    current_experiment: ExperimentDto | None = None


class ExperimentController:
    """Контроллер предобработки / модели и запуска эксперимента."""

    def __init__(
        self,
        *,
        create_experiment_use_case: CreateExperimentUseCase,
        run_experiment_use_case: RunDecisionTreeExperimentUseCase,
    ) -> None:
        self._create_experiment_use_case = create_experiment_use_case
        self._run_experiment_use_case = run_experiment_use_case
        self._preprocessing_page: PreprocessingConfigPage | None = None
        self._model_page: ModelConfigPage | None = None
        self._state = ExperimentUiState()

    def bind_views(
        self,
        *,
        preprocessing_page: PreprocessingConfigPage,
        model_page: ModelConfigPage,
    ) -> None:
        """Привязать страницы конфигурации."""
        self._preprocessing_page = preprocessing_page
        self._model_page = model_page

        self._preprocessing_page.create_experiment_requested.connect(self.create_experiment)
        self._preprocessing_page.run_experiment_requested.connect(self.create_and_run_experiment)

    def set_context(
        self,
        *,
        project_id: str,
        dataset_id: str,
    ) -> None:
        """Установить контекст проекта / набора данных."""
        self._state.project_id = project_id
        self._state.dataset_id = dataset_id
        self._state.current_experiment = None

    def clear(self) -> None:
        """Очистить состояние контроллера."""
        self._state = ExperimentUiState()
        if self._preprocessing_page is not None:
            self._preprocessing_page.clear_content()
        if self._model_page is not None:
            self._model_page.clear_content()

    def create_experiment(self) -> None:
        """Создать эксперимент из текущего состояния формы."""
        if self._preprocessing_page is None or self._model_page is None:
            return

        request_result = self._build_create_request()
        if request_result is None:
            return

        result = self._create_experiment_use_case.execute(request_result)
        if result.is_failure:
            self._show_error(
                title="Создание эксперимента завершилось ошибкой",
                message=result.error.message if result.error else "Неизвестная ошибка.",
                details=result.error.details if result.error else None,
            )
            return

        self._state.current_experiment = result.unwrap()

    def create_and_run_experiment(self) -> None:
        """Создать эксперимент и сразу запустить его."""
        self.create_experiment()
        if self._state.current_experiment is None:
            return

        run_result = self._run_experiment_use_case.execute(
            RunExperimentRequest(
                project_id=self._state.project_id or "",
                experiment_id=self._state.current_experiment.id,
                runtime_metadata={},
            )
        )
        if run_result.is_failure:
            self._show_error(
                title="Запуск эксперимента завершился ошибкой",
                message=run_result.error.message if run_result.error else "Неизвестная ошибка.",
                details=run_result.error.details if run_result.error else None,
            )
            return

        self._state.current_experiment = run_result.unwrap().experiment

    def _build_create_request(self) -> CreateExperimentRequest | None:
        if self._preprocessing_page is None or self._model_page is None:
            return None

        errors_a, warnings_a = self._preprocessing_page.validate_configuration()
        errors_b, warnings_b = self._model_page.validate_configuration()

        self._preprocessing_page.show_validation(errors_a, warnings_a)
        self._model_page.show_validation(errors_b, warnings_b)

        if errors_a or errors_b:
            self._show_error(
                title="Некорректная конфигурация эксперимента",
                message="Исправьте ошибки валидации перед созданием эксперимента.",
                details="\n".join([*errors_a, *errors_b]) or None,
            )
            return None

        if self._state.project_id is None or self._state.dataset_id is None:
            self._show_error(
                title="Нет контекста набора данных",
                message="Выберите набор данных перед настройкой эксперимента.",
            )
            return None

        preprocessing_dto = PreprocessingConfigDto(
            id=None,
            target_column=self._preprocessing_page.get_target_column(),
            feature_columns=self._preprocessing_page.get_feature_columns(),
            excluded_columns=self._preprocessing_page.get_excluded_columns(),
            missing_strategy=self._preprocessing_page.get_missing_strategy(),
            categorical_encoding_strategy=(
                self._preprocessing_page.get_categorical_encoding_strategy()
            ),
            drop_duplicates=self._preprocessing_page.get_drop_duplicates(),
            test_size=self._preprocessing_page.get_test_size(),
            random_state=self._preprocessing_page.get_random_state(),
            stratify_enabled=self._preprocessing_page.get_stratify_enabled(),
        )

        model_dto = ModelConfigDto(
            id=None,
            task_type=self._model_page.get_task_type(),
            algorithm_code=self._model_page.get_algorithm_code(),
            criterion=self._model_page.get_criterion(),
            max_depth=self._model_page.get_max_depth(),
            min_samples_split=self._model_page.get_min_samples_split(),
            min_samples_leaf=self._model_page.get_min_samples_leaf(),
            max_features=self._model_page.get_max_features(),
            splitter=self._model_page.get_splitter(),
            class_weight=self._model_page.get_class_weight(),
            random_state=self._model_page.get_random_state(),
            additional_params={},
        )

        experiment_name = f"Эксперимент для {self._state.dataset_id}"

        return CreateExperimentRequest(
            project_id=self._state.project_id,
            dataset_id=self._state.dataset_id,
            name=experiment_name,
            preprocessing_config=preprocessing_dto,
            model_config=model_dto,
            notes=None,
        )

    def _show_error(self, *, title: str, message: str, details: str | None = None) -> None:
        parent = self._preprocessing_page or self._model_page
        ErrorDialog.show_error(
            title=title,
            message=message,
            details=details,
            parent=parent,
        )
