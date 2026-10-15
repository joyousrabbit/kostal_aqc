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

material_partname = None
def load_material_partname(material_partname_file="Renault Overseas Serial-Prod and Project List 20260319.xlsx"):
    # load from the excel file all sheets and create a dictionary with the "Customer part" as key and the (Material, Part name) as value
    material_partname = {}
    with pd.ExcelFile(material_partname_file) as xls:
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            for index, row in df.iterrows():
                customer_part = row["Customer part"]
                material = row["Material"]
                part_name = row["Part name"]
                material_partname[customer_part] = (material, part_name)
    return material_partname

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
        year_month_day = csvfiles[-1][:8]
        year = int(year_month_day[:4])
        month = int(year_month_day[4:6])
        # start is 6 months before year-month, end is 18 months before year-month
        start = pd.Period(year=year, month=month, freq='M') - 18
        end = pd.Period(year=year, month=month, freq='M') - 6
        all_months = pd.period_range(start=start, end=end, freq='M')
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

        with pd.ExcelWriter(f'result/histograms_comparison_{csvfiles[-1][:8]}.xlsx', engine='openpyxl') as writer:
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

            # get rows where VIN is present in the last file but not in the second last file
            vin_last2 = set(dfs[-2]['VIN'])
            vin_last1 = set(dfs[-1]['VIN'])
            new_vins = vin_last1 - vin_last2
            new_vins_rows = dfs[-1][dfs[-1]['VIN'].isin(new_vins)]
            # get columns "Part number", "Part Designation EN (Serial Life)", "Plant Name", "Customer symptom" and add to the right space of worksheet
            new_vins_rows = new_vins_rows[["Part number", "Part Designation EN (Serial Life)", "Plant Name", "Customer symptom"]]
            # combine with the material and part name from the material_partname dictionary by using the "Part number" as key
            new_vins_rows["Material"] = new_vins_rows["Part number"].map(lambda x: material_partname.get(x, ("", ""))[0])
            new_vins_rows["Part name"] = new_vins_rows["Part number"].map(lambda x: material_partname.get(x, ("", ""))[1])
            # "Part name" and "Material" should be the first two columns
            new_vins_rows = new_vins_rows[["Part name", "Material"] + [col for col in new_vins_rows.columns if col not in ["Part name", "Material"]]]   
            # sort by "Part name" and then by "Material"
            new_vins_rows = new_vins_rows.sort_values(by=["Part name", "Material"])
            new_vins_rows.to_excel(writer, sheet_name='Score', startcol=5, index=False)

            # expend all columns to fit the content
            for column_cells in worksheet.columns:
                length = max(len(str(cell.value)) for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = length + 2

    


def main():
    global material_partname
    material_partname = load_material_partname()

    analyse_folder("data/")

if __name__ == "__main__":
    main()
