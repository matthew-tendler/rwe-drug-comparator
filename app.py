import streamlit as st
from data import search_europe_pmc
from nlp import extract_comparators_from_abstract
import pandas as pd
import re
import requests
from rapidfuzz import process, fuzz

# Known drugs, conditions, and brand/generic mapping as before
KNOWN_DRUGS = [
    "adalimumab", "infliximab", "etanercept", "abatacept", "ustekinumab", "tofacitinib", "vedolizumab", "golimumab", "certolizumab", "azathioprine", "methotrexate", "cyclosporine", "prednisone", "hydroxychloroquine", "rituximab", "belimumab", "secukinumab", "apremilast"
]
KNOWN_CONDITIONS = [
    "ulcerative colitis", "crohn's disease", "rheumatoid arthritis", "psoriasis", "lupus", "asthma", "eczema", "multiple sclerosis", "diabetes", "hypertension", "psoriatic arthritis", "ankylosing spondylitis", "juvenile idiopathic arthritis"
]
BRAND_TO_GENERIC = {
    "advil": "ibuprofen", "motrin": "ibuprofen", "tylenol": "acetaminophen", "panadol": "acetaminophen",
    "humira": "adalimumab", "remicade": "infliximab", "enbrel": "etanercept",
    "victoza": "liraglutide", "trulicity": "dulaglutide", "ozempic": "semaglutide",
    "lipitor": "atorvastatin", "crestor": "rosuvastatin", "zocor": "simvastatin",
    # ...add more as needed
}

def fuzzy_correct(user_input, known_list, threshold=85):
    if not user_input:
        return user_input, None
    match, score, _ = process.extractOne(user_input, known_list, scorer=fuzz.WRatio)
    if score >= threshold:
        return match, None
    elif score >= 70:
        return None, match
    else:
        return user_input, None

def fuzzy_brand_to_generic(user_input, brand_dict, threshold=85):
    if not user_input:
        return None, None, None
    brands = list(brand_dict.keys())
    match, score, _ = process.extractOne(user_input.lower(), brands, scorer=fuzz.WRatio)
    if score >= threshold:
        return match, brand_dict[match], score
    elif score >= 70:
        return match, None, score
    else:
        return None, None, None

def extract_sample_size(abstract):
    if not abstract:
        return None
    match = re.search(r"n\s*=\s*(\d+)", abstract, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d{2,5})\s+(patients|subjects|volunteers|participants)", abstract, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

def search_clinicaltrials_gov(drugs, condition, max_results=20):
    query = " AND ".join([f"{drug}" for drug in drugs]) + f" AND {condition}"
    url = "https://clinicaltrials.gov/api/query/full_studies"
    params = {
        "expr": query,
        "min_rnk": 1,
        "max_rnk": max_results,
        "fmt": "json"
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    studies = resp.json().get("FullStudiesResponse", {}).get("FullStudies", [])
    results = []
    for s in studies:
        study = s.get("Study", {})
        proto = study.get("ProtocolSection", {})
        title = proto.get("IdentificationModule", {}).get("OfficialTitle", "") or proto.get("IdentificationModule", {}).get("BriefTitle", "")
        nct_id = proto.get("IdentificationModule", {}).get("NCTId", "")
        year = proto.get("StatusModule", {}).get("StartDateStruct", {}).get("StartDate", "")[-4:]
        phase = proto.get("DesignModule", {}).get("PhaseList", {}).get("Phase", [""])[0]
        enrollment = proto.get("DesignModule", {}).get("EnrollmentInfo", {}).get("EnrollmentCount", "")
        status = proto.get("StatusModule", {}).get("OverallStatus", "")
        interventions = [i.get("InterventionName", "") for i in proto.get("ArmsInterventionsModule", {}).get("InterventionList", {}).get("Intervention", [])]
        arms = []
        arm_data = proto.get("ArmsInterventionsModule", {}).get("ArmGroupList", {}).get("ArmGroup", [])
        for arm in arm_data:
            label = arm.get("ArmGroupLabel", "")
            a_type = arm.get("ArmGroupType", "")
            desc = arm.get("ArmGroupDescription", "")
            arms.append(f"{label} ({a_type}): {desc}")
        outcomes = proto.get("OutcomesModule", {}).get("PrimaryOutcomeList", {}).get("PrimaryOutcome", [])
        primary_outcome = "; ".join([o.get("PrimaryOutcomeMeasure", "") for o in outcomes])
        results.append({
            "Study Title": title,
            "Year": year,
            "Phase": phase,
            "Enrollment": enrollment,
            "Status": status,
            "Drugs Compared": ", ".join(interventions),
            "Arms": " | ".join(arms),
            "Primary Outcome": primary_outcome,
            "Source": "ClinicalTrials.gov",
            "Link": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else ""
        })
    return results

st.set_page_config(page_title="RWE Drug Comparator", layout="wide")
st.title("RWE Drug Comparator")

def set_example(example):
    st.session_state['input_drugs'] = example['drugs']
    st.session_state['condition'] = example['condition']
    st.session_state['run_search'] = True

st.markdown("""
### How to use this app
1. Enter two or more drugs (brand or generic, separated by commas or semicolons) to compare them head-to-head.
2. Enter a condition (e.g., ulcerative colitis).
3. Select a data source (Europe PMC, ClinicalTrials.gov, or Both).
4. Click 'Search Clinical Trials' to see results.

**Or try one of these examples:**
""")

examples = [
    {"label": "Adalimumab vs Infliximab for Ulcerative Colitis", "drugs": "adalimumab, infliximab", "condition": "ulcerative colitis"},
    {"label": "Humira, Remicade, Enbrel for Rheumatoid Arthritis", "drugs": "Humira, Remicade, Enbrel", "condition": "rheumatoid arthritis"},
    {"label": "Ozempic, Trulicity for Diabetes", "drugs": "Ozempic, Trulicity", "condition": "diabetes"},
    {"label": "Lipitor, Crestor, Zocor for Hypertension", "drugs": "Lipitor, Crestor, Zocor", "condition": "hypertension"},
]
cols = st.columns(len(examples))
for i, ex in enumerate(examples):
    if cols[i].button(ex['label']):
        set_example(ex)

input_drugs = st.text_input("Drugs (comma- or semicolon-separated)", placeholder="e.g. adalimumab, infliximab, etanercept", key='input_drugs')
condition = st.text_input("Condition", placeholder="e.g. ulcerative colitis", key='condition')

data_source = st.selectbox("Data Source", ["Europe PMC", "ClinicalTrials.gov", "Both"], index=0)

run_search = st.session_state.get('run_search', False)
if run_search:
    st.session_state['run_search'] = False
    search_now = True
else:
    search_now = st.button("Search Clinical Trials")

raw_drugs = [d.strip() for d in re.split(r",|;", input_drugs) if d.strip()]

final_drugs = []
display_drugs = []
for d in raw_drugs:
    brand_match, generic_name, brand_score = fuzzy_brand_to_generic(d, BRAND_TO_GENERIC)
    if generic_name:
        display_drugs.append(f"{d} (generic: {generic_name})")
        final_drugs.append(generic_name)
    elif brand_match and not generic_name:
        st.warning(f"Did you mean '{brand_match}' (brand)?")
        st.stop()
    else:
        corrected, suggestion = fuzzy_correct(d, KNOWN_DRUGS)
        if suggestion:
            st.warning(f"Did you mean '{suggestion}'?")
            st.stop()
        final_drugs.append(corrected)
        display_drugs.append(corrected)

corrected_condition, suggestion_condition = fuzzy_correct(condition, KNOWN_CONDITIONS)
if suggestion_condition:
    st.warning(f"Did you mean '{suggestion_condition}' for Condition?")
    st.stop()

if search_now:
    if not final_drugs or not corrected_condition:
        st.warning("Please enter at least two drugs and a condition.")
    else:
        all_results = []
        with st.spinner("Querying selected data source(s)..."):
            if data_source in ["Europe PMC", "Both"]:
                results = search_europe_pmc(final_drugs[0], corrected_condition)
                for r in results:
                    row = {
                        "Study Title": r['title'],
                        "Year": r.get('pub_year', ''),
                        "Phase": "",
                        "Enrollment": extract_sample_size(r.get('abstract', '')),
                        "Status": "",
                        "Drugs Compared": ", ".join([d.title() for d in final_drugs if d and d.lower() in (r.get('abstract', '') or '').lower()]),
                        "Arms": "",
                        "Primary Outcome": "",
                        "Source": "Europe PMC",
                        "Link": f"https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/" if r.get('pmid') else ""
                    }
                    all_results.append((row, r.get('abstract', '')))
            if data_source in ["ClinicalTrials.gov", "Both"]:
                ctgov_results = search_clinicaltrials_gov(final_drugs, corrected_condition)
                for r in ctgov_results:
                    all_results.append((r, None))  # No abstract for ClinicalTrials.gov in this view

        if not all_results:
            st.error("No clinical trials found for that query.")
        else:
            st.success(f"Found {len(all_results)} results for: {', '.join(display_drugs)}")
            table_rows = [row for row, _ in all_results]
            df = pd.DataFrame(table_rows)
            all_columns = list(df.columns)
            default_columns = [col for col in all_columns if col not in ("Arms", "Primary Outcome")]
            selected_columns = st.multiselect(
                "Select columns to display:", all_columns, default=default_columns
            )
            st.dataframe(df[selected_columns])
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download results as CSV",
                data=csv,
                file_name="drug_comparator_results.csv",
                mime="text/csv"
            )
            # Abstract/Arms expanders
            for i, (row, abstract) in enumerate(all_results):
                with st.expander(f"Show details for: {row['Study Title'][:60]}..."):
                    if row["Source"] == "Europe PMC":
                        st.markdown(f"**Abstract:**<br>{abstract or 'No abstract available.'}", unsafe_allow_html=True)
                    elif row["Source"] == "ClinicalTrials.gov":
                        st.markdown(f"**Arms:**<br>{row.get('Arms', 'No arm data.')}", unsafe_allow_html=True)
                        st.markdown(f"**Primary Outcome:**<br>{row.get('Primary Outcome', 'No outcome data.')}", unsafe_allow_html=True)
                    st.markdown(f"[Link to Study]({row['Link']})" if row.get('Link') else "No link available.")

with st.sidebar:
    with st.expander("ℹ️ About this app", expanded=False):
        st.markdown("""
### RWE Drug Comparator

**Technologies & Frameworks:**
- Python 3.12
- Streamlit (interactive web app)
- Pandas (data wrangling)
- RapidFuzz (fuzzy matching, typo correction)
- Europe PMC & ClinicalTrials.gov integration

**NLP & Extraction:**
- Brand-to-generic drug mapping (top US drugs)
- Fuzzy name recognition (typo-tolerant)
- Regex-based sample size extraction
- Comparator and outcome detection
- Biomedical NER: coming soon!

**Data Sources:**
- Europe PMC (clinical trial abstracts & metadata)
- ClinicalTrials.gov (structured arm/intervention data)
- PubMed (article links)

**Features:**
- Multi-drug, side-by-side comparator table
- Brand/generic name recognition & correction
- Sample size, year, phase, outcome, and arms extraction
- Downloadable CSV results
- PubMed/CT.gov links, abstract/arms expanders
- Example queries

**Use Cases:**
- Medical Affairs: Literature review, value dossiers, launch readiness
- RWE/Epidemiology: Comparator mapping, sample size, outcomes, recency
- Regulatory: Track evidence for new drugs vs. standards of care

---
*Built for rapid, transparent, and actionable evidence review.*
        """)
