from dataclasses import dataclass
from io import BytesIO

import qrcode
from django.conf import settings


@dataclass(frozen=True)
class PaymentQrImage:
    """One PNG payment QR code with the file name used as the email attachment."""

    file_name: str
    content: bytes


class PaymentQrService:
    """Builds the Czech QR Platba (SPAYD) codes for the deposit in CZK and EUR."""

    def build_images(self):
        """Return the CZK and the EUR code as PNG images."""
        czk_text = self._spayd(iban=settings.SEZNAMOVAK_IBAN_CZK, amount=settings.SEZNAMOVAK_DEPOSIT_CZK, currency="CZK")
        eur_text = self._spayd(iban=settings.SEZNAMOVAK_IBAN_EUR, amount=settings.SEZNAMOVAK_DEPOSIT_EUR, currency="EUR")
        return [
            PaymentQrImage(file_name="QRPlatba_na_ucet- CZK.png", content=self._render_png(czk_text)),
            PaymentQrImage(file_name="QRPlatba_na_ucet- EUR.png", content=self._render_png(eur_text)),
        ]

    def _spayd(self, *, iban, amount, currency):
        message = f"SEZNAMOVAK {settings.SEZNAMOVAK_YEAR}"
        return f"SPD*1.0*ACC:{iban}*AM:{amount}.00*CC:{currency}*X-VS:{settings.SEZNAMOVAK_VARIABLE_SYMBOL}*MSG:{message}"

    def _render_png(self, text):
        image = qrcode.make(text, box_size=8, border=4)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
