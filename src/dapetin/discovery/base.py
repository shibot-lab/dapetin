from abc import ABC, abstractmethod
from collections.abc import Iterable

from dapetin.domain.models import Business


class DiscoveryProvider(ABC):
    """Adapter interface for external business-discovery providers."""

    name: str

    @abstractmethod
    def search(self, keyword: str, location: str, limit: int = 20) -> Iterable[Business]:
        """Return candidate businesses for a keyword and location."""
        raise NotImplementedError
