import os
import sys

# IIS/wfastcgi: force lib path before any imports
_LIB = r"C:\inetpub\wwwroot\Keyvault\lib"
if _LIB not in sys.path:
    sys.path.insert(0, _LIB)

from app import create_app
from waitress import serve

app = create_app("production")

if __name__ == "__main__":
    # IIS HttpPlatformHandler sets HTTP_PLATFORM_PORT dynamically
    # Fallback to 8443 for standalone usage
    port = int(os.environ.get("HTTP_PLATFORM_PORT", os.environ.get("PORT", "8443")))
    print(f"Starting KeyVault on http://0.0.0.0:{port}")
    serve(app, host="0.0.0.0", port=port, threads=8)
