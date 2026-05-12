import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.ui import build_ui

if __name__ == "__main__":
    demo = build_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
