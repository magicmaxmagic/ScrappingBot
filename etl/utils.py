"""
Utilities for ETL pipeline
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class ETLUtils:
    """Utility functions for ETL operations"""
    
    @staticmethod
    def get_base_path():
        """Get base path depending on environment (Docker or local)"""
        if os.path.exists('/app'):
            return '/app'
        else:
            # Local development - use current directory
            return str(Path(__file__).parent.parent.absolute())
    
    @staticmethod
    def get_data_path():
        """Get data directory path"""
        base_path = ETLUtils.get_base_path()
        return os.path.join(base_path, 'data')
    
    @staticmethod
    def setup_logging(name: str = "etl", level: str = "INFO") -> logging.Logger:
        """Setup logging for ETL operations"""
        logger = logging.getLogger(name)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
            
        logger.setLevel(getattr(logging, level.upper()))
        
        # Create logs directory if it doesn't exist
        base_path = ETLUtils.get_base_path()
        logs_dir = os.path.join(base_path, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # File handler
        fh = logging.FileHandler(os.path.join(logs_dir, f'{name}.log'))
        fh.setLevel(getattr(logging, level.upper()))
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    @staticmethod
    def load_raw_data(file_path: str) -> Optional[List[Dict[str, Any]]]:
        """Load raw scraped data from JSON file"""
        if not os.path.exists(file_path):
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading data from {file_path}: {e}")
            return None
    
    @staticmethod
    def save_data(data: List[Dict[str, Any]], file_path: str) -> bool:
        """Save data to JSON file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            logging.error(f"Error saving data to {file_path}: {e}")
            return False
    
    @staticmethod
    def generate_report(
        phase: str,
        start_time: datetime,
        end_time: datetime,
        stats: Dict[str, Any],
        errors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate ETL phase report"""
        duration = (end_time - start_time).total_seconds()
        
        report = {
            "phase": phase,
            "timestamp": end_time.isoformat(),
            "duration_seconds": duration,
            "success": len(errors or []) == 0,
            "stats": stats,
            "errors": errors or []
        }
        
        return report
    
    @staticmethod
    def save_report(report: Dict[str, Any], file_path: str) -> bool:
        """Save report to JSON file"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            logging.error(f"Error saving report to {file_path}: {e}")
            return False
    
    @staticmethod
    def validate_data_structure(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate data structure and return stats"""
        if not data:
            return {"valid": False, "error": "No data provided"}
        
        # Check if it's a list
        if not isinstance(data, list):
            return {"valid": False, "error": "Data is not a list"}
        
        # Sample validation on first item
        if not data:
            return {"valid": False, "error": "Data list is empty"}
        
        sample = data[0]
        if not isinstance(sample, dict):
            return {"valid": False, "error": "Data items are not dictionaries"}
        
        # Basic field presence check
        required_fields = ['title', 'price', 'location']
        missing_fields = []
        
        for field in required_fields:
            if field not in sample:
                missing_fields.append(field)
        
        stats = {
            "valid": len(missing_fields) == 0,
            "total_records": len(data),
            "sample_keys": list(sample.keys()),
            "missing_required_fields": missing_fields
        }
        
        if missing_fields:
            stats["error"] = f"Missing required fields: {', '.join(missing_fields)}"
        
        return stats
    
    @staticmethod
    def get_file_stats(file_path: str) -> Dict[str, Any]:
        """Get file statistics"""
        if not os.path.exists(file_path):
            return {"exists": False, "error": "File does not exist"}
        
        try:
            stat = os.stat(file_path)
            return {
                "exists": True,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
        except Exception as e:
            return {"exists": False, "error": str(e)}
    
    @staticmethod
    def clean_temp_files(pattern: str = "*.tmp") -> int:
        """Clean temporary files"""
        data_path = ETLUtils.get_data_path()
        temp_dir = Path(os.path.join(data_path, "temp"))
        if not temp_dir.exists():
            return 0
        
        count = 0
        for file in temp_dir.glob(pattern):
            try:
                file.unlink()
                count += 1
            except Exception as e:
                logging.warning(f"Could not delete {file}: {e}")
        
        return count


class DataQualityChecker:
    """Data quality validation utilities"""
    
    @staticmethod
    def check_data_quality(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Comprehensive data quality check"""
        if not data:
            return {"quality_score": 0, "issues": ["No data provided"]}
        
        issues = []
        total_records = len(data)
        
        # Check for duplicates based on title and location
        unique_items = set()
        duplicates = 0
        
        # Check for missing critical fields
        missing_titles = 0
        missing_prices = 0
        missing_locations = 0
        
        # Check for data validity
        invalid_prices = 0
        
        for item in data:
            # Duplicate check
            key = (item.get('title', ''), item.get('location', ''))
            if key in unique_items:
                duplicates += 1
            else:
                unique_items.add(key)
            
            # Missing fields check
            if not item.get('title'):
                missing_titles += 1
            if not item.get('price'):
                missing_prices += 1
            if not item.get('location'):
                missing_locations += 1
            
            # Price validation
            price = item.get('price')
            if price and not isinstance(price, (int, float)) and not str(price).replace('.', '').replace(',', '').isdigit():
                invalid_prices += 1
        
        # Calculate quality score
        quality_issues = [
            duplicates,
            missing_titles,
            missing_prices,
            missing_locations,
            invalid_prices
        ]
        
        max_issues = sum(quality_issues)
        quality_score = max(0, 100 - (max_issues / total_records * 100))
        
        # Compile issues
        if duplicates > 0:
            issues.append(f"{duplicates} duplicate records found")
        if missing_titles > 0:
            issues.append(f"{missing_titles} records missing titles")
        if missing_prices > 0:
            issues.append(f"{missing_prices} records missing prices")
        if missing_locations > 0:
            issues.append(f"{missing_locations} records missing locations")
        if invalid_prices > 0:
            issues.append(f"{invalid_prices} records with invalid prices")
        
        return {
            "quality_score": round(quality_score, 2),
            "total_records": total_records,
            "unique_records": len(unique_items),
            "duplicates": duplicates,
            "missing_titles": missing_titles,
            "missing_prices": missing_prices,
            "missing_locations": missing_locations,
            "invalid_prices": invalid_prices,
            "issues": issues
        }
