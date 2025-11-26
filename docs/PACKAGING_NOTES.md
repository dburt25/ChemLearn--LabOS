# LabOS Packaging Notes

These notes outline how LabOS could be packaged when we are ready to distribute it beyond source installs. They describe target artifacts, layout expectations, and release hygiene so that future packaging work can slot into the existing repository with minimal disruption.

## Packaging targets
- **Source distribution (`sdist`)**: Publish a tarball via PyPI to support reproducible builds and downstream vendors that want to inspect the source. Keep generated data out of the archive and rely on existing JSON fixture patterns for demos.
- **Binary wheel (`manylinux` + platform-specific wheels as needed)**: Provide wheels for quick installs in teaching and demo environments. Avoid compiled extensions so wheels stay pure-Python; if native code is ever introduced, build per-architecture wheels with proper auditwheel repair.
- **Container image (optional)**: Produce a minimal Python base image that installs the released wheel and exposes the Streamlit control panel via an entrypoint. Keep the image dependency-light and rely on mounted volumes for `data/` so the container remains stateless by default.

## Repository layout expectations
- **Single top-level package**: Ensure importable modules remain under `labos/` with console scripts defined via `entry_points` so that `labos` CLI stays consistent between editable installs and packaged builds.
- **Data directories**: Continue to treat `data/` as runtime state. Packaging scripts should exclude it from sdists and wheels (e.g., via `MANIFEST.in` and package data rules) while providing `labos init` to recreate folders after install.
- **CLI wiring**: Keep `app.py` and Streamlit assets adjacent to the package, but wire CLI entry points so they can locate templates and registry defaults without relying on CWD. Prefer `importlib.resources` for any bundled examples.

## Versioning and metadata
- **Semantic versioning**: Follow MAJOR.MINOR.PATCH, with pre-release tags (e.g., `-alpha`, `-beta`) during early drops. Align the version in `pyproject.toml` with module metadata exposed via `labos.__version__`.
- **License and classifiers**: Ensure PyPI metadata declares the license, supported Python versions (3.10+), intended audience (education/research), and OS independence while wheels remain pure-Python.
- **Long description**: Reuse the repository README for PyPI descriptions, ensuring relative links are converted to absolute URLs during build time.

## Build and release pipeline
- **Isolated builds**: Use `python -m build` or equivalent isolated build steps. Lock build requirements in `pyproject.toml` without leaking optional dev dependencies into the runtime install.
- **Signing and integrity**: Upload artifacts with provenance metadata and consider GPG-signed tags for releases. Include checksums alongside downloads for offline verification.
- **Smoke tests**: After building wheels and sdists, run `pip install dist/labos-<version>-py3-none-any.whl` in a fresh virtual environment and execute `labos --help`, `labos init`, and a sample module run to validate packaging completeness.

## Backward compatibility and migration
- **Config stability**: Preserve JSON schema shapes for registries and audit logs between minor versions; document breaking changes and provide migration scripts when necessary.
- **Plugin ecosystem**: If external modules are distributed separately, reserve an `entry_points` group (e.g., `labos.modules`) for discoverable plugins and document compatibility policies across versions.
- **State upgrades**: For changes to on-disk state, provide idempotent upgrade helpers that transform existing `data/` contents rather than requiring manual cleanup.

## What remains to be done
- Draft `pyproject.toml` packaging metadata (classifiers, optional dependencies, entry points) and tighten manifest rules to exclude runtime state.
- Add release automation (CI workflows) that build, test, sign, and publish artifacts to PyPI and a container registry.
- Document support boundaries (Python versions, OS targets) and expected installation footprints for classroom and research environments.
