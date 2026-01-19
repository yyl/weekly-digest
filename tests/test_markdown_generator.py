import unittest
from datetime import datetime
from src.readwise_digest.markdown_generator import MarkdownGenerator

class TestMarkdownGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = MarkdownGenerator()
        self.base_processed_data = {
            'date_range': {
                'start_formatted': '2023-01-01',
                'end_formatted': '2023-01-07'
            },
            'documents': {
                'total_count': 5,
                'total_word_count': 0,
                'average_time_to_archive': 24.5,
                'category_breakdown': {},
                'source_breakdown': {},
                'tag_breakdown': {},
                'documents': []
            },
            'highlights': {
                'total_count': 10,
                'highlights': []
            },
            'generation_timestamp': datetime.now()
        }

    def test_reading_time_under_hour(self):
        # 2250 words / 225 wpm = 10 minutes
        data = self.base_processed_data.copy()
        data['documents']['total_word_count'] = 2250

        markdown = self.generator.generate_digest(data)

        self.assertIn("- **Time Spent Reading**: 10 minutes", markdown)

    def test_reading_time_over_hour(self):
        # 15000 words / 225 wpm = 66.66 minutes -> 1h 7m
        data = self.base_processed_data.copy()
        data['documents']['total_word_count'] = 15000

        markdown = self.generator.generate_digest(data)

        self.assertIn("- **Time Spent Reading**: 1h 7m", markdown)

    def test_reading_time_exact_hour(self):
        # 13500 words / 225 wpm = 60 minutes -> 1h 0m
        data = self.base_processed_data.copy()
        data['documents']['total_word_count'] = 13500

        markdown = self.generator.generate_digest(data)

        self.assertIn("- **Time Spent Reading**: 1h 0m", markdown)

if __name__ == '__main__':
    unittest.main()
