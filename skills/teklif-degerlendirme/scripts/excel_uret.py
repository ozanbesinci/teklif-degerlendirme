"""Reusable preliminary-offer workbook renderer. Never certifies a final award.

Requires openpyxl. Formula caches are intentionally NOT fabricated; recalculate in
Excel/LibreOffice and run the output gate before a verified delivery.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import textwrap


def number(value, *, missing=True):
    if value is None and missing:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError("Tutar/miktar negatif olmayan sonlu sayı veya null olmalı.")


def validate(data):
    if data.get("schema") != "teklif-workbook/v1" or data.get("analysis_mode") != "preliminary":
        raise ValueError("Bu standart şablon yalnız açıkça işaretli ön sonuç içindir.")
    if data.get("recommendation") is not None:
        raise ValueError("Ön sonuç şablonu kesin firma önerisi içeremez.")
    dt.date.fromisoformat(data["analysis_date"])
    if not isinstance(data.get("project"), str) or not data["project"].strip():
        raise ValueError("Proje adı gerekli.")
    offers = data.get("offers")
    if not isinstance(offers, list) or not offers:
        raise ValueError("En az bir teklif gerekli.")
    ids = [offer["id"] for offer in offers]
    if not all(isinstance(x, str) and x for x in ids) or len(ids) != len(set(ids)):
        raise ValueError("Teklif kimlikleri benzersiz olmalı.")
    for offer in offers:
        if not offer.get("name") or not offer.get("currency") or not offer.get("lines"):
            raise ValueError("Firma/para birimi/kalem gerekli.")
        number(offer.get("declared_total"))
        line_ids = set()
        for line in offer["lines"]:
            if not line.get("id") or line["id"] in line_ids or not line.get("source"):
                raise ValueError("Kalem kimliği ve kaynak gerekli; tekrar olamaz.")
            line_ids.add(line["id"])
            number(line.get("quantity")); number(line.get("unit_price"))
    seen = set()
    for item in data.get("scope_items", []):
        if not item.get("id") or item["id"] in seen or not item.get("source"):
            raise ValueError("Kapsam kimliği/kaynağı gerekli; aynı maliyet iki kez yazılamaz.")
        seen.add(item["id"]); number(item.get("amount"))
        if item.get("classification") == "5-A":
            if item.get("offer_id") not in ids:
                raise ValueError("5-A kalemi firma bazlı olmalı.")
        elif item.get("classification") == "5-B":
            allocations = item.get("allocations", [])
            if len(allocations) != len(ids) or {a.get("offer_id") for a in allocations} != set(ids):
                raise ValueError("5-B için bütün firmalarda eşit kapsam kanıtı gerekli.")
            values = set()
            for a in allocations:
                number(a.get("amount"), missing=False)
                dt.date.fromisoformat(a["payment_date"])
                if not a.get("source") or not a.get("currency"):
                    raise ValueError("5-B kanıtı/para birimi eksik.")
                values.add((a["amount"], a["currency"], a["payment_date"]))
            if len(values) != 1 or next(iter(values))[:2] != (item.get("amount"), item.get("currency")):
                raise ValueError("Firma bazlı farklı/eksik tutar veya ödeme tarihi ortak 5-B olamaz.")
        else:
            raise ValueError("Kapsam sınıfı 5-A veya kanıtlı 5-B olmalı.")
    return data


def build(data, output):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.workbook.properties import CalcProperties
    validate(data)
    output = Path(output)
    if output.exists():
        raise ValueError("Var olan çıktı üzerine yazılmaz; yeni revizyon adı seçin.")
    wb = Workbook()
    wb.remove(wb.active)
    tabs = {name: wb.create_sheet(name) for name in ("Karar Özeti", "Teklifler", "Kalemler", "Kapsam ve RFI", "Parametreler")}

    def row(sheet, values, *, header=False):
        sheet.append(values)
        for cell in sheet[sheet.max_row]:
            if isinstance(cell.value, str):
                cell.data_type = "s"  # Source text is never an executable Excel formula.
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.font = Font(name="Calibri", size=11, bold=header, color="FFFFFF" if header else "17324D")
            if header:
                cell.fill = PatternFill("solid", fgColor="17324D")
        sheet.row_dimensions[sheet.max_row].height = 32 if header else 36
        return sheet.max_row

    summary = tabs["Karar Özeti"]
    row(summary, [data["project"], "ÖN SONUÇ — KESİN SATINALMA ÖNERİSİ DEĞİLDİR"], header=True)
    paragraphs = ["Bilinen teklif bedelleri eşit kapsamlı nihai maliyet değildir. Eksik bilgi sıfır kabul edilmez."] + data.get("summary", [])
    for text in paragraphs:
        for part in textwrap.wrap(str(text), width=95, break_long_words=True) or [""]:
            i = row(summary, [part]); summary.merge_cells(start_row=i, start_column=1, end_row=i, end_column=2)
            summary.row_dimensions[i].height = 42
    line_sheet = tabs["Kalemler"]
    row(line_sheet, ["Firma", "Kalem", "Miktar", "Birim fiyat", "Hesap tutarı", "Döviz", "Kaynak"], header=True)
    offers_sheet = tabs["Teklifler"]
    row(offers_sheet, ["Firma", "Döviz", "Beyan toplamı", "Bilinen kalem toplamı", "Fiyatı eksik kalem", "Uyarı"], header=True)
    for offer in data["offers"]:
        start = line_sheet.max_row + 1
        for item in offer["lines"]:
            n = row(line_sheet, [offer["name"], item.get("description", item["id"]), item.get("quantity"), item.get("unit_price"), None, offer["currency"], item["source"]])
            line_sheet.cell(n, 5, f'=IF(COUNT(C{n}:D{n})=2,C{n}*D{n},"")')
            for col in (3, 4): line_sheet.cell(n, col).font = Font(name="Calibri", size=11, color="0000FF")
            for col in (4, 5): line_sheet.cell(n, col).number_format = '#,##0.00'
        end = line_sheet.max_row
        n = row(offers_sheet, [offer["name"], offer["currency"], offer.get("declared_total"), None, None, "Nihai KTM değil; kapsam ve bilgi talepleri açık"])
        offers_sheet.cell(n, 4, f"=SUM('Kalemler'!E{start}:E{end})")
        offers_sheet.cell(n, 5, f"=COUNTBLANK('Kalemler'!E{start}:E{end})")
        for col in (3, 4): offers_sheet.cell(n, col).number_format = '#,##0.00'
    scope = tabs["Kapsam ve RFI"]
    row(scope, ["Kimlik", "Firma/sınıf", "Konu", "Tutar", "Döviz", "Bilgi talebi", "Kaynak"], header=True)
    for item in data.get("scope_items", []):
        row(scope, [item["id"], (item.get("offer_id") or "ORTAK") + " / " + item["classification"], item.get("description"), item.get("amount"), item.get("currency"), item.get("rfi"), item["source"]])
    for item in data.get("rfi", []):
        row(scope, [item.get("id"), item.get("owner"), item.get("question"), None, None, "YANIT BEKLENİYOR", item.get("source")])
    params = tabs["Parametreler"]
    row(params, ["Parametre", "Değer"], header=True)
    row(params, ["Analiz tarihi", dt.datetime.combine(dt.date.fromisoformat(data["analysis_date"]), dt.time())])
    params["B2"].number_format = "yyyy-mm-dd"
    row(params, ["Mod", "preliminary"])
    row(params, ["Çalışma girdisi SHA-256 (kanonik JSON)", hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()])
    row(params, ["Doğrulama", "Gerçek yeniden hesaplama, parametre testi ve bağımsız görsel kontrol bekliyor"])
    for sheet in wb:
        sheet.freeze_panes = "A2"
        sheet.sheet_view.showGridLines = False
        sheet.auto_filter.ref = sheet.dimensions if sheet.title not in {"Karar Özeti", "Parametreler"} else None
        sheet.page_setup.orientation = "landscape"
        sheet.page_setup.paperSize = sheet.PAPERSIZE_A3
        sheet.page_setup.fitToWidth = 1; sheet.page_setup.fitToHeight = 0
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
        sheet.print_title_rows = "1:1"
        for col in sheet.columns:
            sheet.column_dimensions[col[0].column_letter].width = 24
        if sheet.max_column >= 3: sheet.column_dimensions["C"].width = 40
        if sheet.max_column >= 6: sheet.column_dimensions["F"].width = 45
        if sheet.max_column >= 7: sheet.column_dimensions["G"].width = 45
        # Long source/RFI text expands rather than shrinking fonts or clipping silently.
        for cells in sheet.iter_rows(min_row=2):
            lines = max((math.ceil(len(str(c.value or "")) / max(12, sheet.column_dimensions[c.column_letter].width - 2)) for c in cells if c.value is not None), default=1)
            sheet.row_dimensions[cells[0].row].height = max(sheet.row_dimensions[cells[0].row].height or 36, min(400, 16 * lines + 8))
    summary.column_dimensions["A"].width = 45; summary.column_dimensions["B"].width = 65
    params.column_dimensions["B"].width = 90
    wb.calculation = CalcProperties(calcId=191029, fullCalcOnLoad=True, forceFullCalc=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output)
    return {"status": "DRAFT_RECALC_REQUIRED", "output": str(output), "sheets": len(wb.worksheets)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(json.loads(args.data.read_text(encoding="utf-8")), args.output), ensure_ascii=False))
