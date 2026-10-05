"""Verify Codex's real MCP initialization/tool inventory without an AI inference call."""

import json
import queue
import shutil
import subprocess
import threading
import time


def main():
    codex = shutil.which("codex")
    if not codex:
        raise RuntimeError("Install Codex CLI and run connect-agent.ps1 -Codex")
    process = subprocess.Popen(
        [codex, "app-server", "--stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
    )
    messages = queue.Queue()

    def reader():
        for line in process.stdout:
            try:
                messages.put(json.loads(line))
            except json.JSONDecodeError:
                continue

    threading.Thread(target=reader, daemon=True).start()

    def request(identifier, method, params):
        process.stdin.write(json.dumps({"id": identifier, "method": method, "params": params}) + "\n")
        process.stdin.flush()
        deadline = time.monotonic() + 55
        while time.monotonic() < deadline:
            try:
                message = messages.get(timeout=1)
            except queue.Empty:
                continue
            if message.get("id") == identifier:
                if "error" in message:
                    raise RuntimeError(str(message["error"]))
                return message["result"]
        raise TimeoutError("Codex MCP initialization timed out")

    try:
        request(
            1,
            "initialize",
            {
                "clientInfo": {"name": "mustang-verification", "version": "0.1.0"},
                "capabilities": {"experimentalApi": True},
            },
        )
        process.stdin.write('{"method":"initialized"}\n')
        process.stdin.flush()
        result = request(2, "mcpServerStatus/list", {"limit": 100, "detail": "toolsAndAuthOnly"})
        servers = result.get("data", [])
        mustang = next((s for s in servers if s.get("name") == "mustang-tone"), None)
        if not mustang or len(mustang.get("tools", {})) < 15:
            raise RuntimeError("Mustang MCP tool inventory was not initialized in Codex")
        print(f"Codex initialized Mustang MCP: {len(mustang['tools'])} tools")
    finally:
        process.terminate()
        process.wait(timeout=10)


if __name__ == "__main__":
    main()
