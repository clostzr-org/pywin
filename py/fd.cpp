#include <cctype>
#include <filesystem>
#include <iostream>
#include <string>
#include <vector>

#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <shobjidl.h>

#ifdef _MSC_VER
#pragma comment(lib, "Ole32.lib")
#pragma comment(lib, "Shell32.lib")
#pragma comment(lib, "Uuid.lib")
#endif
#endif

namespace fs = std::filesystem;

enum class CliColor {
    reset,
    red,
    green,
    yellow,
    blue,
    magenta,
    cyan,
    dim
};

bool cli_colors_enabled = false;

const char *color(CliColor value) {
    if (!cli_colors_enabled) {
        return "";
    }

    switch (value) {
    case CliColor::red: return "\x1b[31m";
    case CliColor::green: return "\x1b[32m";
    case CliColor::yellow: return "\x1b[33m";
    case CliColor::blue: return "\x1b[34m";
    case CliColor::magenta: return "\x1b[35m";
    case CliColor::cyan: return "\x1b[36m";
    case CliColor::dim: return "\x1b[2m";
    case CliColor::reset: return "\x1b[0m";
    }
    return "";
}

#ifdef _WIN32
class ConsoleColors {
public:
    ConsoleColors() : output_(GetStdHandle(STD_OUTPUT_HANDLE)) {
        if (output_ != INVALID_HANDLE_VALUE &&
            GetConsoleMode(output_, &original_mode_) &&
            SetConsoleMode(output_, original_mode_ | ENABLE_VIRTUAL_TERMINAL_PROCESSING)) {
            enabled_ = true;
        }
    }

    ~ConsoleColors() {
        if (enabled_) {
            SetConsoleMode(output_, original_mode_);
        }
    }

    bool enabled() const {
        return enabled_;
    }

private:
    HANDLE output_;
    DWORD original_mode_ = 0;
    bool enabled_ = false;
};
#endif

// Reform a filename: replace spaces, filter characters.
std::string reform_name(const std::string &filename) {
    std::string result;
    const std::string SPECIAL_CHARS = R"(:\/_-[].()+)";
    for (char c : filename) {
        if (c == ' ') {
            result.push_back('_');
        } else if (std::isalnum(static_cast<unsigned char>(c)) ||
                   SPECIAL_CHARS.find(c) != std::string::npos) {
            result.push_back(c);
        }
    }
    return result;
}

#ifdef _WIN32
bool choose_target_path(bool choose_directory, fs::path &target) {
    const HRESULT init_result = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED);
    if (FAILED(init_result)) {
        std::cerr << color(CliColor::red)
                  << "Could not initialize the Windows file picker (HRESULT 0x"
                  << std::hex << static_cast<unsigned long>(init_result) << std::dec
                  << ")." << color(CliColor::reset) << "\n";
        return false;
    }

    IFileOpenDialog *dialog = nullptr;
    IShellItem *item = nullptr;
    PWSTR selected_path = nullptr;

    HRESULT hr = CoCreateInstance(
        CLSID_FileOpenDialog,
        nullptr,
        CLSCTX_INPROC_SERVER,
        IID_PPV_ARGS(&dialog));
    if (SUCCEEDED(hr)) {
        FILEOPENDIALOGOPTIONS options;
        hr = dialog->GetOptions(&options);
        if (SUCCEEDED(hr)) {
            options |= FOS_FORCEFILESYSTEM;
            if (choose_directory) {
                options |= FOS_PICKFOLDERS;
            } else {
                options |= FOS_FILEMUSTEXIST | FOS_PATHMUSTEXIST;
            }
            hr = dialog->SetOptions(options);
        }
    }
    if (SUCCEEDED(hr)) {
        hr = dialog->Show(nullptr);
    }
    if (SUCCEEDED(hr)) {
        hr = dialog->GetResult(&item);
    }
    if (SUCCEEDED(hr)) {
        hr = item->GetDisplayName(SIGDN_FILESYSPATH, &selected_path);
    }

    const bool selected = SUCCEEDED(hr);
    if (selected) {
        target = fs::path(selected_path);
    } else if (hr != HRESULT_FROM_WIN32(ERROR_CANCELLED)) {
        std::cerr << color(CliColor::red) << "The Windows file picker failed (HRESULT 0x"
                  << std::hex << static_cast<unsigned long>(hr) << std::dec
                  << ")." << color(CliColor::reset) << "\n";
    }

    if (selected_path) {
        CoTaskMemFree(selected_path);
    }
    if (item) {
        item->Release();
    }
    if (dialog) {
        dialog->Release();
    }
    CoUninitialize();
    return selected;
}

bool is_allowed_target(const fs::path &target) {
    fs::path normalized_target = fs::absolute(target).lexically_normal();
    normalized_target.make_preferred();

    const std::wstring drive = normalized_target.root_name().wstring();
    if (drive.size() != 2 ||
        CompareStringOrdinal(drive.c_str(), static_cast<int>(drive.size()),
                             L"C:", 2, TRUE) != CSTR_EQUAL) {
        return true;
    }

    fs::path one_drive_path = fs::path(LR"(C:\Users\Admin\OneDrive)").lexically_normal();
    one_drive_path.make_preferred();
    const std::wstring path_text = normalized_target.native();
    const std::wstring root_text = one_drive_path.native();
    if (path_text.size() < root_text.size() ||
        CompareStringOrdinal(path_text.data(), static_cast<int>(root_text.size()),
                             root_text.data(), static_cast<int>(root_text.size()),
                             TRUE) != CSTR_EQUAL) {
        return false;
    }

    return path_text.size() == root_text.size() ||
           path_text[root_text.size()] == L'\\' ||
           path_text[root_text.size()] == L'/';
}
#else
bool choose_target_path(bool, fs::path &) {
    std::cerr << color(CliColor::red)
              << "Interactive file selection is only available on Windows."
              << color(CliColor::reset) << "\n";
    return false;
}

bool is_allowed_target(const fs::path &) {
    return true;
}
#endif

// Process one file or the immediate contents of a directory.
void process_target(const fs::path &target, bool execute) {
    if (fs::is_regular_file(target)) {
        const auto dir = target.parent_path();
        const auto base = target.filename().string();
        const auto new_base = reform_name(base);
        if (base != new_base) {
            const auto new_path = dir / new_base;
            std::cout << color(CliColor::cyan) << "[FILE]" << color(CliColor::reset)
                      << " Old: " << color(CliColor::red) << base << color(CliColor::reset)
                      << " -> New: " << color(CliColor::green) << new_base
                      << color(CliColor::reset) << "\n";
            if (execute) {
                try {
                    fs::rename(target, new_path);
                } catch (const std::exception &e) {
                    std::cout << color(CliColor::red) << "  [ERROR] Could not rename "
                              << base << ": " << e.what() << color(CliColor::reset) << "\n";
                }
            }
        }
        return;
    }

    if (!fs::is_directory(target)) {
        return;
    }

    std::vector<fs::path> items;
    try {
        for (const auto &entry : fs::directory_iterator(target)) {
            const auto item = entry.path().filename().string();
            if (item != "$RECYCLE.BIN" && item != "System Volume Information") {
                items.push_back(entry.path());
            }
        }
    } catch (const fs::filesystem_error &e) {
        if (e.code() == std::errc::permission_denied) {
            std::cout << color(CliColor::yellow) << "Permission Denied: "
                      << target << color(CliColor::reset) << "\n";
        } else {
            std::cout << color(CliColor::red) << "[ERROR] Could not scan "
                      << target << ": " << e.what() << color(CliColor::reset) << "\n";
        }
        return;
    }

    std::cout << "\n" << color(CliColor::cyan) << "Scanning directory: "
              << target << color(CliColor::reset) << "\n";
    for (std::size_t i = 0; i < items.size(); ++i) {
        const auto &item_path = items[i];
        const auto item = item_path.filename().string();
        const auto new_base = reform_name(item);
        std::string item_index = std::to_string(i + 1);
        if (item_index.size() < 2) {
            item_index.insert(0, 2 - item_index.size(), '0');
        }

        if (item == new_base) {
            if (!execute) {
                std::cout << color(CliColor::dim) << "  [" << item_index
                          << "] Skipped (Same Name): " << item
                          << color(CliColor::reset) << "\n";
            }
            continue;
        }

        const auto new_item_path = item_path.parent_path() / new_base;
        std::cout << "  [" << item_index << "] Old: " << color(CliColor::red)
                  << item << color(CliColor::reset) << "\n"
                  << "  [" << item_index << "] New: " << color(CliColor::green)
                  << new_base << color(CliColor::reset) << "\n";
        if (execute) {
            try {
                fs::rename(item_path, new_item_path);
                std::cout << color(CliColor::green)
                          << "  ----> Renamed successfully."
                          << color(CliColor::reset) << "\n";
            } catch (const std::exception &e) {
                std::cout << color(CliColor::red) << "  [ERROR] Could not rename "
                          << item << ": " << e.what() << color(CliColor::reset) << "\n";
            }
        }
    }
}

int main(int argc, char *argv[]) {
#ifdef _WIN32
    ConsoleColors console_colors;
    cli_colors_enabled = console_colors.enabled();
#endif

    fs::path target;
    if (argc > 1) {
        target = fs::path(argv[1]);
    } else {
        bool choose_directory = true;
        std::string target_type;
        while (true) {
            std::cout << color(CliColor::yellow)
                      << "Choose target type: [f]ile or [d]irectory (default d, q to cancel): "
                      << color(CliColor::reset);
            if (!std::getline(std::cin, target_type)) {
                std::cout << "\n" << color(CliColor::yellow)
                          << "No target selected. Exiting..."
                          << color(CliColor::reset) << "\n";
                return 0;
            }
            for (auto &ch : target_type) {
                ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
            }

            if (target_type.empty() || target_type == "d" ||
                target_type == "dir" || target_type == "directory" ||
                target_type == "folder") {
                choose_directory = true;
                break;
            }
            if (target_type == "f" || target_type == "file") {
                choose_directory = false;
                break;
            }
            if (target_type == "q" || target_type == "quit" || target_type == "cancel") {
                std::cout << color(CliColor::yellow) << "No target selected. Exiting..."
                          << color(CliColor::reset) << "\n";
                return 0;
            }
            std::cout << color(CliColor::yellow)
                      << "Enter f for a file, d for a directory, or q to cancel."
                      << color(CliColor::reset) << "\n";
        }

        if (!choose_target_path(choose_directory, target)) {
            std::cout << color(CliColor::yellow) << "No target selected. Exiting..."
                      << color(CliColor::reset) << "\n";
            return 0;
        }
    }

    std::error_code error;
    target = fs::absolute(target, error).lexically_normal();
    if (error) {
        std::cout << color(CliColor::red) << "Could not resolve path: "
                  << error.message() << color(CliColor::reset) << "\n";
        return 1;
    }
    if (!fs::exists(target, error)) {
        if (error) {
            std::cout << color(CliColor::red) << "Could not access path: "
                      << error.message() << color(CliColor::reset) << "\n";
        } else {
            std::cout << color(CliColor::red) << "Path does not exist: "
                      << target << color(CliColor::reset) << "\n";
        }
        return 1;
    }
    if (!is_allowed_target(target)) {
        std::cout << color(CliColor::red) << "Skipped non-whitelisted C: path: "
                  << target << color(CliColor::reset) << "\n";
        return 1;
    }

    std::cout << "\n" << color(CliColor::magenta)
              << "--- DRY RUN: Previewing Changes ---"
              << color(CliColor::reset) << "\n";
    process_target(target, false);

    std::cout << "\n" << color(CliColor::yellow)
              << "Execute the rename operations? (yes/no): "
              << color(CliColor::reset);
    std::string confirm;
    std::getline(std::cin, confirm);
    for (auto &ch : confirm) {
        ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
    }

    if (confirm == "yes" || confirm == "y") {
        std::cout << "\n" << color(CliColor::cyan)
                  << "Executing transformations..."
                  << color(CliColor::reset) << "\n";
        process_target(target, true);
    } else {
        std::cout << "\n" << color(CliColor::yellow)
                  << "Operation cancelled. Exiting..."
                  << color(CliColor::reset) << "\n";
    }
    return 0;
}
