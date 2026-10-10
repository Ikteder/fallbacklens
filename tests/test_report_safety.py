import unittest
import xml.etree.ElementTree as ET

from fallbacklens.audit import audit_policy
from fallbacklens.loaders import policy_from_data, profile_from_data
from fallbacklens.report import render_html, render_svg


class ReportSafetyTests(unittest.TestCase):
    def test_operator_labels_cannot_break_html_or_svg_markup(self):
        label = (
            '</script><script>synthetic-marker</script><img src=x onerror="marker">&'
        )
        policy = policy_from_data(
            {
                "model_list": [{"model_name": label}],
                "router_settings": {"num_retries": 0},
            }
        )
        profile = profile_from_data(
            {
                "schema_version": 1,
                "as_of": label,
                "sources": [label],
                "models": {
                    label: {
                        "capabilities": [],
                        "context_window_tokens": 1,
                        "input_usd_per_million": 0,
                        "output_usd_per_million": 0,
                        "latency_p95_ms": 1,
                        "zero_data_retention": True,
                    }
                },
                "contracts": [
                    {
                        "name": label,
                        "entrypoint": label,
                        "required_capabilities": [],
                        "required_context_tokens": 0,
                        "require_zero_data_retention": False,
                        "expected_input_tokens": 0,
                        "expected_output_tokens": 0,
                        "max_attempts": 1,
                        "max_cost_usd": 0,
                        "max_latency_ms": 1,
                    }
                ],
            }
        )
        report = audit_policy(policy, profile)
        document = render_html(report)
        self.assertNotIn("<script>synthetic-marker", document)
        self.assertNotIn("<img src=x", document)
        self.assertIn("&lt;script&gt;synthetic-marker", document)
        self.assertIn("\\u003c/script\\u003e", document)
        svg = ET.fromstring(render_svg(report))
        self.assertTrue(
            all(
                element.tag.rsplit("}", 1)[-1] not in {"script", "img"}
                for element in svg.iter()
            )
        )
        self.assertIn(label, [element.text for element in svg.iter()])
