import unittest

from labos.core.provenance import link_job_to_dataset, register_import_result
from labos.core.workflows import run_import_workflow
from labos.modules.import_wizard.stub import MODULE_KEY, build_preview, infer_schema, run_import_stub


class TestImportProvenance(unittest.TestCase):
    def setUp(self) -> None:
        self.records = [
            {"sample": "A", "value": 1.2, "flag": True},
            {"sample": "B", "value": 3.4, "flag": False},
        ]

    def test_schema_and_preview_helpers(self):
        schema = infer_schema(self.records)
        preview = build_preview(self.records, max_rows=1)

        self.assertEqual(schema["row_count"], 2)
        self.assertEqual(preview["row_count"], 1)
        self.assertEqual(preview["rows"][0]["sample"], "A")

    def test_import_stub_and_provenance_linkage(self):
        params = {"data": self.records, "actor": "tester", "job_id": "JOB-1", "experiment_id": "EXP-1"}
        result = run_import_stub(params)

        self.assertEqual(result["module_key"], MODULE_KEY)
        dataset = result["dataset"]
        self.assertIn("schema", dataset["metadata"])
        self.assertIn("preview", dataset["metadata"])

        audit = result["audit"]
        self.assertEqual(audit["action"], "import")
        self.assertEqual(audit["target"], dataset["id"])

        workflow_output = run_import_workflow(params)
        self.assertEqual(workflow_output["links"]["job_id"], "JOB-1")
        self.assertEqual(workflow_output["links"]["experiment_id"], "EXP-1")
        audit_events = workflow_output["audit_events"]
        self.assertTrue(any(evt.get("action") == "register-dataset" for evt in audit_events))
        self.assertTrue(any(evt.get("details", {}).get("dataset_id") == dataset["id"] for evt in audit_events))

    def test_link_job_to_dataset_direction_validation(self):
        with self.assertRaises(ValueError):
            link_job_to_dataset("JOB-X", "DS-Y", direction="sideways")


if __name__ == "__main__":
    unittest.main()
