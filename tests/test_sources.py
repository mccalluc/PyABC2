import warnings

import pytest

from pyabc2 import Key
from pyabc2.parse import Tune
from pyabc2.sources import examples, load_example, load_example_abc, load_url, norbeck, the_session


@pytest.mark.parametrize("tune_name", examples)
def test_examples_load(tune_name):
    tune = load_example(tune_name)
    assert type(tune) is Tune


def test_bad_example_raises():
    with pytest.raises(ValueError):
        load_example_abc("asdf")


def test_example_random():
    tune = load_example()
    assert type(tune) is Tune


@pytest.mark.slow
def test_norbeck_load():
    # NOTE: downloads files if not already present

    # TODO: test Norbeck all matches number of `X:`s in those files
    # TODO: test Norbeck `X` values in files are all unique
    tunes = norbeck.load()  # all
    jigs = norbeck.load("jigs")  # jigs only

    assert 0 < len(jigs) < len(tunes)
    assert all(t in tunes for t in jigs)
    assert set(jigs) < set(tunes)

    assert type(jigs[0]) is Tune

    assert len(set(jigs)) == len(jigs)

    # Some diacritic tests
    assert jigs[512].title == "Buachaillín Buí, An"
    assert jigs[539].title == "30-årsjiggen"
    assert jigs[486].header["composer"] == "Annlaug Børsheim, Norway"

    with pytest.raises(ValueError):
        norbeck.load("asdf")


@pytest.mark.parametrize(
    "url,title,key,type",
    [
        ("https://thesession.org/tunes/182", "The Silver Spear", "D", "reel"),
        ("https://thesession.org/tunes/182#setting22284", "The Silver Spear", "C", "reel"),
    ],
)
def test_the_session_load_url(url, title, key, type):
    tune = the_session.load_url(url)
    assert tune.title == title
    assert tune.key == Key(key)
    assert tune.type == type
    if "#" in url:  # Currently always gets set to a specific setting
        assert tune.url == url
    if "#" not in url:  # First setting
        assert tune.header["reference number"] == "1"


def test_the_session_url_check():
    with pytest.raises(AssertionError):
        the_session.load_url("https://www.google.com")


def test_the_session_load_archive():
    # NOTE: downloads file if not already present

    _ = the_session.load(n=5)  # TODO: all? (depending on time)

    with pytest.warns(UserWarning, match=r"The Session tune\(s\) failed to load"):
        tunes1 = the_session.load(n=200)
        tunes2 = the_session.load(n=200, num_workers=2)
    assert tunes1 == tunes2


def test_the_session_download_invalid():
    with pytest.raises(ValueError):
        _ = the_session.download("asdf")


@pytest.mark.slow
@pytest.mark.parametrize(
    "which", ["aliases", "events", "recordings", "sessions", "sets", "tune_popularity", "tunes"]
)
def test_the_session_load_meta(which):
    import numpy as np
    import pandas as pd
    from pandas.testing import assert_frame_equal

    df1 = the_session.load_meta(which)
    df1_csv = the_session.load_meta(which, format="csv")
    df2 = the_session.load_meta(which, downcast_ints=True)
    df3 = the_session.load_meta(which, convert_dtypes=True)

    try:
        assert df1.equals(df1_csv)
    except AssertionError:
        unequal = ~(df1 == df1_csv)
        df1_ = df1[unequal].dropna(axis="index", how="all").dropna(axis="columns", how="all")
        df1_csv_ = (
            df1_csv[unequal].dropna(axis="index", how="all").dropna(axis="columns", how="all")
        )
        cmp = pd.concat([df1_, df1_csv_.rename(columns=lambda c: f"{c}_csv")], axis="columns")
        warnings.warn(f"CSV and JSON for {which} have differences:\n{cmp}")

    assert_frame_equal(df1, df2, check_dtype=False)
    assert not (df2.dtypes == df1.dtypes).all()
    assert not (df3.dtypes == df1.dtypes).all()
    if "latitude" in df1:
        for df in [df1, df1_csv, df2]:
            assert df.latitude.dtype == np.float64
            assert df.longitude.dtype == np.float64
        # in df3, `pd.Float64Dtype()`


def test_the_session_load_meta_invalid():
    with pytest.raises(ValueError):
        _ = the_session.load_meta("asdf")

    with pytest.raises(ValueError):
        _ = the_session.load_meta("sessions", format="asdf")


def test_int_downcast():
    import numpy as np
    import pandas as pd

    for x, expected_dtype, expected_dtype_ext in [
        # short short (8)
        ([int(1e2)], np.uint8, pd.UInt8Dtype()),
        ([int(1e2), -1], np.int8, pd.Int8Dtype()),
        # short (16)
        ([int(1e4)], np.uint16, pd.UInt16Dtype()),
        ([int(1e4), -1], np.int16, pd.Int16Dtype()),
        # long (32)
        ([int(1e9)], np.uint32, pd.UInt32Dtype()),
        ([int(1e9), -1], np.int32, pd.Int32Dtype()),
        # long long (64)
        ([int(1e18)], np.uint64, pd.UInt64Dtype()),
        ([int(1e18), -1], np.int64, pd.Int64Dtype()),
    ]:
        s = pd.Series(x)
        assert s.dtype == np.int64

        s2 = s.astype(the_session._choose_int_type(s))
        assert s2.dtype == expected_dtype

        s3 = s.astype(the_session._choose_int_type(s, ext=True))
        assert s3.dtype == expected_dtype_ext


def test_load_url():
    tune = load_url("https://thesession.org/tunes/10000")
    assert tune.title == "Brian Quinn's"

    tune = load_url("https://norbeck.nu/abc/display.asp?rhythm=slip+jig&ref=106")
    assert tune.title == "For The Love Of Music"

    with pytest.raises(NotImplementedError):
        _ = load_url("https://www.google.com")
