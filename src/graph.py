"""Модуль построения графа зависимостей и поиска обратных связей."""

from typing import Callable
from src.collector import fetch_npm_dependencies, load_test_repo

DepProvider = Callable[[str, str], dict[str, str]]


def should_skip(package: str, filter_substr: str) -> bool:
    """Проверяет, должен ли пакет быть отфильтрован по подстроке."""
    if not filter_substr:
        return False
    return filter_substr in package


def dfs_collect(
    current_pkg: str,
    current_ver: str,
    provider: DepProvider,
    filter_substr: str,
    graph: dict[str, list[str]],
    visited: set[str],
    visiting: set[str],
) -> None:
    """Рекурсивно обходит граф в глубину (DFS) с защитой от циклов."""
    if should_skip(current_pkg, filter_substr):
        return
    if current_pkg in visited or current_pkg in visiting:
        return
    visiting.add(current_pkg)
    raw_deps = provider(current_pkg, current_ver)
    filtered_deps: list[str] = []
    for dep_name, dep_ver in raw_deps.items():
        if should_skip(dep_name, filter_substr):
            continue
        filtered_deps.append(dep_name)
        dfs_collect(
            dep_name,
            dep_ver,
            provider,
            filter_substr,
            graph,
            visited,
            visiting,
        )
    graph[current_pkg] = filtered_deps
    visiting.remove(current_pkg)
    visited.add(current_pkg)


def build_dependency_graph(
    root_pkg: str,
    root_ver: str,
    repo: str,
    test_mode: bool,
    filter_substr: str,
) -> dict[str, list[str]]:
    """Строит полный транзитивный граф зависимостей пакета."""
    if test_mode:
        test_data = load_test_repo(repo)
        provider: DepProvider = lambda pkg, _: {
            d: "latest" for d in test_data.get(pkg, [])
        }
    else:
        provider = lambda pkg, ver: fetch_npm_dependencies(repo, pkg, ver)
    graph: dict[str, list[str]] = {}
    dfs_collect(
        root_pkg, root_ver, provider, filter_substr, graph, set(), set()
    )
    return graph