"""Package entrypoint for the LabOS CLI.

This shim imports the shared CLI implementation from ``labos.cli.app`` so that
``python -m labos`` and module imports use the same command definitions.
"""

from labos.cli.app import build_parser, main

__all__ = ["build_parser", "main"]

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
