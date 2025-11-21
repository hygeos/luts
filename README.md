# luts.py


[![image](https://img.shields.io/pypi/v/luts.svg)](https://pypi.python.org/pypi/luts)
[![image](https://img.shields.io/conda/vn/conda-forge/luts.svg)](https://anaconda.org/conda-forge/luts)
[![image](https://pepy.tech/badge/luts)](https://pepy.tech/project/luts)

Multidimensional labeled arrays and datasets in Python. This module provides objects whose design is close to [xarray](http://xarray.pydata.org/).

Provides the following objects:

- LUT (look-up table): a multidimensional array with labeled axes.
The equivalent of this object in xarray is [`xarray.DataArray`](http://xarray.pydata.org/en/stable/generated/xarray.DataArray.html)
- MLUT (multi-look-up table): a set of LUTs
The equivalent of this object in xarray is [`xarray.Dataset`](http://xarray.pydata.org/en/stable/generated/xarray.Dataset.html)


## Installation

It can be installed in your current python environment, using one of the commands:
```shell
$ conda install -c conda-forge luts
```

```shell
$ pip install luts
```

```shell
$ # using a git repository
$ pip install git+https://github.com/hygeos/luts.git
```

```shell
$ # using a directory
$ pip install luts/ # or in editable mode: `pip install -e luts/`
```

## Testing

    $ pytest tests
