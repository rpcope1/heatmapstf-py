__author__ = 'Robert P. Cope'

import unittest
from heatmapstf import HeatmapsTFAPI
import time
import traceback

class HackerNewsAPIBasicTests(unittest.TestCase):
    def test_get_all_map_statistics_basic(self):
        try:
            api = HeatmapsTFAPI()
            assert api.get_all_map_statistics()
            raw_response = api.get_all_map_statistics(raw=True)
            assert raw_response
            map_names = [d.get('name') for d in raw_response]
            kill_count = [d.get('kill_count') for d in raw_response]
            assert all(kill_count)
            assert all(map_names)
            assert 'ctf_2fort' in map_names
        except Exception as e:
            traceback.print_exc()
            self.fail("Faulted with exception '{}' on get_item for test item 8863".format(e))

    def test_get_kill_data_basic(self):
        api = HeatmapsTFAPI()
        assert api.get_kill_data('ctf_2fort')
        assert api.get_kill_data('ctf_2fort', raw=True)
        assert api.get_kill_data('ctf_2fort', fields=['id', 'killer_weapon', 'killer_class'], limit=50)


if __name__ == '__main__':
    unittest.main()