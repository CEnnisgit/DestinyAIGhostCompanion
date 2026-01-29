"""Automate the Ghost Companion startup workflow across platforms."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path
from typing import Iterable, Protocol, Sequence

import requests
from dotenv import load_dotenv, set_key
from dataclasses import dataclass, field

def is_frozen() -> bool:
    """Return True when running from a PyInstaller bundle."""

    return getattr(sys, "frozen", False)


def get_repo_root() -> Path:
    """Resolve the directory that holds the bundled application files."""

    if is_frozen():
        return Path(getattr(sys, "_MEIPASS"))  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


def get_state_dir() -> Path:
    """Return a writable directory for launcher state (e.g., the .env file)."""

    if is_frozen():
        return Path(sys.executable).resolve().parent
    return get_repo_root()


REPO_ROOT = get_repo_root()
STATE_DIR = get_state_dir()
FRONTEND_DIR = REPO_ROOT / "frontend"
ENV_FILE = STATE_DIR / ".env"
REQUIREMENTS_FILE = REPO_ROOT / "requirements.txt"

OLLAMA_HOST_DEFAULT = "http://127.0.0.1:11434"
OLLAMA_TAGS_ENDPOINT = "/api/tags"
XAI_API_KEY = "xai-6FCSOQjhzB0RVqFQiiRHEJv6ALoprXw8MlEfmwNwiwegFtrLaK8p2r7Fde1ZotjrifxSRtRbKl5Lo7WK"
OLLAMA_MODEL = "phi3"

REQUIRED_ENV_VARS = {
    "BUNGIE_API_KEY",
    "BUNGIE_CLIENT_ID",
    "BUNGIE_CLIENT_SECRET",
    "BUNGIE_REDIRECT_URI",
    "GHOST_TOKEN_KEY",
    "OLLAMA_HOST",
}

ENV_DEFAULTS = {
    "OLLAMA_HOST": OLLAMA_HOST_DEFAULT,
}


class LaunchError(RuntimeError):
    """Raised when launcher preparation or startup fails."""


class ManagedHandle(Protocol):
    label: str

    def poll(self) -> int | None:
        ...

    def stop(self) -> None:
        ...

    def join(self) -> None:
        ...


@dataclass
class SubprocessHandle:
    label: str
    process: subprocess.Popen[str]
    _threads: list[threading.Thread] = field(default_factory=list)

    def attach_streams(self) -> None:
        if self.process.stdout:
            thread = threading.Thread(
                target=stream_pipe,
                args=(self.process.stdout, self.label),
                daemon=True,
            )
            thread.start()
            self._threads.append(thread)
        if self.process.stderr:
            thread = threading.Thread(
                target=stream_pipe,
                args=(self.process.stderr, f"{self.label} err"),
                daemon=True,
            )
            thread.start()
            self._threads.append(thread)

    def poll(self) -> int | None:
        return self.process.poll()

    def stop(self) -> None:
        if self.process.poll() is None:
            print(f"[launcher] Terminating {self.label} (pid={self.process.pid})")
            self.process.terminate()

    def join(self) -> None:
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
        for thread in self._threads:
            thread.join(timeout=1)


class UvicornHandle:
    """Manage an in-process Uvicorn server when running from a bundled exe."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.label = "backend"
        self._host = host
        self._port = port
        self._exit_code: int | None = None
        self._server: "uvicorn.Server" | None = None  # type: ignore[name-defined]
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._stopped = threading.Event()

    def start(self) -> None:
        self._thread.start()
        if not wait_for_http_service(f"http://{self._host}:{self._port}/"):
            self.stop()
            self.join()
            raise LaunchError("Failed to confirm backend startup.")

    def _run(self) -> None:
        try:
            import uvicorn

            config = uvicorn.Config("server:app", host=self._host, port=self._port, reload=False)
            server = uvicorn.Server(config)
            server.install_signal_handlers = lambda: None  # type: ignore[assignment]
            self._server = server
            server.run()
            self._exit_code = 0
        except Exception:
            traceback.print_exc()
            self._exit_code = 1
        finally:
            self._stopped.set()

    def poll(self) -> int | None:
        if self._thread.is_alive():
            return None
        return self._exit_code or 0

    def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        self._stopped.wait(timeout=10)

    def join(self) -> None:
        self._thread.join(timeout=10)

def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--backend-only",
        action="store_true",
        help="Start only the FastAPI backend.",
    )
    group.add_argument(
        "--frontend-only",
        action="store_true",
        help="Start only the React frontend dev server.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def run_subprocess(command: Sequence[str], *, cwd: Path | None = None) -> None:
    try:
        subprocess.run(command, cwd=cwd, check=True, env=os.environ, shell=True)
    except FileNotFoundError as exc:
        raise LaunchError(f"Command not found: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        raise LaunchError(
            f"Command '{' '.join(command)}' failed with exit code {exc.returncode}"
        ) from exc


def start_process(
    name: str,
    command: Sequence[str],
    *,
    cwd: Path | None = None,
) -> SubprocessHandle:
    try:
        proc = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ,
            shell=True,
        )
    except FileNotFoundError as exc:
        raise LaunchError(f"Failed to start {name}: {command[0]} not found") from exc
    print(f"[launcher] Started {name} (pid={proc.pid}) -> {' '.join(command)}")
    handle = SubprocessHandle(name, proc)
    handle.attach_streams()
    return handle


def start_localtunnel(port: int) -> tuple[SubprocessHandle, str]:
    """Start a localtunnel process for the given port and return (handle, url).

    Requires Node/npm to be installed. Uses npx to avoid global install.
    """
    print("[launcher] Starting localtunnel for HTTPS callback...")
    # Use --yes to auto-install the package without an interactive prompt
    cmd = ["npx", "--yes", "localtunnel@latest", "--port", str(port)]
    proc = subprocess.Popen(
        cmd,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=os.environ,
        shell=True,
    )
    handle = SubprocessHandle("tunnel", proc)

    # Read lines until an https URL appears
    url = ""
    assert proc.stdout is not None
    for _ in range(120):  # ~60s max
        line = proc.stdout.readline()
        if not line:
            break
        print(f"[tunnel] {line.rstrip()}")
        line = line.strip()
        # Localtunnel usually prints the URL on a line containing 'https://'
        if "https://" in line:
            # Pick the first https substring
            from urllib.parse import urlparse

            tokens = [tok for tok in line.split() if tok.startswith("https://")]
            if tokens:
                candidate = tokens[0]
                # Basic validation
                parsed = urlparse(candidate)
                if parsed.scheme == "https" and parsed.netloc:
                    url = candidate
                    break
    if not url:
        raise LaunchError("Failed to obtain tunnel URL from localtunnel output.")
    return handle, url


def start_backend_handle() -> ManagedHandle:
    if is_frozen():
        print("[launcher] Starting backend inside bundled runtime...")
        handle = UvicornHandle()
        handle.start()
        return handle

    # Build uvicorn command; avoid --reload when running with SSL on Windows to
    # prevent protocol mismatches between reloader parent/child processes.
    cert = os.getenv("SSL_CERTFILE")
    key = os.getenv("SSL_KEYFILE")
    use_ssl = bool(cert and key)

    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "server:app",
    ]

    if not use_ssl:
        backend_cmd.append("--reload")
    else:
        backend_cmd += ["--ssl-certfile", cert, "--ssl-keyfile", key]  # type: ignore[list-item]
    return start_process("backend", backend_cmd, cwd=REPO_ROOT)


def pip_install_requirements() -> None:
    if is_frozen():
        print("[launcher] Running from packaged executable; skipping pip install.")
        return

    if not REQUIREMENTS_FILE.exists():
        print("[launcher] requirements.txt not found; skipping dependency install.")
        return

    print("[launcher] Ensuring Python dependencies are installed...")
    run_subprocess(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)]
    )


def ensure_node_tools_available() -> None:
    node_path = shutil.which("node")
    npm_path = shutil.which("npm")
    if node_path and npm_path:
        return

    if not node_path:
        print("[launcher] Node.js executable not found in PATH.")
    if not npm_path:
        print("[launcher] npm executable not found in PATH.")

    raise LaunchError(
        "Node.js and npm are required. Install the latest LTS release from "
        "https://nodejs.org/ and ensure the tools are on your PATH."
    )


def ensure_frontend_dependencies() -> None:
    if is_frozen():
        print("[launcher] Packaged assets include frontend dependencies.")
        return

    node_modules = FRONTEND_DIR / "node_modules"
    if node_modules.exists():
        return
    print("[launcher] Installing frontend dependencies (npm install)...")
    run_subprocess(["npm", "install"], cwd=FRONTEND_DIR)


def ensure_ollama_cli_available() -> None:
    if shutil.which("ollama"):
        return

    raise LaunchError(
        "The 'ollama' CLI was not found. Install Ollama from "
        "https://ollama.com/download and ensure the executable is on your PATH."
    )


def maybe_start_ollama_service() -> SubprocessHandle | None:
    if is_ollama_running():
        print("[launcher] Ollama service already running.")
        return None

    print("[launcher] Starting 'ollama serve' in the background...")
    handle = start_process("ollama", ["ollama", "serve"], cwd=REPO_ROOT)
    host = os.getenv("OLLAMA_HOST", OLLAMA_HOST_DEFAULT).rstrip("/")
    if not wait_for_http_service(host + OLLAMA_TAGS_ENDPOINT):
        raise LaunchError("Failed to verify Ollama service startup.")
    return handle


def is_ollama_running() -> bool:
    host = os.getenv("OLLAMA_HOST", OLLAMA_HOST_DEFAULT).rstrip("/")
    try:
        response = requests.get(host + OLLAMA_TAGS_ENDPOINT, timeout=2)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def wait_for_http_service(url: str, timeout: float = 30.0, interval: float = 1.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code < 500:
                return True
        except requests.RequestException:
            pass
        time.sleep(interval)
    return False


def pull_ollama_model(model: str) -> None:
    print(f"[launcher] Ensuring Ollama model '{model}' is available...")
    try:
        run_subprocess(["ollama", "pull", model])
    except LaunchError as exc:
        raise LaunchError(f"Failed to pull Ollama model '{model}': {exc}") from exc


def load_and_prompt_env() -> None:
    if not ENV_FILE.exists():
        print(f"[launcher] No .env file found. Creating {ENV_FILE}...")
        ENV_FILE.touch()

    print("[launcher] Checking required environment variables...")
    load_dotenv(ENV_FILE)
    updated = False

    for key in sorted(REQUIRED_ENV_VARS):
        current = os.getenv(key)
        if current:
            continue

        default_hint = ENV_DEFAULTS.get(key)
        if default_hint:
            print(
                f"[launcher] {key} is missing; press Enter to use default "
                f"'{default_hint}'."
            )
        prompt = f"Enter value for {key}: "
        value = input(prompt).strip()
        if not value:
            if default_hint:
                value = default_hint
                print(f"[launcher] Using default value for {key}: {value}")
            else:
                raise LaunchError(
                    f"Environment variable {key} is required. Please rerun the launcher."
                )
        set_key(str(ENV_FILE), key, value)
        os.environ[key] = value
        updated = True

    if updated:
        print(f"[launcher] Updated environment variables saved to {ENV_FILE}.")
    else:
        print("[launcher] All required environment variables are present.")


def stream_pipe(pipe: subprocess.PIPE, label: str) -> None:  # type: ignore[type-arg]
    for line in iter(pipe.readline, ""):
        if not line:
            break
        print(f"[{label}] {line.rstrip()}")


def monitor_handles(handles: Sequence[ManagedHandle]) -> None:
    try:
        while True:
            for handle in handles:
                ret = handle.poll()
                if ret is not None:
                    raise LaunchError(f"{handle.label} exited with status {ret}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[launcher] Caught KeyboardInterrupt. Shutting down...")
    finally:
        stop_handles(handles)


def stop_handles(handles: Sequence[ManagedHandle]) -> None:
    for handle in handles:
        handle.stop()
    for handle in handles:
        handle.join()


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)

    start_backend = not args.frontend_only
    start_frontend = not args.backend_only

    if is_frozen():
        start_frontend = False

    pip_install_requirements()
    load_and_prompt_env()

    # Set additional environment variables for subprocesses
    os.environ["OLLAMA_MODEL"] = OLLAMA_MODEL
    os.environ["XAI_API_KEY"] = XAI_API_KEY

    if start_frontend:
        ensure_node_tools_available()
        ensure_frontend_dependencies()

    ollama_handle: ManagedHandle | None = None
    if start_backend:
        ensure_ollama_cli_available()
        ollama_handle = maybe_start_ollama_service()
        pull_ollama_model(OLLAMA_MODEL)

    handles: list[ManagedHandle] = []

    if ollama_handle is not None:
        handles.append(ollama_handle)

    # Optionally start an HTTPS tunnel for OAuth callback
    tunnel_handle: ManagedHandle | None = None
    if os.getenv("USE_TUNNEL", "").lower() in {"1", "true", "yes"}:
        try:
            tunnel_handle, tunnel_url = start_localtunnel(8000)
            handles.append(tunnel_handle)
            # Persist and export a tunnel-based redirect
            from dotenv import set_key

            redirect = f"{tunnel_url.rstrip('/')}/oauth/callback"
            set_key(str(ENV_FILE), "BUNGIE_REDIRECT_URI", redirect)
            os.environ["BUNGIE_REDIRECT_URI"] = redirect
            print(f"[launcher] Using tunneled redirect: {redirect}")
        except LaunchError as exc:
            print(f"[launcher] Tunnel setup failed: {exc}")

    if start_backend:
        handles.append(start_backend_handle())

    if start_frontend:
        # Open the frontend URL
        webbrowser.open("http://localhost:3000")

    if start_frontend:
        frontend_cmd = ["npm", "start"]
        handles.append(start_process("frontend", frontend_cmd, cwd=FRONTEND_DIR))

    if not handles:
        print("[launcher] Nothing to start (both backend and frontend disabled).")
        return 0

    try:
        monitor_handles(handles)
    except LaunchError as exc:
        print(f"[launcher] {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
