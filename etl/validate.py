#!/usr/bin/env python3
"""
ETL Validation Script
Test the ETL pipeline components
"""

import os
import json
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Ajout du path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from etl.utils import ETLUtils, DataQualityChecker


def test_data_extraction():
    """Test data extraction functionality"""
    print("🔍 Testing Data Extraction...")
    
    # Check if raw data exists
    data_path = ETLUtils.get_data_path()
    raw_data_file = os.path.join(data_path, "scraped_data.json")
    file_stats = ETLUtils.get_file_stats(raw_data_file)
    
    if not file_stats["exists"]:
        print(f"❌ Raw data file not found: {raw_data_file}")
        print("   Run scraping first: make scrape-test")
        return False
    
    print(f"✅ Raw data file found:")
    print(f"   Size: {file_stats['size_mb']} MB")
    print(f"   Modified: {file_stats['modified']}")
    
    # Load and validate data
    data = ETLUtils.load_raw_data(raw_data_file)
    if not data:
        print("❌ Could not load raw data")
        return False
    
    validation = ETLUtils.validate_data_structure(data)
    if not validation["valid"]:
        print(f"❌ Data validation failed: {validation.get('error')}")
        return False
    
    print(f"✅ Data structure valid:")
    print(f"   Records: {validation['total_records']}")
    print(f"   Sample keys: {', '.join(validation['sample_keys'][:5])}...")
    
    return True


def test_data_quality():
    """Test data quality checks"""
    print("\n🔍 Testing Data Quality...")
    
    data_path = ETLUtils.get_data_path()
    raw_data_file = os.path.join(data_path, "scraped_data.json")
    data = ETLUtils.load_raw_data(raw_data_file)
    
    if not data:
        print("❌ No data available for quality check")
        return False
    
    quality_report = DataQualityChecker.check_data_quality(data)
    
    print(f"📊 Data Quality Report:")
    print(f"   Quality Score: {quality_report['quality_score']}/100")
    print(f"   Total Records: {quality_report['total_records']}")
    print(f"   Unique Records: {quality_report['unique_records']}")
    
    if quality_report['issues']:
        print(f"   Issues found:")
        for issue in quality_report['issues']:
            print(f"   - {issue}")
    else:
        print("   ✅ No quality issues found!")
    
    return quality_report['quality_score'] >= 70


def test_database_connection():
    """Test database connectivity"""
    print("\n🔍 Testing Database Connection...")
    
    try:
        from etl.loader import PostgreSQLLoader
        
        loader = PostgreSQLLoader()
        if loader.connect():
            print("✅ Database connection successful")
            
            # Test database operation (e.g., list tables)
            list_tables_method = getattr(loader, "list_tables", None)
            tables = list_tables_method() if callable(list_tables_method) else []
            if tables:
                print("✅ Database accessible, tables found")
                # Safely close or disconnect the loader if a method is available
                close_method = (
                    getattr(loader, "close", None)
                    or getattr(loader, "disconnect", None)
                    or getattr(loader, "close_connection", None)
                )
                if callable(close_method):
                    close_method()
                return True
            else:
                print("❌ No tables found or unable to list tables")
                close_method = (
                    getattr(loader, "close", None)
                    or getattr(loader, "disconnect", None)
                    or getattr(loader, "close_connection", None)
                )
                if callable(close_method):
                    close_method()
                return False
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False


def test_etl_components():
    """Test individual ETL components"""
    print("\n🔍 Testing ETL Components...")
    
    try:
        from etl import DataExtractor, DataTransformer, DataValidator
        
        # Test with sample data
        sample_data = [
            {
                "title": "Beautiful condo in Montreal",
                "price": "$450,000",
                "location": "Montreal, QC",
                "area": "900 sq ft",
                "bedrooms": "2",
                "bathrooms": "1",
                "address": "123 Main St",
                "url": "https://example.com/property/1"
            }
        ]
        
        # Test Extractor
        extractor = DataExtractor()
        # Try common extractor method names and call the first available one
        extract_fn = (
            getattr(extractor, "extract_from_data", None)
            or getattr(extractor, "extract", None)
            or getattr(extractor, "extract_data", None)
            or getattr(extractor, "run", None)
        )
        if not callable(extract_fn):
            print("❌ DataExtractor missing extract method (expected one of: extract_from_data, extract, extract_data, run)")
            return False
        extracted = extract_fn(sample_data)
        if extracted:
            print("✅ DataExtractor working")
        else:
            print("❌ DataExtractor failed")
            return False
        
        # Test Transformer
        transformer = DataTransformer()
        transform_fn = (
            getattr(transformer, "transform", None)
            or getattr(transformer, "transform_data", None)
            or getattr(transformer, "run", None)
            or getattr(transformer, "process", None)
        )
        if not callable(transform_fn):
            print("❌ DataTransformer missing transform method (expected one of: transform, transform_data, run, process)")
            return False
        transformed = transform_fn(extracted)
        if transformed:
            print("✅ DataTransformer working")
        else:
            print("❌ DataTransformer failed")
            return False
        
        # Test Validator
        validator = DataValidator()
        # Support multiple possible validator method names and result formats
        validate_fn = (
            getattr(validator, "validate", None)
            or getattr(validator, "validate_data", None)
            or getattr(validator, "run", None)
            or getattr(validator, "process", None)
            or getattr(validator, "check", None)
            or getattr(validator, "validate_records", None)
        )
        if not callable(validate_fn):
            print("❌ DataValidator missing validate method (expected one of: validate, validate_data, run, process, check, validate_records)")
            return False
        validation_result = validate_fn(transformed)
        # Normalize validation_result to determine success
        valid_count = None
        if isinstance(validation_result, dict):
            valid_count = (
                validation_result.get("valid_count")
                or validation_result.get("valid_records")
                or validation_result.get("valid_rows")
                or validation_result.get("valid")
                or validation_result.get("passed")
            )
            if isinstance(valid_count, bool):
                valid_count = 1 if valid_count else 0
        elif isinstance(validation_result, (list, tuple, set)):
            valid_count = len(validation_result)
        elif isinstance(validation_result, bool):
            valid_count = 1 if validation_result else 0
        elif isinstance(validation_result, int):
            valid_count = validation_result
        else:
            valid_count = 0
        if valid_count and valid_count > 0:
            print("✅ DataValidator working")
        else:
            print("❌ DataValidator failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ ETL component test error: {e}")
        return False


def run_full_validation():
    """Run complete ETL validation"""
    print("🚀 Starting ETL Pipeline Validation")
    print("=" * 50)
    
    tests = [
        ("Data Extraction", test_data_extraction),
        ("Data Quality", test_data_quality),
        ("Database Connection", test_database_connection),
        ("ETL Components", test_etl_components)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📋 Validation Summary:")
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All ETL validation tests passed!")
        print("   Your ETL pipeline is ready to use.")
    else:
        print("⚠️  Some validation tests failed.")
        print("   Please check the issues above before using the ETL pipeline.")
    
    # Save validation report
    report = {
        "timestamp": datetime.now().isoformat(),
        "tests": results,
        "all_passed": all_passed
    }
    
    data_path = ETLUtils.get_data_path()
    report_file = os.path.join(data_path, "etl_validation_report.json")
    ETLUtils.save_report(report, report_file)
    print(f"\n📄 Validation report saved to: {report_file}")
    
    return all_passed


def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(description="ETL Pipeline Validation")
    parser.add_argument(
        "--component",
        choices=["extraction", "quality", "database", "etl", "all"],
        default="all",
        help="Which component to test"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    ETLUtils.setup_logging("etl_validation", "INFO")
    
    # Create data directory
    data_path = ETLUtils.get_data_path()
    os.makedirs(data_path, exist_ok=True)
    
    if args.component == "all":
        return run_full_validation()
    elif args.component == "extraction":
        return test_data_extraction()
    elif args.component == "quality":
        return test_data_quality()
    elif args.component == "database":
        return test_database_connection()
    elif args.component == "etl":
        return test_etl_components()


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
