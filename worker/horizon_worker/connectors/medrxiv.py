"""medRxiv JSON API connector (preprints, medical).

Same API shape as bioRxiv. Different server ID.
NATO B2.
"""

from __future__ import annotations

from typing import ClassVar

from .biorxiv import BioRxivConnector


class MedRxivConnector(BioRxivConnector):
    SOURCE_CODE: ClassVar[str] = "medrxiv"
    PARSER_VERSION: ClassVar[str] = "0.2.0"
    # ENDPOINT empty to bypass curl_cffi (see BioRxivConnector for rationale).
    ENDPOINT: ClassVar[str] = ""
    BASE_ENDPOINT: ClassVar[str] = "https://api.biorxiv.org/details/medrxiv/"
    SERVER: ClassVar[str] = "medrxiv"
