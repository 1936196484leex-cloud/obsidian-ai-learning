"""Run: python3 -m unittest -v test_safety.py (no API or vault required)."""
import tempfile
import unittest
from pathlib import Path
from obsidian_utils import HEADINGS, fill_sections, save_note, template
from runner import validate

class SafetyTests(unittest.TestCase):
    def test_manual_and_repeat(self):
        old = "# Day\n\n## Today's Top 3\n- [ ] My own task\n\n## Deep Work\n"
        result = fill_sections(old, {HEADINGS[0]: '- [ ] AI task', HEADINGS[2]: 'Focus'})
        self.assertIn('- [ ] My own task', result)
        self.assertNotIn('AI task', result)
        self.assertEqual(result, fill_sections(result, {HEADINGS[2]: 'Other'}))

    def test_blank_and_duplicate(self):
        old = "## Today's Top 3\n- [ ] \n- [ ] \n- [ ] \n"
        result = fill_sections(old, {HEADINGS[0]: '- [ ] A\n- [ ] B\n- [ ] C'})
        self.assertEqual(result.count('- [ ]'), 3)
        duplicate = '## Deep Work\n\n## Deep Work\n'
        self.assertEqual(duplicate, fill_sections(duplicate, {HEADINGS[2]: 'Focus'}))

    def test_fence(self):
        old = '## Deep Work\n```md\n## Reading\n```\n'
        self.assertTrue(fill_sections(old, {HEADINGS[2]: 'Focus'}).startswith(old))

    def test_backup_and_conflict(self):
        with tempfile.TemporaryDirectory() as root:
            p = Path(root) / 'note.md'
            backups = Path(root) / 'backup'
            save_note(p, None, 'original\r\n', backups)
            save_note(p, 'original\r\n', 'new\n', backups)
            self.assertEqual(next(backups.iterdir()).read_bytes(), b'original\r\n')
            with self.assertRaises(RuntimeError):
                save_note(p, 'original\r\n', 'bad', backups)
            with self.assertRaises(FileExistsError):
                save_note(p, None, 'bad', backups)
            self.assertEqual(p.read_text(), 'new\n')

    def test_response_validation(self):
        with self.assertRaises(ValueError):
            validate('{"top3":["one"],"review":[],"deep_work":"x"}', 'planner')
        with self.assertRaises(ValueError):
            validate('{"top3":["one","two","three"],"review":[],"deep_work":"x\\n## bad"}', 'planner')

    def test_heading_without_final_newline(self):
        result = fill_sections('## Deep Work', {HEADINGS[2]: 'Focus'})
        self.assertEqual(result, '## Deep Work\nFocus\n\n')

    def test_template(self):
        self.assertEqual(template('2026-10-19').count('## '), 9)

if __name__ == '__main__':
    unittest.main()
