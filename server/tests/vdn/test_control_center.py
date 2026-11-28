import unittest

from vdn.control_center import parse_command_line


class CustomCommandParsingTests(unittest.TestCase):
    def test_quoted_arguments_are_preserved(self):
        self.assertEqual(parse_command_line('editor --title "A document name"'),
                         ["editor", "--title", "A document name"])

    def test_empty_command_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Enter an executable"):
            parse_command_line("   ")

    def test_unclosed_quotes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "quoting"):
            parse_command_line('editor "unfinished')


if __name__ == "__main__":
    unittest.main()
