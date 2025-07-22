import re

def extract_comparators_from_abstract(abstract, drug_a, drug_b=None):
    """
    Searches for comparator phrases and extracts possible comparator drug names.
    If drug_b is provided, only return comparators if both drugs appear near comparison.
    Also attempts to extract an outcome/result snippet.
    """
    if not abstract or not drug_a:
        return None, None

    abstract_lc = abstract.lower()
    drug_a_lc = drug_a.lower()
    drug_b_lc = drug_b.lower() if drug_b else None
    comparison_phrases = ["compared with", "versus", "vs.", "vs ", "compared to", "relative to", "in comparison to"]
    found = []
    outcome_snippet = None

    for phrase in comparison_phrases:
        if phrase in abstract_lc:
            before, _, after = abstract_lc.partition(phrase)
            left = re.findall(r"\b[a-zA-Z0-9\-]+\b", before)[-6:]
            right = re.findall(r"\b[a-zA-Z0-9\-]+\b", after)[:6]
            window = left + right
            # Remove common stopwords and drug_a from candidate list
            stopwords = set(["the", "and", "with", "to", "in", "of", "a", "was", "were", "as", "by", "for", "on", "from", "that", "at", "this", "is"])
            comparators = [w for w in window if w not in stopwords and w != drug_a_lc]
            comparators = list(set(comparators))
            # For head-to-head, require both drugs in window
            if drug_b_lc:
                if drug_a_lc in window and drug_b_lc in window:
                    found.extend([drug_b_lc])
                    # Attempt to extract outcome/result snippet (simple: 30 chars before/after phrase)
                    idx = abstract_lc.find(phrase)
                    start = max(0, idx - 30)
                    end = min(len(abstract_lc), idx + len(phrase) + 50)
                    outcome_snippet = abstract[start:end].strip()
            else:
                if comparators:
                    found.extend(comparators)
                    idx = abstract_lc.find(phrase)
                    start = max(0, idx - 30)
                    end = min(len(abstract_lc), idx + len(phrase) + 50)
                    outcome_snippet = abstract[start:end].strip()
    if found:
        return list(set(found)), outcome_snippet
    return None, None
