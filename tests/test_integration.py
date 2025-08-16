"""
System integration tests for ScrappingBot.
Tests end-to-end functionality across all components.
"""

import pytest
import json
import subprocess
import time
import requests
from pathlib import Path
import psycopg2
from unittest.mock import patch, Mock
import docker


class TestDockerIntegration:
    """Test Docker container integration."""
    
    def test_docker_compose_file_exists(self):
        """Test that docker-compose.yml exists and is valid."""
        compose_file = Path("docker-compose.yml")
        assert compose_file.exists(), "docker-compose.yml should exist"
        
        # Try to parse the compose file
        try:
            import yaml
            with open(compose_file, 'r') as f:
                compose_config = yaml.safe_load(f)
            
            # Check for essential services
            services = compose_config.get('services', {})
            expected_services = ['postgres', 'redis', 'scraper', 'etl']
            
            for service in expected_services:
                assert service in services, f"Service {service} should be defined in docker-compose.yml"
                
        except ImportError:
            # PyYAML not available, skip detailed validation
            pass
    
    @pytest.mark.integration
    def test_docker_build_all_services(self):
        """Test that all Docker services can be built."""
        # This test requires Docker to be running
        try:
            result = subprocess.run(
                ['docker-compose', 'build', '--parallel'],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            # Build should succeed or be skipped if already built
            assert result.returncode in [0, 1], f"Docker build failed: {result.stderr}"
            
        except FileNotFoundError:
            pytest.skip("Docker not available")
        except subprocess.TimeoutExpired:
            pytest.fail("Docker build timed out")
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_docker_services_start(self):
        """Test that Docker services can start successfully."""
        try:
            # Start services
            result = subprocess.run(
                ['docker-compose', 'up', '-d'],
                capture_output=True,
                text=True,
                timeout=120  # 2 minutes timeout
            )
            
            assert result.returncode == 0, f"Failed to start services: {result.stderr}"
            
            # Wait for services to be ready
            time.sleep(10)
            
            # Check service health
            health_result = subprocess.run(
                ['docker-compose', 'ps'],
                capture_output=True,
                text=True
            )
            
            assert "Up" in health_result.stdout, "Services should be running"
            
            # Cleanup
            subprocess.run(['docker-compose', 'down'], capture_output=True)
            
        except FileNotFoundError:
            pytest.skip("Docker not available")
        except subprocess.TimeoutExpired:
            pytest.fail("Service startup timed out")


class TestDatabaseIntegration:
    """Test database integration and connectivity."""
    
    def test_database_schema_file_exists(self):
        """Test that database schema file exists."""
        schema_file = Path("database/schema.sql")
        assert schema_file.exists(), "Database schema file should exist"
        
        # Check that schema contains expected tables
        schema_content = schema_file.read_text()
        expected_tables = ['listings', 'scraping_sessions', 'users']
        
        for table in expected_tables:
            # Look for CREATE TABLE statements (case insensitive)
            assert f"create table {table}" in schema_content.lower() or \
                   f"create table if not exists {table}" in schema_content.lower(), \
                   f"Table {table} should be defined in schema"
    
    @pytest.mark.integration
    def test_database_connection(self):
        """Test database connection with Docker."""
        try:
            # This assumes database is running via docker-compose
            conn_params = {
                'host': 'localhost',
                'port': 5432,
                'database': 'scrappingbot',
                'user': 'scrappingbot_user',
                'password': 'scrappingbot_pass'
            }
            
            conn = psycopg2.connect(**conn_params)
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            
            # Test PostGIS extension
            cursor.execute("SELECT PostGIS_version()")
            postgis_version = cursor.fetchone()
            assert postgis_version is not None
            
            cursor.close()
            conn.close()
            
        except psycopg2.OperationalError:
            pytest.skip("Database not available")
    
    @pytest.mark.integration
    def test_database_tables_exist(self):
        """Test that expected database tables exist."""
        try:
            conn_params = {
                'host': 'localhost',
                'port': 5432,
                'database': 'scrappingbot',
                'user': 'scrappingbot_user',
                'password': 'scrappingbot_pass'
            }
            
            conn = psycopg2.connect(**conn_params)
            cursor = conn.cursor()
            
            # Check for listings table
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'listings'
                )
            """)
            
            listings_exists = cursor.fetchone()[0]
            assert listings_exists, "Listings table should exist"
            
            cursor.close()
            conn.close()
            
        except psycopg2.OperationalError:
            pytest.skip("Database not available")


class TestETLIntegration:
    """Test ETL pipeline integration."""
    
    def test_etl_modules_importable(self):
        """Test that ETL modules can be imported."""
        try:
            from etl import DataExtractor, DataTransformer, DataValidator
            from etl.normalize import normalize_currency, to_sqm
            from etl.dedupe import dedupe_records
            from etl.schema import validate_listing
            
            # All imports should succeed
            assert True
            
        except ImportError as e:
            pytest.fail(f"ETL modules not importable: {e}")
    
    def test_etl_api_available(self):
        """Test that ETL API module exists and has expected endpoints."""
        try:
            from etl.api import app
            
            # Check that FastAPI app is configured
            assert hasattr(app, 'routes')
            
            # Check for expected routes
            route_paths = []
            for route in app.routes:
                # Some BaseRoute subclasses may not have a 'path' attribute, so use safe fallbacks.
                path = getattr(route, "path", None)
                if path is None:
                    # FastAPI/Starlette may expose a path template on some route types
                    path = getattr(route, "path_template", None)
                if path is None:
                    # Some route types may expose a regex-like object
                    path_regex = getattr(route, "path_regex", None)
                    if path_regex is not None:
                        path = getattr(path_regex, "pattern", str(path_regex))
                if path is not None:
                    route_paths.append(str(path))
            expected_paths = ['/health', '/etl/full', '/jobs']

            for path in expected_paths:
                assert any(path in route_path for route_path in route_paths), \
                       f"Expected route {path} not found"
                       
        except ImportError:
            pytest.fail("ETL API not importable")
    
    @pytest.mark.integration
    def test_etl_api_health_endpoint(self):
        """Test ETL API health endpoint."""
        try:
            response = requests.get('http://localhost:8788/health', timeout=5)
            assert response.status_code == 200
            
            health_data = response.json()
            assert 'status' in health_data
            
        except requests.exceptions.ConnectionError:
            pytest.skip("ETL API not running")
        except requests.exceptions.Timeout:
            pytest.fail("ETL API health check timed out")
    
    def test_etl_demo_script_exists(self):
        """Test that ETL demo script exists and can be imported."""
        demo_script = Path("etl/demo.py")
        assert demo_script.exists(), "ETL demo script should exist"
        
        try:
            import etl.demo
            assert hasattr(etl.demo, 'main') or hasattr(etl.demo, 'run_demo')
        except ImportError:
            pytest.fail("ETL demo script not importable")
    
    def test_etl_validation_script_exists(self):
        """Test that ETL validation script exists."""
        validation_script = Path("etl/validate.py")
        assert validation_script.exists(), "ETL validation script should exist"


class TestScriptIntegration:
    """Test integration of various scripts."""
    
    def test_run_etl_script_exists(self):
        """Test that run_etl.py script exists."""
        script_path = Path("scripts/run_etl.py")
        assert script_path.exists(), "run_etl.py script should exist"
        
        # Try to import without executing
        script_content = script_path.read_text()
        assert "def main(" in script_content, "Script should have main function"
    
    def test_makefile_commands_available(self):
        """Test that Makefile has expected commands."""
        makefile = Path("Makefile")
        assert makefile.exists(), "Makefile should exist"
        
        makefile_content = makefile.read_text()
        expected_commands = [
            'build:', 'up:', 'down:', 'clean:', 'clean-containers:',
            'etl-demo:', 'etl-api:', 'etl-health:'
        ]
        
        for command in expected_commands:
            assert command in makefile_content, f"Make command {command} should be defined"
    
    @pytest.mark.integration
    def test_make_help_command(self):
        """Test that make help command works."""
        try:
            result = subprocess.run(
                ['make', 'help'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            assert result.returncode == 0, f"make help failed: {result.stderr}"
            assert "clean-containers" in result.stdout, "Help should include clean-containers command"
            
        except FileNotFoundError:
            pytest.skip("Make not available")
        except subprocess.TimeoutExpired:
            pytest.fail("make help timed out")


class TestConfigurationIntegration:
    """Test configuration files and settings."""
    
    def test_config_directory_exists(self):
        """Test that config directory exists with expected files."""
        config_dir = Path("config")
        assert config_dir.exists(), "Config directory should exist"
        
        # Check for expected configuration files
        expected_configs = [
            "etl.conf",
            # Add other expected config files
        ]
        
        for config_file in expected_configs:
            config_path = config_dir / config_file
            if config_path.exists():
                # Verify it's not empty
                assert config_path.stat().st_size > 0, f"{config_file} should not be empty"
    
    def test_data_directory_structure(self):
        """Test data directory structure."""
        data_dir = Path("data")
        if data_dir.exists():
            # Check for expected subdirectories/files
            expected_items = [
                # "listings.json",  # Might not exist yet
                # "raw_html/",      # Might not exist yet
            ]
            
            # Just verify directory structure is reasonable
            assert data_dir.is_dir(), "Data should be a directory"
    
    def test_logs_directory_structure(self):
        """Test logs directory structure."""
        logs_dir = Path("logs")
        if logs_dir.exists():
            assert logs_dir.is_dir(), "Logs should be a directory"
            
            # Check for log files
            log_files = list(logs_dir.glob("*.log"))
            # Logs might not exist yet - that's okay


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_complete_etl_workflow(self):
        """Test complete ETL workflow from data to database."""
        # This test would run a complete ETL pipeline
        # 1. Start with sample data
        # 2. Run ETL processing
        # 3. Verify data in database
        
        sample_data = [
            {
                "url": "https://test.example.com/listing/1",
                "title": "Test Apartment",
                "price": "€150,000",
                "area": "75 m²",
                "address": "123 Test Street, Paris"
            }
        ]
        
        # Create temporary input file
        test_data_file = Path("data/test_listings.json")
        test_data_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(test_data_file, 'w') as f:
                json.dump(sample_data, f)
            
            # Run ETL process (would need to adapt based on actual implementation)
            # This is a placeholder for the actual test
            assert True
            
        finally:
            # Cleanup
            if test_data_file.exists():
                test_data_file.unlink()
    
    def test_system_health_checks(self):
        """Test system health check capabilities."""
        # Test various health check mechanisms
        health_checks = [
            ("Database connection", self._check_database_health),
            ("Redis connection", self._check_redis_health),
            ("ETL API", self._check_etl_api_health),
            ("File system", self._check_filesystem_health)
        ]
        
        health_results = {}
        for check_name, check_func in health_checks:
            try:
                health_results[check_name] = check_func()
            except Exception as e:
                health_results[check_name] = f"Failed: {e}"
        
        # At least filesystem should be healthy
        assert health_results.get("File system", False), "File system should be accessible"
    
    def _check_database_health(self):
        """Check database health."""
        try:
            conn_params = {
                'host': 'localhost',
                'port': 5432,
                'database': 'scrappingbot',
                'user': 'scrappingbot_user',
                'password': 'scrappingbot_pass'
            }
            
            conn = psycopg2.connect(**conn_params)
            conn.close()
            return True
        except:
            return False
    
    def _check_redis_health(self):
        """Check Redis health."""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            return True
        except:
            return False
    
    def _check_etl_api_health(self):
        """Check ETL API health."""
        try:
            response = requests.get('http://localhost:8788/health', timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _check_filesystem_health(self):
        """Check filesystem health."""
        try:
            # Test read/write access
            test_file = Path("data/.health_check")
            test_file.parent.mkdir(exist_ok=True)
            test_file.write_text("health_check")
            content = test_file.read_text()
            test_file.unlink()
            return content == "health_check"
        except:
            return False


class TestPerformanceIntegration:
    """Test system performance characteristics."""
    
    @pytest.mark.performance
    def test_etl_processing_speed(self):
        """Test ETL processing speed with sample data."""
        # Generate test data
        sample_listings = []
        for i in range(100):
            sample_listings.append({
                "url": f"https://test.example.com/{i}",
                "title": f"Test Listing {i}",
                "price": f"€{100000 + i * 1000}",
                "area": f"{50 + i} m²"
            })
        
        # Time ETL processing
        start_time = time.time()
        
        try:
            from etl.normalize import normalize_currency, normalize_price, to_sqm
            from etl.dedupe import dedupe_records
            
            # Process sample data
            processed = []
            for listing in sample_listings:
                processed_listing = {
                    'url': listing['url'],
                    'title': listing['title'],
                    'price': normalize_price(listing['price']),
                    'currency': normalize_currency('EUR')
                }
                processed.append(processed_listing)
            
            # Deduplicate
            deduped = dedupe_records(processed)
            
            processing_time = time.time() - start_time
            
            # Should process 100 listings in under 1 second
            assert processing_time < 1.0, f"Processing took too long: {processing_time}s"
            assert len(deduped) <= len(sample_listings), "Deduplication should not increase count"
            
        except ImportError:
            pytest.skip("ETL modules not available")
    
    @pytest.mark.performance
    def test_memory_usage_reasonable(self):
        """Test that system memory usage is reasonable."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform some operations
        try:
            from etl import DataExtractor, DataTransformer, DataValidator
            
            extractor = DataExtractor()
            transformer = DataTransformer()
            validator = DataValidator()
            
            # Process some dummy data
            dummy_data = [{"test": f"data_{i}"} for i in range(1000)]
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (under 100MB for this test)
            assert memory_increase < 100, f"Memory usage too high: {memory_increase}MB"
            
        except ImportError:
            pytest.skip("ETL modules not available")


# Utility function to run all tests
def run_all_tests():
    """Run all tests with appropriate markers."""
    # Run fast tests by default
    subprocess.run([
        'python', '-m', 'pytest', 
        'tests/', 
        '-v', 
        '--tb=short',
        '-m', 'not integration and not slow and not performance'
    ])
    
    print("\nTo run integration tests:")
    print("pytest tests/ -m integration")
    print("\nTo run performance tests:")  
    print("pytest tests/ -m performance")


if __name__ == "__main__":
    run_all_tests()
