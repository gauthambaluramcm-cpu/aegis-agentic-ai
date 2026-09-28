from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import traceback

from app.aegis_pipeline import main


class AEGISRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            response = {
                "status": "online",
                "service": "AEGIS API"
            }

            self.wfile.write(json.dumps(response).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/run":
            self.send_response(404)
            self.end_headers()
            return

        try:
            print("\n" + "=" * 60)
            print("AEGIS API: Pipeline execution requested")
            print("=" * 60)

            # Run the existing AEGIS pipeline
            main()

            response = {
                "status": "success",
                "message": "AEGIS pipeline executed successfully"
            }

            self.send_response(200)

        except Exception as error:
            print("\nAEGIS pipeline failed:")
            traceback.print_exc()

            response = {
                "status": "error",
                "message": str(error)
            }

            self.send_response(500)

        self.send_header("Content-Type", "application/json")
        self.end_headers()

        self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server_address = ("127.0.0.1", 8000)

    server = HTTPServer(server_address, AEGISRequestHandler)

    print("=" * 60)
    print("AEGIS API SERVER")
    print("=" * 60)
    print("Server running at: http://127.0.0.1:8000")
    print("Health check:      http://127.0.0.1:8000/health")
    print("Pipeline endpoint: http://127.0.0.1:8000/run")
    print("=" * 60)
    print("Press CTRL+C to stop the server.")

    server.serve_forever()