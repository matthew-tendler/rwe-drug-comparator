import streamlit as st
from data import search_europe_pmc
from nlp import extract_comparator_info

st.set_page_config(page_title="RWE Drug Comparator", layout="wide")
st.title("RWE Drug Comparator")

st.markdown("""
This app lets you search real clinical trial abstracts and automatically extract possible comparator info using modern NLP.  
Enter a drug and a condition to get started.
""")

# --- Input fields ---
drug = st.text_input("Drug", placeholder="e.g. adalimumab")
condition = st.text_input("Condition", placeholder="e.g. ulcerative colitis")

if st.button("Search Clinical Trials"):
    if not drug or not condition:
        st.warning("Please enter both a drug and a condition.")
    else:
        with st.spinner("Querying Europe PMC..."):
            results = search_europe_pmc(drug, condition)
        if not results:
            st.error("No clinical trials found for that query.")
        else:
            st.success(f"Found {len(results)} results.")
            for idx, r in enumerate(results, 1):
                st.markdown(f"### {idx}. {r['title']}")
                st.caption(f"{r['journal']} ({r['pub_year']})")
                if r.get('abstract'):
                    st.markdown("**Abstract:**")
                    st.markdown(r['abstract'], unsafe_allow_html=True)

                    # Extract comparator/intervention info (NLP)
                    with st.expander("Show extracted entities (beta)", expanded=False):
                        entities = extract_comparator_info(r['abstract'])
                        if entities:
                            st.json(entities)
                        else:
                            st.write("No entities found.")

                # PubMed link
                if r.get('pmid'):
                    pmid_url = f"https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/"
                    st.markdown(f"[PubMed Link]({pmid_url})")

                # DOI link if present
                if r.get('doi'):
                    doi_url = f"https://doi.org/{r['doi']}"
                    st.markdown(f"[DOI Link]({doi_url})")
                st.markdown("---")

# Add non-intrusive info section in the sidebar
with st.sidebar:
    with st.expander("ℹ️ About this app", expanded=False):
        st.markdown("""
**Technologies & Frameworks**
- Python
- Streamlit

**Data Sources**
- Europe PMC (clinical trial abstracts)
- PubMed (article links)
- DOI (publisher article links)

**NLP**
- Custom extraction via the app's NLP module
        """)
