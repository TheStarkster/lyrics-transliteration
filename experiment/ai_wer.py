import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Dict, Any, List, Tuple, Optional

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")


def tokenize(text: str) -> List[str]:
    return text.strip().lower().split()


def get_token_embeddings(tokens: List[str]) -> List[np.ndarray]:
    return model.encode(tokens, convert_to_tensor=False)


def semantic_distance(embed_a: np.ndarray, embed_b: np.ndarray) -> float:
    sim = np.dot(embed_a, embed_b) / (np.linalg.norm(embed_a) * np.linalg.norm(embed_b))
    return float(1.0 - sim)  # convert numpy.float32 → float


def semantic_wer_core(
    reference: str, hypothesis: str
) -> Tuple[float, int, float, List[Dict[str, Optional[str]]]]:
    ref_tokens = tokenize(reference)
    hyp_tokens = tokenize(hypothesis)

    if not ref_tokens:
        raise ValueError("Reference text is empty")

    ref_embeds = get_token_embeddings(ref_tokens)
    hyp_embeds = get_token_embeddings(hyp_tokens)

    rows, cols = len(ref_tokens) + 1, len(hyp_tokens) + 1
    dp = np.zeros((rows, cols))
    backtrace = [[None] * cols for _ in range(rows)]

    for i in range(rows):
        dp[i][0] = i
        backtrace[i][0] = "D"
    for j in range(cols):
        dp[0][j] = j
        backtrace[0][j] = "I"

    for i in range(1, rows):
        for j in range(1, cols):
            sub_cost = semantic_distance(ref_embeds[i - 1], hyp_embeds[j - 1])
            options = {
                "S": dp[i - 1][j - 1] + sub_cost,
                "D": dp[i - 1][j] + 1,
                "I": dp[i][j - 1] + 1
            }
            action = min(options, key=options.get)
            dp[i][j] = options[action]
            backtrace[i][j] = action

    i, j = len(ref_tokens), len(hyp_tokens)
    total_cost = 0.0
    alignment = []

    while i > 0 or j > 0:
        action = backtrace[i][j]
        if action == "S":
            cost = semantic_distance(ref_embeds[i - 1], hyp_embeds[j - 1])
            total_cost += cost
            alignment.append({
                "ref": ref_tokens[i - 1],
                "hyp": hyp_tokens[j - 1],
                "type": "match" if cost < 0.2 else "substitution",
                "cost": round(float(cost), 4)  # ensure float
            })
            i -= 1
            j -= 1
        elif action == "D":
            total_cost += 1.0
            alignment.append({
                "ref": ref_tokens[i - 1],
                "hyp": None,
                "type": "deletion",
                "cost": 1.0
            })
            i -= 1
        elif action == "I":
            total_cost += 1.0
            alignment.append({
                "ref": None,
                "hyp": hyp_tokens[j - 1],
                "type": "insertion",
                "cost": 1.0
            })
            j -= 1

    alignment.reverse()
    semantic_wer = float(total_cost) / len(ref_tokens)

    return float(semantic_wer), len(ref_tokens), float(total_cost), alignment


def calculate_wer(reference: str, hypothesis: str) -> Dict[str, Any]:
    """
    Public API: Computes semantic WER and returns detailed breakdown.
    Returns only Python-native data types (int, float, str, None, dict, list).
    """
    try:
        wer, total_words, total_cost, alignment = semantic_wer_core(reference, hypothesis)
        return {
            "success": True,
            "wer_details": {
                "semantic_wer_percentage": round(float(wer) * 100, 2),
                "total_words": int(total_words),
                "total_cost": round(float(total_cost), 4),
                "alignment": alignment
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
