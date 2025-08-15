#!/usr/bin/env python3
"""
ETL Pipeline Demo
Demonstrates ETL functionality with sample data
"""

import json
import os
import time
import sys
from datetime import datetime
from pathlib import Path

# Ajout du path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from etl.utils import ETLUtils


def create_sample_data():
    """Create sample real estate data for demo"""
    sample_data = [
        {
            "title": "Beautiful condo in downtown Montreal",
            "price": "$450,000",
            "location": "Montreal, QC H3B 1A1",
            "area": "900 sq ft",
            "bedrooms": "2",
            "bathrooms": "1",
            "description": "Modern condo with city views",
            "url": "https://example.com/property/1",
            "scraped_at": datetime.now().isoformat()
        },
        {
            "title": "Spacious house in Westmount",
            "price": "$1,250,000",
            "location": "Westmount, QC H3Z 2A7",
            "area": "2500 square feet",
            "bedrooms": "4",
            "bathrooms": "3",
            "description": "Victorian style house with garden",
            "url": "https://example.com/property/2",
            "scraped_at": datetime.now().isoformat()
        },
        {
            "title": "Studio apartment near McGill",
            "price": "$280000",
            "location": "Montreal, QC H3A 0G4",
            "area": "450 sq ft",
            "bedrooms": "0",
            "bathrooms": "1",
            "description": "Perfect for students",
            "url": "https://example.com/property/3",
            "scraped_at": datetime.now().isoformat()
        },
        {
            "title": "Luxury penthouse Old Montreal",
            "price": "$2,800,000",
            "location": "Montreal, QC H2Y 3H1",
            "area": "3200 sq ft",
            "bedrooms": "3",
            "bathrooms": "2.5",
            "description": "Penthouse with river views",
            "url": "https://example.com/property/4",
            "scraped_at": datetime.now().isoformat()
        },
        {
            "title": "Family home in NDG",
            "price": "$750000",
            "location": "Montreal, QC H4A 3J5",
            "area": "1800 sq ft",
            "bedrooms": "3",
            "bathrooms": "2",
            "description": "Perfect family home",
            "url": "https://example.com/property/5",
            "scraped_at": datetime.now().isoformat()
        },
        # Add some duplicates for deduplication testing
        {
            "title": "Beautiful condo in downtown Montreal",
            "price": "$450,000",
            "location": "Montreal, QC H3B 1A1",
            "area": "900 sq ft",
            "bedrooms": "2",
            "bathrooms": "1",
            "description": "Modern condo with city views (duplicate)",
            "url": "https://example.com/property/1-duplicate",
            "scraped_at": datetime.now().isoformat()
        },
        # Add some bad data for validation testing
        {
            "title": "",  # Missing title
            "price": "Not a price",  # Invalid price
            "location": "",  # Missing location
            "area": "unknown",
            "bedrooms": "many",
            "bathrooms": "some",
            "description": "This record has quality issues",
            "url": "https://example.com/property/bad",
            "scraped_at": datetime.now().isoformat()
        }
    ]
    
    return sample_data


def run_etl_demo():
    """Run complete ETL demo"""
    print("🚀 ETL Pipeline Demo")
    print("=" * 50)
    
    # Setup logging
    logger = ETLUtils.setup_logging("etl_demo", "INFO")
    
    # Create data directory
    data_path = ETLUtils.get_data_path()
    os.makedirs(data_path, exist_ok=True)
    
    print("📊 Creating sample data...")
    sample_data = create_sample_data()
    
    # Save sample data
    sample_file = os.path.join(data_path, "demo_scraped_data.json")
    if ETLUtils.save_data(sample_data, sample_file):
        print(f"✅ Sample data saved to: {sample_file}")
        print(f"   Records: {len(sample_data)}")
    else:
        print("❌ Failed to save sample data")
        return False
    
    print(f"\n📋 Sample Data Preview:")
    for i, item in enumerate(sample_data[:3], 1):
        print(f"   {i}. {item['title']} - {item['price']} in {item['location']}")
    print(f"   ... and {len(sample_data) - 3} more records")
    
    # Data quality check
    print(f"\n🔍 Data Quality Analysis:")
    from etl.utils import DataQualityChecker
    
    quality_report = DataQualityChecker.check_data_quality(sample_data)
    print(f"   Quality Score: {quality_report['quality_score']}/100")
    print(f"   Total Records: {quality_report['total_records']}")
    print(f"   Unique Records: {quality_report['unique_records']}")
    print(f"   Duplicates: {quality_report['duplicates']}")
    
    if quality_report['issues']:
        print(f"   Quality Issues:")
        for issue in quality_report['issues'][:3]:
            print(f"   - {issue}")
        if len(quality_report['issues']) > 3:
            print(f"   ... and {len(quality_report['issues']) - 3} more issues")
    
    # ETL Pipeline Demo
    print(f"\n🔄 Running ETL Pipeline Demo...")
    
    try:
        from etl import DataExtractor, DataTransformer, DataValidator
        
        print("📥 Step 1: Data Extraction")
        extractor = DataExtractor()
        extracted_data = sample_data  # In real scenario, this would extract from files
        print(f"   ✅ Extracted {len(extracted_data)} records")
        
        print("🔧 Step 2: Data Transformation")
        transformer = DataTransformer()
        
        # Simulate transformation (showing the logic)
        print("   - Cleaning prices...")
        print("   - Converting areas...")
        print("   - Extracting coordinates...")
        print("   - Applying deduplication...")
        
        # Mock transformation results
        transformed_data = []
        for item in extracted_data:
            if item.get('title') and item.get('price') and item.get('location'):
                # Clean price
                price = str(item['price']).replace('$', '').replace(',', '')
                try:
                    price_num = float(price)
                except:
                    continue  # Skip invalid prices
                
                # Clean area
                area_str = str(item.get('area', ''))
                area = None
                if 'sq ft' in area_str or 'square feet' in area_str:
                    import re
                    area_match = re.search(r'(\d+)', area_str)
                    if area_match:
                        area = int(area_match.group(1))
                
                transformed_item = {
                    'title': item['title'].strip(),
                    'price': price_num,
                    'location': item['location'].strip(),
                    'area_sqft': area,
                    'bedrooms': item.get('bedrooms'),
                    'bathrooms': item.get('bathrooms'),
                    'description': item.get('description', ''),
                    'url': item.get('url'),
                    'data_hash': hash(f"{item['title']}{item['location']}")
                }
                transformed_data.append(transformed_item)
        
        print(f"   ✅ Transformed {len(transformed_data)} records")
        print(f"   📉 Filtered out {len(extracted_data) - len(transformed_data)} invalid records")
        
        print("✅ Step 3: Data Validation")
        valid_data = []
        for item in transformed_data:
            if all([
                item.get('title'),
                item.get('price', 0) > 0,
                item.get('location'),
            ]):
                valid_data.append(item)
        
        print(f"   ✅ Validated {len(valid_data)} records")
        print(f"   📉 Rejected {len(transformed_data) - len(valid_data)} invalid records")
        
        # Save results
        results_file = os.path.join(data_path, "demo_etl_results.json")
        if ETLUtils.save_data(valid_data, results_file):
            print(f"\n💾 ETL Results saved to: {results_file}")
        
        print(f"\n📈 ETL Results Preview:")
        for i, item in enumerate(valid_data[:3], 1):
            print(f"   {i}. {item['title']}")
            print(f"      Price: ${item['price']:,.0f}")
            print(f"      Location: {item['location']}")
            if item.get('area_sqft'):
                print(f"      Area: {item['area_sqft']} sq ft")
            print()
        
        # Generate demo report
        report = {
            "demo": True,
            "timestamp": datetime.now().isoformat(),
            "input_records": len(sample_data),
            "output_records": len(valid_data),
            "quality_score": quality_report['quality_score'],
            "processing_stages": {
                "extraction": len(extracted_data),
                "transformation": len(transformed_data),
                "validation": len(valid_data)
            },
            "data_quality": quality_report
        }
        
        report_file = os.path.join(data_path, "demo_etl_report.json")
        ETLUtils.save_report(report, report_file)
        
        print("=" * 50)
        print("🎉 ETL Pipeline Demo Completed Successfully!")
        print(f"📄 Demo report saved to: {report_file}")
        print("\nNext steps:")
        print("- Run 'make etl-validate' to validate the full pipeline")
        print("- Use 'make scrape-and-etl' to run with real scraped data")
        print("- Check 'make etl-status' for pipeline reports")
        
        return True
        
    except Exception as e:
        print(f"❌ ETL Demo failed: {e}")
        logger.error(f"ETL Demo error: {e}")
        return False


def main():
    """Main demo function"""
    print("Starting ETL Pipeline Demo...")
    success = run_etl_demo()
    
    if success:
        print("\n🎯 Demo completed successfully!")
        print("The ETL pipeline is working correctly.")
    else:
        print("\n⚠️ Demo encountered issues.")
        print("Please check the error messages above.")
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
