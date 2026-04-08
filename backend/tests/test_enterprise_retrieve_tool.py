from app.ai_runtime.tools.enterprise_retrieve import EnterpriseRetrieveTool


def test_enterprise_retrieve_tool_returns_private_sample_hits() -> None:
    tool = EnterpriseRetrieveTool()

    result = tool.invoke(
        arguments={
            "question": "空压站夜间空载运行有什么问题？",
            "top_k": 3,
            "payload": {
                "attached_private_sample_ids": ["enterprise_doc_002", "energy_bill_sample_001"],
                "top_k": 3,
            },
        },
        context={"mode": "ask"},
        trace_id="trace-test-enterprise-tool",
    )

    assert result.name == "enterprise_retrieve"
    assert result.status == "success"
    assert result.output["hits"]
    assert result.output["allowed_doc_ids"] == ["energy_bill_sample_001", "enterprise_doc_002"]
    assert all(hit["source_type"] == "private_sample" for hit in result.output["hits"])
