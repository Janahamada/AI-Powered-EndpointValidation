"""API integration tests against the seeded database."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dashboard_summary_shape(client, auth_headers):
    r = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert r.status_code == 200
    d = r.json()
    assert d["total_endpoints"] > 0
    assert 0 <= d["overall_compliance_score"] <= 100
    assert set(d["findings_by_severity"]) == {"critical", "high", "medium", "low"}
    assert len(d["per_control"]) == 4
    assert len(d["trend"]) == 5
    assert d["trend"][-1]["score"] == d["overall_compliance_score"]


def test_endpoints_list_pagination_and_sort(client, auth_headers):
    r = client.get(
        "/api/v1/endpoints",
        headers=auth_headers,
        params={"page_size": 5, "sort": "score", "order": "asc"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["page_size"] == 5
    assert len(body["items"]) == 5
    scores = [i["compliance_score"] for i in body["items"]]
    assert scores == sorted(scores)
    # every row carries all four control statuses
    assert set(body["items"][0]["control_statuses"]) == {
        "antivirus", "edr", "firewall", "bitlocker"
    }


def test_endpoints_search_filter(client, auth_headers):
    r = client.get("/api/v1/endpoints", headers=auth_headers, params={"q": "CORP-SRV-001"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert all("CORP-SRV-001" in i["hostname"] for i in items)


def test_endpoint_detail_has_four_controls(client, auth_headers):
    host = client.get(
        "/api/v1/endpoints", headers=auth_headers, params={"page_size": 1}
    ).json()["items"][0]["hostname"]
    r = client.get(f"/api/v1/endpoints/{host}", headers=auth_headers)
    assert r.status_code == 200
    det = r.json()
    assert det["asset"]["hostname"] == host
    assert len(det["controls"]) == 4
    assert "evidence" in det


def test_endpoint_detail_404(client, auth_headers):
    r = client.get("/api/v1/endpoints/DOES-NOT-EXIST", headers=auth_headers)
    assert r.status_code == 404


def test_chat_compliance_offline_fallback(client, auth_headers):
    # Grab a real IP from an endpoint.
    host = client.get(
        "/api/v1/endpoints", headers=auth_headers, params={"page_size": 1}
    ).json()["items"][0]["hostname"]
    ip = client.get(f"/api/v1/endpoints/{host}", headers=auth_headers).json()["asset"]["ip_address"]
    r = client.post(
        "/api/v1/chat", headers=auth_headers, json={"message": f"check compliance for {ip}"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["use_case"] == "compliance_check"
    assert body["hostname"] == host
    # No crash regardless of whether Ollama is up.
    assert isinstance(body["ai_available"], bool)


def test_chat_empty_message_clarifies(client, auth_headers):
    r = client.post("/api/v1/chat", headers=auth_headers, json={"message": "  "})
    assert r.status_code == 200
    assert r.json()["status"] == "clarification_needed"


def test_chat_not_found_ip(client, auth_headers):
    r = client.post(
        "/api/v1/chat", headers=auth_headers, json={"message": "is 203.0.113.200 compliant"}
    )
    assert r.status_code == 200
    assert r.json()["status"] == "not_found"


def test_chat_fleet_metric_no_ip(client, auth_headers):
    r = client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={"message": "how many endpoints are not encrypted with bitlocker?"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["answer_type"] == "fleet_metric"
    assert len(body["sources"]) >= 1  # answer is attributed to a source


def test_chat_list_endpoints(client, auth_headers):
    r = client.post(
        "/api/v1/chat", headers=auth_headers, json={"message": "which endpoints are failing?"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["answer_type"] == "list"
    assert len(body["table"]) > 0


def test_chat_policy_lookup(client, auth_headers):
    r = client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={"message": "what does the blueprint require for firewall?"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["answer_type"] == "policy"
    assert any(s["kind"] == "blueprint" for s in body["sources"])


def test_system_collection_status(client, auth_headers):
    r = client.get("/api/v1/system/collection", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["blueprint_rules"] == 21
    assert len(body["sources"]) == 5  # asset + 4 controls


def test_blueprint_view(client, auth_headers):
    r = client.get("/api/v1/blueprint", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total_rules"] == 21
    assert len(body["controls"]) == 4
    assert len(body["policies"]) == 10  # AV-01..05 + EDR-01..05
    # firewall & bitlocker carry a golden image; a rule carries a CIS mapping
    fw = next(c for c in body["controls"] if c["control_type"] == "firewall")
    assert fw["golden_image"] is not None
    av = next(c for c in body["controls"] if c["control_type"] == "antivirus")
    assert any(rule["cis"] for rule in av["rules"])
    assert all(rule["policy_reference"] for rule in av["rules"])


def test_reports_generate(client, auth_headers):
    fleet = client.get("/api/v1/reports/fleet.pdf", headers=auth_headers)
    assert fleet.status_code == 200
    assert fleet.content[:5] == b"%PDF-"

    xlsx = client.get("/api/v1/reports/findings.xlsx", headers=auth_headers)
    assert xlsx.status_code == 200
    assert xlsx.content[:2] == b"PK"  # xlsx is a zip

    host = client.get(
        "/api/v1/endpoints", headers=auth_headers, params={"page_size": 1}
    ).json()["items"][0]["hostname"]
    epdf = client.get(f"/api/v1/reports/endpoint/{host}.pdf", headers=auth_headers)
    assert epdf.status_code == 200
    assert epdf.content[:5] == b"%PDF-"
