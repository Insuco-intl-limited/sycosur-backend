import json
import logging
import threading
import time
from datetime import timedelta
from typing import Any, Dict

from django.conf import settings
from django.utils import timezone

import requests

from core_apps.odk.models import AuditLogs, ODKUserSessions
from core_apps.odk.utils import get_ssl_verify

from .poolServices import ODKAccountPool

logger = logging.getLogger(__name__)


class BaseODKService:
    """Base service for interacting with the ODK Central API"""

    def __init__(self, django_user, request=None):
        self.django_user = django_user
        self.request = request
        self.base_url = getattr(
            settings, "ODK_CENTRAL_URL", "https://odk.insuco.net/v1"
        )
        self.current_account = None
        self.current_session_data = None
        self.odk_account_pool = ODKAccountPool()

    def __enter__(self):
        """Context manager to acquire an ODK account from the pool"""
        self.current_account = self.odk_account_pool.get_account()
        self.current_session_data = self.odk_account_pool.get_session_for_account(
            self.current_account
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release the account back to the pool"""
        if self.current_account:
            self.odk_account_pool.return_account(self.current_account)

    def _get_or_create_token(self) -> str:
        """Get or create a valid ODK token for the current account"""
        if not self.current_account:
            raise Exception("No ODK account assigned")

        session_data = self.current_session_data
        account = self.current_account

        # Check if we already have a valid token
        if (
            session_data["token"]
            and session_data["expires_at"]
            and timezone.now() < session_data["expires_at"]
        ):
            return session_data["token"]

        # Otherwise, authenticate
        try:
            response = session_data["session"].post(
                f"{self.base_url}/sessions",
                json={"email": account["email"], "password": account["password"]},
                verify=get_ssl_verify(),
            )
            response.raise_for_status()

            token = response.json().get("token")
            expires_at = timezone.now() + timedelta(
                hours=23
            )  # 23h to avoid expirations

            # Update session data
            session_data["token"] = token
            session_data["expires_at"] = expires_at
            session_data["session"].headers.update(
                {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            )

            # Also save the token for Django user
            thread_id = threading.current_thread().ident
            ODKUserSessions.objects.update_or_create(
                user=self.django_user,
                defaults={
                    "odk_token": token,
                    "token_expired_at": expires_at,
                    "actor_id": account["id"],
                },
            )

            logger.info(
                f"ODK authentication successful for account {account['id']} (threads: {thread_id})"
            )
            return token

        except Exception as e:
            thread_id = threading.current_thread().ident
            logger.error(
                f"ODK authentication failed for account {account['id']}: {e} (thread: {thread_id})"
            )
            raise

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make a request to ODK Central with retry and error handling"""
        # Use configuration or default values
        max_retries = getattr(settings, "ODK_MAX_RETRIES", 5)
        timeout = getattr(settings, "ODK_REQUEST_TIMEOUT", 120)

        # Add default timeout if not specified
        if "timeout" not in kwargs:
            kwargs["timeout"] = timeout
        if "verify" not in kwargs:
            kwargs["verify"] = get_ssl_verify()

        for attempt in range(max_retries):
            try:
                self._get_or_create_token()
                session = self.current_session_data["session"]

                logger.debug(
                    f"Attempt {attempt + 1}/{max_retries} - {method} {self.base_url}/{endpoint}"
                )

                response = session.request(
                    method, f"{self.base_url}/{endpoint}", **kwargs
                )
                response.raise_for_status()

                # For requests that don't return JSON
                if response.status_code == 204 or not response.content:
                    return {"success": True, "status_code": response.status_code}

                return response.json()

            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error to ODK Central ({self.base_url}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                raise Exception(
                    f"Unable to connect to ODK Central server. "
                    f"Please verify that the URL '{self.base_url}' is correct and the server is accessible."
                )
            except requests.exceptions.Timeout as e:
                logger.error(f"Timeout connecting to ODK Central: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                raise Exception(
                    f"ODK Central server is not responding within the timeout period ({timeout}s). "
                    f"Please check server status or increase ODK_REQUEST_TIMEOUT value."
                )
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401:
                    logger.warning(
                        f"Token expired for account {self.current_account['id']}, refreshing..."
                    )
                    self.current_session_data["token"] = None
                    if attempt < max_retries - 1:
                        continue
                status_code = e.response.status_code
                logger.error(
                    f"HTTP error {status_code} during request to ODK Central: {e}"
                )

                if status_code == 404:
                    raise Exception(f"Resource not found: {endpoint}")
                elif status_code == 403:
                    raise Exception(f"Access denied to resource: {endpoint}")
                elif status_code >= 500:
                    if attempt < max_retries - 1:
                        wait_time = 2**attempt
                        logger.info(f"Server error, retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    raise Exception(
                        f"ODK Central server error ({status_code}). Please try again later."
                    )
                raise
            except json.JSONDecodeError as e:
                logger.error(f"JSON decoding error: {e}")
                raise Exception("ODK Central server returned an invalid response.")
            except Exception as e:
                logger.error(f"Unexpected error during request to ODK Central: {e}")
                if attempt < max_retries - 1:
                    wait_time = 2**attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                raise

        raise Exception(f"Maximum number of attempts exceeded for {method} {endpoint}")

    def get_client_ip(self) -> str:
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = self.request.META.get("REMOTE_ADDR")
        return ip

    def _log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: str | int,
        details: dict,
        success: bool = True,
    ) -> None:
        """Log an action in the audit log"""
        try:
            AuditLogs.objects.create(
                user=self.django_user,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                success=success,
                ip_address=self.get_client_ip(),
            )
        except Exception as e:
            logger.error(f"Error while writing to audit log: {e}")
