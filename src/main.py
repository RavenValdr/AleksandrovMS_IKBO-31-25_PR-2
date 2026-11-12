"""Точка входа CLI-инструмента анализа зависимостей пакетов."""

import sys
from src.cli import AppConfig, ConfigError, format_config_kv, parse_and_validate
from src.collector import (
    CollectorError,
    fetch_npm_dependencies,
    load_test_repo,
)
from src.graph import build_dependency_graph, find_reverse_dependencies

STAGE_ONE = 1
STAGE_TWO = 2
STAGE_THREE = 3
STAGE_FOUR = 4
EXIT_FAILURE = 1


def run_stage_two(config: AppConfig) -> None:
    """Выполняет этап 2: вывод прямых зависимостей пакета."""
    if config.test_mode:
        repo_data = load_test_repo(config.repo)
        deps = {d: "latest" for d in repo_data.get(config.package, [])}
    else:
        deps = fetch_npm_dependencies(
            config.repo, config.package, config.version
        )
    print(f"Прямые зависимости {config.package}@{config.version}:")
    for name, ver in sorted(deps.items()):
        print(f"  {name}: {ver}")


def run_stage_three(config: AppConfig) -> None:
    """Выполняет этап 3: построение транзитивного графа DFS."""
    graph = build_dependency_graph(
        config.package,
        config.version,
        config.repo,
        config.test_mode,
        config.filter_substr,
    )
    print("Транзитивный граф зависимостей (DFS):")
    for pkg, deps in graph.items():
        joined = ", ".join(deps) if deps else "(нет зависимостей)"
        print(f"  {pkg} -> {joined}")


def run_stage_four(config: AppConfig) -> None:
    """Выполняет этап 4: поиск обратных зависимостей пакета."""
    if not config.test_mode:
        raise CollectorError("Этап 4 требует --test-mode с полным графом.")
    full_repo = load_test_repo(config.repo)
    rev_deps = find_reverse_dependencies(
        config.package, full_repo, config.filter_substr
    )
    print(f"Обратные зависимости для {config.package}:")
    print("  " + (", ".join(rev_deps) if rev_deps else "(не найдены)"))


def main(argv: list[str] | None = None) -> int:
    """Основная функция диспетчеризации этапов."""
    try:
        config = parse_and_validate(argv)
        if config.stage == STAGE_ONE:
            print(format_config_kv(config))
        elif config.stage == STAGE_TWO:
            run_stage_two(config)
        elif config.stage == STAGE_THREE:
            run_stage_three(config)
        else:
            run_stage_four(config)
    except (ConfigError, CollectorError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return EXIT_FAILURE
    return 0


if __name__ == "__main__":
    sys.exit(main())