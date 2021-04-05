Defining data importation
=========================

To perform import of data within Zimagi, we will also have to define commands 
within the YAML configuration files, but it is worth looking at the Python code 
needed to do the concrete data acquisition first.

The means by which we do this is defined in the code 
``$ZDIR/lib/modules/default/noaa-stations/plugins/source/noaa_stations.py``.
This name (minus the ``.py`` part) is indicated in the file
``$ZDIR/lib/modules/default/noaa-stations/spec/plugins/source.yml``::

  plugin:
    source:
      # Identify providers across modules
      providers:
        noaa_stations:
          requirement:
            min_year:
              type: int
              help: The beginning year to query
            max_year:
              type: int
              help: The end year to query
          option:
            station_ids:
              type: list
              help: A list of station IDs to include
              default: null

Within this configuration, beyond indicating what Python file to incorporate,
we define required and optional fields to make available to that Python code.
In this example, the Python code will *always* have access to integer values for 
``min_year`` and ``max_year`` and *might* have access to a list value named
``station_ids``.  Field names must be spelled as valid Python identifiers.

While some Python code is needed here, it mostly follows a fairly strictly 
stereotyped pattern.  Obviously, the code needed will vary based on the data 
format of the source and any authentication system that might be required to 
access it.  For this module example, we chose data that is publicly available 
and is contained in a fairly straightforward CSV format.

The bulk of this importer is a class called ``Provider`` that needs to define 
three methods, ``.item_columns()``, ``.load_items()``, and ``.load_item()``.
Exactly what other Python libraries you might use are very specific to the 
nature of the data source.  The Zimagi runtime environment **will** make 
available *Pandas* and *requests*, which are certainly two of those that you 
will use very often.

If you need to utilize other libraries, such as database adapters or data format
readers you will need to add them to the Zimagi runtime by **[TODO]**.

Python import code
------------------

Let us look at ``noaa_stations.py`` in a few steps::

    # filename matches name given in plugins data definition
    from systems.plugins.index import BaseProvider
    import requests
    import logging
    import pandas as pd
    import io

    logger = logging.getLogger(__name__)

    class Provider(BaseProvider("source", "noaa_stations")):
	      # Generate a parent class based on 'source' and plugin definition
	      # Three interface methods required: item_columns, load_items, load_item

We do not have to use *requests*, *pandas*, *logging*, or *io*, but they are
particular modules that are useful in the methods below.  All we really need is
to define the class ``Provider`` which has a funny dynamic parent class defined
by passing names to the system class ``BaseProvider``.  You need not think about
the metaclass magic underneath this, just copy the pattern.  Always include 
"source" and the name you defined in ``source.yml`` as strings passed to
``BaseProvider``.

Now let us look at the methods we need::

    def item_columns(self):
        # Return a list of header column names for source dataframe
        return ["station_id", "station_name", "date",
                "temperature", "temperature_attrs",
                "latitude", "longitude", "elevation"]

This one is very simple.  All it does is return a list of string names for 
fields, as we wish to spell them within Zimagi command line or API access.
Continuing, let us look at the simpler ``load_item()`` method next::

    def load_item(self, row, context):
        # Dataframe iterrows passes tuple of (index, object)
        row = row[1]
        # Return values list that maps to header elements in item_columns()
        return [row.STATION, row.NAME, row.DATE,
                None if row.TEMP == 9999.9 else row.TEMP, row.TEMP_ATTRIBUTES,
                row.LATITUDE, row.LONGITUDE, row.ELEVATION]

The task of this method is to take a single ``row`` object and return a list of
values.  The ``row`` object can be anything whatsoever, as long as it lets us
figure out a collection of values to match up with the column names returned by
``item_columns``.  In this specific example, the object received is a tuple 
containing an index and a Pandas Series (as we will see).  The index into the 
underlying Pandas DataFrame is irrelevant to us, but the Series has everything
we care about.

To return a Python list of values, we mostly just access each record in the 
Series, which at this point have names corresponding to the column names in the
source CSV files.  You can see that those are spelled a bit differently than
the names we prefer to use in our module (if nothing else, we do not want the 
names in ALLCAPS), but the translation is obvious enough from their spelling.

We can also, of course, line up the index positions of the column names we used
with the items returned by the method.  In one case, we do some minor data 
cleanup by marking the "missing data" sentinel of 9999.9 as explicitly None 
(i.e. the Python ``None``, which gets represented as ``NULL`` in the RDBMS). In
concept though, we could do whatever other calculation or substitution we wished
to within this method.

Loading items
-------------

The heavy lifting of this data import ``Provider`` class is performed in the
method ``.load_items()``.  Of course, being Python code, we are free to define
whatever other methods might be useful to us within this class, as long as they
do not use these few reserved names::

    def load_items(self, context):
        base_url = "https://www.ncei.noaa.gov/data/global-summary-of-the-day/access"
        for year in range(self.field_min_year, self.field_max_year+1):
            year_url = f"{base_url}/{year}"
            if not self.field_station_ids:
                # Want all files for this year
                pass
            else:
                # Only pull the list of station_ids given
                for station_id in self.field_station_ids:
                    station_url = f"{year_url}/{station_id}.csv"
                    self.command.info(f"Fetching data from {station_url}")
                    resp = requests.get(station_url)
                    if resp.status_code == 200:
                        logger.info(f"Pulled {station_url}")
                        df = pd.read_csv(io.StringIO(resp.text))
                        yield from df.iterrows()
                    else:
                        logger.info(f"Station {station_id} not present for {year}")

The implementation shown here is partial.  It only accepts the case where 
station IDs are explicitly provided.  We have yet to implement the common case 
where we load "all stations matching the years given."  To do that, we will have
to program a little bit of web scraping to read the directory at the base URL
and figure out which CSV files exist.

Bracketing the part not fleshed out, we see everything that is functionally 
needed in the ``else:`` block.  We start at a base URL which we know, by 
examination and by the documentation of the data source, contains subdirectories
named after years.  Moreover, we have indicated, in the ``source.yml`` file
discussed above, that the fields named ``min_year`` and ``max_year`` are 
required to be present, and to be integers.  To use them within the Python code,
we prefix their names with ``field_``.  

This code loops over years matching the range defined by the fields, then uses
the *requests* module to determine whether a corresponding CSV URL exists. We
also log the status of what was done, which is useful but not required.

The essential operation of the ``.load_items()`` method is that it yields each 
individual ``row`` object of the sort that ``.load_item()`` will consume.  That
concludes the Python code needed for this module.  What remains is entirely to 
configure commands that the Zimagi runtime will use to utilize this Python code
(once combined with base scaffolding code behind the scenes).
