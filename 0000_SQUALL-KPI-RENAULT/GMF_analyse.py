import os
import csv
import sys
import pandas as pd

try:
    from openpyxl.styles import Font, PatternFill
except ImportError:  # pragma: no cover
    Font = None
    PatternFill = None

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def analyse_folder(folder_path):
    #list all files in the folder containing year-month-day.csv
    files = sorted(os.listdir(folder_path))
    csvfiles = [file for file in files if file.endswith(".csv")]
    dfs = []
    for file in csvfiles:
        file_path = os.path.join(folder_path, file)
        df = pd.read_csv(file_path, delimiter='\t', encoding='utf-16')
        dfs.append(df)
        
    for df in dfs:
        vehicle_build_date =  pd.to_datetime(df['Vehicle build Date'])
        df['Year-Month'] = vehicle_build_date.dt.to_period('M')

    # compare two histograms and print the difference
    if len(dfs) >= 2:
        histogram_last2 = dfs[-2].groupby('Year-Month').size()
        histogram_last1 = dfs[-1].groupby('Year-Month').size()
        all_months = pd.period_range(start=min(histogram_last2.index.min(), histogram_last1.index.min()), end=max(histogram_last2.index.max(), histogram_last1.index.max()), freq='M')
        histogram_last2 = histogram_last2.reindex(all_months, fill_value=0)
        histogram_last1 = histogram_last1.reindex(all_months, fill_value=0)
        difference = histogram_last1 - histogram_last2

        # Export the comparison to Excel and color the Difference column.
        # Positive values -> green, negative values -> red, zero -> neutral.
        # Also add a final totals row with the sum of each column.
        comparison = pd.concat(
            [
                histogram_last2.rename(csvfiles[-2][:8]),
                histogram_last1.rename(csvfiles[-1][:8]),
                difference.rename('Difference'),
            ],
            axis=1,
        )
        comparison.index = comparison.index.strftime('%Y-%m')

        totals = pd.Series(
            {
                csvfiles[-2][:8]: int(histogram_last2.sum()),
                csvfiles[-1][:8]: int(histogram_last1.sum()),
            },
            name='Total'
        )
        comparison = pd.concat([comparison, totals.to_frame().T])

        with pd.ExcelWriter('histograms_comparison.xlsx', engine='openpyxl') as writer:
            comparison.to_excel(writer, sheet_name='Score')

            worksheet = writer.sheets['Score']
            worksheet.cell(row=1, column=1).value = 'Vehicle build Date'

            if Font is not None and PatternFill is not None:
                for row_idx in range(2, len(comparison) + 2):
                    value = comparison.iloc[row_idx - 2, 2]
                    cell = worksheet.cell(row=row_idx, column=3)

                    if value > 0:
                        cell.fill = PatternFill(fill_type='solid', fgColor='C6EFCE')
                        cell.font = Font(color='006100', bold=True)
                    elif value < 0:
                        cell.fill = PatternFill(fill_type='solid', fgColor='FFC7CE')
                        cell.font = Font(color='9C0006', bold=True)
                    else:
                        cell.fill = PatternFill(fill_type='solid', fgColor='FFFFFF')
                        cell.font = Font(color='000000')

                # bold the totals row for readability
                for col_idx in range(1, 4):
                    worksheet.cell(row=len(comparison) + 1, column=col_idx).font = Font(bold=True)
    


def main():
    analyse_folder("data/")


if __name__ == "__main__":
    main()
