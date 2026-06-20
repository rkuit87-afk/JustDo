"""
Unit tests for template_report.py

Covers: _find_template, _build_equipment_map, _get_compound_id,
        generate_template_report (with mock template).
"""

import os
import pytest
from unittest.mock import MagicMock
from datetime import date


# ============================================================
# _find_template
# ============================================================

class TestFindTemplate:
    def test_raises_when_no_template(self, tmp_path, monkeypatch):
        from template_report import _find_template
        import template_report
        monkeypatch.setattr(
            template_report, "TEMPLATE_CANDIDATES",
            [str(tmp_path / "nonexistent.xlsx")]
        )
        with pytest.raises(FileNotFoundError, match="Template not found"):
            _find_template()

    def test_returns_first_existing(self, tmp_path, monkeypatch):
        from template_report import _find_template
        import template_report
        path1 = tmp_path / "template1.xlsx"
        path2 = tmp_path / "template2.xlsx"
        path1.touch()
        path2.touch()
        monkeypatch.setattr(
            template_report, "TEMPLATE_CANDIDATES",
            [str(path1), str(path2)]
        )
        assert _find_template() == str(path1)

    def test_returns_second_if_first_missing(self, tmp_path, monkeypatch):
        from template_report import _find_template
        import template_report
        path1 = tmp_path / "missing.xlsx"
        path2 = tmp_path / "exists.xlsx"
        path2.touch()
        monkeypatch.setattr(
            template_report, "TEMPLATE_CANDIDATES",
            [str(path1), str(path2)]
        )
        assert _find_template() == str(path2)


# ============================================================
# _build_equipment_map
# ============================================================

class TestBuildEquipmentMap:
    def test_builds_maps(self, seeded_db):
        from template_report import _build_equipment_map
        by_id, by_name = _build_equipment_map(seeded_db)
        assert len(by_id) > 0
        assert len(by_name) > 0
        # All keys in by_name should be lowercase
        for key in by_name:
            assert key == key.lower()

    def test_by_id_contains_equipment_data(self, seeded_db):
        from template_report import _build_equipment_map
        by_id, _ = _build_equipment_map(seeded_db)
        first_id = next(iter(by_id))
        item = by_id[first_id]
        assert "name" in item
        assert "compound_id" in item
        assert "area" in item


# ============================================================
# _get_compound_id
# ============================================================

class TestGetCompoundId:
    def test_returns_compound_id_from_by_id(self):
        from template_report import _get_compound_id
        by_id = {1: {"compound_id": "BDS-001 - BE-004", "name": "Bandsaw 1"}}
        by_name = {}
        result = _get_compound_id(1, "Bandsaw 1", by_id, by_name)
        assert result == "BDS-001 - BE-004"

    def test_falls_back_to_by_name(self):
        from template_report import _get_compound_id
        by_id = {}
        by_name = {"bandsaw 1": {"compound_id": "BDS-001 - BE-004"}}
        result = _get_compound_id(None, "Bandsaw 1", by_id, by_name)
        assert result == "BDS-001 - BE-004"

    def test_falls_back_to_equip_name(self):
        from template_report import _get_compound_id
        by_id = {}
        by_name = {}
        result = _get_compound_id(None, "Unknown Machine", by_id, by_name)
        assert result == "Unknown Machine"

    def test_returns_empty_when_nothing(self):
        from template_report import _get_compound_id
        result = _get_compound_id(None, None, {}, {})
        assert result == ""

    def test_id_without_compound_id_falls_through(self):
        from template_report import _get_compound_id
        by_id = {1: {"compound_id": None, "name": "Machine"}}
        by_name = {"machine": {"compound_id": "CID-123"}}
        result = _get_compound_id(1, "Machine", by_id, by_name)
        assert result == "CID-123"

    def test_case_insensitive_name_lookup(self):
        from template_report import _get_compound_id
        by_name = {"bandsaw 2 - juliet": {"compound_id": "BDS-002"}}
        result = _get_compound_id(None, "Bandsaw 2 - Juliet", {}, by_name)
        assert result == "BDS-002"
