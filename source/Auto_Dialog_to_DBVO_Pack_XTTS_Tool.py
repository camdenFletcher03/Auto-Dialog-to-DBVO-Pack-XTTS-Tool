import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import re
from pathlib import Path
import subprocess
import sys
import requests
import threading
import csv
import json
import wave
import audioop
import time
import string
from concurrent.futures import ThreadPoolExecutor, as_completed

def install_deps():
    packages = ["requests"]
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            print(f"Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

install_deps()

class AutoDialogToDBVOTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Auto Dialog to DBVO Pack XTTS Tool")
        self.root.geometry("1480x980")
        self.progress_var = tk.DoubleVar()
        self.create_widgets()
        
        # Start scanning for LipGenerator.exe on startup automatically
        threading.Thread(target=self.scan_for_lip_gen, daemon=True).start()

    def create_widgets(self):
        tk.Label(self.root, text="Auto Dialog to DBVO Pack XTTS Tool", 
                 font=("Arial", 18, "bold")).pack(pady=15)

        # CSV Input
        frame = tk.Frame(self.root)
        frame.pack(fill="x", padx=25, pady=12)
        tk.Label(frame, text="xEdit CSV File:").pack(side="left")
        self.csv_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.csv_var, width=95).pack(side="left", padx=8, fill="x", expand=True)
        tk.Button(frame, text="Browse", command=self.browse_csv).pack(side="right")

        # Lip Tool Path Input
        lip_exe_frame = tk.Frame(self.root)
        lip_exe_frame.pack(fill="x", padx=25, pady=8)
        tk.Label(lip_exe_frame, text="LipGenerator.exe Path:").pack(side="left")
        self.lip_exe_var = tk.StringVar(value="")
        tk.Entry(lip_exe_frame, textvariable=self.lip_exe_var, width=95).pack(side="left", padx=8, fill="x", expand=True)
        tk.Button(lip_exe_frame, text="Browse", command=self.browse_lip_exe).pack(side="right")

        # Fuz Tool Path Input
        fuz_exe_frame = tk.Frame(self.root)
        fuz_exe_frame.pack(fill="x", padx=25, pady=8)
        tk.Label(fuz_exe_frame, text="BmlFuzEncode.exe Path:").pack(side="left")
        self.fuz_exe_var = tk.StringVar(value=str(Path(__file__).parent / "BmlFuzEncode.exe"))
        tk.Entry(fuz_exe_frame, textvariable=self.fuz_exe_var, width=95).pack(side="left", padx=8, fill="x", expand=True)
        tk.Button(fuz_exe_frame, text="Browse", command=self.browse_fuz_exe).pack(side="right")

        # XTTS / Voice Settings UI elements
        xtts = tk.LabelFrame(self.root, text="XTTS Settings", padx=12, pady=10)
        
        tk.Label(xtts, text="Server URL:").grid(row=0, column=0, sticky="w")
        self.xtts_url = tk.StringVar(value="http://127.0.0.1:8020")
        tk.Entry(xtts, textvariable=self.xtts_url, width=48).grid(row=0, column=1, padx=8)

        tk.Label(xtts, text="Voice:").grid(row=1, column=0, sticky="w")
        self.voice_var = tk.StringVar(value="default")
        self.voice_combo = ttk.Combobox(xtts, textvariable=self.voice_var, width=45)
        self.voice_combo.grid(row=1, column=1, padx=8)
        tk.Button(xtts, text="Refresh Voices", command=self.refresh_voices).grid(row=1, column=2, padx=5)

        # Output Folder UI Elements
        out_frame = tk.Frame(self.root)
        out_frame.pack(fill="x", padx=25, pady=8)
        tk.Label(out_frame, text="Output Folder:").pack(side="left")
        
        initial_folder_name = f"({self.voice_var.get().strip()}) Voicepack"
        self.output_var = tk.StringVar(value=str(Path.cwd() / initial_folder_name))
        
        tk.Entry(out_frame, textvariable=self.output_var, width=95).pack(side="left", padx=8, fill="x", expand=True)
        tk.Button(out_frame, text="Browse", command=self.browse_output).pack(side="right")

        self.voice_var.trace_add("write", self.update_default_output_dir)
        xtts.pack(fill="x", padx=25, pady=10)

        # Controls
        ctrl = tk.Frame(self.root)
        ctrl.pack(pady=10)
        tk.Button(ctrl, text="Load & Preview", bg="#4444aa", fg="white", command=self.load_csv_preview).pack(side="left", padx=8)
        tk.Button(ctrl, text="Generate + Package for DBVO", bg="#006400", fg="white", font=("Arial", 12, "bold"), 
                  command=self.start_thread).pack(side="left", padx=12)

        # Progress
        prog_frame = tk.Frame(self.root)
        prog_frame.pack(fill="x", padx=25, pady=8)
        ttk.Progressbar(prog_frame, variable=self.progress_var, maximum=100).pack(fill="x", padx=5)
        self.progress_label = tk.Label(prog_frame, text="Ready")
        self.progress_label.pack()

        # Log
        tk.Label(self.root, text="Log:").pack(anchor="w", padx=25)
        self.log_text = scrolledtext.ScrolledText(self.root, height=24, font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True, padx=25, pady=8)

        self.log("Ready. Automatically packages for DBVO after generation.")

    def scan_for_lip_gen(self):
        self.log("Scanning drives for LipGenerator.exe...")
        target_rel_path = os.path.join("SteamLibrary", "steamapps", "common", "Skyrim Special Edition", "Tools", "LipGen", "LipGenerator", "LipGenerator.exe")
        
        # Generates ['C', 'D', 'E', ..., 'Z']
        available_drives = [d for d in string.ascii_uppercase if os.path.exists(f"{d}:")]
        
        for drive in available_drives:
            potential_path = Path(f"{drive}:/") / target_rel_path
            if potential_path.exists():
                self.lip_exe_var.set(str(potential_path))
                self.log(f"Auto-Detected LipGenerator at: {potential_path}")
                return
        
        self.log("LipGenerator.exe not found automatically. Please locate it manually.")

    def update_default_output_dir(self, *args):
        voicename = self.voice_var.get().strip() or "default"
        current_path = Path(self.output_var.get())
        # Safely updates the directory name dynamically while keeping user's chosen root
        parent_dir = current_path.parent
        self.output_var.set(str(parent_dir / f"({voicename}) Voicepack"))

    def log(self, msg: str):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def browse_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            self.csv_var.set(path)
            self.log(f"Selected: {path}")

    def browse_lip_exe(self):
        path = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
        if path:
            self.lip_exe_var.set(path)
            self.log(f"Selected Lip Tool: {path}")

    def browse_fuz_exe(self):
        path = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe")])
        if path:
            self.fuz_exe_var.set(path)
            self.log(f"Selected Fuz Tool: {path}")

    def browse_output(self):
        voicename = self.voice_var.get().strip() or "default"
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            # Sets the exact folder path cleanly
            target_folder = Path(path) / f"({voicename}) Voicepack"
            self.output_var.set(str(target_folder))
            self.log(f"Output folder set to: {target_folder}")

    def refresh_voices(self):
        try:
            r = requests.get(f"{self.xtts_url.get().rstrip('/')}/speakers", timeout=8)
            r.raise_for_status()
            speakers = r.json()
            voices = [s.get("name", s) for s in speakers] if isinstance(speakers, list) else list(speakers.keys())
            self.voice_combo['values'] = voices or ["default"]
            if voices:
                self.voice_var.set(voices[0])
            self.log(f"Loaded {len(voices)} voices.")
        except Exception as e:
            self.log(f"Voice refresh failed: {e}")

    def load_csv_preview(self):
        csv_path = self.csv_var.get().strip()
        if not csv_path or not os.path.isfile(csv_path):
            messagebox.showerror("Error", "Select CSV first.")
            return
        try:
            lines = self.load_xedit_csv(Path(csv_path))
            self.log(f"Preview: Found {len(lines)} player dialogue lines.")
        except Exception as e:
            self.log(f"Preview error: {e}")

    def load_xedit_csv(self, csv_path: Path):
        player_lines = []
        try:
            with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    record_type = (row.get("RecordType") or "").strip().upper()
                    text = row.get("Text")
                    if record_type == "DIAL" and text:
                        player_lines.append(text)
        except Exception as e:
            self.log(f"CSV parse error: {e}")
        return player_lines

    def fix_and_save_wav(self, raw_audio: bytes, target_path: Path):
        import struct
        temp_path = target_path.with_suffix(".tmp.wav")
        try:
            fmt_code = struct.unpack("<H", raw_audio[20:22])[0]
            
            if fmt_code == 3:
                n_channels = struct.unpack("<H", raw_audio[22:24])[0]
                frame_rate = struct.unpack("<I", raw_audio[24:28])[0]
                bits_per_sample = struct.unpack("<H", raw_audio[34:36])[0]
                
                idx = 12
                while idx < len(raw_audio) - 8:
                    chunk_header = raw_audio[idx:idx+4]
                    chunk_size = struct.unpack("<I", raw_audio[idx+4:idx+8])[0]
                    if chunk_header == b"data":
                        raw_data = raw_audio[idx+8:idx+8+chunk_size]
                        break
                    idx += 8 + chunk_size
                else:
                    raise ValueError("Could not find data chunk in float WAV.")
                
                if bits_per_sample == 32:
                    num_samples = len(raw_data) // 4
                    floats = struct.unpack(f"<{num_samples}f", raw_data)
                    
                    int16_samples = []
                    for f in floats:
                        val = int(f * 32767.0)
                        if val > 32767: val = 32767
                        elif val < -32768: val = -32768
                        int16_samples.append(val)
                    
                    data = struct.pack(f"<{len(int16_samples)}h", *int16_samples)
                    sample_width = 2
                else:
                    raise ValueError(f"Unsupported float bit-depth: {bits_per_sample}")
            else:
                with open(temp_path, "wb") as f:
                    f.write(raw_audio)
                    
                with wave.open(str(temp_path), "rb") as src_wav:
                    n_channels = src_wav.getnchannels()
                    sample_width = src_wav.getsampwidth()
                    frame_rate = src_wav.getframerate()
                    n_frames = src_wav.getnframes()
                    data = src_wav.readframes(n_frames)
            
            if n_channels > 1:
                data = audioop.tomono(data, sample_width, 1, 1)
                
            if sample_width != 2:
                data, _ = audioop.lin2lin(data, sample_width, 2)
                sample_width = 2
                
            if frame_rate != 44100:
                state = None
                data, state = audioop.ratecv(data, sample_width, 1, frame_rate, 44100, state)

            with wave.open(str(target_path), "wb") as dst_wav:
                dst_wav.setnchannels(1)
                dst_wav.setsampwidth(2)
                dst_wav.setframerate(44100)
                dst_wav.writeframes(data)
                
            return True
        except Exception as e:
            self.log(f"WAV conversion failure: {e}")
            return False
        finally:
            if temp_path.exists():
                os.remove(temp_path)

    def generate_lip(self, wav_path: Path, text: str):
        lip_exe = Path(self.lip_exe_var.get().strip())
        if not lip_exe.exists():
            self.log(f"LipGenerator.exe not found at: {lip_exe}")
            return False
        
        safe_text = text.replace("'", "")
        cmd = [str(lip_exe), str(wav_path), safe_text]
        lip_path = wav_path.with_suffix(".lip")

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
                if lip_path.exists():
                    return True
                
                self.log(f"  -> LipGen failed (Attempt {attempt}/{max_retries}) for: {wav_path.name}")
            except subprocess.TimeoutExpired:
                self.log(f"  -> LipGen timed out (Attempt {attempt}/{max_retries}) for: {wav_path.name}")
            except Exception as e:
                self.log(f"  -> LipGen error (Attempt {attempt}/{max_retries}): {e}")
            
            if attempt < max_retries:
                time.sleep(0.4)
                
        return lip_path.exists()

    def convert_to_fuz(self, wav_path: Path, lip_path: Path, fuz_path: Path):
        try:
            bml_path = Path(self.fuz_exe_var.get().strip())
            if not bml_path.exists():
                self.log(f"BmlFuzEncode.exe not found at: {bml_path}")
                return False
            
            cmd = [str(bml_path), str(fuz_path), str(wav_path), str(lip_path)]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
            return result.returncode == 0
        except Exception as e:
            self.log(f"Fuz conversion error: {e}")
            return False

    def download_audio_only(self, line, wav_dir):
        cleaned_text = re.sub(r' ', '_', line)
        cleaned_text = re.sub(r'[\\/:*?"<>|]', '', cleaned_text)
        safe_name = cleaned_text[:120] if len(cleaned_text) > 120 else cleaned_text
        wav_path = wav_dir / f"{safe_name}.wav"

        try:
            payload = {
                "text": line,
                "voice_id": self.voice_var.get(),
                "speaker_wav": f"{self.voice_var.get()}.wav",
                "language": "en"
            }
            r = requests.post(f"{self.xtts_url.get().rstrip('/')}/tts_to_audio/", json=payload, timeout=25)
            if r.status_code == 200:
                if self.fix_and_save_wav(r.content, wav_path):
                    return True, line, wav_path, safe_name
        except Exception:
            pass
        return False, line, None, safe_name

    def start_thread(self):
        threading.Thread(target=self.start_extraction, daemon=True).start()

    def start_extraction(self):
        csv_path_str = self.csv_var.get().strip()
        if not csv_path_str or not os.path.isfile(csv_path_str):
            messagebox.showerror("Error", "Select a valid xEdit CSV file.")
            return

        voicename = self.voice_var.get().strip() or "default"
        output_dir = Path(self.output_var.get().strip())

        output_dir.mkdir(parents=True, exist_ok=True)
        wav_dir = output_dir / "WAV_Reference"
        wav_dir.mkdir(exist_ok=True)
        
        fuz_dir = output_dir / "ae" / "Sound" / "DBVO" / voicename
        fuz_dir.mkdir(parents=True, exist_ok=True)

        json_dir = output_dir / "common" / "DragonbornVoiceOver" / "voice_packs"
        json_dir.mkdir(parents=True, exist_ok=True)

        json_data = {
            "voice_pack_name": f"{voicename} Voice",
            "voice_pack_id": f"{voicename}"
        }
        json_file_path = json_dir / f"{voicename}_voice_pack.json"
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)

        fomod_dir = output_dir / "fomod"
        fomod_dir.mkdir(parents=True, exist_ok=True)

        info_xml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<fomod>
  <Name>{voicename} DBVO Voice Pack</Name>
  <Author>Auto XTTS Voice Pack Tool by Zpc44</Author>
  <Version>1.0</Version>
</fomod>"""

        module_config_content = f"""<?xml version="1.0" encoding="utf-8"?>
<config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">
  <moduleName>{voicename}</moduleName>
  <requiredInstallFiles>
    <folder source="ae" destination="" priority="0" />
    <folder source="common" destination="" priority="0" />
  </requiredInstallFiles>
  <installSteps order="Explicit">
    <installStep name="Voice Packs">
      <optionalFileGroups order="Explicit">
        <group name="Select voice pack" type="SelectAny">
          <plugins order="Explicit">
            <plugin name="{voicename}">
              <description>Voice files.</description>
              <files>
                <folder source="ae" destination="" priority="0" />
              </files>
              <typeDescriptor><type name="Optional" /></typeDescriptor>
            </plugin>
          </plugins>
        </group>
      </optionalFileGroups>
    </installStep>
  </installSteps>
</config>"""

        with open(fomod_dir / "info.xml", "w", encoding="utf-8") as f:
            f.write(info_xml_content)
            
        with open(fomod_dir / "ModuleConfig.xml", "w", encoding="utf-8") as f:
            f.write(module_config_content)

        self.log("Detecting Player Dialogue via DIAL records...")
        player_lines = self.load_xedit_csv(Path(csv_path_str))

        if not player_lines:
            messagebox.showwarning("No Lines", "No player dialogue lines found.")
            return

        deduped = sorted(set(player_lines))
        source_name = Path(csv_path_str).stem

        txt_path = output_dir / f"{source_name}_player_lines.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"Player Dialogue Lines - {source_name}\n\n")
            for i, line in enumerate(deduped, 1):
                f.write(f"{i:04d}. {line}\n\n")

        self.log(f"Extracted {len(deduped)} player dialogue lines.")

        sync_pipeline_queue = []
        
        if deduped:
            self.log(f"\n[Phase 1/2] Generating audio files on 4 threads...")
            self.progress_var.set(0)

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(self.download_audio_only, line, wav_dir) for line in deduped]
                for idx, future in enumerate(as_completed(futures)):
                    success, orig_line, wav_path, safe_name = future.result()
                    if success:
                        sync_pipeline_queue.append((orig_line, wav_path, safe_name))
                    
                    progress = ((idx + 1) / len(deduped)) * 50
                    self.root.after(0, lambda p=progress, n=safe_name: (
                        self.progress_var.set(p),
                        self.progress_label.config(text=f"Audio Gen: {int(p*2)}% — {n}")
                    ))

        total_audio = 0
        if sync_pipeline_queue:
            self.log(f"\n[Phase 2/2] Processing Lip & FUZ generation sequentially on a single thread...")
            total_tasks = len(sync_pipeline_queue)
            
            for idx, (orig_line, wav_path, safe_name) in enumerate(sync_pipeline_queue):
                lip_path = wav_path.with_suffix(".lip")
                fuz_path = fuz_dir / f"{safe_name}.fuz"
                
                if self.generate_lip(wav_path, orig_line):
                    if self.convert_to_fuz(wav_path, lip_path, fuz_path):
                        total_audio += 1
                else:
                    self.log(f"CRITICAL: Dropped file generation after 3 retries for: {safe_name}")

                progress = 50 + (((idx + 1) / total_tasks) * 50)
                self.root.after(0, lambda p=progress, n=safe_name: (
                    self.progress_var.set(p),
                    self.progress_label.config(text=f"Lip & FUZ Sync: {int((p-50)*2)}% — {n}")
                ))

        self.log(f"\nFINISHED!")
        self.log(f"Player dialogue lines parsed: {len(deduped)}")
        self.log(f"Successful .fuz voice mappings: {total_audio}")
        self.log(f"FOMOD configuration completed successfully.")
        self.log(f"Full DBVO pack constructed at: {output_dir.absolute()}")
        messagebox.showinfo("Success", f"DBVO Voice Pack Ready!\nLines Parsed: {len(deduped)}\nFUZ Packed: {total_audio}\n\nZip the folder and install as mod.")

if __name__ == "__main__":
    app = AutoDialogToDBVOTool()
    app.root.mainloop()