"""Application entry point for Windows Internals DFIR Knowledge Assistant."""

import logging
from dfir_assistant.config import get_settings

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure application logging."""
    settings = get_settings()
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> None:
    """Main entry point."""
    setup_logging()
    settings = get_settings()
    
    logger.info("Starting Windows Internals DFIR Knowledge Assistant")
    logger.info(f"Model: {settings.model_name}")
    logger.info(f"Ollama URL: {settings.ollama_url}")
    logger.info(f"Qdrant URL: {settings.qdrant_url}")
    
    # Import here to avoid circular imports
    from dfir_assistant.ui.gradio_app import create_app
    
    app = create_app()
    app.launch(
        server_name=settings.server_host,
        server_port=settings.server_port,
        share=False,
    )


if __name__ == "__main__":
    main()
