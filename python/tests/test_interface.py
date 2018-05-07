"""
Basic tests for the information API.
"""
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import unittest
import tempfile
import os

import six
import numpy as np

import kastore as kas
import kastore.exceptions as exceptions


class InterfaceTest(unittest.TestCase):
    """
    Superclass of tests that assess the kastore module interface.
    """
    def setUp(self):
        fd, path = tempfile.mkstemp(prefix="kas_test_info")
        os.close(fd)
        self.temp_file = path

    def tearDown(self):
        try:
            os.unlink(self.temp_file)
        except OSError:
            pass


class TestBasicInfo(InterfaceTest):
    """
    Check that the info we return is accurate.
    """

    def verify(self, data):
        kas.dump(data, self.temp_file)
        for use_mmap in [True, False]:
            new_data = kas.load(self.temp_file, use_mmap=use_mmap)
            for key, array in new_data.items():
                info = new_data.info(key)
                s = str(info)
                self.assertGreater(len(s), 0)
                self.assertEqual(array.nbytes, info.size)
                self.assertEqual(array.shape, info.shape)
                self.assertEqual(array.dtype, np.dtype(info.dtype))

    def test_all_dtypes(self):
        dtypes = [
            "int8", "uint8", "uint32", "int32", "uint64", "int64", "float32", "float64"]
        for n in range(10):
            data = {dtype: np.arange(n, dtype=dtype) for dtype in dtypes}
            self.verify(data)


class TestClosedStore(InterfaceTest):
    """
    Checks that a closed store is no longer accessible.
    """
    def verify_closed(self, store):
        self.assertRaises(exceptions.StoreClosedError, store.get, "a")
        self.assertRaises(exceptions.StoreClosedError, store.info, "a")
        self.assertRaises(exceptions.StoreClosedError, list, six.iterkeys(store))
        self.assertRaises(exceptions.StoreClosedError, list, six.iteritems(store))

    def test_context_manager(self):
        N = 100
        data = {"a": np.arange(N)}
        kas.dump(data, self.temp_file)
        with kas.load(self.temp_file) as store:
            self.assertIn("a", store)
            self.assertTrue(np.array_equal(store["a"], np.arange(N)))
        self.verify_closed(store)

    def test_manual_close(self):
        N = 100
        data = {"a": np.arange(N)}
        kas.dump(data, self.temp_file)
        store = kas.load(self.temp_file)
        self.assertIn("a", store)
        self.assertTrue(np.array_equal(store["a"], np.arange(N)))
        store.close()
        self.verify_closed(store)


@unittest.skip("Fails with Bus error")
class TestMmapErrors(InterfaceTest):
    """
    Checks that we correctly detect file errors when using mmaps.
    """
    def write_data(self):
        N = 1000
        data = {"{}".format(j): np.arange(N) for j in range(100)}
        kas.dump(data, self.temp_file)

    def test_truncated_file(self):
        self.write_data()
        store = kas.load(self.temp_file)
        # Truncate the underlying file.
        with open(self.temp_file, "w"):
            pass
        print(store["0"])
        store.close()
