# prompt evaluation script

# Tests both extraction prompt versions on the same set of queries, logs the results, and picks the winner based on how many features each version correctly extracts.

# Run this separately


import json
from datetime import datetime
from llm_client import call_llm
from prompts import EXTRACTION_PROMPT_V1, EXTRACTION_PROMPT_V2

# test queries: covering different levels of detail
TEST_QUERIES = [
    "How much would a 3-bedroom ranch with a big garage in a good neighborhood cost?",
    "I'm looking at a 2-story house, about 2000 sqft, built in 1995, 2 full baths, in the NridgHt area. It has a 2-car garage and a finished basement around 800 sqft.",
    "What's the price for a small 1-bedroom house with no garage, average quality, built in the 1960s?",
    "Large 4-bed 3-bath colonial in Somerst, excellent kitchen, about 3000 sqft living space, built 2005, 3-car garage, fireplace, big lot around 12000 sqft",
    "just a basic starter home, nothing fancy, maybe 1200 square feet",
]

# what we expect each query to extract (only the 12 model features)
EXPECTED_FEATURES = [
    {"garage_cars": 3},  # query 0 — "big garage" → 3 cars
    {"gr_liv_area": 2000, "year_built": 1995, "full_bath": 2, "garage_cars": 2, "bsmtfin_sf_1": 800},  # query 1
    {"garage_cars": 0, "overall_qual": 5},  # query 2
    {"full_bath": 3, "kitchen_qual": "Ex", "gr_liv_area": 3000, "year_built": 2005, "garage_cars": 3, "lot_area": 12000},  # query 3
    {"gr_liv_area": 1200},  # query 4
]


def parse_json(text):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)


def score_extraction(extracted_features, expected):
    # how many expected features were correctly extracted
    correct = 0
    total = len(expected)
    details = []

    for key, expected_val in expected.items():
        actual = extracted_features.get(key)
        if actual == expected_val:
            correct += 1
            details.append(f"  ✓ {key}: {actual}")
        else:
            details.append(f"  ✗ {key}: expected={expected_val}, got={actual}")

    return correct, total, details


def run_eval():
    results = []
    v1_total_score = 0
    v2_total_score = 0
    v1_total_possible = 0
    v2_total_possible = 0

    print("=" * 70)
    print("PROMPT VERSION EVALUATION")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Queries: {len(TEST_QUERIES)}")
    print("=" * 70)

    for i, query in enumerate(TEST_QUERIES):
        print(f"\n--- Query {i+1}: \"{query[:60]}...\"")
        expected = EXPECTED_FEATURES[i]

        for version, template in [("V1", EXTRACTION_PROMPT_V1), ("V2", EXTRACTION_PROMPT_V2)]:
            prompt = template.format(query=query)
            try:
                raw = call_llm(prompt)
                parsed = parse_json(raw)
                features = parsed.get("features", {})
                confident = parsed.get("confident_features", [])
                missing = parsed.get("missing_features", [])

                correct, total, details = score_extraction(features, expected)
                status = "OK"
            except Exception as e:
                features = {}
                confident = []
                missing = []
                correct, total = 0, len(expected)
                details = [f"  ERROR: {e}"]
                status = "FAIL"

            if version == "V1":
                v1_total_score += correct
                v1_total_possible += total
            else:
                v2_total_score += correct
                v2_total_possible += total

            print(f"\n  [{version}] Status: {status} | Score: {correct}/{total}")
            print(f"  Confident: {confident}")
            for d in details:
                print(d)

            results.append({
                "query_index": i,
                "version": version,
                "query": query,
                "status": status,
                "score": f"{correct}/{total}",
                "confident_features": confident,
                "missing_features": missing,
                "extracted": features,
            })

    # final comparison
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print(f"  V1 total: {v1_total_score}/{v1_total_possible}")
    print(f"  V2 total: {v2_total_score}/{v2_total_possible}")
    winner = "V1" if v1_total_score >= v2_total_score else "V2"
    print(f"  Winner: {winner}")
    print("=" * 70)

    # save full log
    log = {
        "timestamp": datetime.now().isoformat(),
        "v1_score": f"{v1_total_score}/{v1_total_possible}",
        "v2_score": f"{v2_total_score}/{v2_total_possible}",
        "winner": winner,
        "details": results,
    }
    with open("prompt_eval_log.json", "w") as f:
        json.dump(log, f, indent=2)
    print("\nFull log saved to prompt_eval_log.json")


if __name__ == "__main__":
    run_eval()