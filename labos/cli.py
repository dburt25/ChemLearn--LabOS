"""Command line interface for ChemLearn LabOS.

This module delegates to ``labos.cli.app`` so both the package entrypoint and
the top-level module share a single implementation.
"""

from labos.cli.app import build_parser, main

__all__ = ["build_parser", "main"]

if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
