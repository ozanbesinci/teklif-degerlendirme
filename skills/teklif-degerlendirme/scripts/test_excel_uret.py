import copy
import tempfile
import unittest
from pathlib import Path
from openpyxl import load_workbook
from excel_uret import build, validate


def fixture():
    return {"schema": "teklif-workbook/v1", "project": "Synthetic fixture", "analysis_mode": "preliminary",
            "analysis_date": "2026-09-21", "recommendation": None, "summary": ["Long finding " * 60],
            "offers": [{"id": "A", "name": "Supplier A", "currency": "USD", "declared_total": 0,
                        "lines": [{"id": "L1", "description": "=UNTRUSTED()", "quantity": 2, "unit_price": 0, "source": "fixture:1"},
                                  {"id": "L2", "description": "Unknown price", "quantity": 1, "unit_price": None, "source": "fixture:2"}]}]}


class ExcelTests(unittest.TestCase):
    def test_formulas_null_zero_and_literal_source_text(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "test.xlsx"
            result = build(fixture(), path)
            self.assertEqual(result["status"], "DRAFT_RECALC_REQUIRED")
            wb = load_workbook(path)
            self.assertEqual(len(wb.sheetnames), 5)
            self.assertEqual(wb["Kalemler"]["D2"].value, 0)
            self.assertIsNone(wb["Kalemler"]["D3"].value)
            self.assertEqual(wb["Kalemler"]["B2"].data_type, "s")
            self.assertEqual(wb["Kalemler"]["E2"].value, '=IF(COUNT(C2:D2)=2,C2*D2,"")')
            self.assertGreater(wb["Karar Özeti"].max_row, 5)
            self.assertTrue(all(row.height >= 36 for key, row in wb["Karar Özeti"].row_dimensions.items() if key > 1))
            wb.close()
            with self.assertRaises(ValueError): build(fixture(), path)

    def test_missing_scope_cannot_be_common_5b(self):
        data = fixture()
        data["scope_items"] = [{"id": "S1", "classification": "5-B", "amount": None, "currency": "USD", "source": "fixture"}]
        with self.assertRaises(ValueError): validate(data)
        data["scope_items"][0].update(classification="5-A", offer_id="A")
        validate(data)

    def test_common_scope_requires_all_equal_amounts_and_dates(self):
        data = fixture(); other = copy.deepcopy(data["offers"][0]); other["id"] = "B"; data["offers"].append(other)
        allocations = [{"offer_id": x, "amount": 10, "currency": "USD", "payment_date": "2026-10-01", "source": "fixture"} for x in ("A", "B")]
        data["scope_items"] = [{"id": "S1", "classification": "5-B", "amount": 10, "currency": "USD", "source": "fixture", "allocations": allocations}]
        validate(data)
        allocations[1]["payment_date"] = "2026-11-01"
        with self.assertRaises(ValueError): validate(data)

    def test_final_recommendation_and_invalid_numbers_rejected(self):
        for value in (float("nan"), float("inf"), -1, True):
            data = fixture(); data["offers"][0]["lines"][0]["unit_price"] = value
            with self.assertRaises(ValueError): validate(data)
        data = fixture(); data["recommendation"] = "A"
        with self.assertRaises(ValueError): validate(data)


if __name__ == "__main__": unittest.main()
