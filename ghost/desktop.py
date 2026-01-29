from __future__ import annotations

import os
import sys
import threading
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets  # type: ignore
from PySide6.QtWebEngineWidgets import QWebEngineView  # type: ignore
from PySide6.QtWebEngineCore import QWebEnginePage  # type: ignore
from dotenv import load_dotenv, set_key  # type: ignore

from .assistant import GhostAssistant
from . import personalities
from .voice import Recorder, pcm16le_to_wav_bytes, make_stt_provider, make_tts_provider
import requests
import time
import threading as _threading
import uvicorn
import subprocess
from subprocess import Popen


@dataclass
class AppConfig:
    provider: Optional[str] = None
    persona: str = "destiny_ghost"


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def get_repo_root() -> Path:
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS"))  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def get_state_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    # For dev runs, keep .env in repo root
    return get_repo_root()


class FirstRunDialog(QtWidgets.QDialog):
    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Ghost Companion – First‑run Setup")
        layout = QtWidgets.QFormLayout(self)

        self.bungie_api = QtWidgets.QLineEdit(self)
        self.bungie_api.setEchoMode(QtWidgets.QLineEdit.Password)
        self.openai_key = QtWidgets.QLineEdit(self)
        self.openai_key.setEchoMode(QtWidgets.QLineEdit.Password)
        self.eleven_key = QtWidgets.QLineEdit(self)
        self.eleven_key.setEchoMode(QtWidgets.QLineEdit.Password)
        self.eleven_voice = QtWidgets.QLineEdit(self)
        self.ollama_host = QtWidgets.QLineEdit(self)
        self.ollama_host.setPlaceholderText("http://127.0.0.1:11434")

        layout.addRow("BUNGIE_API_KEY*", self.bungie_api)
        layout.addRow("OPENAI_API_KEY", self.openai_key)
        layout.addRow("ELEVEN_API_KEY", self.eleven_key)
        layout.addRow("ELEVEN_VOICE_ID", self.eleven_voice)
        layout.addRow("OLLAMA_HOST", self.ollama_host)

        hint = QtWidgets.QLabel("* Required. You can set others later in Settings.")
        hint.setStyleSheet("color: #888")
        layout.addRow(hint)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        layout.addRow(btns)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

    def values(self) -> dict[str, str]:
        return {
            "BUNGIE_API_KEY": self.bungie_api.text().strip(),
            "OPENAI_API_KEY": self.openai_key.text().strip(),
            "ELEVEN_API_KEY": self.eleven_key.text().strip(),
            "ELEVEN_VOICE_ID": self.eleven_voice.text().strip(),
            "OLLAMA_HOST": self.ollama_host.text().strip(),
        }


class BackendServer:
    def __init__(self, host: str = "127.0.0.1", port: int | None = 8000) -> None:
        self._host = host
        self._port = int(port or 8765)
        self._server: uvicorn.Server | None = None
        self._thread: _threading.Thread | None = None

    def _wait_ready(self, timeout_s: float = 60.0) -> bool:
        use_https = bool(os.getenv("SSL_CERTFILE") and os.getenv("SSL_KEYFILE"))
        scheme = "https" if use_https else "http"
        url = f"{scheme}://{self._host}:{self._port}/"
        attempts = int(timeout_s / 0.2)
        for _ in range(attempts):
            try:
                r = requests.get(url, timeout=0.3, verify=not use_https)
                if r.status_code < 500:
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    def start(self) -> None:
        # Try a small range of ports in case a previous instance is running
        candidates = [self._port + i for i in range(0, 6)]
        last_err: Exception | None = None
        for p in candidates:
            try:
                self._port = p
                self._thread = _threading.Thread(target=self._run, daemon=True)
                self._thread.start()
                if self._wait_ready(timeout_s=60.0):
                    return
            except Exception as e:
                last_err = e
        raise RuntimeError(f"Backend did not start in time on ports {candidates}: {last_err}")

    def _run(self) -> None:
        try:
            cert = os.getenv("SSL_CERTFILE")
            key = os.getenv("SSL_KEYFILE")
            if cert and key:
                config = uvicorn.Config(
                    "server:app",
                    host=self._host,
                    port=self._port,
                    reload=False,
                    log_level="info",
                    ssl_certfile=cert,
                    ssl_keyfile=key,
                )
            else:
                config = uvicorn.Config("server:app", host=self._host, port=self._port, reload=False, log_level="info")
            server = uvicorn.Server(config)
            server.install_signal_handlers = lambda: None  # type: ignore
            self._server = server
            server.run()
        except Exception:
            pass

    def stop(self) -> None:
        if self._server is not None:
            self._server.should_exit = True
        self._thread.join(timeout=5)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Ghost Companion")
        self.resize(1024, 768)

        # Load and ensure environment
        self._env_path = get_state_dir() / ".env"
        load_dotenv(self._env_path)
        self._ensure_env()

        # Decide UI mode before starting backend so env is set correctly
        url, serve_frontend = self._prepare_ui_mode()
        if serve_frontend:
            os.environ["SERVE_FRONTEND"] = "1"

        # Start backend in-process (API on chosen port)
        try:
            self._backend = BackendServer()
            self._backend.start()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Backend Error", f"Failed to start backend:\n{e}")
            raise

        # Web view + status overlay
        self.web = QWebEngineView(self)
        # Accept self-signed local TLS when using HTTPS for callback and create popups
        main_window = self
        class PermissiveWebPage(QWebEnginePage):
            def certificateError(self, error):  # type: ignore[override]
                return True

            def createWindow(self, _type):  # type: ignore[override]
                # Create a true popup window so window.close() works and window.opener is set
                dialog = QtWidgets.QDialog(main_window)
                dialog.setWindowTitle("Authentication")
                dialog.setModal(True)
                dialog.resize(640, 760)
                layout = QtWidgets.QVBoxLayout(dialog)
                view = QWebEngineView(dialog)
                layout.addWidget(view)
                page = PermissiveWebPage(view)
                view.setPage(page)
                # Close dialog when page requests close (e.g., after callback)
                def _on_window_close_requested():
                    dialog.close()
                try:
                    page.windowCloseRequested.connect(_on_window_close_requested)  # type: ignore[attr-defined]
                except Exception:
                    pass
                dialog.show()
                return page

            # Auto-grant media capture in the embedded webview so the
            # React UI can access microphone without a stuck permission prompt.
            def featurePermissionRequested(self, securityOrigin, feature):  # type: ignore[override]
                try:
                    self.setFeaturePermission(
                        securityOrigin,
                        feature,
                        QWebEnginePage.PermissionGrantedByUser,
                    )
                except Exception:
                    pass
        self.web.setPage(PermissiveWebPage(self.web))
        self.setCentralWidget(self.web)
        if serve_frontend:
            use_https = bool(os.getenv("SSL_CERTFILE") and os.getenv("SSL_KEYFILE"))
            scheme = "https" if use_https else "http"
            # Add a cache-busting query to force reload of newly built assets
            cache_bust = str(int(time.time()))
            url = f"{scheme}://{self._backend._host}:{self._backend._port}/?v={cache_bust}"
        self.web.setUrl(QtCore.QUrl(url))

        # Remove the status bar from the window (hide by default)
        try:
            bar = self.statusBar()  # lazily creates if missing
            bar.setVisible(False)
        except Exception:
            pass

        # Kick a background health check and show toast on problems
        _threading.Thread(target=self._post_start_health_check, daemon=True).start()

    # --------------- Env setup ---------------
    def _ensure_env(self) -> None:
        api_key = os.getenv("BUNGIE_API_KEY", "").strip()
        if api_key:
            return
        # Prompt first-run dialog
        dlg = FirstRunDialog(self)
        if dlg.exec() != QtWidgets.QDialog.Accepted:
            QtWidgets.QMessageBox.warning(self, "Missing API Key", "BUNGIE_API_KEY is required to use the app.")
            # Leave window open so user can quit or open dialog again later (future settings)
            return
        vals = dlg.values()
        # Require Bungie key
        if not vals.get("BUNGIE_API_KEY"):
            QtWidgets.QMessageBox.warning(self, "Missing API Key", "Please provide BUNGIE_API_KEY to continue.")
            return
        # Persist to .env and process env
        self._env_path.parent.mkdir(exist_ok=True, parents=True)
        for k, v in vals.items():
            if v:
                os.environ[k] = v
                try:
                    set_key(str(self._env_path), k, v)
                except Exception:
                    pass
        # Reload dotenv to ensure consistency
        load_dotenv(self._env_path, override=True)

    def _port_alive(self, host: str, port: int, timeout: float = 0.2) -> bool:
        try:
            r = requests.get(f"http://{host}:{port}/", timeout=timeout)
            return r.status_code < 500
        except Exception:
            return False

    def _prepare_ui_mode(self) -> tuple[str, bool]:
        """Return (url, serve_frontend) deciding between dev server and built UI.

        If a dev server is running (or requested via DESKTOP_WEB_DEV=1), use it.
        Otherwise ensure a production build exists and serve via backend.
        """
        self._dev_proc: Popen | None = None
        fe_dir = get_repo_root() / "frontend"

        # If port 3000 already alive, use it.
        if self._port_alive("127.0.0.1", 3000):
            return "http://127.0.0.1:3000/", False

        # If DESKTOP_WEB_DEV=1, attempt to start dev server
        if os.getenv("DESKTOP_WEB_DEV") == "1":
            try:
                self._dev_proc = subprocess.Popen(["npm", "start"], cwd=str(fe_dir), shell=True)
                # Wait up to 60s for dev server
                for _ in range(300):
                    if self._port_alive("127.0.0.1", 3000):
                        return "http://127.0.0.1:3000/", False
                    time.sleep(0.2)
            except FileNotFoundError:
                QtWidgets.QMessageBox.warning(self, "npm not found", "Install Node.js to use dev mode.")
            except Exception:
                pass

        # Fallback to serving built UI from backend
        self._ensure_frontend_build(auto=True)
        return "http://127.0.0.1:8765/", True

    # --------------- Health + diagnostics ---------------
    def _post_start_health_check(self) -> None:
        try:
            # Prefer explicit health endpoint
            host = getattr(self._backend, "_host", "127.0.0.1")
            port = getattr(self._backend, "_port", 8765)
            use_https = bool(os.getenv("SSL_CERTFILE") and os.getenv("SSL_KEYFILE"))
            scheme = "https" if use_https else "http"
            base = f"{scheme}://{host}:{port}"
            ok = False
            for _ in range(30):
                try:
                    r = requests.get(f"{base}/health", timeout=0.5, verify=not use_https)
                    if r.status_code == 200 and r.json().get("ok"):
                        ok = True
                        break
                except Exception:
                    pass
                time.sleep(0.5)
            if not ok:
                self._emit_warning("Backend health check failed. See logs/server.log")
                self._dump_diagnostics()
                return
            # Check auth/status endpoint presence (should be 200 even unauthenticated)
            try:
                r2 = requests.get(f"{base}/auth/status", timeout=1.0)
                if r2.status_code >= 400:
                    self._emit_warning("/auth/status returned an error. Check server routes.")
                    self._dump_diagnostics()
            except Exception:
                self._emit_warning("Failed contacting /auth/status. Check server.")
                self._dump_diagnostics()
        except Exception:
            # Best effort diagnostics only
            pass

    def _emit_warning(self, msg: str) -> None:
        # Keep the status bar hidden; use a dialog for visibility
        QtCore.QTimer.singleShot(0, lambda: QtWidgets.QMessageBox.warning(self, "Diagnostics", msg))

    def _dump_diagnostics(self) -> None:
        try:
            logs_dir = get_repo_root() / "logs"
            logs_dir.mkdir(exist_ok=True)
            out = logs_dir / "desktop_diagnostics.txt"
            parts: list[str] = []
            parts.append("Desktop diagnostics snapshot\n")
            parts.append(f"Qt version: {QtCore.qVersion()}\n")
            parts.append(f"Python: {sys.executable}\n")
            # Tail desktop bootstrap
            try:
                boot = (logs_dir / "desktop_bootstrap.log").read_text(encoding="utf-8")
                tail = "\n".join(boot.splitlines()[-200:])
                parts.append("\n--- desktop_bootstrap.log (tail) ---\n" + tail + "\n")
            except Exception:
                pass
            # Tail server log
            try:
                srv = (logs_dir / "server.log").read_text(encoding="utf-8")
                tail2 = "\n".join(srv.splitlines()[-200:])
                parts.append("\n--- server.log (tail) ---\n" + tail2 + "\n")
            except Exception:
                pass
            out.write_text("".join(parts), encoding="utf-8")
        except Exception:
            pass

    def _ensure_frontend_build(self) -> None:
        self._ensure_frontend_build(auto=False)

    def _ensure_frontend_build(self, auto: bool = False) -> None:
        repo = get_repo_root()
        fe_dir = repo / "frontend"
        build_dir = fe_dir / "build"
        if build_dir.exists():
            return
        if not auto:
            ret = QtWidgets.QMessageBox.question(
                self,
                "Build Web UI",
                "The React build wasn't found. Build it now?\n(This requires Node.js and npm)",
            )
            if ret != QtWidgets.QMessageBox.Yes:
                return
        self.statusBar().showMessage("Building frontend… this may take a minute")
        try:
            # Always prefer 'npm install' to update lockfiles if out-of-sync.
            subprocess.run(["npm", "install"], cwd=str(fe_dir), check=True, shell=True)
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(
                self,
                "npm not found",
                "Could not find Node.js/npm on PATH. Please install Node.js and try again.",
            )
            return
        except subprocess.CalledProcessError as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Install failed",
                f"`npm install` failed with exit code {e.returncode}.",
            )
            return
        try:
            subprocess.run(["npm", "run", "build"], cwd=str(fe_dir), check=True, shell=True)
            self.statusBar().showMessage("Frontend build complete", 5000)
        except subprocess.CalledProcessError as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Build failed",
                f"`npm run build` failed with exit code {e.returncode}.",
            )

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # type: ignore[override]
        try:
            self._backend.stop()
        except Exception:
            pass
        try:
            if getattr(self, "_dev_proc", None) is not None:
                self._dev_proc.terminate()
        except Exception:
            pass
        return super().closeEvent(event)


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    try:
        w = MainWindow()
        w.show()
        code = app.exec()
    except Exception as e:
        QtWidgets.QMessageBox.critical(None, "Fatal Error", str(e))
        code = 1
    sys.exit(code)


if __name__ == "__main__":
    main()
