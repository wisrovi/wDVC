# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-08-14

### Fixed
- **DVC Cache Corruption**: Fixed a critical bug in `Dockerfile.worker` that caused DVC to corrupt the cache during image builds. The `dvc gc --workspace -f` command was removed from the build phase since it was aggressively deleting cache entries before volumes were mounted, leading to "md5 mismatch" and "broken data" errors when users attempted to `dvc pull` via bind mounts.
- **Cross-device Link Errors**: Enforced `dvc config cache.type copy` inside the worker image to prevent failed hardlink creations between the internal OverlayFS and the external bind-mounted volumes. Large directories (e.g. `20250403_Dataset.202504.0031`) now download flawlessly without 0-byte or broken files.

### Changed
- **Worker Image Build Process**: Restructured `Dockerfile.worker` to cleanly import the internal `.dvc` state and Git configurations without polluting the runtime cache state.

## [1.0.0] - Initial Release

### Added
- Enterprise-grade Data Versioning Platform integration with Redis.
- DVC automated pipelines for MinIO (S3) datasets.
- Worker orchestration via `docker-compose.worker.yaml`.
- Initial Gradio UI architecture and deployment scripts.
