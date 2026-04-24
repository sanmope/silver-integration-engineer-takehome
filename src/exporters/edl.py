from exporters.base import BaseExporter
from typing import IO, Iterator
from models import Indicator, IndicatorType, Severity

class EdlExporter(BaseExporter):
    """
    Exports indicators as plain-text EDL (one value per line).
    Only exports IPs, domains, and URLs — hashes are excluded.
    
    Args:
        min_severity: Minimum severity to include.
    """
    def __init__(
        self,
        min_severity: Severity | None = None
    ):
        super().__init__(
            indicator_types=[IndicatorType.IP, IndicatorType.DOMAIN, IndicatorType.URL],
            min_severity=min_severity
            )


    def export(self, indicators: Iterator[Indicator], output: IO) -> int:
        """
        Write filtered indicator values to output, one per line.
        
        Returns:
            Number of indicators written.
        """
        count = 0
        indicators = self.filter(indicators)

        
        for indicator in indicators:
            output.write(
                indicator.value + "\n"
            )
            count += 1
        
        return count
    

    def content_type(self) -> str:
        return "text/plain"
    
    def file_extension(self) -> str:
        return "txt"

    

