import json
import unittest
from unittest.mock import Mock
import llm_probe
import harvest_cf_public


class ProbeContracts(unittest.TestCase):
    def test_unknown_and_ambiguous_never_leave_machine(self):
        for key in ("unknown-secret", "sk-ambiguous-secret"):
            get = Mock()
            self.assertEqual(llm_probe.probe_key(key, get=get)["state"], "provider_required")
            get.assert_not_called()

    def test_public_catalog_is_not_authentication_and_does_not_receive_key(self):
        get = Mock(return_value=(200, {"data": [{"id": "test-model"}]}))
        result = llm_probe.probe_key("sk-or-v1-test-secret", get=get)
        self.assertEqual(result["state"], "public_catalog")
        self.assertFalse(result["valid"])
        self.assertEqual(result["models"], ["test-model"])
        self.assertEqual(get.call_count, 1)
        self.assertNotIn("Authorization", get.call_args.args[1])

    def test_authentication_requires_negative_control(self):
        get = Mock(side_effect=[(401, None), (200, {"data": [{"id": "test"}]})])
        result = llm_probe.probe_key("gsk_test-secret", get=get)
        self.assertTrue(result["auth_verified"])
        self.assertFalse(result["quota_verified"])
        self.assertFalse(result["inference_verified"])
        self.assertEqual(get.call_count, 2)
        self.assertEqual(get.call_args_list[0].args[0], get.call_args_list[1].args[0])

    def test_auth_rejection_never_broadcasts(self):
        get = Mock(side_effect=[(401, None), (403, None)])
        result = llm_probe.probe_key("sk-ambiguous", "deepseek", get=get)
        self.assertEqual(result["state"], "auth_rejected")
        self.assertEqual(get.call_count, 2)
        self.assertTrue(all(call.args[0].startswith("https://api.deepseek.com/")
                            for call in get.call_args_list))

    def test_quota_has_no_retry_or_rotation(self):
        get = Mock(side_effect=[(401, None), (429, None)])
        self.assertEqual(llm_probe.probe_key("gsk_test", get=get)["state"], "quota_limited")
        self.assertEqual(get.call_count, 2)

    def test_html_or_empty_contract_is_not_valid(self):
        for data in ("html", {}, [], {"data": "not-a-list"}):
            get = Mock(side_effect=[(401, None), (200, data)])
            self.assertFalse(llm_probe.probe_key("gsk_test", get=get)["valid"])

    def test_legacy_pool_shape_and_output_redaction(self):
        get = Mock(return_value=(200, {"data": [{"id": "model"}]}))
        receipt = llm_probe.probe_entries(
            [{"valor": "gsk_super-secret", "clave": "sensitive-alias"}], get=get)
        serialized = json.dumps(receipt)
        self.assertNotIn("super-secret", serialized)
        self.assertNotIn("sensitive-alias", serialized)
        self.assertNotIn("key_prefix", serialized)

    def test_exception_redaction(self):
        get = Mock(side_effect=RuntimeError("sensitive-secret"))
        result = llm_probe.probe_key("gsk_secret", get=get)
        self.assertNotIn("sensitive", json.dumps(result))
        self.assertEqual(result["error_class"], "RuntimeError")

    def test_batch_is_bounded(self):
        with self.assertRaises(ValueError):
            llm_probe.probe_entries(["x"] * 101)

    def test_invalid_provider_type_is_local_rejection(self):
        get = Mock()
        result = llm_probe.probe_key("gsk_test", {"invalid": "object"}, get=get)
        self.assertEqual(result["state"], "provider_required")
        get.assert_not_called()

    def test_echoed_key_in_model_name_is_not_retained(self):
        get = Mock(return_value=(200, {"data": [{"id": "model-gsk_secret"}]}))
        result = llm_probe.probe_key("gsk_secret", get=get)
        self.assertNotIn("gsk_secret", json.dumps(result))


class HarvestContracts(unittest.TestCase):
    def test_inventory_never_supplies_arbitrary_hosts(self):
        inventory = {"jaimepvicente_account": {"workers": [
            "safe-node", "safe-node", "../escape", "https://bad", "other"]}}
        self.assertEqual(harvest_cf_public.targets(inventory, 1),
                         ["https://safe-node.jaimepvicente.workers.dev/health"])

    def test_http_200_alone_is_not_health(self):
        for data in ({}, {"ok": "true"}, {"ok": 1}, [], None):
            self.assertFalse(harvest_cf_public.summarize(200, data)["health_verified"])

    def test_body_and_credentials_are_not_retained(self):
        result = harvest_cf_public.summarize(200, {
            "ok": True, "version": "V270", "api_key": "secret", "response": "private"})
        self.assertTrue(result["health_verified"])
        self.assertFalse(result["inference_verified"])
        self.assertNotIn("secret", json.dumps(result))
        self.assertNotIn("private", json.dumps(result))

    def test_redirects_are_not_followed(self):
        for cls in (harvest_cf_public.NoRedirect, llm_probe.NoRedirect):
            self.assertIsNone(cls().redirect_request(None, None, 302, "", {}, "https://other"))


if __name__ == "__main__":
    unittest.main()
