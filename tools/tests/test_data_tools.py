import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
from data_tools import RepositoryData


class DataToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        directory = self.root / 'data/team-kandu'
        directory.mkdir(parents=True)
        (directory / 'rtl_stops.csv').write_text('code,name,lat,lon\n207,B.Dharavandhoo,5.1,73.1\n208,B.Eydhafushi,5.2,73.2\n', encoding='utf-8')
        (self.root / 'research').mkdir()
        (self.root / 'research/01_note.md').write_text('# Test research\nVerified example.', encoding='utf-8')
        self.repo = RepositoryData(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_catalogue_is_useful_without_raw_data(self):
        result = self.repo.list_datasets()
        rows = {row['id']: row for row in result['datasets']}
        self.assertTrue(rows['rtl_stops']['available'])
        self.assertFalse(rows['mtcc']['available'])
        self.assertIn('SYNTHETIC', ' '.join(rows['mtcc']['caveats']))

    def test_describe_csv_preserves_headers_and_records_sample_scope(self):
        result = self.repo.describe_dataset('rtl_stops')
        self.assertEqual(result['columns'], ['code', 'name', 'lat', 'lon'])
        self.assertEqual(result['rows_inspected'], 2)
        self.assertNotIn('total_rows', result)

    def test_sample_limit_is_enforced_and_values_are_not_coerced(self):
        result = self.repo.sample_rows('rtl_stops', 1)
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['rows'][0]['code'], '207')
        for limit in [0, 51, True, '5']:
            with self.assertRaises(ValueError):
                self.repo.sample_rows('rtl_stops', limit)

    def test_unknown_ids_and_research_traversal_are_rejected(self):
        with self.assertRaises(ValueError):
            self.repo.describe_dataset('../../outside')
        with self.assertRaises(ValueError):
            self.repo.read_research('../README.md')
        self.assertEqual(self.repo.read_research('01_note.md')['truncated'], False)
        self.repo.catalogue['escape'] = {'id': 'escape', 'path': '../outside.csv'}
        with self.assertRaises(ValueError):
            self.repo.describe_dataset('escape')

    def test_missing_data_has_actionable_metadata(self):
        result = self.repo.describe_dataset('mtcc')
        self.assertFalse(result['available'])
        self.assertIn('download', result['next_step'].lower())

    def test_research_can_be_discovered_before_reading(self):
        self.assertEqual(self.repo.read_research()['notes'][0]['name'], '01_note.md')

    def test_stdio_negotiation_discovery_and_call(self):
        messages = [
            {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'test','version':'1'}}},
            {'jsonrpc':'2.0','method':'notifications/initialized'},
            {'jsonrpc':'2.0','id':2,'method':'tools/list'},
            {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'data_list_datasets','arguments':{}}},
            {'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':'data_sample_rows','arguments':{'dataset_id':'rtl_stops','limit':51}}},
        ]
        process = subprocess.run([sys.executable, str(TOOLS/'data_mcp.py'), '--root', str(self.root)], input='\n'.join(map(json.dumps,messages))+'\n', capture_output=True, text=True, timeout=15)
        self.assertEqual(process.returncode, 0, process.stderr)
        replies = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(len(replies), 4)
        self.assertEqual(replies[0]['result']['protocolVersion'], '2025-06-18')
        self.assertEqual(len(replies[1]['result']['tools']), 4)
        self.assertFalse(replies[2]['result']['isError'])
        self.assertTrue(replies[3]['result']['isError'])


if __name__ == '__main__':
    unittest.main()
