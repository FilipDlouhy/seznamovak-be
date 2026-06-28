import logging
from functools import partial

import httpx
from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)

BREVO_CONTACTS_URL = "https://api.brevo.com/v3/contacts"


class NewsletterService:
    """Adds newsletter subscribers to the Brevo list when Brevo is configured."""

    def subscribe(self, *, email):
        """Register the contact after the transaction commits, do nothing without a Brevo key."""
        if not settings.BREVO_API_KEY:
            return
        transaction.on_commit(partial(self._add_contact, email))

    def _add_contact(self, email):
        try:
            response = httpx.post(
                BREVO_CONTACTS_URL,
                headers={"api-key": settings.BREVO_API_KEY},
                json={"email": email, "listIds": [settings.BREVO_LIST_ID], "updateEnabled": True},
                timeout=settings.BREVO_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except Exception:
            logger.exception("Could not add %s to the Brevo list", email)
