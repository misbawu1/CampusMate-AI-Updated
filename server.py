"""Serve the CampusMate browser app locally or on a hosted service."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import webbrowser

from tools import find_relevant_resources, load_knowledge


PROJECT_FOLDER = Path(__file__).resolve().parent
MODEL = "gemini-3.5-flash-lite"
SYSTEM_INSTRUCTION = (
    "You are CampusMate, a friendly campus guide. Campus resources found by the local search "
    "are provided with the student's question. Use only those records for campus-specific "
    "facts. If no resource was found and the question is about this campus, say CampusMate "
    "could not find that information and suggest a broader search. Do not invent services, "
    "locations, hours, or contacts. Answer general questions outside campus information "
    "normally. For health questions, do not diagnose or give treatment instructions; direct "
    "the student to the Student Health Center only when it appears in the supplied records. "
    "Keep answers to three short sentences."
)


class CampusMateHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/ask":
            self.send_error(404)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"error": "The question could not be read."})
            return

        if content_length < 1 or content_length > 10000:
            self._send_json(400, {"error": "Please send a shorter question."})
            return

        try:
            payload = json.loads(self.rfile.read(content_length))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "The question could not be read."})
            return

        question = payload.get("question", "") if isinstance(payload, dict) else ""
        if not isinstance(question, str) or not question.strip():
            self._send_json(400, {"error": "Type a question first."})
            return
        if len(question) > 1000:
            self._send_json(400, {"error": "Please keep your question under 1,000 characters."})
            return

        if not os.environ.get("GEMINI_API_KEY"):
            self._send_json(
                503,
                {"error": "Gemini key not available. Close and reopen VS Code, then start CampusMate again."},
            )
            return

        try:
            from google import genai

            resources = load_knowledge()
            matches = find_relevant_resources(resources, question.strip())
            matching_resources = [
                {
                    "name": item.get("name", ""),
                    "description": item.get("description", ""),
                    "contact": item.get("contact", ""),
                }
                for item in matches
            ]
            prompt = (
                f"Campus resource search results:\n"
                f"{json.dumps(matching_resources, ensure_ascii=False)}\n\n"
                f"Student question: {question.strip()}"
            )
            self._start_event_stream()
            self._send_event({"type": "status", "message": "CampusMate is checking resources and asking Gemini…"})

            client = genai.Client()
            stream = client.interactions.create(
                model=MODEL,
                input=prompt,
                system_instruction=SYSTEM_INSTRUCTION,
                generation_config={"thinking_level": "minimal"},
                store=False,
                stream=True,
                timeout=30,
            )
            got_text = False
            final_output = ""
            final_status = "unknown"
            event_types = set()
            for event in stream:
                event_type = getattr(event, "event_type", "unknown")
                event_types.add(str(event_type))
                delta = getattr(event, "delta", None)
                if event_type == "step.delta" and delta and getattr(delta, "type", None) == "text" and getattr(delta, "text", None):
                    self._send_event({"type": "text", "text": delta.text})
                    got_text = True
                elif event_type in {"error", "interaction.error"}:
                    self._send_event({"type": "error", "message": "Gemini couldn't finish the answer. Please try again."})
                    return
                elif event_type == "interaction.completed":
                    interaction = getattr(event, "interaction", None)
                    final_status = getattr(interaction, "status", "unknown")
                    final_output = getattr(interaction, "output_text", "") or ""

            # Some SDK/API responses include the final answer on the completed
            # interaction even when no text delta was delivered to this loop.
            if not got_text and final_output:
                self._send_event({"type": "text", "text": final_output})
                got_text = True

            if got_text:
                self._send_event({"type": "done"})
            else:
                print(
                    "Gemini stream finished without answer text. "
                    f"Status: {final_status}; events: {', '.join(sorted(event_types))}"
                )
                self._send_event({"type": "error", "message": "Gemini returned no answer. Please try again."})
        except Exception as error:
            print(f"Gemini request failed: {type(error).__name__}")
            self._send_event({"type": "error", "message": "CampusMate couldn't get an AI answer. Check the VS Code terminal and try again."})

    def _start_event_stream(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True

    def _send_event(self, payload):
        message = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.wfile.write(b"data: " + message + b"\n\n")
        self.wfile.flush()

    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    handler = partial(CampusMateHandler, directory=str(PROJECT_FOLDER))
    hosted_port = os.environ.get("PORT")
    host = "0.0.0.0" if hosted_port else "127.0.0.1"
    port = int(hosted_port) if hosted_port else 8000
    try:
        server = ThreadingHTTPServer((host, port), handler)
    except OSError:
        if hosted_port:
            raise
        server = ThreadingHTTPServer((host, 0), handler)
    if hosted_port:
        print(f"CampusMate is listening on {host}:{server.server_port}")
    else:
        address = f"http://127.0.0.1:{server.server_port}/"
        print(f"CampusMate is open at {address}")
        print("Keep this window open while you use CampusMate. Press Ctrl+C to stop it.")
        threading.Timer(0.7, lambda: webbrowser.open(address)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCampusMate server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
