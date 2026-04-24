from exporters.base import BaseExporter
from typing import IO, Iterator
from models import Indicator, IndicatorType, Severity
from csv import DictWriter

class CsvExporter(BaseExporter):
    """Exports indicators as CSV with columns: type, value, severity, tags, updated_at."""

    def export(self,indicators: Iterator[Indicator], output: IO) -> int:
        """
        Write filtered indicators to output as CSV.
        
        Returns:
            Number of indicators written.
        """

        count = 0
        indicators = self.filter(indicators)
        
        #Creating csv
        header = ['type','value','severity','tags','updated_at']
        writer = DictWriter(output,fieldnames = header)
        writer.writeheader()

        for i in indicators:
            row = {'type':i.type,'value': i.value, 'severity':i.severity, 'tags':",".join(i.tags), 'updated_at':i.updated_at}
            writer.writerow(row)
            count += 1
        
        return count
    

    def content_type(self) -> str:
        return "text/csv"
    
    def file_extension(self) -> str:
        return "csv"
