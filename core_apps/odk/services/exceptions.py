# core_apps/odk/services/exceptions.py

import logging

from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class ODKValidationError(Exception):
    """Exception levée lors d'erreurs de validation ODK"""

    def __init__(self, message, error_detail=None):
        super().__init__(message)
        self.error_detail = error_detail

    def extract_validation_messages(self):
        """Extraire les messages d'erreur spécifiques depuis error_detail"""
        validation_messages = []
        if self.error_detail:
            if isinstance(self.error_detail, dict):
                # Cas où ODK retourne un objet avec des détails
                if "message" in self.error_detail:
                    validation_messages.append(self.error_detail["message"])
                if "details" in self.error_detail:
                    if isinstance(self.error_detail["details"], list):
                        validation_messages.extend(self.error_detail["details"])
                    else:
                        validation_messages.append(str(self.error_detail["details"]))
            elif isinstance(self.error_detail, list):
                validation_messages = self.error_detail
            else:
                validation_messages.append(str(self.error_detail))
        return validation_messages

    def to_response(self, error_message="Validation error", log_message=None):
        """Créer une Response structurée pour cette exception de validation"""
        if log_message:
            logger.error(log_message)

        validation_messages = self.extract_validation_messages()

        response_data = {
            "error": error_message,
            "detail": str(self),
            # "validation_errors": self.error_detail,
            "validation_messages": validation_messages,
        }

        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
