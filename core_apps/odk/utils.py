import logging
import os

import requests
from dotenv import load_dotenv
from urllib3.exceptions import InsecureRequestWarning

from config.env import CUR_ENV_FILE

logger = logging.getLogger(__name__)

if os.path.isfile(CUR_ENV_FILE):
    load_dotenv(CUR_ENV_FILE)


def get_ssl_verify():
    """
    Determine if SSL verification should be used for ODK requests.
    For development environments, this can be disabled via an environment variable.
    """
    verify_ssl = os.getenv("ODK_VERIFY_SSL", "True").lower() in ("true", "1", "t")

    if not verify_ssl:
        # Suppress only the single warning from urllib3 needed.
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        logger.warning(
            "SSL verification is disabled for ODK Central API calls. This should not be used in production."
        )

    return verify_ssl
