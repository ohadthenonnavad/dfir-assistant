"""Windows Internals DFIR Knowledge Assistant.

AI-powered Senior DFIR Analyst assistant for Windows memory forensics
and incident response.
"""

__version__ = "0.1.0"
__author__ = "DFIR Team"

from dfir_assistant.config import Settings, get_settings

__all__ = ["Settings", "get_settings", "__version__"]
