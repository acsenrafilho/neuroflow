"""PyInstaller entrypoint for the Windows WSL launcher."""

from neuroflow.windows_launcher.app import main

if __name__ == "__main__":
    raise SystemExit(main())
