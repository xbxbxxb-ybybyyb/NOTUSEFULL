import unittest
import pandas as pd



class TestPandas(unittest.TestCase):

    def test_pickle(self):
        unpickled_df = pd.read_pickle('sample_pickle.pkl')
        origin_df = pd.DataFrame({"bar": range(5, 10), "foo": range(5)})
        self.assertTrue(origin_df.equals(unpickled_df))
        print("finish read pickle!")
         
