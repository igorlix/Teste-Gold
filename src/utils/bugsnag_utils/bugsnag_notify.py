import os, bugsnag
from bugsnag.handlers import BugsnagHandler
import logging

def configure_bugsnag():
    API_KEY = os.getenv("BUGSNAG_API_KEY")

    if not API_KEY:
        # ajuda muito na investigação caso a env não chegue
        logging.getLogger(__name__).warning("BUGSNAG_API_KEY ausente no ambiente do serving")

    bugsnag.configure(
        api_key=API_KEY,
        release_stage="dev",
        project_root="/"
    )
    # Integrar com logs
    logger = logging.getLogger(__name__)
    handler = BugsnagHandler()
    logger.addHandler(handler)
