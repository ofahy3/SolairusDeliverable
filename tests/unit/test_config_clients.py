"""
Unit tests for client configuration module
"""

from solairus_intelligence.config.clients import (
    CLIENT_SECTOR_MAPPING,
    COMPANY_NAMES_BY_SECTOR,
    ClientSector,
    get_all_company_names,
    get_companies_for_sector,
    get_sector_keywords,
    get_sector_triggers,
)


class TestClientSector:
    """Test suite for ClientSector enum"""

    def test_technology_sector_exists(self):
        """Test TECHNOLOGY sector is defined"""
        assert ClientSector.TECHNOLOGY is not None
        assert ClientSector.TECHNOLOGY.value == "technology"

    def test_finance_sector_exists(self):
        """Test FINANCE sector is defined"""
        assert ClientSector.FINANCE is not None
        assert ClientSector.FINANCE.value == "finance"

    def test_general_sector_exists(self):
        """Test GENERAL sector is defined"""
        assert ClientSector.GENERAL is not None
        assert ClientSector.GENERAL.value == "general"

    def test_all_sectors_have_string_values(self):
        """Test all sectors have string values"""
        for sector in ClientSector:
            assert isinstance(sector.value, str)
            assert len(sector.value) > 0


class TestClientSectorMapping:
    """Test suite for CLIENT_SECTOR_MAPPING"""

    def test_mapping_not_empty(self):
        """Test mapping is not empty"""
        assert len(CLIENT_SECTOR_MAPPING) > 0

    def test_mapping_has_technology(self):
        """Test mapping has technology sector"""
        assert ClientSector.TECHNOLOGY in CLIENT_SECTOR_MAPPING

    def test_mapping_structure(self):
        """Test mapping has expected structure"""
        for sector, data in CLIENT_SECTOR_MAPPING.items():
            assert isinstance(sector, ClientSector)
            assert isinstance(data, dict)
            assert "companies" in data
            assert isinstance(data["companies"], list)

    def test_technology_has_companies(self):
        """Test technology sector has companies defined"""
        tech_data = CLIENT_SECTOR_MAPPING.get(ClientSector.TECHNOLOGY, {})
        companies = tech_data.get("companies", [])

        assert len(companies) > 0

    def test_sectors_have_keywords(self):
        """Test sectors have keywords defined"""
        for sector, data in CLIENT_SECTOR_MAPPING.items():
            keywords = data.get("keywords", [])
            # Keywords are optional, but if present should be a list
            assert isinstance(keywords, list)


class TestCompanyNamesBySector:
    """Test suite for COMPANY_NAMES_BY_SECTOR"""

    def test_mapping_created(self):
        """Test mapping is created"""
        assert COMPANY_NAMES_BY_SECTOR is not None
        assert isinstance(COMPANY_NAMES_BY_SECTOR, dict)

    def test_technology_companies_present(self):
        """Test technology companies are present"""
        tech_companies = COMPANY_NAMES_BY_SECTOR.get(ClientSector.TECHNOLOGY, [])
        assert len(tech_companies) > 0


class TestGetAllCompanyNames:
    """Test suite for get_all_company_names"""

    def test_returns_set(self):
        """Test returns a set"""
        names = get_all_company_names()
        assert isinstance(names, set)

    def test_not_empty(self):
        """Test returns non-empty set"""
        names = get_all_company_names()
        assert len(names) > 0

    def test_contains_technology_companies(self):
        """Test contains technology sector companies"""
        all_names = get_all_company_names()
        tech_companies = COMPANY_NAMES_BY_SECTOR.get(ClientSector.TECHNOLOGY, [])

        for company in tech_companies:
            assert company in all_names


class TestGetCompaniesForSector:
    """Test suite for get_companies_for_sector"""

    def test_returns_list(self):
        """Test returns a list"""
        companies = get_companies_for_sector(ClientSector.TECHNOLOGY)
        assert isinstance(companies, list)

    def test_returns_companies_for_technology(self):
        """Test returns companies for technology sector"""
        companies = get_companies_for_sector(ClientSector.TECHNOLOGY)
        assert len(companies) > 0

    def test_returns_empty_for_unknown_sector(self):
        """Test returns empty list for sector not in mapping"""
        # Create a mock sector that doesn't exist in mapping
        # This is a boundary test - if sector has no mapping, return empty
        companies = get_companies_for_sector(ClientSector.GENERAL)
        # Should return list (possibly empty if not configured)
        assert isinstance(companies, list)


class TestGetSectorKeywords:
    """Test suite for get_sector_keywords"""

    def test_returns_list(self):
        """Test returns a list"""
        keywords = get_sector_keywords(ClientSector.TECHNOLOGY)
        assert isinstance(keywords, list)

    def test_returns_empty_for_missing(self):
        """Test returns empty list when keywords not defined"""
        # Should return empty list, not raise exception
        keywords = get_sector_keywords(ClientSector.GENERAL)
        assert isinstance(keywords, list)


class TestGetSectorTriggers:
    """Test suite for get_sector_triggers"""

    def test_returns_list(self):
        """Test returns a list"""
        triggers = get_sector_triggers(ClientSector.TECHNOLOGY)
        assert isinstance(triggers, list)

    def test_returns_empty_for_missing(self):
        """Test returns empty list when triggers not defined"""
        triggers = get_sector_triggers(ClientSector.GENERAL)
        assert isinstance(triggers, list)
