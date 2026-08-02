import os
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Optional

from backend.app.core.config import settings


@dataclass
class SandboxResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    is_docker: bool


class DockerSandboxRunner:
    def __init__(self):
        self.docker_bin = shutil.which("docker")
        self.timeout = settings.SANDBOX_TIMEOUT_SECONDS
        self.memory_limit = settings.SANDBOX_MEMORY_LIMIT
        self.cpu_limit = settings.SANDBOX_CPU_LIMIT

    def run_isolated_command(
        self, work_dir: Path, command: str, image: str = "python:3.11-slim"
    ) -> SandboxResult:
        work_dir = work_dir.resolve()

        if self.docker_bin:
            # Build docker command with isolation flags
            docker_cmd = [
                self.docker_bin,
                "run",
                "--rm",
                "--network=none",
                f"--memory={self.memory_limit}",
                f"--memory-swap={self.memory_limit}",
                f"--cpus={self.cpu_limit}",
                "--read-only",
                "--tmpfs=/tmp:rw,noexec,nosuid,size=32m",
                "--pids-limit=32",
                "--cap-drop=ALL",
                "--user=10001:10001",
                "-v", f"{work_dir}:/code:ro",
                "-w", "/code",
                image,
                "sh", "-c", command,
            ]
            try:
                proc = subprocess.run(
                    docker_cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                return SandboxResult(
                    exit_code=proc.returncode,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    timed_out=False,
                    is_docker=True,
                )
            except subprocess.TimeoutExpired:
                return SandboxResult(
                    exit_code=124,
                    stdout="",
                    stderr=f"Execution timed out after {self.timeout} seconds",
                    timed_out=True,
                    is_docker=True,
                )
            except Exception as e:
                return SandboxResult(
                    exit_code=1,
                    stdout="",
                    stderr=str(e),
                    timed_out=False,
                    is_docker=True,
                )
        else:
            # Fallback mock sandbox for environments without running Docker daemon
            try:
                proc = subprocess.run(
                    ["sh", "-c", command],
                    cwd=work_dir,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                return SandboxResult(
                    exit_code=proc.returncode,
                    stdout=proc.stdout,
                    stderr=proc.stderr,
                    timed_out=False,
                    is_docker=False,
                )
            except subprocess.TimeoutExpired:
                return SandboxResult(
                    exit_code=124,
                    stdout="",
                    stderr=f"Execution timed out after {self.timeout} seconds",
                    timed_out=True,
                    is_docker=False,
                )


docker_sandbox_runner = DockerSandboxRunner()
