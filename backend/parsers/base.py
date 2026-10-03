from abc import ABC, abstractmethod
from typing import BinaryIO, Union
from backend.models.finding import FindingCreate


class BaseParser(ABC):
    """Abstract base class for scanner output parsers."""

    @abstractmethod
    def parse(self, content: Union[bytes, str]) -> list[FindingCreate]:
        """
        Parse raw scanner file content and return a list of structured FindingCreate objects.
        """
        pass
