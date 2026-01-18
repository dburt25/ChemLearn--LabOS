from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class IngestResult:
    input_path: Path
    input_hash: str
    output_dir: Path
