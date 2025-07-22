import requests

def search_europe_pmc(drug, condition, max_results=10):
    """
    Query Europe PMC for studies mentioning both the drug and the condition.
    """
    query = f"{drug} AND {condition}"
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": query,
        "format": "json",
        "resultType": "core",
        "pageSize": max_results,
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    docs = resp.json().get("resultList", {}).get("result", [])
    results = []
    for doc in docs:
        results.append({
            "title": doc.get("title"),
            "abstract": doc.get("abstractText"),
            "pmid": doc.get("pmid"),
            "journal": doc.get("journalTitle"),
            "pub_year": doc.get("pubYear"),
            "doi": doc.get("doi"),
            "source": "Europe PMC"
        })
    return results
