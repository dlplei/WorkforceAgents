import sys
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from agent import knowledge

def test_loader():
    print(f"Loaded {len(knowledge.policy_documents)} policies.")
    assert len(knowledge.policy_documents) == 7, f"Expected 7 policies, got {len(knowledge.policy_documents)}"
    for p in knowledge.policy_documents:
        print(f"✓ {p.id}: {p.title} [{p.category}] - applicable to: {p.applicable_to}")
        assert p.id.startswith("POL-")
        assert len(p.title) > 0
        assert len(p.content) > 10

    # Test retrieval
    annual_leave_results = knowledge.retrieve_knowledge("年假多少天")
    print("\nRetrieval test for '年假多少天':")
    for r in annual_leave_results:
        print(f"  Result doc: {r.doc_id} - {r.title} (score: {r.score})")
    assert any(r.doc_id == "POL-001" for r in annual_leave_results)

    # Test get_policy_by_id
    doc1 = knowledge.get_policy_by_id("POL-001")
    assert doc1 is not None and doc1.title == "员工年假管理办法"

    # Test get_policy_categories
    cats = knowledge.get_policy_categories()
    print(f"\nCategories: {cats}")
    assert "休假" in cats
    assert "差旅" in cats
    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    test_loader()
