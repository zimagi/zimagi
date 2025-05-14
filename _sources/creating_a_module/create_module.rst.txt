=================
Creating a module
=================

This tutorial will demonstrate to developers how to create a Zimagi module.
As an example, we will create a module that obtains data from a public data
source provided by the United States National Oceanic and Atmospheric
Administration (NOAA).

This module is available in a public GitHub repository at:

  https://github.com/zimagi/module-noaa-stations

Our module development will be performed locally, which provides an interactive
environment for enhancing and testing feature as they are added.

The example we will work through utilizes a large collection of CSV files, each
of which is regular in form.  At a particular URL, there are subdirectories
named as years, and within each of those directories are many individual CSV
files, each containing information about data from one weather station during
that year.

Inside each of these CSV files, rows contain a mixture of information about the
station itself, such as its name, altitude and latitude, and information about
the observation, such as temperature, humidity, visibility, precipitation, and
so on.

For comparison, you may want to look at comparisons with a standalone script
written for a similar purpose.
