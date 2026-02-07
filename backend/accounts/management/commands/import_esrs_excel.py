from django.core.management.base import BaseCommand
import pandas as pd
import os
from accounts.models import ESRSCategory, ESRSStandard, ESRSDisclosure

class Command(BaseCommand):
    help = 'Import ESRS Data Points from EFRAG IG 3 Excel file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', nargs='?', type=str, default='backend/data/EFRAG_IG_3.xlsx', help='Path to the Excel file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            self.stdout.write(self.style.WARNING('Please download "EFRAG IG 3 List of Data Points" Excel file and place it in backend/data/EFRAG_IG_3.xlsx'))
            return

        self.stdout.write(f'Reading {file_path}...')
        
        try:
            # Load Excel - usually the data is in the second or third sheet, or "Data Points" sheet
            # We'll try to find the sheet named "Data list" or similar, or just read the first one that looks like data
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names
            self.stdout.write(f'Sheets found: {sheet_names}')
            
            # Heuristic: Look for "list" or "data" in sheet name
            target_sheet = None
            for sheet in sheet_names:
                if "list" in sheet.lower() or "data" in sheet.lower():
                    target_sheet = sheet
                    break
            
            if not target_sheet:
                target_sheet = sheet_names[0]
                
            self.stdout.write(f'Using sheet: {target_sheet}')
            
            # Read data
            df = pd.read_excel(file_path, sheet_name=target_sheet)
            
            # Normalize columns - strip whitespace, maybe lower case for matching
            df.columns = df.columns.astype(str).str.strip()
            
            self.stdout.write(f'Columns: {list(df.columns)}')
            
            # Required columns map (we might need to adjust these based on the actual file)
            # Standard EFRAG IG 3 columns often look like:
            # "ESRS" (Standard), "DR" (Disclosure Requirement), "ID", "Datapoint", "Data Type"
            # Let's map dynamically
            
            col_map = self._map_columns(df.columns)
            if not col_map['Standard'] or not col_map['ID'] or not col_map['Description']:
                 self.stdout.write(self.style.ERROR('Could not map required columns. Please check the file format.'))
                 return

            self._import_data(df, col_map)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing excel: {e}'))
            import traceback
            traceback.print_exc()

    def _map_columns(self, columns):
        """Identify columns based on keywords"""
        map_c = {
            'Standard': None, # E1, S1...
            'DR': None,       # E1-1...
            'ID': None,       # Unique ID
            'Description': None, # Name/Description
            'Paragraph': None,
            'Type': None,     # Narrative, Monetary, etc
        }
        
        for col in columns:
            l_col = col.lower()
            if 'esrs' in l_col and not map_c['Standard']:
                 map_c['Standard'] = col
            elif ('dr' in l_col or 'disclosure requirement' in l_col) and not map_c['DR']:
                 map_c['DR'] = col
            elif ('id' in l_col or 'unique' in l_col) and 'guid' not in l_col and not map_c['ID']:
                 map_c['ID'] = col
            elif ('description' in l_col or 'label' in l_col or 'name' in l_col) and not map_c['Description']:
                 map_c['Description'] = col
            elif 'paragraph' in l_col and not map_c['Paragraph']:
                 map_c['Paragraph'] = col
            elif ('type' in l_col) and not map_c['Type']:
                 map_c['Type'] = col
                 
        self.stdout.write(f'Column Mapping: {map_c}')
        return map_c

    def _import_data(self, df, col_map):
        count_cat = 0
        count_std = 0
        count_dr = 0
        count_dp = 0
        
        # Ensure categories exist
        cats = self._ensure_categories()
        
        # Cache for standards/drs to reduce DB hits
        standards_cache = {}
        drs_cache = {}
        
        for index, row in df.iterrows():
            std_code = str(row[col_map['Standard']]).strip() if pd.notna(row[col_map['Standard']]) else 'Unknown'
            dr_code = str(row[col_map['DR']]).strip() if col_map['DR'] and pd.notna(row[col_map['DR']]) else std_code
            dp_id = str(row[col_map['ID']]).strip() if pd.notna(row[col_map['ID']]) else ''
            desc = str(row[col_map['Description']]).strip() if pd.notna(row[col_map['Description']]) else ''
            
            if not dp_id:
                continue
                
            # 1. Standard
            if std_code not in standards_cache:
                cat = self._determine_category(std_code, cats)
                standard, created = ESRSStandard.objects.get_or_create(
                    code=std_code,
                    standard_type='ESRS',
                    defaults={
                        'name': f'ESRS {std_code}', # We might want to improve this name 
                        'category': cat,
                        'description': f'European Sustainability Reporting Standard {std_code}'
                    }
                )
                standards_cache[std_code] = standard
                if created: count_std += 1
            
            current_std = standards_cache[std_code]
            
            # 2. Parent Disclosure Requirement (The higher level grouping)
            # EFRAG Excel has "DR" column. e.g. "E1-1". 
            # We want to ensure this DR exists as a parent record.
            
            if dr_code not in drs_cache:
                # Create the Parent DR
                parent_dr, created = ESRSDisclosure.objects.get_or_create(
                    code=dr_code,
                    standard=current_std,
                    defaults={
                        'name': dr_code, # Placeholder name
                        'description': 'Disclosure Requirement',
                        'requirement_text': 'Disclosure Requirement',
                        'is_mandatory': True,
                        'standard_type': 'ESRS'
                    }
                )
                drs_cache[dr_code] = parent_dr
                if created: count_dr += 1
            
            parent_dr = drs_cache[dr_code]
            
            # 3. Data Point (The specific line)
            # This is also an ESRSDisclosure in our model, but with a parent
            
            ESRSDisclosure.objects.update_or_create(
                code=dp_id,
                standard=current_std,
                defaults={
                    'parent': parent_dr,
                    'name': desc[:499], # Truncate if too long (max 500)
                    'description': desc,
                    'requirement_text': desc, # For now, same as description
                    'is_mandatory': True, # Assume mandatory unless column says otherwise
                    'standard_type': 'ESRS'
                }
            )
            count_dp += 1
            
            if index % 100 == 0:
                self.stdout.write(f'Processed {index} rows...')

        self.stdout.write(self.style.SUCCESS(f'Import Complete!'))
        self.stdout.write(f'Standards: {count_std}')
        self.stdout.write(f'DRs (Parents): {count_dr}')
        self.stdout.write(f'Data Points: {count_dp}')

    def _ensure_categories(self):
        c_env, _ = ESRSCategory.objects.get_or_create(code='E', standard_type='ESRS', defaults={'name': 'Environmental', 'order': 1})
        c_soc, _ = ESRSCategory.objects.get_or_create(code='S', standard_type='ESRS', defaults={'name': 'Social', 'order': 2})
        c_gov, _ = ESRSCategory.objects.get_or_create(code='G', standard_type='ESRS', defaults={'name': 'Governance', 'order': 3})
        c_cross, _ = ESRSCategory.objects.get_or_create(code='CC', standard_type='ESRS', defaults={'name': 'Cross-cutting', 'order': 0})
        return {'E': c_env, 'S': c_soc, 'G': c_gov, 'CC': c_cross}

    def _determine_category(self, std_code, cats):
        if std_code.startswith('E'): return cats['E']
        if std_code.startswith('S'): return cats['S']
        if std_code.startswith('G'): return cats['G']
        return cats['CC']
