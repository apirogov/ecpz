# ecpz - **E**valuate **C**++ using **P**ython and **Z**ig

Do you need to evaluate some simple C++ code from inside your application,
and it should work cross-platform (Linux, Mac and Windows) without causing a headache?

You've seen it all, [quine-relay](https://github.com/mame/quine-relay) stopped
being amusing years ago, and you feel the itch for something new?

No problem, *easy-peasy with `ecpz`!*

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

### Creating a Quine

Usually, using I/O to let code open itself directly is forbidden and considered bad sportsmanship.
Everybody agrees that the following things are clear cases of cheating:

* reading a hard-coded string filename
* using the `argv[0]` trick to reflect back the name of the current file/executable
* reading the file using some compile- or runtime reflection capabilities of the programming language
* adding and using a special `quine` command in a custom programming language or environment

We will do none of these things. Create some source file `FILE` with the following content:

```cpp
#include "ecpz/subprocess.hpp"
int main(int i, char** a) {
    using b = std::istreambuf_iterator<char>; using c = std::string;
    auto d = [](auto e){ std::ifstream f(e, std::ios::binary); return c(b(f), b()); };
    std::vector<c> e(i+3, a[i-1]); e[0]="ecpz"; e[1]="run";
    auto f = i%2 == 0 ? subprocess::run(e).output : d(a[i-1]);
    subprocess::set_bin(); std::cout<<f;
}
```

Now run it with `ecpz run FILE FILE` and convince yourself that we do not cheat in
such despicable and reprehensible ways as the ones listed above!

<details>
  <summary>Spoiler</summary>

  Nobody ever said that we cannot just...

  * run a C++ source file through `ecpz`,
    * which uses a Python package,
      * which provides the `zig` toolchain,
        * which provides `clang`,
    * to compile and then run the program, which
      * runs its arguments through `ecpz`,
        * compiling and then running the same program, which now finally
          * prints the file passed to it as the argument

  Or, at least *I* did not get the memo that this is illegal.
  In that case I apologize for wasting your time.

  But even *if* this is still cheating -
  isn't cheating in glorious ways not also a form of *art*?

</details>

## Limitations

The following issues are fixable, i.e. only a matter of more effort and time:

* currently only synchronous execution is supported, no I/O buffering or streaming
* currently it is not possible to pipe input data into `ecpz run` to pass it as stdin

## Acknowledgements

Thanks to [sheredom](https://github.com/sheredom)
for creating [subprocess.h](https://github.com/sheredom/subprocess.h),
the only true header-only C(++) subprocess library I could find!
