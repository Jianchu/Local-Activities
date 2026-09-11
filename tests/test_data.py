import json
import sys
import unittest
from pathlib import Path
from urllib.parse import urlparse
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from collect import dates

class CalendarTests(unittest.TestCase):
    def test_date_ranges(self):
        self.assertEqual(dates('September 18, 2026 - October 4, 2026'), ('2026-09-18','2026-10-04'))
        self.assertEqual(dates('05 May 2026 to 22 Dec 2026, Library'), ('2026-05-05','2026-12-22'))
        self.assertEqual(dates('Date to be confirmed'), (None,None))

    def test_published_data(self):
        data = json.loads((ROOT/'public/data/events.json').read_text(encoding='utf-8'))
        self.assertEqual({e['city'] for e in data['events']}, {'Surrey','Richmond'})
        ids = set()
        for e in data['events']:
            for key in ['title','description','time','location','url','category','startDate','endDate']:
                self.assertTrue(e[key], (e['title'],key))
            self.assertNotIn(e['id'],ids)
            ids.add(e['id'])
            self.assertLessEqual(e['startDate'],e['endDate'])
            self.assertIn(urlparse(e['url']).hostname, ['www.surrey.ca','www.richmond.ca'])

    def test_session_specific_venues(self):
        data = json.loads((ROOT/'public/data/events.json').read_text(encoding='utf-8'))
        for e in data['events']:
            if e['title'] == 'Garden Work Parties':
                self.assertNotEqual(e['location'], 'Various')

if __name__ == '__main__':
    unittest.main()
