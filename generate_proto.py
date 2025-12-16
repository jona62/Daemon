#!/usr/bin/env python3
"""Generate protobuf files."""

import subprocess
import sys
from pathlib import Path


def main():
    proto_dir = Path("task_daemon/proto")
    proto_file = proto_dir / "task_daemon.proto"

    print(f"Generating protobuf code from {proto_file}...")

    cmd = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"--proto_path={proto_dir}",
        f"--python_out={proto_dir}",
        f"--grpc_python_out={proto_dir}",
        str(proto_file),
    ]

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("✓ Protobuf code generated successfully")

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
