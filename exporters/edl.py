from base import BaseExporter
from typing import IO, Iterator
from models import Indicator, IndicatorType, Severity

class EdlExporter(BaseExporter):
    def __init__(
        self,
        min_severity: Severity | None = None
    ):
        super().__init__(
            indicator_types=[IndicatorType.IP, IndicatorType.DOMAIN, IndicatorType.URL],
            min_severity=min_severity
            )


    def export(self, indicators: Iterator[Indicator], output: IO) -> int:
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

    

