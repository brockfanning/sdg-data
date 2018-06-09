# -*- coding: utf-8 -*-
"""
This script converts the "wide" data in `data-wide` into "tidy" CSVs in `data`.

"""

import glob
import os.path
import pandas as pd
import yaml

# For more readable code below.
HEADER_YEAR_WIDE = 'year'
HEADER_YEAR_TIDY = 'Year'
HEADER_VALUE_TIDY = 'Value'
FOLDER_DATA_CSV_TIDY = 'data'
FOLDER_DATA_CSV_WIDE = 'data-wide'
FOLDER_META = 'meta'

def tidy_blank_dataframe():
    """This starts a blank dataframe with our required tidy columns."""

    blank = pd.DataFrame({HEADER_YEAR_WIDE:[], HEADER_VALUE_TIDY:[]})
    blank[HEADER_YEAR_WIDE] = blank[HEADER_YEAR_WIDE].astype(int)

    return blank

def tidy_melt(df, value_var, var_name):
    """This runs a Pandas melt() call with common parameters."""

    return pd.melt(
        df,
        id_vars=[HEADER_YEAR_WIDE],
        value_vars=[value_var],
        var_name=var_name,
        value_name=HEADER_VALUE_TIDY)

def get_metadata(csv_filename):
    meta_path = os.path.join(FOLDER_META, csv_filename \
        .split('indicator_')[1]                        \
        .split('.csv')[0] + '.md')
    with open(meta_path, 'r') as stream:
        try:
            for doc in yaml.safe_load_all(stream):
                if hasattr(doc, 'items'):
                    return doc
        except yaml.YAMLError as e:
            print(e)

def tidy_dataframe(df, indicator_variable):
    """This converts the data from wide to tidy, based on the column names."""

    tidy = tidy_blank_dataframe()
    for column in df.columns.tolist():
        if column == indicator_variable:
            # The main column gets converted into rows without any categories.
            melted = tidy_melt(df, indicator_variable, indicator_variable)
            del melted[indicator_variable]
            tidy = tidy.append(melted)
        elif '|' not in column and ':' in column:
            # Columns matching the pattern 'category:value' get converted into
            # rows where 'category' is set to 'value'.
            category_parts = column.split(':')
            category_name = category_parts[0]
            category_value = category_parts[1]
            melted = tidy_melt(df, column, category_name)
            melted[category_name] = category_value
            tidy = tidy.append(melted)
        elif '|' in column and ':' in column:
            # Columns matching the pattern 'category1:value1|category2:value2'
            # get converted to rows where 'category1' is set to 'value1' and
            # 'category2' is set to 'value2'.
            merged = tidy_blank_dataframe()
            categories_in_column = column.split('|')
            for category_in_column in categories_in_column:
                if category_in_column == indicator_variable:
                    # Handle the case where the 'all' column has units.
                    # Eg: all|unit:gdp_global, all|unit:gdp_national.
                    melted = tidy_melt(df, column, indicator_variable)
                    del melted[indicator_variable]
                    merged = merged.merge(melted, on=[HEADER_YEAR_WIDE, indicator_variable], how='outer')
                else:
                    category_parts = category_in_column.split(':')
                    category_name = category_parts[0]
                    category_value = category_parts[1]
                    melted = tidy_melt(df, column, category_name)
                    melted[category_name] = category_value
                    merged = merged.merge(melted, on=[HEADER_YEAR_WIDE, HEADER_VALUE_TIDY], how='outer')
            tidy = tidy.append(merged)

    # Use the tidy year column ('Year') instead of the wide year column ('year').
    tidy = tidy.rename({ HEADER_YEAR_WIDE: HEADER_YEAR_TIDY }, axis='columns')
    # For human readability, move 'year' to the front, and 'value' to the back.
    cols = tidy.columns.tolist()
    cols.pop(cols.index(HEADER_YEAR_TIDY))
    cols.pop(cols.index(HEADER_VALUE_TIDY))
    cols = [HEADER_YEAR_TIDY] + cols + [HEADER_VALUE_TIDY]
    tidy = tidy[cols]

    # Remove any rows with no value.
    tidy = tidy.dropna(subset=[HEADER_VALUE_TIDY])

    return tidy

def tidy_csv(csv):
    """This runs all checks and processing on a CSV file and reports exceptions."""

    csv_filename = os.path.split(csv)[-1]
    metadata = get_metadata(csv_filename)

    # If there is no 'indicator_variable' then we can skip this one.
    if metadata['indicator_variable'] is None:
        return True

    try:
        df = pd.read_csv(csv, dtype=str)
    except Exception as e:
        print(csv, e)
        return False

    try:
        tidy = tidy_dataframe(df, metadata['indicator_variable'])
    except Exception as e:
        print(csv, e)
        return False

    try:
        tidy_path = os.path.join(FOLDER_DATA_CSV_TIDY, csv_filename)
        tidy.to_csv(tidy_path, index=False, encoding='utf-8')
        print('Converted ' + csv_filename + ' to tidy format.')
    except Exception as e:
        print(csv, e)
        return False

    return True

def main():
    """Tidy up all of the indicator CSVs in the data folder."""

    status = True

    # Create the place to put the files.
    os.makedirs(FOLDER_DATA_CSV_TIDY, exist_ok=True)
    # Read all the files in the source location.
    csvs = glob.glob(FOLDER_DATA_CSV_WIDE + "/indicator*.csv")
    print("Attempting to tidy " + str(len(csvs)) + " wide CSV files...")

    for csv in csvs:
        status = status & tidy_csv(csv)

    return status

if __name__ == '__main__':
    if not main():
        raise RuntimeError("Failed tidy conversion")
    else:
        print("Success")