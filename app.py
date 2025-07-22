import streamlit as st
from data import search_europe_pmc
from nlp import extract_comparators_from_abstract
import pandas as pd

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
                df = pd.DataFrame(table_rows)
                # Column selector
                all_columns = list(df.columns)
                default_columns = [col for col in all_columns if col != "Outcome Snippet"]
                selected_columns = st.multiselect(
                    "Select columns to display:", all_columns, default=default_columns
                )
                st.dataframe(df[selected_columns])
                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download results as CSV",
                    data=csv,
                    file_name="drug_comparator_results.csv",
                    mime="text/csv"
                )
                # Abstract expanders
                for i, row in df.iterrows():
                    with st.expander(f"Show abstract for: {row['Study Title']}"):
                        # You may need to fetch the abstract from the original results list
                        st.markdown(results[i].get('abstract', 'No abstract available.'), unsafe_allow_html=True)
            else:
                st.warning("No studies found with explicit comparators in the abstract for your query.")
