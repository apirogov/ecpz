#pragma once

#include <cstdio>  // FILE*, fread, fclose
#include <cstdlib> // getenv
#include <iostream>
#include <vector>
#include <stdexcept>
#include <optional>
#include <string>
#include <sstream>
#include <fstream>
#include <filesystem>

// for resolving PATH:
#ifdef _WIN32
#include <windows.h>
#define PATH_SEPARATOR ';'
#else
#include <unistd.h>
#define PATH_SEPARATOR ':'
#endif

// for forcing binary stdout/stderr:
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif

// subprocess.h copy shipped with ecpz
// (assuming its top level module dir is passed as include path):
#include "ecpz/subprocess.h"

namespace subprocess {

/// Force binary output
static void set_bin() {
#ifdef _WIN32
    _setmode(_fileno(stdout), _O_BINARY);
    _setmode(_fileno(stderr), _O_BINARY);
#endif
}

struct Result {
    int exit_code = 0;
    std::string output;
    std::string err;
};

/// Synchronously run a subprocess with given arguments and standard input and return the result.
Result run(std::vector<std::string> args, std::string const& input = "") {
    /// Split a string.
    auto const split_string = [](std::string const& str) {
        std::vector<std::string> tokens;
        std::istringstream iss(str);
        std::string token;

        while (iss >> token) {
            tokens.push_back(token);
        }

        return tokens;
    };
    // std::string::{starts,ends}_with backports (for compatibility with older standards)
    auto const starts_with = [](std::string const& str, std::string const& prefix) {
        if (prefix.size() > str.size()) return false;
        return std::equal(prefix.begin(), prefix.end(), str.begin());
    };
    auto const ends_with = [](std::string const& str, std::string const& suffix) {
        if (suffix.size() > str.size()) return false;
        return std::equal(suffix.rbegin(), suffix.rend(), str.rbegin());
    };

    /// Check whether a path is an executable.
    auto const is_executable = [](std::filesystem::path const& filepath) {
#ifdef _WIN32
        DWORD attribs = GetFileAttributes(filepath.string().c_str());
        return (attribs != INVALID_FILE_ATTRIBUTES && !(attribs & FILE_ATTRIBUTE_DIRECTORY));
#else
        return (access(filepath.string().c_str(), X_OK) == 0);
#endif
    };

    /// Try to resolve a command using the PATH environment variable.
    auto const resolve_executable = [&is_executable](std::string cmd) -> std::optional<std::string> {
        if (cmd.find('/') != std::string::npos || cmd.find('\\') != std::string::npos) {
                return (is_executable(cmd) ? std::optional(cmd) : std::nullopt); // Given path is explicit
        }
        if (char const* path_env = std::getenv("PATH")) {
            std::string path(path_env);
            std::stringstream ss(path);
            std::string token;

            while (std::getline(ss, token, PATH_SEPARATOR)) {
                auto const cmd_path = std::filesystem::path(token);
                if (auto const fullpath = cmd_path / cmd; is_executable(fullpath)) {
                    return fullpath.string();
                }
#ifdef _WIN32
                if (auto const fullpath = cmd_path / (cmd + ".exe"); is_executable(fullpath)) {
                    return fullpath.string();
                }
#endif
            }
        }
        return {};
    };

    /// Read the stdout or stderr of a completed subprocess.
    auto const read_output = [](auto const& process, bool const err=false) -> std::string {
        FILE *file = err ? subprocess_stderr(&process): subprocess_stdout(&process);

        std::string result;
        char stdout_buffer[1025];

        while (auto const bytes_read = fread(stdout_buffer, sizeof(char), 1024, file)) {
            result.append(stdout_buffer, bytes_read);
        };

        fclose(file);
        return result;
    };

    // --------

    if (args.empty()) {
        throw std::runtime_error("no command to run!");
    }

    std::vector<std::string> cmd;

    // resolve executable
    if (auto const& path = resolve_executable(args[0])) {
        auto const filepath = *path;
#ifdef _WIN32
    if (!ends_with(filepath, ".exe")) {
        // We're on Windows + given command is not an .exe (i.e. not directly executable).
        //
        // We need to figure out the correct interpreter for the script.
        //
        // Here is all the reasonable speculation we do, hoping for the best:
        //
        // * we assume it is a Python script
        // * we assume this script was properly installed, because it is in fact on PATH
        // * we assume this Python version + Windows combination ensure scripts are installed
        //   in a certain way (there are alternative variations how this actually works)
        // * we assume it is a Python script with shebang (#!) header
        // * we assume the shebang command does not contain extra arguments (just #!<something>.exe)
        // * we assume the user is in a (v)env where this script is was installed (pip install or equivalent)
        //
        // Accidentally, this could also work for other interpreters that respect shebang.
        //
        // Note that on UNIX systems, the OS respects shebang and all of this is simply not needed.
        //
        // We refuse to do this for a UNIX user who just ****ed up and calls a script with unset +x flag.
        std::string firstLine;
        std::ifstream file(filepath);
        if (!std::getline(file, firstLine)) {
            throw std::runtime_error("Could not read first line of script: " + filepath);
        }
        file.close();
        if(!starts_with(firstLine, "#!") || !ends_with(firstLine, ".exe")) {
            throw std::runtime_error("Expected #![...].exe in first line, found: " + firstLine);
        }
        // add identified interpreter
        cmd.push_back(firstLine.substr(2));
    }
#endif
    // add resolved executable or script path
    cmd.push_back(filepath);
    // add the actual args of the command
    cmd.insert(cmd.end(), args.begin() + 1, args.end());
} else {
        throw std::runtime_error("Could not resolve executable: " + args[0]);
    }

    // prepare C-compatible args
    std::vector<const char*> cCmd;
    cCmd.reserve(args.size());
    for (const auto& str : cmd) {
        cCmd.push_back(str.c_str());
    }
    cCmd.push_back(NULL);

    // run subprocess with inherited environment and return result
    struct subprocess_s process;
    int exit_code;
    int const subproc_opts = subprocess_option_inherit_environment;
    if (auto const result = subprocess_create(cCmd.data(), subproc_opts, &process); result != 0) {
        throw std::runtime_error("could not create process!");
    }
    if (auto const result = subprocess_join(&process, &exit_code); result != 0) {
        throw std::runtime_error("could not complete process execution!");
    }
    return Result {
        .exit_code = exit_code,
        .output = read_output(process),
        .err = read_output(process, true),
    };
}

}
