"""Точка входа CLI-инструмента анализа зависимостей пакетов."""

import sys
from src.cli import AppConfig, ConfigError, format_config_kv, parse_and_validate
from src.collector import (
    CollectorError,
    fetch_npm_dependencies,
    load_test_repo,
)
from src.graph import build_dependency_graph

STAGE_ONE = 1
STAGE_TWO = 2
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


def main(argv: list[str] | None = None) -> int:
    """Основная функция диспетчеризации этапов."""
    try:
        config = parse_and_validate(argv)
        if config.stage == STAGE_ONE:
            print(format_config_kv(config))
        elif config.stage == STAGE_TWO:
            run_stage_two(config)
        else:
            run_stage_three(config)
    except (ConfigError, CollectorError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return EXIT_FAILURE
    return 0


if __name__ == "__main__":
    sys.exit(main())