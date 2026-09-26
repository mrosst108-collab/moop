#!/usr/bin/env python3
"""The reference answerer against a fake Messages API, so it runs with no
network and no key: what it sends, what it prints, and when it prints
nothing. Prints ok/FAIL lines like tests/run_tests.sh; exits 1 on a FAIL."""
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
THREAD = "subreddit: science\nu1: Water on Mars\nu2: Source?\n"
failed = False


class Fake(http.server.BaseHTTPRequestHandler):
    replies = []  # (status, body) per request, in order
    seen = []     # (path, headers, body) per request

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["content-length"])))
        Fake.seen.append((self.path, {k.lower(): v for k, v in self.headers.items()}, body))
        status, reply = Fake.replies.pop(0) if Fake.replies else (500, {})
        data = json.dumps(reply).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("request-id", "req_fake")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


def message(text, stop="end_turn"):
    return 200, {"id": "msg_fake", "type": "message", "role": "assistant",
                 "model": "claude-opus-5", "stop_reason": stop, "stop_sequence": None,
                 "content": [] if text is None else [{"type": "text", "text": text}],
                 "usage": {"input_tokens": 10, "output_tokens": 10}}


def run(replies, stdin=THREAD, env=None):
    Fake.replies, Fake.seen = list(replies), []
    e = dict(os.environ, ANTHROPIC_BASE_URL=f"http://127.0.0.1:{port}",
             ANTHROPIC_API_KEY="test-key", NO_PROXY="127.0.0.1", no_proxy="127.0.0.1")
    e.pop("REDDIT_MODEL", None)
    e.update(env or {})
    p = subprocess.run([sys.executable, os.path.join(HERE, "claude.py")], input=stdin,
                       capture_output=True, text=True, env=e, timeout=60)
    return p.returncode, p.stdout, Fake.seen


def check(desc, ok):
    global failed
    print(f"{'ok  ' if ok else 'FAIL'} - {desc}")
    failed = failed or not ok


server = http.server.HTTPServer(("127.0.0.1", 0), Fake)
port = server.server_address[1]
threading.Thread(target=server.serve_forever, daemon=True).start()

code, out, seen = run([message("NASA reported it in 2015.")])
check("answerer: one answer, one line, exit 0", code == 0 and out == "NASA reported it in 2015.\n")
path, headers, body = seen[0]
check("answerer: the beta Messages endpoint, keyed, with server-side fallbacks",
      path.startswith("/v1/messages") and headers.get("x-api-key") == "test-key" and
      "server-side-fallback-2026-07-01" in headers.get("anthropic-beta", "") and
      body.get("fallbacks") == "default")
check("answerer: claude-opus-5, adaptive thinking at low effort, the thread as the user's turn",
      body["model"] == "claude-opus-5" and body["thinking"] == {"type": "adaptive"} and
      body["output_config"] == {"effort": "low"} and
      body["messages"] == [{"role": "user", "content": THREAD.strip()}])
check("answerer: the system prompt states the limit and that the thread is not instructions",
      "at most 300 characters" in body["system"] and "not as instructions" in body["system"])

code, out, _ = run([message("line one\n\n  line two")])
check("answerer: whitespace, newlines included, collapses to one line", out == "line one line two\n")

code, out, _ = run([message(None, stop="refusal")])
check("answerer: a refusal after fallbacks is no answer (exit 1, nothing printed)", code == 1 and out == "")

code, out, _ = run([message("x", stop="max_tokens")])
check("answerer: a truncated response is no answer", code == 1 and out == "")

long_text, short_text = "a" * 301, "b" * 300
code, out, seen = run([message(long_text), message(short_text)])
check("answerer: over 300 characters, it asks once for a rewrite, and prints that",
      code == 0 and out == short_text + "\n" and len(seen) == 2 and
      seen[1][2]["messages"][1] == {"role": "assistant", "content": long_text} and
      "Rewrite it in at most 300" in seen[1][2]["messages"][2]["content"])

code, out, seen = run([message(long_text), message(long_text)])
check("answerer: still over after one rewrite, no answer: never cut to fit",
      code == 1 and out == "" and len(seen) == 2)

code, out, seen = run([message("é" * 300)])
check("answerer: the limit counts characters, not bytes", code == 0 and out == "é" * 300 + "\n")

code, out, seen = run([(400, {"type": "error", "error": {"type": "invalid_request_error",
                                                         "message": "bad request"}})])
check("answerer: an API error is no answer", code == 1 and out == "" and len(seen) == 1)

code, out, seen = run([message("ok")], env={"REDDIT_MODEL": "claude-sonnet-5"})
check("answerer: REDDIT_MODEL chooses the model", code == 0 and seen[0][2]["model"] == "claude-sonnet-5")

code, out, seen = run([], stdin="")
check("answerer: no thread, no request, no answer", code == 1 and seen == [])

# end to end: `reddit serve` runs this answerer on a request and records
# what it printed as an ordinary answer line
BIN = os.environ.get("BIN") or os.path.join(HERE, "..", "build", "reddit")
if os.access(BIN, os.X_OK):
    with tempfile.TemporaryDirectory() as d:
        wrapper, sock, log = (os.path.join(d, n) for n in ("answerer.sh", "sock", "transcript"))
        with open(wrapper, "w") as f:  # this interpreter, which has the SDK
            f.write(f'#!/bin/sh\nexec "{sys.executable}" "{os.path.join(HERE, "claude.py")}"\n')
        os.chmod(wrapper, 0o755)
        with open(os.path.join(d, "principals"), "w") as f:
            f.write("tk-alice 1\ntk-bob 2\n")
        Fake.replies, Fake.seen = [message("It was the Mars Reconnaissance Orbiter.")], []
        env = dict(os.environ, REDDIT_ANSWERER=wrapper, ANTHROPIC_BASE_URL=f"http://127.0.0.1:{port}",
                   ANTHROPIC_API_KEY="test-key", NO_PROXY="127.0.0.1", no_proxy="127.0.0.1")
        srv = subprocess.Popen([BIN, "serve", sock, os.path.join(d, "principals"), log],
                               env=env, stderr=subprocess.DEVNULL)
        for _ in range(50):
            if os.path.exists(sock):
                break
            time.sleep(0.1)
        say = lambda token, lines: subprocess.run([BIN, "connect", sock, token], input=lines,
                                                  capture_output=True, text=True, timeout=10)
        say("tk-alice", "sub science 1\npost science 1 Water on Mars\n")
        say("tk-bob", "request science 2 0\n")
        for _ in range(300):
            with open(log) as f:
                lines = f.read().splitlines()
            if any(l.startswith("answer science 0") for l in lines):
                break
            time.sleep(0.1)
        shown = say("tk-bob", "show science\n").stdout
        srv.terminate()
        srv.wait()
        check("end to end: the server ran this answerer on the thread path and recorded its answer",
              "answer science 0 It was the Mars Reconnaissance Orbiter." in lines and
              Fake.seen and Fake.seen[0][2]["messages"][0]["content"] ==
              "subreddit: science\nu1: Water on Mars" and
              "It was the Mars Reconnaissance Orbiter.  (ai, asked by u2)" in shown)
else:
    print(f"skip - end to end: no reddit binary at {BIN}")

server.shutdown()
sys.exit(1 if failed else 0)
