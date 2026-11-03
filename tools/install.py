"""Install/uninstall lives in tools/install.ps1.
The Microsoft Store Python virtualizes writes under %APPDATA%: files would land in its private LocalCache and the
game would never see them (verified 2026-11-03). Child processes may inherit that container, so this module refuses
instead of delegating:
    powershell -NoProfile -File tools\\install.ps1 -Version 1.0.0
    powershell -NoProfile -File tools\\install.ps1 -Uninstall"""
import sys

if __name__ == '__main__':
    sys.exit(__doc__)
