# Deployment Notes - Environment Configuration

## Problem Solved

The application was attempting to write to `/mnt/user-data/outputs/` which:
- Is a Linux/container-specific path
- Does not exist on macOS
- Caused "Read-only file system" errors

## Solution Implemented

Created an **intelligent environment detection system** that automatically adapts to:
- **Local Development** (macOS/Linux/Windows)
- **Docker Containers**
- **Google Cloud Run**

### New Configuration Module

**File:** `config.py`

**Features:**
- Auto-detects runtime environment
- Creates appropriate output directories
- Platform-agnostic paths
- Zero configuration required

**Detection Logic:**
1. Cloud Run: Checks for `K_SERVICE` environment variable
2. Docker: Checks for `/.dockerenv` or docker in cgroup
3. Local: Uses project directory for outputs

### Output Paths

| Environment | Output Directory |
|------------|------------------|
| Local Development | `./outputs/` (project directory) |
| Docker | `/mnt/user-data/outputs/` |
| Cloud Run | `/mnt/user-data/outputs/` |

## Files Modified

1. **`config.py`** (NEW)
   - Environment detection
   - Dynamic path configuration
   - Logging for transparency

2. **`main.py`**
   - Imports `get_status_file_path` and `ENV_CONFIG`
   - Uses dynamic paths for status files
   - Logs environment configuration on startup

3. **`document_generator.py`**
   - Imports `get_output_dir`
   - Uses dynamic paths for saving reports
   - Removed hardcoded `/mnt/` path

4. **`web_app.py`**
   - Imports `get_output_dir`
   - Uses dynamic paths for download endpoint
   - Removed hardcoded `/mnt/` path

## Benefits

### Cross-Platform Compatibility
Works seamlessly on macOS, Linux, Windows without code changes.

### Cloud-Ready
Maintains compatibility with Docker and Cloud Run deployments.

### Developer-Friendly
Local development uses intuitive `./outputs/` directory in project folder.

### Zero Configuration
Automatically detects and configures itself.

### Backward Compatible
Cloud/Docker deployments continue working exactly as before.

## Testing Performed

✅ Environment detection working correctly
✅ Local output directory created successfully
✅ Document generation working
✅ Web application serving files correctly
✅ Download endpoint returning 200 OK

## Usage

No changes required for developers. The system automatically:
1. Detects the environment on startup
2. Creates appropriate directories
3. Uses correct paths for all operations

## Logging

The application now logs environment information on startup:

```
INFO:config:Environment detected: Local environment on Darwin | Output: /Users/mac-54/Desktop/mro-intelligence/outputs
INFO:main:Initialized with: Local environment on Darwin | Output: /Users/mac-54/Desktop/mro-intelligence/outputs
```

This helps verify correct configuration and troubleshoot any issues.

## Future Enhancements

The config system can be extended to support:
- Custom output directories via environment variables
- Different paths for different file types
- Temporary file cleanup
- Cloud storage integration (S3, GCS)
