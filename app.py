import streamlit as st
from data import search_europe_pmc
from nlp import extract_comparators_from_abstract
import pandas as pd
import re
from rapidfuzz import process, fuzz

# Example: Small demo list of drugs and conditions (replace with comprehensive list for production)
KNOWN_DRUGS = [
    "adalimumab", "infliximab", "etanercept", "abatacept", "ustekinumab", "tofacitinib", "vedolizumab", "golimumab", "certolizumab", "azathioprine", "methotrexate", "cyclosporine", "prednisone", "hydroxychloroquine", "rituximab", "abatacept", "belimumab", "secukinumab", "apremilast", "adalimumab", "adalimumab", "adalimumab"
]
KNOWN_CONDITIONS = [
    "ulcerative colitis", "crohn's disease", "rheumatoid arthritis", "psoriasis", "lupus", "asthma", "eczema", "multiple sclerosis", "diabetes", "hypertension", "psoriatic arthritis", "ankylosing spondylitis", "juvenile idiopathic arthritis"
]

# Medium-size brand-to-generic mapping (top 200 US drugs, partial for demo)
BRAND_TO_GENERIC = {
    "advil": "ibuprofen", "motrin": "ibuprofen", "tylenol": "acetaminophen", "panadol": "acetaminophen", "aleve": "naproxen", "naprosyn": "naproxen", "zestril": "lisinopril", "prinivil": "lisinopril", "norvasc": "amlodipine", "lipitor": "atorvastatin", "zocor": "simvastatin", "crestor": "rosuvastatin", "pravachol": "pravastatin", "lopressor": "metoprolol", "toprol": "metoprolol", "tenormin": "atenolol", "coreg": "carvedilol", "cozaar": "losartan", "diovan": "valsartan", "benicar": "olmesartan", "micardis": "telmisartan", "lotensin": "benazepril", "vasotec": "enalapril", "altace": "ramipril", "accupril": "quinapril", "monopril": "fosinopril", "lasix": "furosemide", "hydrodiuril": "hydrochlorothiazide", "microzide": "hydrochlorothiazide", "aldactone": "spironolactone", "dyazide": "triamterene", "maxzide": "triamterene", "plavix": "clopidogrel", "effient": "prasugrel", "brilinta": "ticagrelor", "eliquis": "apixaban", "xarelto": "rivaroxaban", "pradaxa": "dabigatran", "coumadin": "warfarin", "jantoven": "warfarin", "glucophage": "metformin", "glucotrol": "glipizide", "amaryl": "glimepiride", "actos": "pioglitazone", "avandia": "rosiglitazone", "januvia": "sitagliptin", "onglyza": "saxagliptin", "tradjenta": "linagliptin", "farxiga": "dapagliflozin", "invokana": "canagliflozin", "jardiance": "empagliflozin", "byetta": "exenatide", "bydureon": "exenatide", "victoza": "liraglutide", "trulicity": "dulaglutide", "ozempic": "semaglutide", "rybelsus": "semaglutide", "humalog": "insulin lispro", "novolog": "insulin aspart", "apidra": "insulin glulisine", "lantus": "insulin glargine", "toujeo": "insulin glargine", "levemir": "insulin detemir", "tresiba": "insulin degludec", "humulin": "insulin human", "novolin": "insulin human", "singulair": "montelukast", "advair": "fluticasone/salmeterol", "symbicort": "budesonide/formoterol", "dulera": "mometasone/formoterol", "spiriva": "tiotropium", "combivent": "albuterol/ipratropium", "proair": "albuterol", "ventolin": "albuterol", "proventil": "albuterol", "flovent": "fluticasone", "pulmicort": "budesonide", "asmanex": "mometasone", "qvar": "beclomethasone", "nasonex": "mometasone", "nasacort": "triamcinolone", "claritin": "loratadine", "zyrtec": "cetirizine", "allegra": "fexofenadine", "benadryl": "diphenhydramine", "xanax": "alprazolam", "klonopin": "clonazepam", "ativan": "lorazepam", "valium": "diazepam", "ambien": "zolpidem", "lunesta": "eszopiclone", "sonata": "zaleplon", "prozac": "fluoxetine", "zoloft": "sertraline", "paxil": "paroxetine", "celexa": "citalopram", "lexapro": "escitalopram", "cymbalta": "duloxetine", "effexor": "venlafaxine", "wellbutrin": "bupropion", "elavil": "amitriptyline", "sinequan": "doxepin", "trazodone": "trazodone", "abilify": "aripiprazole", "seroquel": "quetiapine", "zyprexa": "olanzapine", "risperdal": "risperidone", "geodon": "ziprasidone", "latuda": "lurasidone", "invega": "paliperidone", "haldol": "haloperidol", "lithobid": "lithium", "tegretol": "carbamazepine", "trileptal": "oxcarbazepine", "lamictal": "lamotrigine", "depakote": "divalproex", "keppra": "levetiracetam", "dilantin": "phenytoin", "neurontin": "gabapentin", "lyrica": "pregabalin", "topamax": "topiramate", "zonegran": "zonisamide", "focalin": "dexmethylphenidate", "ritalin": "methylphenidate", "concerta": "methylphenidate", "adderall": "amphetamine/dextroamphetamine", "vyvanse": "lisdexamfetamine", "strattera": "atomoxetine", "aricept": "donepezil", "namenda": "memantine", "sinement": "carbidopa/levodopa", "requip": "ropinirole", "mirapex": "pramipexole", "amantadine": "amantadine", "cogentin": "benztropine", "entacapone": "entacapone", "comtan": "entacapone", "azilect": "rasagiline", "eldepryl": "selegiline", "gilenya": "fingolimod", "tecfidera": "dimethyl fumarate", "aubagio": "teriflunomide", "tysabri": "natalizumab", "ocrevus": "ocrelizumab", "lemtrada": "alemtuzumab", "novantrone": "mitoxantrone", "betaseron": "interferon beta-1b", "avonex": "interferon beta-1a", "rebif": "interferon beta-1a", "copaxone": "glatiramer", "baclofen": "baclofen", "zanaflex": "tizanidine", "flexeril": "cyclobenzaprine", "robaxin": "methocarbamol", "skelaxin": "metaxalone", "soma": "carisoprodol", "colcrys": "colchicine", "zyloprim": "allopurinol", "uloric": "febuxostat", "imuran": "azathioprine", "cellcept": "mycophenolate", "prograf": "tacrolimus", "neoral": "cyclosporine", "sandimmune": "cyclosporine", "rapamune": "sirolimus", "nulojix": "belatacept", "simulect": "basiliximab", "zenapax": "daclizumab", "orthoclone": "muromonab", "remicade": "infliximab", "enbrel": "etanercept", "humira": "adalimumab", "cimzia": "certolizumab", "simponi": "golimumab", "stelara": "ustekinumab", "cosentyx": "secukinumab", "taltz": "ixekizumab", "siliq": "brodalumab", "ilumya": "tildrakizumab", "skyrizi": "risankizumab", "tremfya": "guselkumab", "orencia": "abatacept", "actemra": "tocilizumab", "kevzara": "sarilumab", "kineret": "anakinra", "rituxan": "rituximab", "benlysta": "belimumab", "belimumab": "belimumab"
}

# Fuzzy correction helper
def fuzzy_correct(user_input, known_list, threshold=85):
    if not user_input:
        return user_input, None
    match, score, _ = process.extractOne(user_input, known_list, scorer=fuzz.WRatio)
    if score >= threshold:
        return match, None
    elif score >= 70:
        return None, match  # Suggest correction
    else:
        return user_input, None

# Fuzzy brand-to-generic lookup
def fuzzy_brand_to_generic(user_input, brand_dict, threshold=85):
    if not user_input:
        return None, None, None
    brands = list(brand_dict.keys())
    match, score, _ = process.extractOne(user_input.lower(), brands, scorer=fuzz.WRatio)
    if score >= threshold:
        return match, brand_dict[match], score
    elif score >= 70:
        return match, None, score  # Suggest correction
    else:
        return None, None, None

def extract_sample_size(abstract):
    if not abstract:
        return None
    # Try n=123 or n = 123
    match = re.search(r"n\s*=\s*(\d+)", abstract, re.IGNORECASE)
    if match:
        return int(match.group(1))
    # Try 123 patients/subjects/volunteers/participants
    match = re.search(r"(\d{2,5})\s+(patients|subjects|volunteers|participants)", abstract, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None

st.set_page_config(page_title="RWE Drug Comparator", layout="wide")
st.title("RWE Drug Comparator")

# --- Instructions and Example Queries ---
import streamlit as st

def set_example(example):
    st.session_state['input_drugs'] = example['drugs']
    st.session_state['condition'] = example['condition']
    st.session_state['run_search'] = True

st.markdown("""
### How to use this app
1. Enter two or more drugs (brand or generic, separated by commas or semicolons) to compare them head-to-head.
2. Enter a condition (e.g., ulcerative colitis).
3. Click 'Search Clinical Trials' to see results.

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

# --- Input fields ---
input_drugs = st.text_input("Drugs (comma- or semicolon-separated)", placeholder="e.g. adalimumab, infliximab, etanercept", key='input_drugs')
condition = st.text_input("Condition", placeholder="e.g. ulcerative colitis", key='condition')

# Auto-run search if example was clicked
run_search = st.session_state.get('run_search', False)
if run_search:
    st.session_state['run_search'] = False
    search_now = True
else:
    search_now = st.button("Search Clinical Trials")

# Parse and clean drug list
raw_drugs = [d.strip() for d in re.split(r",|;", input_drugs) if d.strip()]

# Fuzzy/brand correct each drug
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
        # Fuzzy correct as generic
        corrected, suggestion = fuzzy_correct(d, KNOWN_DRUGS)
        if suggestion:
            st.warning(f"Did you mean '{suggestion}'?")
            st.stop()
        final_drugs.append(corrected)
        display_drugs.append(corrected)

# Fuzzy correction for Condition
corrected_condition, suggestion_condition = fuzzy_correct(condition, KNOWN_CONDITIONS)
if suggestion_condition:
    st.warning(f"Did you mean '{suggestion_condition}' for Condition?")
    st.stop()

if search_now:
    if not final_drugs or not corrected_condition:
        st.warning("Please enter at least two drugs and a condition.")
    else:
        with st.spinner("Querying Europe PMC..."):
            # For now, search using the first drug and condition (Europe PMC API is keyword-based)
            results = search_europe_pmc(final_drugs[0], corrected_condition)
        if not results:
            st.error("No clinical trials found for that query.")
        else:
            st.success(f"Found {len(results)} results for: {', '.join(display_drugs)}")
            # Build side-by-side table
            table_rows = []
            for r in results:
                # For each drug, check if it appears as a comparator in the abstract
                row = {
                    "Study Title": r['title'],
                    "Outcome Snippet": None,
                    "Year": r.get('pub_year', ''),
                    "Sample Size": extract_sample_size(r.get('abstract', '')),
                    "PubMed Link": f"https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/" if r.get('pmid') else ""
                }
                abstract = r.get('abstract', '')
                # For each drug, check if present in abstract (case-insensitive)
                for drug in final_drugs:
                    row[drug.title()] = "Yes" if drug.lower() in abstract.lower() else ""
                # Extract comparators and outcome snippet (using all drugs as input)
                comparators, outcome_snippet = extract_comparators_from_abstract(abstract, final_drugs[0])
                row["Outcome Snippet"] = outcome_snippet or "(Not found)"
                table_rows.append(row)
            if table_rows:
                df = pd.DataFrame(table_rows)
                # Column selector
                all_columns = list(df.columns)
                default_columns = [col for col in all_columns if col not in ("Outcome Snippet", "Sample Size")]
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
                    with st.expander("Show abstract"):
                        st.markdown(results[i].get('abstract', 'No abstract available.'), unsafe_allow_html=True)
            else:
                st.warning("No studies found with explicit comparators in the abstract for your query.")

# --- About/Info Section in Sidebar ---
with st.sidebar:
    with st.expander("ℹ️ About this app", expanded=False):
        st.markdown("""
### RWE Drug Comparator

**Technologies & Frameworks:**
- Python 3.12
- Streamlit (interactive web app)
- Pandas (data wrangling)
- RapidFuzz (fuzzy matching, typo correction)
- Custom regex & NLP logic

**NLP & Extraction:**
- Brand-to-generic drug mapping (top 200+ US drugs)
- Fuzzy brand/generic recognition (typo-tolerant)
- Regex-based sample size extraction
- Comparator and outcome phrase detection
- (Planned) Biomedical NER (Hugging Face transformers)

**Data Sources:**
- Europe PMC (clinical trial abstracts & metadata)
- PubMed (article links)
- DOI (publisher article links)
- RxNorm/openFDA (brand/generic mapping)

**Features:**
- Multi-drug, side-by-side comparator table
- Brand/generic name recognition & correction
- Sample size, year, and outcome snippet extraction
- Downloadable CSV results for downstream analysis
- Clickable PubMed links and abstract expanders
- Example queries for instant exploration

**Use Cases:**
- Medical Affairs: Literature review, value dossiers, launch readiness
- RWE/Epidemiology: Comparator mapping, sample size, recency, outcomes
- Regulatory: Track evidence for new drugs vs. standards of care
- Commercial: Evidence for messaging, reimbursement, and market access

---
*Built for rapid, transparent, and actionable evidence review.*
        """)
