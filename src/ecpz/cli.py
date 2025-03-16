"""Implementation of ecpz CLI commands."""

import importlib.resources as pkg_resources
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Optional

import typer
from dotenv import load_dotenv

load_dotenv()


@dataclass
class CommonArgs:
    """Command line args shared across subcommands."""

    clang_args: list[str]
    prelude: Path
    print_source: bool
    verbose: bool


def read_input(file_path: Optional[Path] = None) -> str:
    """Read input from given file path or stdin."""
    if file_path is None or str(file_path) == "-":
        content = sys.stdin.read()
    else:
        with open(file_path, "r") as file:
            content = file.read()

    return content


def get_own_directory():
    """Return directory to be passed as include directory.

    Allows to use e.g. `#include "ecpz/subprocess.hpp"`
    """
    return pkg_resources.files(__package__).resolve().parent


def compile_and_run(code: str, args: CommonArgs) -> str:
    """Compile and run the given test code inside a temporary directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        base_name = "code"
        source_file_path = temp_dir_path / f"{base_name}.cpp"
        binary_file_path = temp_dir_path / f"{base_name}.exe"

        with open(source_file_path, "w") as temp_file:
            temp_file.write(code)

        compile_cmd = [sys.executable, "-m", "zig", "c++"]
        compile_cmd += args.clang_args
        compile_cmd += [f"-I{get_own_directory()}"]
        compile_cmd += ["-o", f"{binary_file_path}", f"{source_file_path}"]

        if args.verbose:
            typer.echo(" ".join(compile_cmd))
            typer.echo("-" * 32)

        # NOTE: exit code is not forwarded correctly, so we check if the executable exists
        subprocess.check_call(compile_cmd, cwd=temp_dir)  # noqa: S603
        if not binary_file_path.is_file():
            raise typer.Exit(1)  # compilation failed (error is automatically printed)

        try:
            result = subprocess.run(  # noqa: S603
                [binary_file_path],
                cwd=temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            result.check_returncode()
        except subprocess.CalledProcessError as e:
            typer.echo(e.stdout, nl=False)
            typer.echo(e.stderr, err=True, nl=False)
            raise typer.Exit(e.returncode) from e

    return result.stdout


app = typer.Typer()


@app.callback()
def common(
    ctx: typer.Context,
    clang_arg: Annotated[
        Optional[list[str]],
        typer.Option(help="Additional arguments to pass through to the compiler"),
    ] = None,
    prelude: Annotated[
        Optional[Path],
        typer.Option(
            exists=True,
            readable=True,
            file_okay=True,
            dir_okay=False,
            help="Additional code to be added to the input (i.e. default include).",
            envvar="ECPZ_PRELUDE",
        ),
    ] = None,
    print_source: Annotated[
        bool, typer.Option(help="Print compiled source code")
    ] = False,
    verbose: Annotated[bool, typer.Option(help="Print compilation command")] = False,
):
    """Process common CLI arguments."""
    clang_arg = clang_arg or []
    ctx.ensure_object(dict)
    ctx.obj = CommonArgs(clang_arg, prelude, print_source, verbose)


@app.command()
def run(
    ctx: typer.Context,
    code: Path = typer.Argument(None),
):
    """Compile the provided C++ code (file or stdin) and run the resulting executable."""
    print(compile_and_run(read_input(code), ctx.obj), end="")


@app.command(name="print")
def std_print(
    ctx: typer.Context,
    fmt: str,
    exprs: list[str],
    no_newline: Annotated[
        bool,
        typer.Option(
            "-n", "--no-newline", help="Do not add a newline to the end of the output."
        ),
    ] = False,
):
    """Evaluate C++23 expressions and print result using std::print(ln)."""
    ctx.obj.clang_args += ["-std=c++23"]
    input_code = "#include <print>\n"
    if ctx.obj.prelude:
        input_code += f'#include "{Path(ctx.obj.prelude).resolve()}"\n'

    args = ",\n\t\t".join([f'"{fmt}"'] + exprs)
    input_code += "\nint main(){\n"
    input_code += f"\tstd::print{'' if no_newline else 'ln'}(\n\t\t{args}\n\t);"
    input_code += "\n}\n"

    if ctx.obj.print_source:
        typer.echo(input_code)
        typer.echo("-" * 32)

    print(compile_and_run(input_code, ctx.obj), end="")
