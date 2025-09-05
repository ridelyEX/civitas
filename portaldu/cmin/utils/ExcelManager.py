import logging
import pandas as pd
import warnings

logger = logging.getLogger(__name__)

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
            }),
            'text': workbook.add_format({
                'text_wrap': True,
                'valign': 'vcenter',
                'border': 1,
            })
        }

    def datetime_columns(self, df):
        datetime_columns = []
        
        for column in df.columns:
            if df[column].dtype == 'object':
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    dt_series = pd.to_datetime(
                        df[column],
                        errors='coerce',
                        format='%Y-%m-%d',
                        infer_datetime_format=True
                    )
                    
                if dt_series.notna().sum() > len(df) * 0.5:
                    datetime_columns.append(column)
                    
                    df[column] = dt_series.dt.tz_localize(None) if dt_series.dt.tz is not None else dt_series
        
            elif pd.api.types.is_datetime64_any_dtype(df[column]):
                datetime_columns.append(column)

                if hasattr(df[column].dtype, 'tz') and df[column].dtype.tz is not None:
                    df[column] = df[column].dt.tz_localize(None)
        
        
        return datetime_columns


    def auto_adjust_columns(self, df, worksheet):
        for i, col in enumerate(df.columns):
            max_length = max(
                len(str(col)),
                df[col].astype(str).str.len().max() if not df[col].empty else 0,
            )

            width = min(max(max_length + 2, 10), 50)
            worksheet.set_column(i, i, width)

    def process_sheet(self, df, sheet_name, writer):
        try:
            if df.empty:
                logger.warning(f"DataFrame vacío {sheet_name}")
                return
            
            df_copy = df.copy()

            datetime_columns = self.datetime_columns(df_copy)

            df_copy.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)

            worksheet = writer.sheets[sheet_name]

            self._apply_formats(worksheet, df_copy, datetime_columns)

            self.auto_adjust_columns(df_copy, worksheet)

        except Exception as e:
            logger.error(f"Error procesando la hoja {sheet_name}:{str(e)}")
            raise
        
        
    def _apply_formats(self, worksheet,df, datetime_columns):
        for col_num, column in enumerate(df.columns):
            worksheet.write(0, col_num, column, self.formats['header'])
            
        for row_num in range(1, len(df) + 1):
            for col_num, column in enumerate(df.columns):
                value = df.iloc[row_num -1, col_num]
                
                if pd.isna(value):
                    worksheet.write(row_num, col_num, '', self.formats['text'])
                elif column in datetime_columns:
                    if pd.notna(value):
                        worksheet.write_datetime(row_num, col_num, value, self.formats['datetime'])
                    else:
                        worksheet.write(row_num, col_num, '', self.formats['text'])
                else:
                    worksheet.write(row_num, col_num, str(value), self.formats['text'])