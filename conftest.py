"""Make top-level modules (main, job) importable in tests."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
