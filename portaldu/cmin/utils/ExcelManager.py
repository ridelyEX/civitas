import pandas as pd

class ExcelManager:
    def __init__(self):
        self.formats = {}

    def create_formats(self, workbook):
        self.formats = {
            'header': workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'vcenter',
                'align': 'center',
                'fg_color': '#3995FF',
                'border': 1,
                'font_color': 'white'
            }),
            'date': workbook.add_format({
                'num_format': 'dd/mm/yyyy',
                'border': 1
            }),
            'datetime': workbook.add_format({
                'num_format': 'dd/mm/yyyy hh:mm',
                'border': 1
            })
        }

        self.data_formats = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        self.date_formats = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'num_format': 'dd/mm/yyyy'
        })

        self.datetime_formats = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
            'num_format': 'dd/mm/yyyy hh:mm'
        })

    def convertir_fecha(self, df):
        for column in df.columns:
            if df[column].dtype == 'object':
                try:
                    dt_series = pd.to_datetime(df[column], errors='coerce')

                    if pd.api.types.is_datetime64_any_dtype(dt_series) and not dt_series.isna().all():
                        if hasattr(dt_series.dt, 'tz') and dt_series.dt.tz is not None:
                            df[column] = dt_series.dt.tz_localize(None)
                        else:
                            df[column] = dt_series
                except Exception:
                    continue

            elif pd.api.types.is_datetime64_any_dtype(df[column]):
                try:
                    if hasattr(df[column].dt, 'tz') and df[column].dt.tz is not None:
                        df[column] = df[column].dt.tz_localize(None)
                except Exception:
                    continue

        return df


    def auto_adjust_columns(self, df, worksheet):
        for i, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max() if not df.empty else 0,
                len(str(col))
            )

            worksheet.set_column(i, i, min(max_length +2, 50))

    def process_sheet(self, df, sheet_name, writer):
        if df.empty:
            return

        df = self.convertir_fecha(df)

        df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)

        worksheet = writer.sheets[sheet_name]

        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, self.formats)

        for row_num in range(1, len(df) + 1):
            for col_num in range(len(df.columns)):
                cell_value = df.iloc[row_num-1, col_num]

                if pd.isna(cell_value):
                    worksheet.write(row_num, col_num, '', self.data_formats)
                elif isinstance(cell_value, pd.Timestamp):
                    worksheet.write(row_num, col_num, cell_value, self.datetime_formats)
                elif isinstance(cell_value, pd.Timestamp):
                    worksheet.write(row_num, col_num, cell_value, self.date_formats)
                else:
                    worksheet.write(row_num, col_num, str(cell_value), self.date_formats)

        self.auto_adjust_columns(worksheet, df)