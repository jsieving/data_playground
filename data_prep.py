'''
Data sources
-------------------------------------------------------------------------------
Confirmed cases and deaths:
Accessed from https://github.com/CSSEGISandData/COVID-19

Testing and populations:
    Accessed from https://covidtracking.com/
        - Population is calculated as the sum of populations for all locales
        within a state or territory.
        - Test positivity is computed as the ratio of reported positive tests to
        reported tests, as aggregated in this source.

-------------------------------------------------------------------------------
'''

import pandas as pd


def add_state(total_tests_frame, pos_ratios_frame, name, abbr):
    '''
    Adds data for a single state or territory to a table accumulating all state
    data. Fetches a .json file, then separates out total tests over time and
    computed positivity ratio over time, and adds these columns to the
    respective DataFrames passed in.

    Params
    DataFrame `total_tests_frame`: table of combined per-state time series
    DataFrame `pos_ratios_frame`: table of combined per-state time series
    string `name`: column name for state/territory
    string `abbr`: 2-letter abbreviation for state/territory

    Returns
    DataFrame `total_tests_frame`: copy of input with additional column added
    DataFrame `pos_ratios_frame`: copy of input with additional column added
    '''
    data_url = f"https://covidtracking.com/api/v1/states/%s/daily.json" % abbr.lower()
    data = pd.read_json(data_url)
    data["date"] = pd.to_datetime(data["date"], format='%Y%m%d')
    data = data.set_index("date")
    positive = pd.Series(data = data["positive"])
    total_tests = pd.Series(data = data["totalTestResults"])
    pos_ratios = positive.div(total_tests)

    if len(total_tests_frame.index) < len(total_tests.index):
        total_tests_frame = total_tests_frame.reindex(total_tests.index)

    if len(pos_ratios_frame.index) < len(pos_ratios.index):
        pos_ratios_frame = pos_ratios_frame.reindex(pos_ratios.index)

    total_tests_frame[name] = total_tests
    pos_ratios_frame[name] = pos_ratios

    return total_tests_frame, pos_ratios_frame

def save_csv_commented(file_name, dataframe, settings=None):
    '''
    Writes a DataFrame to the given file name with comments added at the top
    according to the contents of the settings dictionary.

    Params
    string `file_name`: file path of .csv file to write to
    DataFrame `dataframe`: table to save
    dict `settings`: pairs of DataPage attribute options and their values
    '''
    f = open(file_name, 'w')
    if settings is not None:
        for key, val in settings.items():
            # ampersand (&) is comment character
            f.write("&%s:,%s,\n" % (str(key), str(val)))
    
    dataframe.to_csv(f)
    f.close()

def prepare():
    '''
    Downloads, cleans, restructures and saves data as csv files to play
    with in the application. These files can be modified and others can be
    created in a similar format.

    Basically a script wrapped in a function so that the main application can
    handily provide the option of re-fetching data when it's launched.
    '''
    ##### Testing and populations accessed from https://covidtracking.com/

    total_tests_frame = pd.DataFrame()

    pos_ratios_frame = pd.DataFrame()

    names_file = open("state_info/state_names.txt")
    names = [name.strip() for name in names_file.readlines()]
    abbrs_file = open("state_info/state_abbrs.txt")
    abbrs = [abbr.strip() for abbr in abbrs_file.readlines()]

    for name, abbr in zip(names, abbrs):
        total_tests_frame, pos_ratios_frame = add_state(total_tests_frame, pos_ratios_frame, name, abbr)
    
    total_tests_frame = total_tests_frame.sort_index(axis='index')

    pos_ratios_frame = pos_ratios_frame.sort_index(axis='index')

    total_tests_settings = {"ylabel": "Tests", "delta_allowed": True, "per_capita_allowed": True}

    save_csv_commented("tables/Tests_US.csv", total_tests_frame, total_tests_settings)

    save_csv_commented("tables/Positivity_Ratio_US.csv", pos_ratios_frame, {"ylabel": "Fraction of total tests 'positive'"})

    
    ##### Confirmed cases accessed from https://github.com/CSSEGISandData/COVID-19
    
    confirmed_time_series_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv"

    confirmed_time_series = pd.read_csv(confirmed_time_series_url, header=0, index_col=6)

    confirmed_time_series = confirmed_time_series.drop(labels=["Diamond Princess", "Grand Princess"], axis=0)

    confirmed_time_series = confirmed_time_series.drop(labels=["UID", "iso2", "iso3", "code3", "FIPS", "Country_Region", "Lat", "Long_", "Combined_Key"], axis=1)

    confirmed_time_series = confirmed_time_series.groupby(['Province_State']).sum()

    confirmed_time_series = confirmed_time_series.T

    confirmed_time_series = confirmed_time_series.set_index(pd.to_datetime(confirmed_time_series.index, format='%m/%d/%y'))

    confirmed_settings = {"ylabel": "Cases", "log_allowed": True, "delta_allowed": True, "per_capita_allowed": True, "suggested_scaling": 1000000}
    
    save_csv_commented("tables/Confirmed_US.csv", confirmed_time_series, confirmed_settings)


    ##### Deaths accessed from https://github.com/CSSEGISandData/COVID-19

    deaths_time_series_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv"

    deaths_time_series = pd.read_csv(deaths_time_series_url, header=0, index_col=6)

    deaths_time_series = deaths_time_series.drop(labels=["Diamond Princess", "Grand Princess"], axis=0)

    deaths_time_series = deaths_time_series.drop(labels=["UID", "iso2", "iso3", "code3", "FIPS", "Country_Region", "Lat", "Long_", "Combined_Key"], axis=1)

    deaths_time_series = deaths_time_series.groupby(['Province_State']).sum()

    population_data = pd.Series(data = deaths_time_series["Population"])

    deaths_time_series = deaths_time_series.drop(labels=["Population"], axis=1)

    deaths_time_series = deaths_time_series.T

    deaths_time_series = deaths_time_series.set_index(pd.to_datetime(deaths_time_series.index, format='%m/%d/%y'))

    population_data.to_csv("state_info/Population_US.csv")

    deaths_settings = {"ylabel": "Deaths", "log_allowed": True, "delta_allowed": True, "per_capita_allowed": True, "suggested_scaling": 1000000}

    save_csv_commented("tables/Deaths_US.csv", deaths_time_series, deaths_settings)


if __name__ == "__main__":
    prepare()