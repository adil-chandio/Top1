import unittest
from unittest.mock import patch
from ranged_movie import RangeReader

class Response:
    def __init__(self,status,data,content_range):
        self.status=status; self.data=data; self.headers={'Content-Range':content_range};self.reads=0
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,n):self.reads+=1;return self.data[:n]

class RangeTests(unittest.TestCase):
    def test_ignoring_range_never_reads_body(self):
        response=Response(200,b'whole archive','')
        with patch('urllib.request.urlopen',return_value=response),self.assertRaises(ValueError):
            RangeReader('https://example.invalid/archive.zip')
        self.assertEqual(response.reads,0)
    def test_wrong_range_rejected(self):
        response=Response(206,b'x','bytes 1-1/100')
        with patch('urllib.request.urlopen',return_value=response),self.assertRaises(ValueError):
            RangeReader('https://example.invalid/archive.zip')
    def test_bounded_read_and_seek(self):
        responses=[Response(206,b'a','bytes 0-0/10'),Response(206,b'hi','bytes 8-9/10')]
        with patch('urllib.request.urlopen',side_effect=responses):
            reader=RangeReader('https://example.invalid/archive.zip')
            reader.seek(-2,2)
            self.assertEqual(reader.read(100),b'hi')
            self.assertEqual(reader.read(),b'')
            self.assertEqual(reader.transferred,3)
            with self.assertRaises(ValueError):reader.seek(-1)

if __name__=='__main__':unittest.main()
