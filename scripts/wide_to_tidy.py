# -*- coding: utf-8 -*-
"""
This script converts the "wide" data in `data-wide` into "tidy" CSVs in `data`.

"""

import glob
import os.path
import pandas as pd
import yaml

# For more readable code below.
HEADER_ALL = 'all'
HEADER_YEAR_WIDE = 'year'
HEADER_YEAR_TIDY = 'Year'
HEADER_VALUE_TIDY = 'Value'
FOLDER_DATA_CSV_TIDY = 'data'
FOLDER_DATA_CSV_WIDE = 'data-wide'
FOLDER_META = 'meta'
FOLDER_DATA_CSV_SUBNATIONAL = 'data-wide/subnational'

# Allows for more human-friendly folder names in the repository.
FOLDER_NAME_CONVERSIONS = {
    'state': 'GeoCode',
    'AL': '0400000US01',
    'AK': '0400000US02',
    'AZ': '0400000US04',
    'AR': '0400000US05',
    'CA': '0400000US06',
    'CO': '0400000US08',
    'CT': '0400000US09',
    'DE': '0400000US10',
    'DC': '0400000US11',
    'FL': '0400000US12',
    'GA': '0400000US13',
    'HI': '0400000US15',
    'ID': '0400000US16',
    'IL': '0400000US17',
    'IN': '0400000US18',
    'IA': '0400000US19',
    'KS': '0400000US20',
    'KY': '0400000US21',
    'LA': '0400000US22',
    'ME': '0400000US23',
    'MD': '0400000US24',
    'MA': '0400000US25',
    'MI': '0400000US26',
    'MN': '0400000US27',
    'MS': '0400000US28',
    'MO': '0400000US29',
    'MT': '0400000US30',
    'NE': '0400000US31',
    'NV': '0400000US32',
    'NH': '0400000US33',
    'NJ': '0400000US34',
    'NM': '0400000US35',
    'NY': '0400000US36',
    'NC': '0400000US37',
    'ND': '0400000US38',
    'OH': '0400000US39',
    'OK': '0400000US40',
    'OR': '0400000US41',
    'PA': '0400000US42',
    'RI': '0400000US44',
    'SC': '0400000US45',
    'SD': '0400000US46',
    'TN': '0400000US47',
    'TX': '0400000US48',
    'UT': '0400000US49',
    'VT': '0400000US50',
    'VA': '0400000US51',
    'WA': '0400000US53',
    'WV': '0400000US54',
    'WI': '0400000US55',
    'WY': '0400000US56',
    'AS': '0400000US60',
    'FM': '0400000US64',
    'GU': '0400000US66',
    'MH': '0400000US68',
    'MP': '0400000US69',
    'PW': '0400000US70',
    'PR': '0400000US72',
    'UM': '0400000US74',
    'VI': '0400000US78'
}

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

def fix_data_issues(df):
    changes = {
        'yes': 1,
        'no': 0,
        'not_applicable': 0
    }
    df[HEADER_VALUE_TIDY].replace(changes, inplace=True)
    return df

def tidy_dataframe(df, indicator_variable):
    """This converts the data from wide to tidy, based on the column names."""

    tidy = tidy_blank_dataframe()
    columns = df.columns.tolist()
    # If the indicator specifies an 'indicator_variable' that does not actually
    # exist in the CSV, treat it as None.
    if indicator_variable is not None and indicator_variable not in columns:
        indicator_variable = None
    # In some cases we just have to guess at the main column, and we don't
    # want to guess twice.
    main_column_picked = False
    # Loop through each column in the CSV file.
    for column in columns:
        if indicator_variable is None and column != HEADER_YEAR_WIDE and not main_column_picked:
            # If the indicator doesn't specify an indicator variable, and this
            # is not the Year column, then assume it's the main column. The
            # main column gets converted into rows without any categories.
            main_column_picked = True
            melted = tidy_melt(df, column, column)
            del melted[column]
            tidy = tidy.append(melted)
        elif column == indicator_variable:
            # Otherwise if this is the indicator variable, use this as the main
            # column.
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

    # Fix any data issues.
    tidy = fix_data_issues(tidy)

    # For rows with no value, use 0.
    tidy[HEADER_VALUE_TIDY].fillna(0, inplace=True)

    # If the CSV has no rows, we have to add one to get past data validation.
    if (len(tidy) == 0):
        tidy = tidy.append({HEADER_YEAR_TIDY: 2018, HEADER_VALUE_TIDY: 0}, ignore_index=True)

    return tidy

def tidy_csv_from_subnational_folder(csv, folder_name, subfolder_name):
    """This converts a CSV into a dataframe, tweaks the headers, and returns it."""

    try:
        df = pd.read_csv(csv, dtype=str)
    except Exception as e:
        print(csv, e)
        return False

    # Convert the folder structure into a column according to our syntax rules.
    # For example: state/alabama will turn into 'state:alabama'.
    subfolder_column = folder_name + ':' + subfolder_name

    # Add this to the columns in the dataframe.
    columns = dict()
    for column in df.columns.tolist():
        fixed = column
        if column == HEADER_ALL:
            fixed = subfolder_column
        elif column.startswith(HEADER_ALL + '|'):
            fixed = column.replace(HEADER_ALL + '|', subfolder_column + '|')
        elif column == HEADER_YEAR_WIDE:
            fixed = HEADER_YEAR_WIDE
        else:
            fixed = subfolder_column + '|' + column
        columns[column] = fixed

    return df.rename(columns, axis='columns')

def tidy_csv(csv, subnational_folders):
    """This runs all checks and processing on a CSV file and reports exceptions."""

    csv_filename = os.path.split(csv)[-1]
    metadata = get_metadata(csv_filename)

    try:
        df = pd.read_csv(csv, dtype=str)
    except Exception as e:
        print(csv, e)
        return False

    # Look in any subnational folders for a corresponding file.
    for folder in subnational_folders:
        folder_name = os.path.basename(os.path.normpath(folder))
        if folder_name in FOLDER_NAME_CONVERSIONS:
            folder_name = FOLDER_NAME_CONVERSIONS[folder_name]
        for subfolder in subnational_folders[folder]:
            subfolder_name = os.path.basename(os.path.normpath(subfolder))
            if subfolder_name in FOLDER_NAME_CONVERSIONS:
                subfolder_name = FOLDER_NAME_CONVERSIONS[subfolder_name]
            subnational_file = subfolder + csv_filename
            if os.path.isfile(subnational_file):
                dis_df = tidy_csv_from_subnational_folder(subnational_file, folder_name, subfolder_name)
                df = pd.merge(df, dis_df, how='outer', on=HEADER_YEAR_WIDE)

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

    # Check here to see if there subnational data.
    subnational_folders = dict()
    folders = glob.glob(FOLDER_DATA_CSV_SUBNATIONAL + '/*/')
    for folder in folders:
        subfolders = glob.glob(folder + '/*/')
        if (subfolders):
            subnational_folders[folder] = subfolders

    for csv in csvs:
        status = status & tidy_csv(csv, subnational_folders)

    return status

if __name__ == '__main__':
    if not main():
        raise RuntimeError("Failed tidy conversion")
    else:
        print("Success")