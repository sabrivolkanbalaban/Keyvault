from app import create_app
from waitress import serve

app = create_app("production")

if __name__ == "__main__":
    print("Starting KeyVault on http://0.0.0.0:8443")
    serve(app, host="0.0.0.0", port=8443, threads=8)
