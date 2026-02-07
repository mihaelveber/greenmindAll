from django.core.management.base import BaseCommand
import pandas as pd
import os

from accounts.models import ESRSCategory, ESRSStandard, ESRSDisclosure


class Command(BaseCommand):
    help = "Import ESRS IG3 Data Points from EFRAG Excel into ESRS models"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            type=str,
            default="backend/data/EFRAG_IG_3.xlsx",
            help="Path to EFRAG IG3 Excel file",
        )
        parser.add_argument(
            "--sheet",
            type=str,
            default=None,
            help="Optional sheet name to import (e.g. 'ESRS E1'). Defaults to all ESRS sheets.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Optional row limit for testing",
        )

    def handle(self, *args, **options):
        file_path = options["file_path"]
        sheet_filter = options["sheet"]
        limit = options["limit"]

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"File not found: {file_path}"))
            return

        self.stdout.write(f"Reading {file_path}...")

        xls = pd.ExcelFile(file_path)
        sheet_names = [s for s in xls.sheet_names if s != "Index"]
        if sheet_filter:
            if sheet_filter not in sheet_names:
                self.stdout.write(self.style.ERROR(f"Sheet not found: {sheet_filter}"))
                return
            sheet_names = [sheet_filter]

        self.stdout.write(f"Sheets: {sheet_names}")

        categories = self._ensure_categories()
        standards_cache = {}
        drs_cache = {}

        total_rows = 0
        total_standards = 0
        total_drs = 0
        total_datapoints = 0

        for sheet in sheet_names:
            self.stdout.write(f"\nProcessing sheet: {sheet}")
            header_row = self._detect_header_row(file_path, sheet)
            if header_row is None:
                self.stdout.write(self.style.WARNING(f"Skipping {sheet}: header row not found"))
                continue

            df = pd.read_excel(file_path, sheet_name=sheet, header=header_row)
            df.columns = df.columns.astype(str).str.strip()

            if limit:
                df = df.head(limit)

            col_map = self._map_columns(df.columns)
            missing = [k for k, v in col_map.items() if v is None]
            if missing:
                self.stdout.write(self.style.WARNING(f"Missing columns in {sheet}: {missing}"))

            for idx, row in df.iterrows():
                total_rows += 1

                standard_code = self._clean_value(row.get(col_map["ESRS"]))
                dr_code = self._clean_value(row.get(col_map["DR"]))
                datapoint_id = self._clean_value(row.get(col_map["ID"]))
                name = self._clean_value(row.get(col_map["Name"]))
                paragraph = self._clean_value(row.get(col_map["Paragraph"]))
                data_type = self._clean_value(row.get(col_map["Data Type"]))
                conditional = self._clean_value(row.get(col_map["Conditional"]))

                if not datapoint_id or not standard_code:
                    continue

                if standard_code not in standards_cache:
                    category = self._determine_category(standard_code, categories)
                    standard, created = ESRSStandard.objects.get_or_create(
                        code=standard_code,
                        standard_type="ESRS",
                        defaults={
                            "name": f"ESRS {standard_code}",
                            "category": category,
                            "description": f"European Sustainability Reporting Standard {standard_code}",
                        },
                    )
                    standards_cache[standard_code] = standard
                    if created:
                        total_standards += 1

                standard = standards_cache[standard_code]

                if dr_code:
                    dr_key = f"{standard_code}:{dr_code}"
                    if dr_key not in drs_cache:
                        parent_dr, created = ESRSDisclosure.objects.get_or_create(
                            code=dr_code,
                            standard=standard,
                            standard_type="ESRS",
                            defaults={
                                "name": dr_code,
                                "description": "Disclosure Requirement",
                                "requirement_text": "Disclosure Requirement",
                                "is_mandatory": True,
                            },
                        )
                        drs_cache[dr_key] = parent_dr
                        if created:
                            total_drs += 1
                    parent_dr = drs_cache[dr_key]
                else:
                    parent_dr = None

                description_parts = [name]
                if paragraph:
                    description_parts.append(f"Paragraph: {paragraph}")
                if data_type:
                    description_parts.append(f"Data Type: {data_type}")
                if conditional:
                    description_parts.append(f"Conditional: {conditional}")

                description = "\n".join([p for p in description_parts if p])

                ESRSDisclosure.objects.update_or_create(
                    code=datapoint_id,
                    standard=standard,
                    standard_type="ESRS",
                    defaults={
                        "parent": parent_dr,
                        "name": (name or datapoint_id)[:499],
                        "description": description or (name or datapoint_id),
                        "requirement_text": description or (name or datapoint_id),
                        "is_mandatory": True,
                    },
                )
                total_datapoints += 1

                if total_rows % 500 == 0:
                    self.stdout.write(f"Processed {total_rows} rows...")

        self.stdout.write(self.style.SUCCESS("Import complete"))
        self.stdout.write(f"Standards created: {total_standards}")
        self.stdout.write(f"Disclosure Requirements created: {total_drs}")
        self.stdout.write(f"Data points processed: {total_datapoints}")

    def _detect_header_row(self, file_path: str, sheet: str) -> int | None:
        preview = pd.read_excel(file_path, sheet_name=sheet, header=None, nrows=30)
        for i, row in preview.iterrows():
            row_values = [str(v) for v in row.values if pd.notna(v)]
            joined = " | ".join(row_values).lower()
            if "instructions" in joined:
                continue
            if all(k in joined for k in ["id", "esrs", "dr", "paragraph", "name"]):
                return i
        return None

    def _map_columns(self, columns):
        mapping = {
            "ID": None,
            "ESRS": None,
            "DR": None,
            "Paragraph": None,
            "Related AR": None,
            "Name": None,
            "Data Type": None,
            "Conditional": None,
        }

        for col in columns:
            col_l = col.lower().strip()
            if col_l == "id":
                mapping["ID"] = col
            elif col_l == "esrs":
                mapping["ESRS"] = col
            elif col_l == "dr":
                mapping["DR"] = col
            elif "paragraph" in col_l:
                mapping["Paragraph"] = col
            elif "related ar" in col_l:
                mapping["Related AR"] = col
            elif col_l == "name":
                mapping["Name"] = col
            elif "data type" in col_l:
                mapping["Data Type"] = col
            elif "conditional" in col_l:
                mapping["Conditional"] = col

        return mapping

    def _clean_value(self, value):
        if value is None:
            return ""
        try:
            if pd.isna(value):
                return ""
        except Exception:
            pass
        return str(value).strip()

    def _ensure_categories(self):
        c_env, _ = ESRSCategory.objects.get_or_create(
            code="E", standard_type="ESRS", defaults={"name": "Environmental", "order": 1}
        )
        c_soc, _ = ESRSCategory.objects.get_or_create(
            code="S", standard_type="ESRS", defaults={"name": "Social", "order": 2}
        )
        c_gov, _ = ESRSCategory.objects.get_or_create(
            code="G", standard_type="ESRS", defaults={"name": "Governance", "order": 3}
        )
        c_cross, _ = ESRSCategory.objects.get_or_create(
            code="CC", standard_type="ESRS", defaults={"name": "Cross-cutting", "order": 0}
        )
        return {"E": c_env, "S": c_soc, "G": c_gov, "CC": c_cross}

    def _determine_category(self, std_code, cats):
        if std_code.startswith("E"):
            return cats["E"]
        if std_code.startswith("S"):
            return cats["S"]
        if std_code.startswith("G"):
            return cats["G"]
        return cats["CC"]