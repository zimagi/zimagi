from django.conf import settings

import pandas


def merge(*dataframes, required_fields = None, ffill = False):
    results = None

    for dataframe in dataframes:
        if dataframe is not None:
            if results is None:
                results = dataframe
            else:
                results = results.join(dataframe, how = 'outer')

                if isinstance(dataframe.index.dtype, pandas.core.dtypes.dtypes.DatetimeTZDtype):
                    results.index = pandas.to_datetime(results.index, utc = True)
                    results.index = results.index.tz_convert(settings.TIME_ZONE)

    if required_fields:
        results.dropna(subset = list(required_fields), how = 'any', inplace = True)

    if ffill:
        results.ffill(inplace = True)

    return results

def concatenate(*dataframes, ffill = False):
    results = pandas.concat(dataframes, join = 'outer', sort = False)
    results = results[~results.index.duplicated(keep = 'last')].sort_index()

    if ffill:
        results.ffill(inplace = True)

    return results


def get_csv_file_name(path):
    return "{}.csv".format(path)
