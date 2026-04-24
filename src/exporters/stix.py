from exporters.base import BaseExporter
from typing import IO, Iterator
from models import Indicator, IndicatorType, Severity
import stix2
import logging

logger = logging.getLogger(__name__)

class StixExporter(BaseExporter):
    """
    Exports indicators as a STIX 2.1 bundle using the stix2 library.
    Unknown indicator types are logged as warnings and skipped.
    """
    
    def export(self,indicators: Iterator[Indicator], output: IO) -> int:
        """
        Write filtered indicators as a STIX 2.1 JSON bundle to output.
        
        Returns:
            Number of indicators written.
        """

        count = 0
        indicators = self.filter(indicators)

        #Mapping to stix pattern
        stix_map = {
        IndicatorType.IP:'ipv4-addr:value',
        IndicatorType.DOMAIN: 'domain-name:value',
        IndicatorType.URL: 'url:value',
        IndicatorType.HASH: 'file:hashes.MD5'
        }

        objects = []

        for i in indicators:
            if i.type not in stix_map:
                logger.warning("Indicator not in stix fomat %s",i.type)
                continue
            obj = stix2.Indicator(
            name=i.value,
            pattern=f'[{stix_map[i.type]} = \'{i.value}\']',
            pattern_type="stix",
            valid_from=i.first_seen,
            )
            objects.append(obj)
            count += 1
        
        bundle = stix2.Bundle(objects)

        output.write(bundle.serialize(pretty=True))

        return count
    

    def content_type(self) -> str:
        return "application/stix+json"
    
    def file_extension(self) -> str:
        return "json"