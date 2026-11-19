#include <iostream>
#include <string>
#include <vector>
#include <fstream>
#include <sstream>

#ifdef _WIN32
#include <windows.h>
#else
#include <cstdlib>
#endif

// Cross-platform clipboard setter
void setClipboard(const std::string &text) {
#ifdef _WIN32
    if (!OpenClipboard(nullptr)) {
        std::cerr << "Error: Unable to open clipboard.\n";
        return;
    }
    EmptyClipboard();
    HGLOBAL hGlob = GlobalAlloc(GMEM_MOVEABLE, text.size() + 1);
    if (!hGlob) {
        std::cerr << "Error: Memory allocation failed.\n";
        CloseClipboard();
        return;
    }
    memcpy(GlobalLock(hGlob), text.c_str(), text.size() + 1);
    GlobalUnlock(hGlob);
    if (!SetClipboardData(CF_TEXT, hGlob)) {
        std::cerr << "Error: Failed to set clipboard data.\n";
    }
    CloseClipboard();
    GlobalFree(hGlob);
#else
    const char *cmd =
#ifdef __APPLE__
        "pbcopy"
#else
        "xclip -selection clipboard"
#endif
    ;
    FILE *pipe = popen(cmd, "w");
    if (!pipe) {
#ifdef __APPLE__
        std::cerr << "Error: 'pbcopy' not found. Please install it.\n";
#else
        std::cerr << "Error: 'xclip' not found. Please install it (e.g., sudo apt install xclip).\n";
#endif
        return;
    }
    fwrite(text.c_str(), sizeof(char), text.size(), pipe);
    pclose(pipe);
#endif
}

// Cross-platform clipboard getter (fills output parameter)
void getClipboard(std::string &outText) {
    outText.clear();
#ifdef _WIN32
    if (!OpenClipboard(nullptr)) {
        std::cerr << "Error: Unable to open clipboard.\n";
        return;
    }
    HANDLE hData = GetClipboardData(CF_TEXT);
    if (!hData) {
        std::cerr << "Error: No text data in clipboard.\n";
        CloseClipboard();
        return;
    }
    char *pszText = static_cast<char*>(GlobalLock(hData));
    if (!pszText) {
        std::cerr << "Error: Failed to lock clipboard data.\n";
        CloseClipboard();
        return;
    }
    outText.assign(pszText);
    GlobalUnlock(hData);
    CloseClipboard();
#else
    const char *cmd =
#ifdef __APPLE__
        "pbpaste"
#else
        "xclip -selection clipboard -o"
#endif
    ;
    FILE *pipe = popen(cmd, "r");
    if (!pipe) {
#ifdef __APPLE__
        std::cerr << "Error: 'pbpaste' not found. Please install it.\n";
#else
        std::cerr << "Error: 'xclip' not found. Please install it (e.g., sudo apt install xclip).\n";
#endif
        return;
    }
    char buffer[128];
    while (fgets(buffer, sizeof(buffer), pipe)) {
        outText += buffer;
    }
    pclose(pipe);
#endif
}

int main(int argc, char *argv[]) {
    std::string content;

    if (argc > 1) {
        std::string option = argv[1];
        if (option == "-s") {
            // Collect all strings after -s
            std::ostringstream oss;
            for (int i = 2; i < argc; ++i) {
                if (i > 2) oss << " ";
                oss << argv[i];
            }
            content = oss.str();
            setClipboard(content);
        } else if (option == "-f" && argc > 2) {
            std::ifstream file(argv[2]);
            if (file) {
                std::ostringstream oss;
                oss << file.rdbuf();
                content = oss.str();
                setClipboard(content);
            } else {
                std::cerr << "Error: Cannot open file " << argv[2] << "\n";
                return 1;
            }
        } else {
            std::cerr << "Usage:\n"
                      << "  " << argv[0] << " -s <strings...>\n"
                      << "  " << argv[0] << " -f <filename>\n"
                      << "  " << argv[0] << " (no options: print clipboard)\n";
            return 1;
        }
    } else {
        // No options: print clipboard
        getClipboard(content);
        std::cout << content << "\n";
    }

    return 0;
}
