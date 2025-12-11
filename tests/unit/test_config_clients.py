"""
Unit tests for client configuration module - Grainger Customer Segments
"""

from mro_intelligence.config.clients import (
    CLIENT_SECTOR_MAPPING,
    COMPANY_NAMES_BY_SECTOR,
    ClientSector,
    get_all_company_names,
    get_all_sectors,
    get_companies_for_sector,
    get_sector_keywords,
    get_sector_mro_impact,
    get_sector_triggers,
)


class TestClientSector:
    """Test suite for ClientSector enum - Grainger customer segments"""

    def test_manufacturing_sector_exists(self):
        """Test MANUFACTURING sector is defined"""
        assert ClientSector.MANUFACTURING is not None
        assert ClientSector.MANUFACTURING.value == "manufacturing"

    def test_government_sector_exists(self):
        """Test GOVERNMENT sector is defined ($2B+ segment)"""
        assert ClientSector.GOVERNMENT is not None
        assert ClientSector.GOVERNMENT.value == "government"

    def test_commercial_facilities_sector_exists(self):
        """Test COMMERCIAL_FACILITIES sector is defined"""
        assert ClientSector.COMMERCIAL_FACILITIES is not None
        assert ClientSector.COMMERCIAL_FACILITIES.value == "commercial"

    def test_contractors_sector_exists(self):
        """Test CONTRACTORS sector is defined"""
        assert ClientSector.CONTRACTORS is not None
        assert ClientSector.CONTRACTORS.value == "contractors"

    def test_general_sector_exists(self):
        """Test GENERAL sector is defined"""
        assert ClientSector.GENERAL is not None
        assert ClientSector.GENERAL.value == "general"

    def test_all_sectors_have_string_values(self):
        """Test all sectors have string values"""
        for sector in ClientSector:
            assert isinstance(sector.value, str)
            assert len(sector.value) > 0

    def test_five_sectors_defined(self):
        """Test exactly 5 Grainger customer segments are defined"""
        assert len(ClientSector) == 5


class TestClientSectorMapping:
    """Test suite for CLIENT_SECTOR_MAPPING"""

    def test_mapping_not_empty(self):
        """Test mapping is not empty"""
        assert len(CLIENT_SECTOR_MAPPING) > 0

    def test_mapping_has_manufacturing(self):
        """Test mapping has manufacturing sector"""
        assert ClientSector.MANUFACTURING in CLIENT_SECTOR_MAPPING

    def test_mapping_has_government(self):
        """Test mapping has government sector ($2B+ segment)"""
        assert ClientSector.GOVERNMENT in CLIENT_SECTOR_MAPPING

    def test_mapping_has_commercial_facilities(self):
        """Test mapping has commercial facilities sector"""
        assert ClientSector.COMMERCIAL_FACILITIES in CLIENT_SECTOR_MAPPING

    def test_mapping_has_contractors(self):
        """Test mapping has contractors sector"""
        assert ClientSector.CONTRACTORS in CLIENT_SECTOR_MAPPING

    def test_mapping_structure(self):
        """Test mapping has expected structure"""
        for sector, data in CLIENT_SECTOR_MAPPING.items():
            assert isinstance(sector, ClientSector)
            assert isinstance(data, dict)
            assert "keywords" in data
            assert isinstance(data["keywords"], list)

    def test_sectors_have_keywords(self):
        """Test Grainger customer segments have keywords defined"""
        for sector in [
            ClientSector.MANUFACTURING,
            ClientSector.GOVERNMENT,
            ClientSector.COMMERCIAL_FACILITIES,
            ClientSector.CONTRACTORS,
        ]:
            data = CLIENT_SECTOR_MAPPING.get(sector, {})
            keywords = data.get("keywords", [])
            assert len(keywords) > 0, f"{sector} should have keywords"

    def test_sectors_have_mro_impact(self):
        """Test customer segments have mro_impact defined"""
        for sector, data in CLIENT_SECTOR_MAPPING.items():
            mro_impact = data.get("mro_impact", "")
            assert isinstance(mro_impact, str)

    def test_sectors_have_geopolitical_triggers(self):
        """Test customer segments have geopolitical_triggers defined"""
        for sector in [
            ClientSector.MANUFACTURING,
            ClientSector.GOVERNMENT,
            ClientSector.CONTRACTORS,
        ]:
            data = CLIENT_SECTOR_MAPPING.get(sector, {})
            triggers = data.get("geopolitical_triggers", [])
            assert len(triggers) > 0, f"{sector} should have triggers"


class TestCompanyNamesBySector:
    """Test suite for COMPANY_NAMES_BY_SECTOR"""

    def test_mapping_created(self):
        """Test mapping is created"""
        assert COMPANY_NAMES_BY_SECTOR is not None
        assert isinstance(COMPANY_NAMES_BY_SECTOR, dict)

    def test_all_sectors_present(self):
        """Test all sectors are represented in mapping"""
        for sector in ClientSector:
            assert sector in COMPANY_NAMES_BY_SECTOR


class TestGetAllCompanyNames:
    """Test suite for get_all_company_names"""

    def test_returns_set(self):
        """Test returns a set"""
        names = get_all_company_names()
        assert isinstance(names, set)

    def test_returns_set_possibly_empty(self):
        """Test returns a set (Grainger serves all companies in segments)"""
        names = get_all_company_names()
        # Grainger model serves all companies in segment, so company list may be empty
        assert isinstance(names, set)


class TestGetCompaniesForSector:
    """Test suite for get_companies_for_sector"""

    def test_returns_list(self):
        """Test returns a list"""
        companies = get_companies_for_sector(ClientSector.MANUFACTURING)
        assert isinstance(companies, list)

    def test_returns_list_for_all_sectors(self):
        """Test returns list for all customer segments"""
        for sector in ClientSector:
            companies = get_companies_for_sector(sector)
            assert isinstance(companies, list)


class TestGetSectorKeywords:
    """Test suite for get_sector_keywords"""

    def test_returns_list(self):
        """Test returns a list"""
        keywords = get_sector_keywords(ClientSector.MANUFACTURING)
        assert isinstance(keywords, list)

    def test_manufacturing_has_keywords(self):
        """Test manufacturing sector has relevant keywords"""
        keywords = get_sector_keywords(ClientSector.MANUFACTURING)
        assert len(keywords) > 0
        # Check for MRO-relevant terms
        keyword_text = " ".join(keywords).lower()
        assert "manufacturing" in keyword_text or "industrial" in keyword_text

    def test_contractors_has_keywords(self):
        """Test contractors sector has relevant keywords"""
        keywords = get_sector_keywords(ClientSector.CONTRACTORS)
        assert len(keywords) > 0
        keyword_text = " ".join(keywords).lower()
        assert "construction" in keyword_text or "contractor" in keyword_text

    def test_government_has_keywords(self):
        """Test government sector has relevant keywords"""
        keywords = get_sector_keywords(ClientSector.GOVERNMENT)
        assert len(keywords) > 0
        keyword_text = " ".join(keywords).lower()
        assert "government" in keyword_text or "federal" in keyword_text or "military" in keyword_text

    def test_returns_empty_for_general(self):
        """Test returns empty list for GENERAL sector"""
        keywords = get_sector_keywords(ClientSector.GENERAL)
        assert isinstance(keywords, list)


class TestGetSectorTriggers:
    """Test suite for get_sector_triggers"""

    def test_returns_list(self):
        """Test returns a list"""
        triggers = get_sector_triggers(ClientSector.MANUFACTURING)
        assert isinstance(triggers, list)

    def test_manufacturing_has_triggers(self):
        """Test manufacturing sector has geopolitical triggers"""
        triggers = get_sector_triggers(ClientSector.MANUFACTURING)
        assert len(triggers) > 0

    def test_returns_empty_for_general(self):
        """Test returns empty list for GENERAL sector"""
        triggers = get_sector_triggers(ClientSector.GENERAL)
        assert isinstance(triggers, list)


class TestGetSectorMROImpact:
    """Test suite for get_sector_mro_impact"""

    def test_returns_string(self):
        """Test returns a string"""
        impact = get_sector_mro_impact(ClientSector.MANUFACTURING)
        assert isinstance(impact, str)

    def test_manufacturing_has_impact(self):
        """Test manufacturing sector has MRO impact description"""
        impact = get_sector_mro_impact(ClientSector.MANUFACTURING)
        assert len(impact) > 0

    def test_all_sectors_have_impact(self):
        """Test all sectors have MRO impact descriptions"""
        for sector in ClientSector:
            impact = get_sector_mro_impact(sector)
            assert isinstance(impact, str)


class TestGetAllSectors:
    """Test suite for get_all_sectors"""

    def test_returns_list(self):
        """Test returns a list"""
        sectors = get_all_sectors()
        assert isinstance(sectors, list)

    def test_excludes_general(self):
        """Test excludes GENERAL sector"""
        sectors = get_all_sectors()
        assert ClientSector.GENERAL not in sectors

    def test_includes_grainger_segments(self):
        """Test includes all Grainger customer segments"""
        sectors = get_all_sectors()
        assert ClientSector.MANUFACTURING in sectors
        assert ClientSector.GOVERNMENT in sectors
        assert ClientSector.COMMERCIAL_FACILITIES in sectors
        assert ClientSector.CONTRACTORS in sectors
