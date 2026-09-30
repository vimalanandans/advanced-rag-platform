from pathlib import Path

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from rag_workbench.graph import pipeline_from_yaml
from rag_workbench.ingestion import ingest_path
from rag_workbench.runtime import WorkbenchRuntime


def _write_text_pdf(path: Path) -> None:
    """Build a tiny deterministic PDF fixture without committing opaque binary data."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
    })
    contents = DecodedStreamObject()
    contents.set_data(b"BT /F1 14 Tf 72 720 Td (A RAG system must abstain when approved evidence is insufficient.) Tj ET")
    page[NameObject("/Contents")] = contents
    with path.open("wb") as output:
        writer.write(output)


def test_pdf_evidence_is_located_and_can_ground_a_cited_answer(tmp_path: Path):
    root = Path(__file__).parent.parent
    source = tmp_path / "abstention-policy.pdf"
    _write_text_pdf(source)
    evidence = ingest_path(source)

    assert len(evidence) == 1
    assert evidence[0].locator == "page:1"
    assert "must abstain" in evidence[0].content

    runtime = WorkbenchRuntime()
    runtime.set_evidence(evidence)
    plan = runtime.compile(pipeline_from_yaml((root / "configs/pipelines/baseline.yaml").read_text()))
    result = runtime.run(plan, "When must a RAG system abstain?")

    assert not result.abstained
    assert [citation.id for citation in result.citations] == [evidence[0].id]
