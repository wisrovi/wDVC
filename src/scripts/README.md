# DVC Data Management Scripts

This directory contains scripts to facilitate data versioning with DVC (Data Version Control), including uploading file metadata and downloading specific files and folders from remote storage (such as MinIO).

## 1. Initial Setup

Make sure you have DVC and Python dependencies installed. Python dependencies are listed in `src/scripts/requirements.txt`.

```bash
pip install -r src/scripts/requirements.txt
```

## 2. Available Scripts

### 2.1. `dvc_up.sh` (Folder Metadata Upload)

This script is used to generate a file inventory within a folder and upload its metadata to DVC.

**Usage:**

```bash
./src/scripts/upload/dvc_up.sh <path_to_folder>
```

**Example:**

```bash
./src/scripts/upload/dvc_up.sh val/Atributos
```

**Alias (optional):**
For convenience, you can create an alias in your `.bashrc` or `.zshrc`:

```bash
alias dvc_upload='./src/scripts/upload/dvc_up.sh'
```

Then, you can use it like this:

```bash
dvc_upload val/Atributos
```

**Internal Functioning:**
This script calls `files_inventory.py` to create a CSV file with the metadata of the files in the specified folder, and then uses `dvc add` and `dvc push` to version and upload this metadata.

### 2.2. `download_complete_folder.sh` (Complete Folder Download)

This script uses `dvc pull` to download a complete folder that is being versioned by DVC.

**Usage:**

```bash
./src/scripts/download/download_complete_folder.sh <folder_name>
```

**Example:**

```bash
./src/scripts/download/download_complete_folder.sh 20240220_baches
```

**Alias (optional):**
You can create an alias:

```bash
alias dvc_download_folder='./src/scripts/download/download_complete_folder.sh'
```

Then, you can use it like this:

```bash
dvc_download_folder 20240220_baches
```

### 2.3. `download_some_file.py` (Individual File Download)

This script allows downloading an individual file managed by DVC, recreating its directory structure locally.

**Usage:**

```bash
python src/scripts/download/download_some_file.py <file_path_in_dvc> [OPTIONS]
```

**Arguments:**

*   `<file_path_in_dvc>`: The path of the file within the DVC repository, relative to the `val/` folder (e.g., `20240220_baches/Baches/baches/image.jpg`).
*   `--dvc-config <path>`: Path to the DVC config file (default: `.dvc/config` in the repository root).
*   `--remote <remote_name>`: Name of the DVC remote to use (if multiple exist).
*   `--output-prefix <output_prefix>`: Directory prefix for the output (e.g., `val` to save in `val/20240220_baches/...`). By default, files are downloaded into the folder structure relative to the current location.

**Example:**

```bash
python src/scripts/download/download_some_file.py "20240220_baches/Baches/baches/baches2024-02-20-10h40m22s943.xml"
```

**Example with output prefix (recommended if running from the root and you want to save in `val/`):**

```bash
python src/scripts/download/download_some_file.py "20240220_baches/Baches/baches/baches2024-02-20-10h40m22s943.xml" --output-prefix val
```

**Alias (optional):**
You can create an alias for this script:

```bash
alias dvc_download_file='python /app/src/scripts/download/download_some_file.py'
```

Then, you can use it like this:

```bash
dvc_download_file "20240220_baches/Baches/baches/baches2024-02-20-10h40m22s943.xml" --output-prefix val
```

**Important Note on Paths:**
The `download_some_file.py` script expects the file path (`<file_path_in_dvc>`) to be relative to the `val/` folder within the DVC repository. Internally, the script adds the `val/` prefix to construct the full path that DVC needs.

## 3. Improvement Recommendations

Here are some recommendations to make these scripts even more robust and easier to maintain:

*   **Centralized Configuration**: Consider using a configuration file (YAML, TOML) to define DVC remotes, common paths, or prefixes, instead of hardcoding them or passing them as arguments repeatedly.
*   **Automated Testing**: 
    *   **Python**: Implement unit tests with `pytest` for `files_inventory.py` and `download_some_file.py`.
    *   **Shell**: Use tools like `shellcheck` for static analysis and frameworks like `bats-core` for integration testing of Bash scripts.
*   **Dependency Management**: Ensure that `src/scripts/requirements.txt` lists *all* Python dependencies for *all* scripts.
*   **Additional Documentation**: Maintain an updated `README.md` in this directory (`src/scripts/`) explaining the purpose of each script, its arguments, usage examples, and any recommended aliases.
*   **Explicit `python3` Usage**: Although `python` usually points to `python3` on modern systems, explicitly using `python3` in Bash scripts ensures compatibility.
*   **DVC Error Handling**: Although the scripts already have error handling, more specific logic could be added for different types of DVC failures (e.g., incorrect credentials, file not found on remote).