import streamlit as st
from data import search_europe_pmc
from nlp import extract_comparators_from_abstract

st.set_page_config(page_title="RWE Drug Comparator", layout="wide")
st.title("RWE Drug Comparator")

st.markdown("""
Enter a drug and condition below.  
Optionally, enter a comparator drug for head-to-head searches.
""")

# --- Input fields ---
drug_a = st.text_input("Drug A", placeholder="e.g. adalimumab")
drug_b = st.text_input("Comparator Drug (optional)", placeholder="e.g. infliximab")
condition = st.text_input("Condition", placeholder="e.g. ulcerative colitis")

if st.button("Search Clinical Trials"):
    if not drug_a or not condition:
        st.warning("Please enter at least Drug A and a condition.")
    else:
        with st.spinner("Querying Europe PMC..."):
            results = search_europe_pmc(drug_a, condition)
        if not results:
            st.error("No clinical trials found for that query.")
        else:
            # Build a list of studies with comparators
            table_rows = []
            for r in results:
                comparators, outcome_snippet = extract_comparators_from_abstract(
                    r.get('abstract', ''), drug_a, drug_b if drug_b else None
                )
                if drug_b:
                    # Head-to-head: require both drugs to be present
                    if comparators:
                        table_rows.append({
                            "Study Title": r['title'],
                            "Drug A": drug_a.title(),
                            "Comparator": drug_b.title(),
                            "Outcome Snippet": outcome_snippet or "(Not found)",
                            "PubMed Link": f"https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/" if r.get('pmid') else ""
                        })
                else:
                    # Just show whatever comparators found for Drug A
                    if comparators:
                        table_rows.append({
                            "Study Title": r['title'],
                            "Drug A": drug_a.title(),
                            "Comparator(s)": ", ".join([c.title() for c in comparators]),
                            "Outcome Snippet": outcome_snippet or "(Not found)",
                            "PubMed Link": f"https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/" if r.get('pmid') else ""
                        })
            if table_rows:
                st.success(f"Found {len(table_rows)} studies with comparators.")
                st.dataframe(table_rows)
            else:
                st.warning("No studies found with explicit comparators in the abstract for your query.")
