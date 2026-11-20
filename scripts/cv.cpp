// volctrl.cpp
#include <windows.h>
#include <mmdeviceapi.h>
#include <endpointvolume.h>
#include <iostream>
#include <string>

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cout << "Usage: cv [0-100|[m]ute|[u]nmute]" << std::endl;
        return 0;
    }

    std::string arg = argv[1];
    HRESULT hr;
    IMMDeviceEnumerator* pEnum = nullptr;
    IMMDevice* pDevice = nullptr;
    IAudioEndpointVolume* pVolume = nullptr;

    CoInitialize(nullptr);

    hr = CoCreateInstance(__uuidof(MMDeviceEnumerator), nullptr, CLSCTX_ALL,
                          __uuidof(IMMDeviceEnumerator), (void**)&pEnum);
    if (FAILED(hr)) return 1;

    hr = pEnum->GetDefaultAudioEndpoint(eRender, eConsole, &pDevice);
    if (FAILED(hr)) return 1;

    hr = pDevice->Activate(__uuidof(IAudioEndpointVolume),
                           CLSCTX_ALL, nullptr, (void**)&pVolume);
    if (FAILED(hr)) return 1;

    if (_stricmp(arg.c_str(), "m") == 0) {
        pVolume->SetMute(TRUE, nullptr);
    } else if (_stricmp(arg.c_str(), "u") == 0) {
        pVolume->SetMute(FALSE, nullptr);
    } else {
        try {
            float val = std::stof(arg) / 100.0f;
            if (val < 0.0f) val = 0.0f;
            if (val > 1.0f) val = 1.0f;
            pVolume->SetMasterVolumeLevelScalar(val, nullptr);
        } catch (...) {
            std::cout << "[Error] Invalid argument: " << arg << std::endl;
        }
    }

    pVolume->Release();
    pDevice->Release();
    pEnum->Release();
    CoUninitialize();
    return 0;
}
