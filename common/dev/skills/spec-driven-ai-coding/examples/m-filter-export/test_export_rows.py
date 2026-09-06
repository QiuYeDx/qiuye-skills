from __future__ import annotations
import copy
import csv
import io
import unittest
from export_rows import export_rows


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.rows = [{"id":"A1","name":"甲记录","status":"done"},
                     {"id":"B2","name":"乙记录","status":"todo"},
                     {"id":"C3","name":"丙记录","status":"done"}]

    def parsed(self, output):
        return list(csv.DictReader(io.StringIO(output)))

    def test_done_selection_preserves_order(self):
        self.assertEqual([r["id"] for r in self.parsed(export_rows(self.rows, "done"))], ["A1", "C3"])

    def test_todo_selection(self):
        self.assertEqual([r["id"] for r in self.parsed(export_rows(self.rows, "todo"))], ["B2"])

    def test_empty_input_has_only_header(self):
        self.assertEqual(export_rows([], "done"), "id,name,status\r\n")

    def test_no_match_has_only_header(self):
        self.assertEqual(export_rows([self.rows[1]], "done"), "id,name,status\r\n")

    def test_rejects_bad_filter(self):
        for value in ("all", "", None, []):
            with self.subTest(value=value), self.assertRaises(ValueError):
                export_rows(self.rows, value)

    def test_rejects_invalid_rows_even_if_not_selected(self):
        cases = [{"id":"A1","status":"todo"}, {"id":"A1","name":"甲","status":"bad"},
                 {"id":"=cmd","name":"甲","status":"todo"}, {"id":"A1","name":4,"status":"todo"}, "bad"]
        for row in cases:
            with self.subTest(row=row), self.assertRaises(ValueError):
                export_rows([row], "done")

    def test_input_not_mutated(self):
        before = copy.deepcopy(self.rows)
        export_rows(self.rows, "done")
        self.assertEqual(self.rows, before)

    def test_csv_quoting_and_newlines(self):
        name = '甲,"乙"\n丙'
        result = self.parsed(export_rows([{"id":"A1","name":name,"status":"done"}], "done"))
        self.assertEqual(result[0]["name"], name)

    def test_formula_leading_text_is_prefixed(self):
        for name in ("=1+1", "+1+1", "-1+1", "@SUM(A1)", "  =1+1", "\ttext"):
            with self.subTest(name=name):
                rows = [{"id":"A1","name":name,"status":"done"}]
                self.assertEqual(self.parsed(export_rows(rows, "done"))[0]["name"], "'" + name)
                self.assertEqual(rows[0]["name"], name)

    def test_generator_input(self):
        self.assertEqual(len(self.parsed(export_rows((r for r in self.rows), "done"))), 2)


if __name__ == "__main__":
    unittest.main()
