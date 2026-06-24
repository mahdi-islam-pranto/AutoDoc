import json
from typing import List, Dict

# load the doctors document from the local system
JSON_PATH = "documents/doctors.json"

def load_doctor_documents(json_path: str) -> List[Dict]:
    """
    Load doctors from JSON file and convert them into searchable documents.
    
    Returns:
        List of dicts with:
        - doc_id
        - content (for embedding / RAG)
        - degree
        - designation
        - experience
        - visit_fee
        - follow_up_fee
        - email
        - branch
        - specialization
        - description
        - metadata
    """

    # load the doctors document from the local system
    with open(json_path, "r", encoding="utf-8") as f:
        doctors = json.load(f)

    # create a list to store the documents
    documents = []

    for doctor in doctors:
        # Basic validation
        # if not all(k in doctor for k in ("doctor_id", "name", "department")):
        #     continue

        # create the content for the document
        content = (
            f"{doctor['name']} is a doctor specializing in {doctor['specialization_name']} with {doctor['experience_years']} years of experience. "
            f"{doctor['name']} hold a {doctor['degree']} degrees and currently work as a {doctor['designation']}. "
            f"Doctor id: {doctor['id']}. "
            f"Description: {doctor['description']} "
            f"Opening Hours: {doctor['opening_hours']}. "
            f"Contact: email: {doctor['email']}, Branch: {doctor['branch_name']}. "
            f"Fees: Visiting fee:{doctor['first_visit_fee']}, Follow-up fee:{doctor['follow_up_fee']}."
        )

        doc = {
            "doc_id": doctor["id"],
            "content": content,
            "metadata": {
                "name": doctor["name"],
                "specialization": doctor["specialization_name"],
                "doctor_no": doctor["doctor_no"],
                "degree": doctor["degree"],
            }
        }

        documents.append(doc)

    return documents

# test the function
if __name__ == "__main__":
    documents = load_doctor_documents(JSON_PATH)
    print(documents)
