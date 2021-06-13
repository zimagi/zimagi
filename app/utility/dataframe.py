import pandas


def merge(*dataframes, required_fields = None, ffill = False):
    results = None

    for dataframe in dataframes:
        if dataframe is not None:
            if results is None:
                results = dataframe
            else:
                results = results.join(dataframe, how = 'outer')

    if required_fields is not None:
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
