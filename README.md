# Auto Dialog to DBVO Pack XTTS Tool

An automated Python GUI utility that converts exported Skyrim player dialogue text into fully packaged **Dragonborn Voice Over (DBVO)** voice packs using local **XTTS** servers. It parses xEdit CSV data, synthesizes audio, builds lip-sync files, packages everything into `.fuz` format, and outputs a ready-to-install **FOMOD** mod structure.

## Features

* **xEdit CSV Parsing:** Automatically extracts dialogue text (`DIAL` records) from exported sheets.
* **XTTS Server Integration:** Connects seamlessly to a local XTTS API instance to fetch audio samples using specialized speaker profiles.
* **Automated Audio Conversion:** Converts multi-channel or 32-bit float audio outputs down to standard mono 16-bit PCM, 44.1kHz `.wav` configurations automatically.
* **Auto-Sourced Tools:** Automatically scans local drives on launch for your Steam installation of `LipGenerator.exe` to save setup steps.
* **Multi-Threaded Pipelines:** Processes voice downloads in parallel across 4 concurrent threads, then hands files off to a safe, sequential pipeline for local lip sync and `.fuz` assembly.
* **Text Patch Customization:** Supports optional find-and-replace dictionaries to fix voice-line pronunciation or structural problems on the fly.
* **Complete FOMOD Assembly:** Creates dynamic folder setups containing matching `.json` manifests, internal Skyrim sound structures (`ae/Sound/DBVO/...`), and valid XML installers for instant Mod Organizer 2 or Vortex integration.

## Installation & Setup

1. **Clone the Repo:**
```bash
git clone https://github.com/camdenFletcher03/Auto-Dialog-to-DBVO-Pack-XTTS-Tool.git
cd Auto-Dialog-to-DBVO-Pack-XTTS-Tool

```


2. **Prerequisites:**
* Python 3.8+ installed.
* A working local **XTTS server** (https://github.com/daswer123/xtts-api-server) instance running (default address: `http://127.0.0.1:8020`).
* **BmlFuzEncode.exe** placed in the root directory of this script.
* **LipGenerator.exe** (typically found inside the Skyrim Special Edition Creation Kit tools directory).


3. **Run the App:**
```bash
python Auto_Dialog_to_DBVO_Pack_XTTS_Tool.py

```


*The script will self-install any missing dependencies (like `requests`) on its first launch.*


### How to Export the Required CSV from xEdit

Before using the tool, you need to extract the player dialogue data from your desired mod list using **xEdit (SSEEdit)** and the provided Pascal script (`Export_Player_Dialog.pas`).

### 1. Install the Script

1. Copy the contents of `Export_Player_Dialog.pas`.
2. Navigate to your xEdit installation folder (e.g., where `SSEEdit.exe` lives).
3. Open the `Edit Scripts` folder and create a new file named `Export_Player_Dialog.pas`. Paste the code inside and save.

### 2. Run the Export in xEdit

1. Launch **xEdit** with your complete mod load order loaded.
2. In the left-hand navigation pane, find the plugin(s) you want to generate a voice pack for (e.g., `Skyrim.esm` or a custom quest mod).
3. Right-click the folder, and select **Apply Script**.
4. In the script dropdown menu, search for **`Export_Player_Dialog`** and click **OK**.

### 3. Save the Output

1. The script will run and automatically filter out non-vocalized text, debug logs, action strings, and system placeholders.
2. Once processing finishes, a save prompt will appear.
3. Save the file as `Player_Dialog.csv` somewhere accessible.
4. Feed this exact `.csv` file into the **Auto Dialog to DBVO Pack XTTS Tool** GUI to begin generating your voice lines!

## How to Use

1. **Paths & Setup:** Locate your xEdit exported CSV file and verify that the paths to `LipGenerator.exe` and `BmlFuzEncode.exe` are assigned.
2. **Choose Voice:** Click **Refresh Voices** to populate your XTTS speaker profiles, choose your voice, and optionally click **Play Voice Sample** to confirm output quality.
3. **Run:** Click **Generate + Package for DBVO**.
4. **Install:** Once the completion pop-up shows, navigate to your specified output path, compress the directory into a `.zip` or `.7z` file, and install it directly via your mod manager.
