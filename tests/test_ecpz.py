"""Test ecpz subcommands."""

from typer.testing import CliRunner

from ecpz.cli import app

runner = CliRunner()


hello_source = """
#include <print>

int main() {
  std::print("Hello, world!");
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
    assert result.stdout == "Hello, world!"


prelude_header = """
#include <numbers>
#include <type_traits>

inline double tau() {
  return 2 * std::numbers::pi;
}
"""


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


cpp_ecpz_test_source = """
#include "ecpz/subprocess.hpp"

int main() {
    auto const result = subprocess::run({"ecpz", "print", "-n", "{}", "\\\"Hello, world!\\\""});
    if (result.output != "Hello, world!") {
        std::cerr << "Unexpected result string: '" << result.output << "'" << std::endl;;
        return 1;
    }
    std::cout << result.output;
    std::cerr << result.err;
    return result.exit_code;
}
"""


def test_call_from_cpp(tmp_path):
    """Test using ecpz from inside C++."""
    source_path = tmp_path / "cpp_ecpz.cpp"
    with open(source_path, "w") as file:
        file.write(cpp_ecpz_test_source)

    result = runner.invoke(
        app,
        ["--clang-arg", "-std=c++23", "run", str(source_path)],
    )
    # FIXME: on Mac, the result has a trailing \x01
    assert result.stdout == "Hello, world!"
    assert result.exit_code == 0
