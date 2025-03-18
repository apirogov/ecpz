"""Test ecpz subcommands."""

from typer.testing import CliRunner

from ecpz.cli import app, get_own_directory

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


cpp_ecpz_test_source = r"""
#include "ecpz/subprocess.hpp"

int main() {
    auto const result = subprocess::run({"ecpz", "print", "-c", "-n", "%s", "\"Hello,\\r\\n world!\""});
    if (result.output != "Hello,\r\n world!") {
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
    # check that line endings are preserved
    assert result.stdout_bytes == b"Hello,\r\n world!"
    assert result.exit_code == 0


def test_quine(tmp_path):
    """Test the ecpz quine."""
    ref_file_path = get_own_directory() / "ecpz" / "quine.cpp"
    with open(ref_file_path, "rb") as f:
        quine_code = f.read()

    source_path = tmp_path / "q.cpp"
    with open(source_path, "wb") as file:
        file.write(quine_code)

    result = runner.invoke(app, ["run", str(source_path), str(source_path)])
    assert result.stdout_bytes == quine_code
