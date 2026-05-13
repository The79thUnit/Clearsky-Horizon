"""medRxiv JSON API connector (preprints, medical).

Same API shape as bioRxiv. Different server ID.
NATO B2.
"""

from __future__ import annotations

from typing import ClassVar

from .biorxiv import BioRxivConnector


class MedRxivConnector(BioRxivConnector):
    SOURCE_CODE: ClassVar[str] = "medrxiv"
    PARSER_VERSION: ClassVar[str] = "0.1.0"
    ENDPOINT: ClassVar[str] = "https://api.biorxiv.org/details/medrxiv/30d/0/json"
