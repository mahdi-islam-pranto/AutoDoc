from langchain_core.documents import Document

def convert_to_langchain_documents(doctor_dicts):
    lc_documents = []
    for doctor in doctor_dicts:
        content = (
            f"Doctor id: {doctor['doc_id']}\n"
            f"{doctor['content']}"
        )


# sample = {'doc_id': '1', 'content': 'Associate Prof. Dr. Kamrun Sattar Dahlia is a doctor specializing in 1 with 12 years of experience. Associate Prof. Dr. Kamrun Sattar Dahlia hold a MBBS, MCPS, DGO, FCPS (Gynae) degrees and currently work as a Consultant Doctor id: 1. Description: None Contact: email: Associate.prof.dr.kamrun.sattar.dalia@tbhml.com, Branch: 1. Fees: Visiting fee:700.00, Follow-up fee:400.00.', 'metadata': {'name': 'Associate Prof. Dr. Kamrun Sattar Dahlia', 'specialization': '1', 'opening_hours': 'Monday to Saturday, 10am to 4pm'}}

        doc = Document(
            page_content=content,
            metadata={
                "id": doctor["doc_id"],
                "name": doctor["metadata"]["name"],
                "specialization": doctor["metadata"]["specialization"],
                "opening_hours": doctor["metadata"].get("opening_hours", "")
            }
        )

        lc_documents.append(doc)

    return lc_documents