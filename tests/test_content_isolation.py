"""
Critical test: Ensure no prior client content can leak into Grainger deliverables.
This test should ALWAYS pass. Any failure is a critical bug.
"""

import pytest
import sys
from pathlib import Path

# Add the project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mro_intelligence.config.content_blocklist import BLOCKED_TERMS, BLOCKED_PATTERNS, check_content


class TestNoContamination:
    """Tests to ensure no prior client content exists in the codebase"""

    def test_no_blocked_terms_in_source_code(self):
        """Scan all Python files for blocked terms."""
        violations = []

        for py_file in Path("mro_intelligence").rglob("*.py"):
            content = py_file.read_text()
            # Skip the blocklist file itself
            if "content_blocklist" in str(py_file):
                continue
            # Skip grainger_profile.py - it legitimately contains exclude_keywords
            if "grainger_profile" in str(py_file):
                continue

            file_violations = check_content(content)
            if file_violations:
                violations.append(f"{py_file}: {file_violations}")

        assert not violations, f"Contamination found:\n" + "\n".join(violations)

    def test_no_blocked_terms_in_config(self):
        """Scan config files for blocked terms (excluding blocklist and grainger profile exclude list)."""
        violations = []

        for config_file in Path("config").rglob("*.py"):
            # Skip blocklist file
            if "blocklist" in str(config_file):
                continue
            # Skip grainger_profile.py - it legitimately contains exclude_keywords
            if "grainger_profile" in str(config_file):
                continue
            content = config_file.read_text()
            file_violations = check_content(content)
            if file_violations:
                violations.append(f"{config_file}: {file_violations}")

        # Also check mro_intelligence/config
        for config_file in Path("mro_intelligence/config").rglob("*.py"):
            if "blocklist" in str(config_file):
                continue
            # Skip grainger_profile.py - it legitimately contains exclude_keywords
            if "grainger_profile" in str(config_file):
                continue
            content = config_file.read_text()
            file_violations = check_content(content)
            if file_violations:
                violations.append(f"{config_file}: {file_violations}")

        assert not violations, f"Contamination in config:\n" + "\n".join(violations)

    def test_no_blocked_terms_in_templates(self):
        """Scan any template files."""
        violations = []

        for template_file in Path(".").rglob("*.html"):
            # Skip htmlcov directory (coverage reports contain blocklist code)
            if "htmlcov" in str(template_file):
                continue
            content = template_file.read_text()
            file_violations = check_content(content)
            if file_violations:
                violations.append(f"{template_file}: {file_violations}")

        for template_file in Path(".").rglob("*.jinja*"):
            content = template_file.read_text()
            file_violations = check_content(content)
            if file_violations:
                violations.append(f"{template_file}: {file_violations}")

        assert not violations, f"Contamination in templates:\n" + "\n".join(violations)

    def test_no_contamination_in_readme(self):
        """README should not mention prior client terms."""
        readme_path = Path("README.md")
        if readme_path.exists():
            readme = readme_path.read_text()
            violations = check_content(readme)
            assert not violations, f"Contamination in README:\n{violations}"

    def test_no_contamination_in_agents_md(self):
        """AGENTS.md should not mention prior client terms."""
        agents_path = Path("AGENTS.md")
        if agents_path.exists():
            agents = agents_path.read_text()
            violations = check_content(agents)
            assert not violations, f"Contamination in AGENTS.md:\n{violations}"

    def test_output_directory_clean(self):
        """Ensure no old outputs with contaminated names exist."""
        violations = []
        outputs_dir = Path("outputs")

        if outputs_dir.exists():
            for output_file in outputs_dir.rglob("*"):
                if output_file.is_file() and output_file.suffix in [".docx", ".json", ".txt"]:
                    # For text files, check content
                    if output_file.suffix in [".json", ".txt"]:
                        try:
                            content = output_file.read_text()
                            file_violations = check_content(content)
                            if file_violations:
                                violations.append(f"{output_file}: {file_violations}")
                        except Exception:
                            pass

        assert not violations, f"Contaminated outputs found:\n" + "\n".join(violations)

    def test_blocklist_is_comprehensive(self):
        """Verify blocklist contains essential terms."""
        essential_terms = [
            "solairus",
            "aviation",
            "aircraft",
            "pilot",
            "jet fuel",
            "fbo",
            "charter",
            "high net worth",
        ]

        blocked_terms_lower = [t.lower() for t in BLOCKED_TERMS]

        for term in essential_terms:
            assert term in blocked_terms_lower, f"Essential blocked term missing: {term}"


class TestGraingerSpecificContent:
    """Verify Grainger-specific content is in place."""

    def test_grainger_mentioned_in_readme(self):
        """README should mention Grainger."""
        readme_path = Path("README.md")
        if readme_path.exists():
            readme = readme_path.read_text().lower()
            assert "grainger" in readme or "mro" in readme, "README should mention Grainger or MRO"

    def test_mro_package_structure(self):
        """MRO package should exist with correct structure."""
        assert Path("mro_intelligence").exists(), "mro_intelligence package not found"
        assert Path("mro_intelligence/__init__.py").exists(), "Package init file missing"
        assert Path("mro_intelligence/core").exists(), "Core module missing"
        assert Path("mro_intelligence/cli.py").exists(), "CLI module missing"

    def test_no_contaminated_directory_names(self):
        """No directories should contain prior client name."""
        violations = []

        for path in Path(".").rglob("*"):
            if ".git" in str(path):
                continue
            # Skip test files that reference the contamination check
            if "test_content_isolation" in str(path):
                continue
            if "solairus" in path.name.lower():
                violations.append(str(path))

        assert not violations, f"Contamination in path names:\n" + "\n".join(violations)


class TestContentBlocklistFunctionality:
    """Test that the blocklist functions work correctly."""

    def test_check_content_detects_blocked_terms(self):
        """Verify check_content catches blocked terms."""
        violations = check_content("This is about Solairus Aviation")
        assert len(violations) > 0, "Should detect blocked terms"

    def test_check_content_detects_aviation_terms(self):
        """Verify check_content catches aviation terms."""
        violations = check_content("The business aviation industry is growing")
        assert len(violations) > 0, "Should detect 'business aviation'"

    def test_check_content_allows_clean_text(self):
        """Verify check_content allows MRO content."""
        violations = check_content(
            "Grainger MRO market analysis shows strong manufacturing demand"
        )
        assert len(violations) == 0, f"Should allow MRO content, got: {violations}"

    def test_check_content_detects_n_numbers(self):
        """Verify check_content catches aircraft N-numbers."""
        violations = check_content("Aircraft registration N12345 was spotted")
        assert len(violations) > 0, "Should detect N-number pattern"

    def test_check_content_case_insensitive(self):
        """Verify check_content is case insensitive."""
        violations = check_content("SOLAIRUS AVIATION provides services")
        assert len(violations) > 0, "Should detect uppercase blocked terms"


class TestProcessorValidation:
    """Test that processors validate content."""

    def test_ergomind_processor_has_validation(self):
        """Verify ErgoMind processor has validate_response method."""
        from mro_intelligence.core.processors.ergomind import ErgoMindProcessor

        processor = ErgoMindProcessor()
        assert hasattr(processor, "validate_response"), "Processor should have validate_response"

    def test_ergomind_processor_filters_blocked_content(self):
        """Verify processor filters blocked content."""
        from mro_intelligence.core.processors.ergomind import ErgoMindProcessor

        processor = ErgoMindProcessor()
        result = processor.validate_response("Solairus Aviation is expanding")
        assert result is None, "Should filter blocked content"

    def test_ergomind_processor_allows_clean_content(self):
        """Verify processor allows clean content."""
        from mro_intelligence.core.processors.ergomind import ErgoMindProcessor

        processor = ErgoMindProcessor()
        result = processor.validate_response("Manufacturing output increased 5%")
        assert result is not None, "Should allow clean content"


class TestDocumentGeneratorValidation:
    """Test that document generator validates output."""

    def test_generator_has_validation(self):
        """Verify DocumentGenerator has validate_output method."""
        from mro_intelligence.core.document.generator import DocumentGenerator

        generator = DocumentGenerator()
        assert hasattr(generator, "validate_output"), "Generator should have validate_output"

    def test_generator_rejects_blocked_content(self):
        """Verify generator rejects blocked content."""
        from mro_intelligence.core.document.generator import DocumentGenerator

        generator = DocumentGenerator()

        with pytest.raises(ValueError) as exc_info:
            generator.validate_output("Report for Solairus Aviation")

        assert "CONTAMINATION DETECTED" in str(exc_info.value)

    def test_generator_allows_clean_content(self):
        """Verify generator allows clean content."""
        from mro_intelligence.core.document.generator import DocumentGenerator

        generator = DocumentGenerator()
        # Should not raise
        generator.validate_output("MRO Market Intelligence Report for Grainger")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
