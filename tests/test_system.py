#!/usr/bin/env python
"""
Test Suite for Solairus Intelligence Report Generator
Validates all components work together correctly
"""

import asyncio
import sys
from pathlib import Path

# Test color output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_test(message, status="INFO"):
    """Print colored test output"""
    if status == "PASS":
        print(f"{Colors.OKGREEN}✓{Colors.ENDC} {message}")
    elif status == "FAIL":
        print(f"{Colors.FAIL}✗{Colors.ENDC} {message}")
    elif status == "WARN":
        print(f"{Colors.WARNING}⚠{Colors.ENDC} {message}")
    else:
        print(f"{Colors.OKBLUE}ℹ{Colors.ENDC} {message}")

async def test_imports():
    """Test all required imports"""
    print(f"\n{Colors.HEADER}Testing Imports{Colors.ENDC}")
    
    try:
        import aiohttp
        print_test("aiohttp imported successfully", "PASS")
    except ImportError:
        print_test("aiohttp import failed - run: pip install aiohttp", "FAIL")
        return False
        
    try:
        from docx import Document
        print_test("python-docx imported successfully", "PASS")
    except ImportError:
        print_test("python-docx import failed - run: pip install python-docx", "FAIL")
        return False
        
    try:
        import fastapi
        print_test("FastAPI imported successfully", "PASS")
    except ImportError:
        print_test("FastAPI import failed - run: pip install fastapi", "FAIL")
        return False
        
    try:
        import pandas
        print_test("pandas imported successfully", "PASS")
    except ImportError:
        print_test("pandas import failed - run: pip install pandas", "FAIL")
        return False
        
    return True

async def test_ergomind_connection():
    """Test ErgoMind API connection"""
    print(f"\n{Colors.HEADER}Testing ErgoMind Connection{Colors.ENDC}")
    
    try:
        from ergomind_client import ErgoMindClient
        
        client = ErgoMindClient()
        async with client:
            # Test health endpoint
            print_test("Testing ErgoMind API connection...")
            connected = await client.test_connection()
            
            if connected:
                print_test("ErgoMind API connection successful", "PASS")
                return True
            else:
                print_test("ErgoMind API connection failed - check API key and network", "FAIL")
                return False
                
    except Exception as e:
        print_test(f"ErgoMind test failed: {str(e)}", "FAIL")
        return False

async def test_intelligence_processor():
    """Test intelligence processing"""
    print(f"\n{Colors.HEADER}Testing Intelligence Processor{Colors.ENDC}")
    
    try:
        from intelligence_processor import IntelligenceProcessor, ClientSector
        
        processor = IntelligenceProcessor()
        
        # Test with sample text
        sample_text = """
        The Federal Reserve raised interest rates by 25 basis points, 
        signaling continued monetary tightening. This will impact 
        corporate financing and business aviation demand.
        """
        
        result = processor.process_intelligence(sample_text, "economic")
        
        if result.relevance_score > 0:
            print_test(f"Intelligence processing successful (relevance: {result.relevance_score:.2f})", "PASS")
        else:
            print_test("Intelligence processing returned zero relevance", "WARN")
            
        if result.so_what_statement:
            print_test("'So What' statement generated successfully", "PASS")
        else:
            print_test("'So What' statement generation failed", "FAIL")
            
        return True
        
    except Exception as e:
        print_test(f"Intelligence processor test failed: {str(e)}", "FAIL")
        return False

async def test_document_generator():
    """Test document generation"""
    print(f"\n{Colors.HEADER}Testing Document Generator{Colors.ENDC}")
    
    try:
        from document_generator import DocumentGenerator
        from intelligence_processor import IntelligenceItem, SectorIntelligence, ClientSector
        
        generator = DocumentGenerator()
        
        # Create sample data
        sample_item = IntelligenceItem(
            raw_content="Test",
            processed_content="Test intelligence content",
            category="test",
            relevance_score=0.8,
            so_what_statement="This is a test impact statement.",
            affected_sectors=[ClientSector.TECHNOLOGY]
        )
        
        sector_intel = {
            ClientSector.TECHNOLOGY: SectorIntelligence(
                sector=ClientSector.TECHNOLOGY,
                items=[sample_item],
                summary="Test summary"
            )
        }
        
        # Generate test document
        doc = generator.create_report([sample_item], sector_intel, "Test Month")
        
        # Save test document
        output_dir = Path("/mnt/user-data/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = output_dir / "test_report.docx"
        doc.save(str(test_file))
        
        if test_file.exists():
            print_test(f"Test document created successfully: {test_file}", "PASS")
            return True
        else:
            print_test("Document creation failed", "FAIL")
            return False
            
    except Exception as e:
        print_test(f"Document generator test failed: {str(e)}", "FAIL")
        return False

async def test_query_orchestrator():
    """Test query orchestration"""
    print(f"\n{Colors.HEADER}Testing Query Orchestrator{Colors.ENDC}")
    
    try:
        from query_orchestrator import QueryOrchestrator
        
        orchestrator = QueryOrchestrator()
        
        # Check query templates
        template_count = len(orchestrator.query_templates)
        print_test(f"Loaded {template_count} query templates", "PASS")
        
        # Check high-priority queries
        high_priority = [t for t in orchestrator.query_templates if t.priority >= 8]
        print_test(f"Found {len(high_priority)} high-priority queries", "PASS")
        
        return True
        
    except Exception as e:
        print_test(f"Query orchestrator test failed: {str(e)}", "FAIL")
        return False

async def test_full_pipeline():
    """Test the complete pipeline in test mode"""
    print(f"\n{Colors.HEADER}Testing Complete Pipeline (Test Mode){Colors.ENDC}")
    
    try:
        from main import SolairusIntelligenceGenerator
        
        print_test("Initializing report generator...")
        generator = SolairusIntelligenceGenerator()
        
        print_test("Running pipeline in test mode (limited queries)...")
        filepath, status = await generator.generate_monthly_report(test_mode=True)
        
        if status['success']:
            print_test(f"Pipeline completed successfully", "PASS")
            print_test(f"Report saved to: {status['report_path']}", "PASS")
            print_test(f"Quality score: {status['quality_score']:.1%}", "PASS")
            return True
        else:
            print_test(f"Pipeline failed: {status.get('errors', ['Unknown error'])}", "FAIL")
            return False
            
    except Exception as e:
        print_test(f"Pipeline test failed: {str(e)}", "FAIL")
        return False

async def run_all_tests():
    """Run all tests"""
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}Solairus Intelligence Report Generator - Test Suite{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    all_passed = True
    
    # Test imports
    if not await test_imports():
        all_passed = False
        print_test("\nStopping tests - required imports failed", "FAIL")
        return False
    
    # Test individual components
    tests = [
        test_intelligence_processor,
        test_document_generator,
        test_query_orchestrator,
        test_ergomind_connection,
    ]
    
    for test in tests:
        if not await test():
            all_passed = False
    
    # Only run full pipeline if ErgoMind is connected
    if all_passed:
        print_test("\n🚀 All component tests passed! Running full pipeline test...", "INFO")
        if not await test_full_pipeline():
            all_passed = False
    
    # Summary
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
    if all_passed:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✅ ALL TESTS PASSED!{Colors.ENDC}")
        print(f"\nYour system is ready to generate intelligence reports.")
        print(f"\nNext steps:")
        print(f"1. Run the web app: python web_app.py")
        print(f"2. Or generate directly: python main.py --test")
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.ENDC}")
        print(f"\nPlease fix the issues above before proceeding.")
        print(f"Common solutions:")
        print(f"- Install missing dependencies: pip install -r requirements.txt")
        print(f"- Check ErgoMind API credentials in ergomind_client.py")
        print(f"- Ensure you have internet connectivity")
    
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    return all_passed

if __name__ == "__main__":
    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
