# ecpz - **E**valuate **C**++ using **P**ython and **Z**ig

Do you need to evaluate some simple C++ code from inside your application,
it should work cross-platform (Linux, Mac and Windows) without causing a headache?

*Easy-peasy with `ecpz`!*

----

This little package combines the ubiquity of Python and ingeniuity of the Zig
toolchain to give you the ability to compile C++ snippets without pain.

If you have a non-trivial project consisting of more than one source file,
you should probably configure and build it properly using e.g. [CMake](https://github.com/Kitware/CMake).

If you need an interactive C++ code execution environment (i.e. a REPL),
check out [cling](https://github.com/root-project/cling).

But if for some reason you need to produce and execute some ad-hoc throw-away
C++ snippets as a part of your workflow, `ecpz` might be just what you need!

## Usage

Install `ecpz` using `pip` or `uv` and check `ecpz --help` for all options.

In the following, the features of `ecpz` are illustrated by some examples.

### `ecpz run`

Compile and run a single source file provided either as argument or via standard input.

For example, create `hello.cpp`:

```cpp
#include <print>

int main() {
  std::println("Hello world!");
}
```

And run it:

```bash
$ cat hello.cpp | ecpz --clang-arg -std=c++23 run
Hello world!
```

### `ecpz print`

Evaluates some expressions and pretty-print them using `std::print(ln)` *(note that this automatically implies `-std=c++23`)*.

For example, create a header `prelude.hpp`:

```cpp
#include <numbers>
#include <type_traits>

inline double tau() {
  return 2 * std::numbers::pi;
}
```

And now run:

```bash
$ ecpz --prelude prelude.hpp print "{:.3f} {} {} {}" "tau()" "[](){ int i=0; ++i; return i; }()" "std::is_same_v<int, double>" "std::is_same_v<int, int32_t>"
6.283 1 false true
```

You can set the `ECPZ_PRELUDE` environment variable to the path of your custom
header to make it always included by default. Note that as usual, CLI arguments
override equivalent environment variables.

## Ideas And Roadmap

- [ ] integration into C++ using e.g. [subprocess.h](https://github.com/sheredom/subprocess.h) (i.e. compile C++ anywhere you have Python)
- [ ] Line-based and JSON batch mode (series of expressions that are evaluated and returned back)
- [ ] string processing mode (transform text/lines/tokens like awk but with a C++ function)

## Acknowledgements

Thanks to [sheredom](https://github.com/sheredom) for creating [subprocess.h](https://github.com/sheredom/subprocess.h)
