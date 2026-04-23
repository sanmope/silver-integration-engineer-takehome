import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import io
import json
from exporters.edl import EdlExporter
from exporters.csv_exporter import CsvExporter
from exporters.stix import StixExporter
from models import Indicator, IndicatorType, Severity

def test_edl_min_severity_low(sample_indicators):
    edl = EdlExporter(
        min_severity = Severity.LOW,
    )
    output = io.StringIO()
    edl.export(sample_indicators,output)
    result = output.getvalue()

    #All cases execpt Low should be present
    assert ("1.2.3.4" in result)
    assert ("5.6.7.8" in result)
    assert ("malware.com" in result)

def test_edl_min_severity_high(sample_indicators):
    edl = EdlExporter(
        min_severity = Severity.HIGH,
    )
    output = io.StringIO()
    edl.export(sample_indicators,output)
    result = output.getvalue()

    assert "1.2.3.4" in result  # CRITICAL
    assert "malware.com" in result  # HIGH
    assert "5.6.7.8" not in result  # MEDIUM - Filtered

def test_edl_counts_correctly(sample_indicators):
    edl = EdlExporter(
        min_severity = Severity.LOW,
    )
    output = io.StringIO()
    result = edl.export(sample_indicators,output)
    

    #All cases execpt Low should be present
    assert (result == 3)

def test_edl_hash_filtered(sample_indicators):
    edl = EdlExporter(
        min_severity = Severity.LOW,
    )
    output = io.StringIO()
    edl.export(sample_indicators,output)
    result = output.getvalue()
    

    #All cases execpt Low should be present
    assert ("d41d8cd98f00b204e9800998ecf8427e" not in result)


def test_csv_correct_header(sample_indicators):
    csv = CsvExporter(
        indicator_types = [IndicatorType.IP],
        min_severity = Severity.HIGH,
    )

    output = io.StringIO()
    csv.export(sample_indicators,output)
    result = output.getvalue()

    lines = result.split("\n")
    assert lines[0].strip() == "type,value,severity,tags,updated_at"
    

def test_csv_correct_count(sample_indicators):
    csv = CsvExporter(
        indicator_types = [IndicatorType.IP],
        min_severity = Severity.LOW,
    )

    output = io.StringIO()
    result = csv.export(sample_indicators,output)


    #All cases execpt Low should be present
    assert (result == 2)
    
def test_stix_export(sample_indicators):
    stix = StixExporter()
    output = io.StringIO()
    count = stix.export(sample_indicators, output)
    result = json.loads(output.getvalue())

    assert result["type"] == "bundle"
    assert len(result["objects"]) == count
    
    patterns = [obj["pattern"] for obj in result["objects"]]
    assert "[ipv4-addr:value = '1.2.3.4']" in patterns
    
