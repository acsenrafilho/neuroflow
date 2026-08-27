# Installation

NeuroFlow is the portal (Python API + HTML UI). Neuroimaging CLIs such as FreeSurfer, FSL, and SCT stay on the **host** and are never installed by NeuroFlow. See [Host tools](host-tools.md).

## Pick your path

| You want to… | Path |
|--------------|------|
| **Use** the portal (no coding) | Download a zip from [GitHub Releases](https://github.com/acsenrafilho/neuroflow/releases/latest) — [Linux](#linux-packaged), [macOS](#macos-packaged-experimental), or [Windows](#windows-packaged) |
| **Develop** or change the code | Clone the repo on Ubuntu/Debian — [Developers (from source)](#developers-from-source) |

End users do **not** need git, Poetry, Node, or `make`.

## What you must install yourself

| Item | Who installs it |
|------|-----------------|
| NeuroFlow portal | You download the release zip (or build from source) |
| WSL2 + Ubuntu (Windows only) | You, via [Microsoft’s guide](https://learn.microsoft.com/windows/wsl/install) — NeuroFlow never auto-installs WSL |
| FreeSurfer, FSL, SCT | You, with each vendor’s official installer, on the OS where the portal runs |

There is no Docker requirement and no login in the current MVP.

## Linux packaged

1. Open the [latest release](https://github.com/acsenrafilho/neuroflow/releases/latest).
2. Download `neuroflow-<version>-linux-*.zip`.
3. Extract the archive. You should see a `neuroflow/` folder that contains the `neuroflow` executable and an `_internal/` directory. **Keep them together** — do not delete `_internal/`.
4. Make the binary executable:

   ```bash
   chmod +x neuroflow/neuroflow
   ```

5. Run:

   ```bash
   ./neuroflow/neuroflow
   ```

6. After about one second the portal opens a browser at [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Leave the terminal open while you use the app.
7. Stop with **Ctrl+C** in that terminal.

**Data:** jobs and datasets under `~/.neuroflow/jobs` and `~/.neuroflow/datasets`.

**Not this path:** `make desktop-install` is only for a from-source Poetry install on Linux, not for the release zip.

### Common failures (Linux)

| Symptom | What to check |
|---------|----------------|
| Permission denied | Run `chmod +x neuroflow/neuroflow` again. |
| Missing libraries / crash on start | Keep `_internal/` next to the binary after extract. |
| Port 8000 busy | Stop the other process using port 8000, then try again. |
| Browser did not open | Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) yourself. |

## macOS packaged (experimental)

The macOS release zip is **experimental**. Host neuroimaging tools must still be native installs where vendors support them.

1. Open the [latest release](https://github.com/acsenrafilho/neuroflow/releases/latest).
2. Download `neuroflow-<version>-macos-*.zip`.
3. Extract the archive. Keep the `neuroflow/` folder and its `_internal/` directory together.
4. Run:

   ```bash
   ./neuroflow/neuroflow
   ```

5. If Gatekeeper blocks the binary:
   - **System Settings → Privacy & Security → Open Anyway**, or
   - after extract: `xattr -dr com.apple.quarantine neuroflow`
6. A browser should open at [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Leave the terminal open.
7. Stop with **Ctrl+C**.

**Data:** `~/.neuroflow/jobs` and `~/.neuroflow/datasets`.

Install FreeSurfer, FSL, and SCT on macOS (`PATH` or `NEUROFLOW_*` overrides), then rescan — see [Host tools](host-tools.md).

## Windows packaged

On Windows, processing runs in **WSL2 Ubuntu** — not on native Windows. You click NeuroFlow, use the site in Chrome, and jobs execute inside Ubuntu. Full detail: **[Windows and WSL](windows-wsl.md)**.

**Requirements:** Windows 11 + WSL2 (primary), distro name **Ubuntu**, **x86_64** only. NeuroFlow **never** auto-installs WSL.

1. Install WSL2 + Ubuntu yourself ([Microsoft guide](https://learn.microsoft.com/windows/wsl/install)). Finish first Ubuntu launch (Linux username and password).
2. Download `neuroflow-<version>-windows-x86_64.zip` from the [latest release](https://github.com/acsenrafilho/neuroflow/releases/latest).
3. Extract the archive. Keep **`NeuroFlow.exe`**, **`_internal/`**, and **`linux-payload/`** together.
4. Double-click **`NeuroFlow.exe`**.
5. If WSL or Ubuntu is missing, follow the on-screen Microsoft link, then click again.
6. When Ubuntu is ready, the launcher copies the Linux portal into Ubuntu, starts it, and opens your browser at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).
7. Stop later with: `NeuroFlow.exe --stop` (does not run `wsl --shutdown`; does not cancel running jobs).

**SmartScreen:** unsigned builds may show “Windows protected your PC”. Choose **More info → Run anyway** when you trust the release source.

### Launcher flags

| Command | Behavior |
|---------|----------|
| `NeuroFlow.exe` | Detect WSL, start the portal (or open the browser if already up). |
| `NeuroFlow.exe --status` | Print detection state and exit. |
| `NeuroFlow.exe --stop` | Stop the Linux portal via pidfile. |
| `NeuroFlow.exe --open-wsl-docs` | Open Microsoft’s WSL install guide. |

**Data:** under the Ubuntu home (`~/.neuroflow/`), not under `C:\Users\...` as the primary store.

Install FreeSurfer, FSL, and SCT **inside Ubuntu**, then rescan — see [Host tools](host-tools.md) and [Windows and WSL](windows-wsl.md).

## After the UI loads (all OS)

1. Open [Home](http://127.0.0.1:8000/). The **Processing modules** table lists FreeSurfer, FSL, and SCT.
2. **Ready** means the CLI was found on the host where the portal runs. **Install on host** means install or fix `PATH` / env, then rescan.
3. Rescan without restarting: open [Host tools](host-tools.md) in the app and click **Rescan host tools**, or:

   ```bash
   curl -X POST http://127.0.0.1:8000/api/v1/host/rescan
   ```

4. Next: [Using the portal](using.md).

## Developers (from source)

**OS:** Ubuntu 22.04+ or Debian 12+ with `apt` (other platforms: install the toolchain yourself; `make setup` is apt-only for now).

**Toolchain** (what `make setup` can check and suggest via apt / Poetry installer):

- Python 3.10+
- [Poetry](https://python-poetry.org/)
- Node.js 18+ (frontend build)

### Install NeuroFlow from source

```bash
git clone https://github.com/acsenrafilho/neuroflow.git
cd neuroflow
make setup
```

`make setup` runs `scripts/setup.sh`:

1. Verifies apt, Python, Poetry, and Node
2. Prints suggested `apt` / Poetry / NodeSource commands when something is missing
3. Asks before running those installs (`--yes` skips the prompt; `--dry-run` prints only)
4. Creates `.env` from `.env.example` if needed
5. Runs `poetry install`, builds the frontend, and runs an informational `neuroflow scan`

```bash
./scripts/setup.sh --dry-run   # print suggestions only
./scripts/setup.sh --yes       # apply suggested system installs without prompting
```

Manual path (when the toolchain is already installed):

```bash
cp .env.example .env
make install
make frontend-build
```

`.env.example` sets `NEUROFLOW_SERVE_FRONTEND=1` so the built UI is served from the API at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

### Run (development)

```bash
make api
# or: poetry run neuroflow serve
```

Uses uvicorn with auto-reload on `127.0.0.1:8000`. Stop with **Ctrl+C**.

### Desktop / application menu (Linux, from-source only)

After `make setup`:

```bash
make desktop-install
```

This installs a NeuroFlow entry under `~/.local/share/applications/` and, when present, `~/Desktop/`. Clicking it starts the API with `--no-reload` in the background and opens the browser.

Stop a background instance:

```bash
./scripts/neuroflow-stop.sh
```

**Data (from source):** defaults are `./data/jobs` and `./data/datasets` (see `.env.example`). Packaged zips use `~/.neuroflow/` instead.

For frontend preview pitfalls, Makefile targets, and maintainer release builds, see [Development](../development.md).

## URLs

| What | URL |
|------|-----|
| Tool hub | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) |
| In-app user guide | [http://127.0.0.1:8000/help/](http://127.0.0.1:8000/help/) |
| FreeSurfer module | [http://127.0.0.1:8000/tools/freesurfer.html](http://127.0.0.1:8000/tools/freesurfer.html) |
| FSL package | [http://127.0.0.1:8000/packages/fsl.html](http://127.0.0.1:8000/packages/fsl.html) |
| SCT package | [http://127.0.0.1:8000/packages/sct.html](http://127.0.0.1:8000/packages/sct.html) |
| OpenAPI | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |

Next: [Using the portal](using.md).
