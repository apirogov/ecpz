"""Test ecpz subcommands."""

from typer.testing import CliRunner

from ecpz.cli import app

runner = CliRunner()


prelude_header = """
#include <numbers>
#include <type_traits>

inline double tau() {
  return 2 * std::numbers::pi;
}
"""

hello_source = """
#include <print>

int main() {
  std::print("Hello world!");
}
"""


def test_run(tmp_path):
    """Test ecpz run."""
    source_path = tmp_path / "hello.cpp"
    with open(source_path, "w") as file:
        file.write(hello_source)

    result = runner.invoke(
        app,
        ["--clang-arg", "-std=c++23", "run", str(source_path)],
    )
    assert result.exit_code == 0
    assert result.stdout == "Hello world!"


def test_print(tmp_path):
    """Test ecpz print."""
    prelude_path = tmp_path / "prelude.hpp"
    with open(prelude_path, "w") as file:
        file.write(prelude_header)

    result = runner.invoke(
        app,
        [
            "--prelude",
            str(prelude_path),
            "print",
            "{:.3f} {} {} {}",
            "tau()",
            "[](){ int i=0; ++i; return i; }()",
            "std::is_same_v<int, double>",
            "std::is_same_v<int, int32_t>",
        ],
    )
    assert result.exit_code == 0
    assert result.stdout == "6.283 1 false true\n"
