"""
Pharma Sales Analytics -- Streamlit Cloud Entry Point
=====================================================
Root wrapper so Streamlit Community Cloud default 'streamlit_app.py' works automatically.
"""

import sys
from pathlib import Path

# Ensure project root is in Python path
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Execute main dashboard app
import dashboard.app
