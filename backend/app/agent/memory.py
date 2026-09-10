import numpy as np
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from backend.app.models.entities import Expense, Budget, RecurringExpense, UserPreference

def compute_text_embedding(text: str, dim: int = 1536) -> List[float]:
    """
    Deterministic pseudo-semantic embedding vector for testing/local mode.
    Maps word hashes and n-grams into normalized unit vector space.
    """
    vec = np.zeros(dim, dtype=np.float32)
    words = text.lower().split()
    if not words:
        return vec.tolist()
    for i, word in enumerate(words):
        h = hash(word)
        idx = abs(h) % dim
        vec[idx] += 1.0 / (i + 1.0)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec.tolist()

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))

class PersonalizedMemory:
    """Manages user-specific financial memory, profile baselines, and semantic transaction search."""

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def get_spending_profile(self) -> Dict[str, Any]:
        """Calculates user baseline averages, top merchants, category normal ranges."""
        expenses = self.db.query(Expense).filter(Expense.user_id == self.user_id).all()
        if not expenses:
            return {
                "total_transactions": 0,
                "category_averages": {},
                "top_merchants": {},
                "typical_ranges": {}
            }

        cat_data: Dict[str, List[float]] = {}
        merchant_counts: Dict[str, int] = {}

        for e in expenses:
            amt = float(e.amount)
            cat_data.setdefault(e.category, []).append(amt)
            m = e.merchant.title()
            merchant_counts[m] = merchant_counts.get(m, 0) + 1

        category_averages = {cat: round(float(np.mean(vals)), 2) for cat, vals in cat_data.items()}
        typical_ranges = {
            cat: {
                "min": round(float(np.percentile(vals, 15)), 2),
                "max": round(float(np.percentile(vals, 85)), 2),
                "avg": round(float(np.mean(vals)), 2),
                "count": len(vals)
            }
            for cat, vals in cat_data.items()
        }

        # Sort top merchants
        top_merchants = dict(sorted(merchant_counts.items(), key=lambda item: item[1], reverse=True)[:5])

        return {
            "total_transactions": len(expenses),
            "category_averages": category_averages,
            "typical_ranges": typical_ranges,
            "top_merchants": top_merchants
        }

    def search_similar_transactions(
        self,
        merchant_or_desc: str,
        category: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Finds closest past transactions via semantic vector and text matching."""
        target_embedding = compute_text_embedding(merchant_or_desc)
        query = self.db.query(Expense).filter(Expense.user_id == self.user_id)
        if category:
            query = query.filter(Expense.category == category)
        expenses = query.order_by(Expense.date.desc()).limit(100).all()

        scored = []
        for e in expenses:
            emb = e.embedding
            score = 0.0
            if emb and isinstance(emb, list):
                score = cosine_similarity(target_embedding, emb)
            elif e.merchant.lower() in merchant_or_desc.lower() or merchant_or_desc.lower() in e.merchant.lower():
                score = 0.85
            scored.append((score, e))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for sim, exp in scored[:limit]:
            results.append({
                "id": exp.id,
                "amount": float(exp.amount),
                "merchant": exp.merchant,
                "category": exp.category,
                "date": exp.date.isoformat(),
                "similarity": round(sim, 2)
            })
        return results

    def compare_with_historical_behavior(
        self,
        amount: float,
        merchant: str,
        category: str
    ) -> str:
        """Compares current transaction against learned user patterns."""
        similar = self.search_similar_transactions(merchant, category=category, limit=3)
        profile = self.get_spending_profile()
        cat_stats = profile.get("typical_ranges", {}).get(category)

        if not cat_stats or cat_stats["count"] == 0:
            return f"First recorded expense in {category}. Establishing normal baseline."

        normal_min = cat_stats["min"]
        normal_max = cat_stats["max"]
        normal_avg = cat_stats["avg"]

        if normal_min <= amount <= normal_max:
            return f"Consistent with your normal spending pattern in {category} (typical range: ₹{int(normal_min)}–₹{int(normal_max)})."
        elif amount < normal_min:
            return f"Lower than your typical {category} expenditure (typical avg: ₹{int(normal_avg)})."
        else:
            multiple = round(amount / normal_avg, 1) if normal_avg > 0 else 1.0
            return f"Higher than your typical {category} spending (₹{int(normal_min)}–₹{int(normal_max)}). It is {multiple}x above your average ₹{int(normal_avg)}."
