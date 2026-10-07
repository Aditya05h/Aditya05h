"""Regression checks for calendar accuracy, caching, and SVG output."""
from datetime import date, timedelta
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from render_art import metrics, monthly_totals, render, render_stats
from update_contributions import parse_calendar, update_image_links, validate_days


def sample_days():
    first = date(2025, 10, 7)
    days = [{'date': (first + timedelta(days=i)).isoformat(), 'count': 0, 'level': 0}
            for i in range(366)]
    for index, count in [(0, 30), (-2, 12), (-1, 12)]:
        days[index].update(count=count, level=4)
    return days


def html_for(days, total=54):
    return f'<h2>{total} contributions in the last year</h2>' + ''.join(
        f'<td id="d{i}" data-date="{day["date"]}" data-level="{day["level"]}"></td>'
        f'<tool-tip for="d{i}">{day["count"]} contributions on this date.</tool-tip>'
        for i, day in enumerate(days))


class ActivityTests(unittest.TestCase):
    def setUp(self):
        self.days = sample_days()
        self.data = {'username': 'Aditya05h', 'days': self.days,
                     'fetched_at': '2026-10-07T12:34:00+00:00'}

    def test_exact_daily_and_yearly_counts(self):
        parsed = parse_calendar(html_for(self.days))
        self.assertEqual(parsed[-1]['count'], 12)
        self.assertEqual(metrics(parsed)[0], 54)
        self.assertEqual(sum(monthly_totals(parsed).values()), 54)

    def test_incomplete_or_inconsistent_calendar_fails(self):
        with self.assertRaisesRegex(ValueError, 'yearly total'):
            parse_calendar(html_for(self.days, total=55))
        with self.assertRaisesRegex(ValueError, 'missing dates'):
            validate_days(self.days[:100] + self.days[101:])
        with self.assertRaisesRegex(ValueError, 'count for'):
            parse_calendar(html_for(self.days).replace('12 contributions', 'unavailable'))

    def test_month_boundaries_keep_both_octobers(self):
        months = monthly_totals(self.days)
        self.assertEqual(months['2025-10'], 30)
        self.assertEqual(months['2026-10'], 24)
        self.assertEqual(len(months), 13)

    def test_today_zero_preserves_only_yesterdays_streak(self):
        self.assertEqual(metrics(self.days)[2:4], (2, 2))
        self.days[-1].update(count=0, level=0)
        self.assertEqual(metrics(self.days)[2], 1)
        self.days[-2].update(count=0, level=0)
        self.assertEqual(metrics(self.days)[2], 0)

    def test_no_activity(self):
        for day in self.days:
            day.update(count=0, level=0)
        self.assertEqual(metrics(self.days)[:4], (0, 0, 0, 0))
        ET.fromstring(render_stats(self.data))

    def test_both_images_share_snapshot_and_exact_numbers(self):
        calendar = ET.fromstring(render(self.data))
        stats = ET.fromstring(render_stats(self.data))
        ns = {'s': 'http://www.w3.org/2000/svg'}
        cells = [r for r in calendar.findall('s:rect', ns) if 'cell' in r.get('class', '')]
        self.assertEqual(len(cells), len(self.days))
        values = {t.get('data-metric'): t.text for t in stats.findall('.//s:text', ns)
                  if t.get('data-metric')}
        self.assertEqual(values['contributions'], '54')
        self.assertEqual(len(values), 6)
        self.assertNotIn('<set ', render_stats(self.data))
        for svg in (render(self.data), render_stats(self.data)):
            self.assertIn('Updated 07 Oct 2026, 12:34 UTC', svg)

    def test_cache_versions_update_together_without_changing_bio(self):
        readme = '<p>Software Development Engineer</p>\n' + ''.join(
            f'<img src="./assets/{name}.svg?v=old" width="860" />'
            for name in ('contributions', 'stats'))
        changed = update_image_links(readme, 'Aditya05h', 'abc123')
        self.assertEqual(changed.count('?v=abc123'), 2)
        self.assertIn('<p>Software Development Engineer</p>', changed)
        self.assertEqual(update_image_links(changed, 'Aditya05h', 'abc123'), changed)
        with self.assertRaises(ValueError):
            update_image_links('<p>Missing charts</p>', 'Aditya05h', 'abc123')

    def test_saved_snapshot_totals_match_every_view(self):
        data = json.loads((Path(__file__).resolve().parents[1] / 'data/contributions.json').read_text())
        validate_days(data['days'])
        total = sum(d['count'] for d in data['days'])
        self.assertEqual(sum(monthly_totals(data['days']).values()), total)
        self.assertIn(f'{total:,} contributions in the last year', render(data))
        self.assertIn(f'{total} contributions,', render_stats(data))


if __name__ == '__main__':
    unittest.main()
