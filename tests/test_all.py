"""Модульные тесты для всех пяти этапов практической работы."""

import unittest
from src.cli import ConfigError, format_config_kv, parse_and_validate
from src.collector import clean_semver
from src.graph import build_dependency_graph, find_reverse_dependencies
from src.visualizer import generate_mermaid


class TestCliStage1(unittest.TestCase):
    """Тестирование конфигурации и обработки ошибок (Этап 1)."""

    def test_valid_cli_args(self) -> None:
        """Проверяет успешный разбор валидных параметров."""
        cfg = parse_and_validate(
            [
                "--package",
                "express",
                "--repo",
                "https://registry.npmjs.org",
                "--version",
                "4.18.2",
                "--filter",
                "debug",
                "--stage",
                "1",
            ]
        )
        output = format_config_kv(cfg)
        self.assertIn("package=express", output)
        self.assertIn("version=4.18.2", output)

    def test_invalid_url_raises(self) -> None:
        """Проверяет ошибку при некорректном URL репозитория."""
        with self.assertRaises(ConfigError):
            parse_and_validate(
                ["--package", "express", "--repo", "not_a_url"]
            )

    def test_invalid_test_package_name(self) -> None:
        """Проверяет требование больших латинских букв в тесте."""
        with self.assertRaises(ConfigError):
            parse_and_validate(
                [
                    "--package",
                    "lowercase",
                    "--repo",
                    "tests/data/linear_repo.json",
                    "--test-mode",
                ]
            )


class TestGraphStages3And4(unittest.TestCase):
    """Тестирование DFS, циклов, фильтрации и обратных связей."""

    def test_cycle_and_filter_handling(self) -> None:
        """Проверяет обход циклов и фильтрацию пакета Z (Этап 3)."""
        graph = build_dependency_graph(
            "A",
            "1.0.0",
            "tests/data/cycle_repo.json",
            True,
            "Z",
        )
        self.assertIn("A", graph)
        self.assertIn("B", graph)
        self.assertIn("C", graph)
        self.assertIn("D", graph)
        self.assertNotIn("Z", graph)
        self.assertNotIn("Z", graph["A"])

    def test_reverse_dependencies(self) -> None:
        """Проверяет поиск обратных зависимостей (Этап 4)."""
        repo = {
            "A": ["B", "C"],
            "B": ["D"],
            "C": ["D"],
            "D": [],
        }
        rev = find_reverse_dependencies("D", repo, "")
        self.assertEqual(rev, ["A", "B", "C"])


class TestVisualizerStage5(unittest.TestCase):
    """Тестирование генерации диаграмм Mermaid (Этап 5)."""

    def test_mermaid_generation(self) -> None:
        """Проверяет корректность синтаксиса Mermaid."""
        graph = {"A": ["B"], "B": []}
        code = generate_mermaid(graph)
        self.assertTrue(code.startswith("graph TD"))
        self.assertIn("node_A --> node_B", code)

    def test_semver_cleaner(self) -> None:
        """Проверяет очистку версий npm."""
        self.assertEqual(clean_semver("^4.18.2"), "4.18.2")
        self.assertEqual(clean_semver("*"), "latest")


if __name__ == "__main__":
    unittest.main()