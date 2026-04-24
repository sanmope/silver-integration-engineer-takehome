from abc import ABC, abstractmethod
from typing import IO, Iterator

from models import Indicator, IndicatorType, Severity

class BaseExporter(ABC):
    """ Base class for indicator exporters with type and severity filtering.
    
        Args:
            indicator_types: Allowed indicator types. None means all types.
            min_severity: Minimum severity to include. None means all severities.
    """
    def __init__(
        self,
        indicator_types: list[IndicatorType] | None = None,
        min_severity: Severity | None = None,
    ):
        self.indicator_types = indicator_types
        self.min_severity = min_severity
    
    def filter(self, indicators: Iterator[Indicator]) -> Iterator[Indicator]:
        """ Yield indicators matching configured type and severity filters.
        
            Args:
                indicators: Iterator of indicators to filter.
            
            Returns:
                Filtered iterator of indicators.
        """
        severity_order = [Severity.LOW,Severity.MEDIUM,Severity.HIGH,Severity.CRITICAL]
        min_index = severity_order.index(self.min_severity) if self.min_severity else 0

        for indicator in indicators:
            if self.indicator_types and indicator.type not in self.indicator_types:
                continue
            if severity_order.index(indicator.severity) < min_index:
                continue
            yield indicator
    
    @abstractmethod
    def export(self, indicators: Iterator[Indicator], output: IO) -> int:
        """Export indicators to output stream."""


    @abstractmethod
    def content_type(self) -> str:
        """Return MMIE type for this export format."""

    @abstractmethod
    def file_extension(self) -> str:
        """Return file extension for this export format."""
    



