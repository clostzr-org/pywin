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
        std::cerr << "Could not initialize the Windows file picker (HRESULT 0x"
                  << std::hex << static_cast<unsigned long>(init_result) << std::dec << ").\n";
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
        std::cerr << "The Windows file picker failed (HRESULT 0x"
                  << std::hex << static_cast<unsigned long>(hr) << std::dec << ").\n";
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
    std::cerr << "Interactive file selection is only available on Windows.\n";
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
            std::cout << "[FILE] Old: " << base << " -> New: " << new_base << "\n";
            if (execute) {
                try {
                    fs::rename(target, new_path);
                } catch (const std::exception &e) {
                    std::cout << "  [ERROR] Could not rename " << base << ": " << e.what() << "\n";
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
            std::cout << "Permission Denied: " << target << "\n";
        } else {
            std::cout << "[ERROR] Could not scan " << target << ": " << e.what() << "\n";
        }
        return;
    }

    std::cout << "\nScanning directory: " << target << "\n";
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
                std::cout << "  [" << item_index << "] Skipped (Same Name): " << item << "\n";
            }
            continue;
        }

        const auto new_item_path = item_path.parent_path() / new_base;
        std::cout << "  [" << item_index << "] Old: " << item << "\n"
                  << "  [" << item_index << "] New: " << new_base << "\n";
        if (execute) {
            try {
                fs::rename(item_path, new_item_path);
                std::cout << "  ----> Renamed successfully.\n";
            } catch (const std::exception &e) {
                std::cout << "  [ERROR] Could not rename " << item << ": " << e.what() << "\n";
            }
        }
    }
}

int main(int argc, char *argv[]) {
    fs::path target;
    if (argc > 1) {
        target = fs::path(argv[1]);
    } else {
        bool choose_directory = true;
        std::string target_type;
        while (true) {
            std::cout << "Choose target type: [f]ile or [d]irectory (default d, q to cancel): ";
            if (!std::getline(std::cin, target_type)) {
                std::cout << "\nNo target selected. Exiting...\n";
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
                std::cout << "No target selected. Exiting...\n";
                return 0;
            }
            std::cout << "Enter f for a file, d for a directory, or q to cancel.\n";
        }

        if (!choose_target_path(choose_directory, target)) {
            std::cout << "No target selected. Exiting...\n";
            return 0;
        }
    }

    std::error_code error;
    target = fs::absolute(target, error).lexically_normal();
    if (error) {
        std::cout << "Could not resolve path: " << error.message() << "\n";
        return 1;
    }
    if (!fs::exists(target, error)) {
        if (error) {
            std::cout << "Could not access path: " << error.message() << "\n";
        } else {
            std::cout << "Path does not exist: " << target << "\n";
        }
        return 1;
    }
    if (!is_allowed_target(target)) {
        std::cout << "Skipped non-whitelisted C: path: " << target << "\n";
        return 1;
    }

    std::cout << "\n--- DRY RUN: Previewing Changes ---\n";
    process_target(target, false);

    std::cout << "\nExecute the rename operations? (yes/no): ";
    std::string confirm;
    std::getline(std::cin, confirm);
    for (auto &ch : confirm) {
        ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
    }

    if (confirm == "yes" || confirm == "y") {
        std::cout << "\nExecuting transformations...\n";
        process_target(target, true);
    } else {
        std::cout << "\nOperation cancelled. Exiting...\n";
    }
    return 0;
}
