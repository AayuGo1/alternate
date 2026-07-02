"""
excel_loader.py

Handles downloading the Excel workbook from GitHub, caching it via
Streamlit, and converting raw bytes into an openpyxl Workbook object.

This module contains NO business logic, NO parsing of sheet contents,
NO KPI calculations, and NO dataframe creation.
"""

from __future__ import annotations

import logging
from io import BytesIO
from typing import Final

import requests
import streamlit as st
from openpyxl import load_workbook
from openpyxl.workbook.workbook import Workbook
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout as RequestsTimeout

import config

logger: Final[logging.Logger] = logging.getLogger(__name__)
logger.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))

_TIMEOUT_SECONDS: Final[int] = 30
_MAX_RETRIES: Final[int] = 3


class ExcelDownloadError(Exception):
    """Raised when the Excel workbook cannot be downloaded."""


class ExcelCorruptedError(Exception):
    """Raised when the downloaded workbook cannot be opened."""


def _validate_url(url: str) -> None:
    """Validate GitHub raw URL."""
    if not url or not url.strip():
        raise ExcelDownloadError("RAW_GITHUB_URL is empty.")

    if not (url.startswith("http://") or url.startswith("https://")):
        raise ExcelDownloadError(f"Invalid RAW_GITHUB_URL: {url}")


@st.cache_data(ttl=config.RAW_CACHE_TTL_SECONDS, show_spinner=False)
def download_excel() -> bytes:
    """
    Download Excel workbook from GitHub.

    Returns
    -------
    bytes
    """

    url = config.RAW_GITHUB_URL
    _validate_url(url)

    last_error: Exception |None = None

    for attempt in range(1, _MAX_RETRIES + 1):

        try:

            logger.info(
                "Downloading workbook (%d/%d): %s",
                attempt,
                _MAX_RETRIES,
                url,
            )

            response = requests.get(
                url,
                timeout=_TIMEOUT_SECONDS,
            )

            if response.status_code == 404:
                raise ExcelDownloadError(
                    "Workbook not found (HTTP 404).\n"
                    "Check GITHUB_OWNER / GITHUB_REPO / EXCEL_FILENAME."
                )

            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "")

            if (
                "spreadsheet" not in content_type.lower()
                and "excel" not in content_type.lower()
                and "octet-stream" not in content_type.lower()
            ):
                logger.warning(
                    "Unexpected content type: %s",
                    content_type,
                )

            if not response.content:
                raise ExcelDownloadError("Downloaded workbook is empty.")

            logger.info(
                "Workbook downloaded successfully (%d bytes)",
                len(response.content),
            )

            return response.content

        except ExcelDownloadError:
            raise

        except RequestsTimeout as exc:
            last_error = exc
            logger.warning(
                "Timeout (%d/%d): %s",
                attempt,
                _MAX_RETRIES,
                exc,
            )

        except RequestsConnectionError as exc:
            last_error = exc
            logger.warning(
                "Connection error (%d/%d): %s",
                attempt,
                _MAX_RETRIES,
                exc,
            )

        except requests.RequestException as exc:
            last_error = exc
            logger.warning(
                "Request failed (%d/%d): %s",
                attempt,
                _MAX_RETRIES,
                exc,
            )

    raise ExcelDownloadError(
        f"Failed to download workbook after {_MAX_RETRIES} attempts.\n{last_error}"
    )


def load_workbook_from_bytes(file_bytes: bytes) -> Workbook:
    """
    Convert workbook bytes into an openpyxl Workbook.
    """

    if not file_bytes:
        raise ExcelCorruptedError("Workbook bytes are empty.")

    try:

        workbook = load_workbook(
            filename=BytesIO(file_bytes),
            data_only=True,
            read_only=True,
        )

        logger.info(
            "Workbook opened successfully (%d sheets)",
            len(workbook.sheetnames),
        )

        return workbook

    except Exception as exc:
        logger.exception("Workbook could not be opened.")

        raise ExcelCorruptedError(
            f"Workbook appears corrupted.\n{exc}"
        ) from exc


def refresh_cache() -> None:
    """Clear cached workbook."""
    logger.info("Clearing workbook cache.")
    download_excel.clear()


def get_workbook() -> Workbook:
    """
    Download and open workbook.

    Returns
    -------
    Workbook
    """
    return load_workbook_from_bytes(download_excel())
