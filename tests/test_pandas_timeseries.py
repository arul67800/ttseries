import datetime
import unittest

import pandas
import pytz
import redis

from ttseries import RedisPandasTimeSeries
from ttseries.utils import np_datetime64_to_timestamp


class RedisPandasTimeSeriesTest(unittest.TestCase):
    """
    """

    def setUp(self):
        # https://github.com/pandas-dev/pandas/issues/9287
        self.columns = ["value"]
        self.dtypes = {"value": "int64"}
        self.timezone = pytz.timezone("Asia/Shanghai")
        redis_client = redis.StrictRedis()

        self.time_series = RedisPandasTimeSeries(redis_client,
                                                 columns=self.columns,
                                                 timezone=self.timezone,
                                                 dtypes=self.dtypes,
                                                 max_length=20)

    def tearDown(self):
        self.time_series.flush()

    def prepare_dataframe(self, length):
        now = datetime.datetime.now()
        date_range = pandas.date_range(now, periods=length,
                                       freq="1min", tz=self.timezone)

        return pandas.DataFrame([i + 1 for i in range(len(date_range))],
                                index=date_range, columns=self.columns)

    def dataframe_empty(self, columns, dtypes, index=None):
        data_frame = pandas.DataFrame(index=index)
        for column, dtype in zip(columns, dtypes):
            data_frame[column] = pandas.Series(dtype=dtype)
        return data_frame

    def test_add(self):
        key = "AAPL:SECOND"
        data_frame = self.prepare_dataframe(10)
        series_item = data_frame.iloc[0]

        self.time_series.add(key, series_item)
        datetime_value = data_frame.index.values[0]

        timestamp = np_datetime64_to_timestamp(datetime_value)

        result = self.time_series.get(key, timestamp)
        pandas.testing.assert_series_equal(series_item, result)

    def test_get_slice(self):
        key = "AAPL:SECOND"
        data_frame = self.prepare_dataframe(20)
        self.time_series.add_many(key, data_frame)

        results_frame = self.time_series.get_slice(key)
        pandas.testing.assert_frame_equal(data_frame, results_frame)

    def test_iter(self):
        key = "AAPL:SECOND"
        data_frame = self.prepare_dataframe(10)
        self.time_series.add_many(key, data_frame)
        new_data_frame = self.dataframe_empty(self.columns,
                                       dtypes=[int])

        for series in self.time_series.iter(key):
            new_data_frame = new_data_frame.append(series)
        pandas.testing.assert_frame_equal(data_frame, new_data_frame)
