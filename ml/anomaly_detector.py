import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from sklearn.ensemble import IsolationForest
import logging

logger = logging.getLogger("anomaly_detector")

CATEGORIES = [
    "Food", "Groceries", "Transport", "Shopping", "Entertainment",
    "Bills", "Healthcare", "Education", "Travel", "Subscriptions",
    "Rent", "Utilities", "Transfers", "Other"
]

CATEGORY_MAP = {cat: i for i, cat in enumerate(CATEGORIES)}

class AnomalyResult:
    def __init__(
        self,
        is_anomaly: bool,
        anomaly_score: float,
        reason: str,
        layer_results: Dict[str, Any]
    ):
        self.is_anomaly = is_anomaly
        self.anomaly_score = round(anomaly_score, 3)
        self.reason = reason
        self.layer_results = layer_results

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_anomaly": self.is_anomaly,
            "anomaly_score": self.anomaly_score,
            "reason": self.reason,
            "layer_results": self.layer_results
        }

class MultiLayerAnomalyDetector:
    """
    3-Layer Hybrid Anomaly Detection Engine:
    - Layer 1: Rule-based heuristic constraints
    - Layer 2: Statistical distribution metrics (Z-score & IQR)
    - Layer 3: Unsupervised Machine Learning (Isolation Forest)
    """

    def __init__(self, sensitivity: float = 0.70):
        self.sensitivity = sensitivity
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.08,
            random_state=42
        )
        self.is_fitted = False

    def fit(self, historical_expenses: List[Dict[str, Any]]):
        """Fit Isolation Forest on historical user expenses if sufficient data exists."""
        if len(historical_expenses) < 10:
            self.is_fitted = False
            return

        features = []
        for exp in historical_expenses:
            feat = self._extract_features(exp, historical_expenses)
            features.append(feat)

        X = np.array(features)
        try:
            self.model.fit(X)
            self.is_fitted = True
        except Exception as e:
            logger.warning(f"Failed to fit Isolation Forest: {e}")
            self.is_fitted = False

    def _extract_features(
        self,
        expense: Dict[str, Any],
        historical_expenses: List[Dict[str, Any]]
    ) -> List[float]:
        """Extract ML feature vector: amount, cat_code, day_of_week, deviation_ratio, merchant_freq."""
        amount = float(expense.get("amount", 0.0))
        cat = expense.get("category", "Other")
        cat_code = float(CATEGORY_MAP.get(cat, len(CATEGORIES) - 1))
        
        # Day of week
        date_val = expense.get("date")
        if isinstance(date_val, str):
            try:
                date_obj = pd.to_datetime(date_val)
                day_of_week = float(date_obj.dayofweek)
            except Exception:
                day_of_week = 2.0
        elif hasattr(date_val, "weekday"):
            day_of_week = float(date_val.weekday())
        else:
            day_of_week = 2.0

        # Category average amount
        same_cat_amounts = [
            float(e["amount"]) for e in historical_expenses
            if e.get("category") == cat and float(e.get("amount", 0)) > 0
        ]
        cat_mean = np.mean(same_cat_amounts) if same_cat_amounts else amount
        deviation_ratio = (amount / cat_mean) if cat_mean > 0 else 1.0

        # Merchant frequency
        merchant = expense.get("merchant", "").lower()
        same_merchant_count = sum(
            1 for e in historical_expenses if e.get("merchant", "").lower() == merchant
        )
        merchant_freq = float(same_merchant_count) / max(len(historical_expenses), 1)

        return [amount, cat_code, day_of_week, deviation_ratio, merchant_freq]

    def detect(
        self,
        target_expense: Dict[str, Any],
        historical_expenses: List[Dict[str, Any]]
    ) -> AnomalyResult:
        """
        Evaluate expense through Layer 1 (Rules), Layer 2 (Stats), Layer 3 (ML),
        combining signals into an interpreted anomaly result.
        """
        amount = float(target_expense.get("amount", 0.0))
        category = target_expense.get("category", "Other")
        merchant = target_expense.get("merchant", "Unknown")

        # Category-filtered historical data
        same_cat_expenses = [
            e for e in historical_expenses
            if e.get("category") == category
        ]
        cat_amounts = [float(e["amount"]) for e in same_cat_expenses if float(e.get("amount", 0)) > 0]
        all_amounts = [float(e["amount"]) for e in historical_expenses if float(e.get("amount", 0)) > 0]

        reasons = []

        # =====================================================================
        # LAYER 1: RULE-BASED DETECTION
        # =====================================================================
        layer1_flag = False
        layer1_score = 0.0

        if cat_amounts:
            cat_avg = np.mean(cat_amounts)
            # Rule 1: Expense > 3.0x category average
            if cat_avg > 0 and amount > 3.0 * cat_avg and amount > 1500:
                layer1_flag = True
                layer1_score = min(1.0, 0.5 + (amount / (cat_avg * 4.0)) * 0.5)
                reasons.append(f"Exceeds typical {category} spending (₹{int(cat_avg)} avg) by {round(amount / cat_avg, 1)}x")

            # Rule 2: Food / dining spike threshold
            if category == "Food" and amount >= 3500 and (cat_avg < 1500):
                layer1_flag = True
                layer1_score = max(layer1_score, 0.85)
                if not any("typical Food spending" in r for r in reasons):
                    reasons.append(f"Significantly higher than typical restaurant meals (₹{amount:,.0f} vs avg ₹{int(cat_avg)})")

        # Rule 3: Single transaction exceeding large absolute spike
        if all_amounts:
            overall_max = max(all_amounts)
            if amount > overall_max * 1.5 and amount > 5000:
                layer1_flag = True
                layer1_score = max(layer1_score, 0.90)
                reasons.append(f"Single highest expense recorded (previous maximum was ₹{int(overall_max)})")

        # =====================================================================
        # LAYER 2: STATISTICAL DETECTION (Z-Score & IQR)
        # =====================================================================
        layer2_flag = False
        layer2_score = 0.0
        z_score = 0.0
        iqr_upper_bound = 0.0

        sample_set = cat_amounts if len(cat_amounts) >= 5 else all_amounts
        if len(sample_set) >= 4:
            mean = np.mean(sample_set)
            std = np.std(sample_set)
            if std > 0:
                z_score = (amount - mean) / std
                if z_score > 2.2: # Statistical threshold for outlier
                    layer2_flag = True
                    layer2_score = min(1.0, (z_score / 4.0))
                    reasons.append(f"Statistical deviation: Z-score is {round(z_score, 1)}σ above standard distribution")

            # IQR calculation
            q25, q75 = np.percentile(sample_set, [25, 75])
            iqr = q75 - q25
            iqr_upper_bound = q75 + (1.5 * iqr)
            if amount > iqr_upper_bound and amount > 1200:
                layer2_flag = True
                layer2_score = max(layer2_score, 0.75)
                if not any("Z-score" in r for r in reasons):
                    reasons.append(f"Exceeds interquartile range upper fence (₹{int(iqr_upper_bound)})")

        # =====================================================================
        # LAYER 3: MACHINE LEARNING (Isolation Forest)
        # =====================================================================
        layer3_flag = False
        layer3_score = 0.0

        # Fit model on the fly if needed
        if not self.is_fitted and len(historical_expenses) >= 10:
            self.fit(historical_expenses)

        if self.is_fitted:
            try:
                feat = np.array([self._extract_features(target_expense, historical_expenses)])
                # decision_function returns negative for anomalies
                raw_decision = self.model.decision_function(feat)[0]
                prediction = self.model.predict(feat)[0] # -1 for anomaly, 1 for normal
                
                # Transform decision score to 0..1 scale (lower decision = more anomalous)
                ml_anomaly_prob = float(1.0 / (1.0 + np.exp(raw_decision * 10.0)))
                layer3_score = ml_anomaly_prob

                if prediction == -1 or ml_anomaly_prob > self.sensitivity:
                    layer3_flag = True
                    reasons.append("Multi-dimensional pattern anomaly identified by Isolation Forest model")
            except Exception as e:
                logger.warning(f"Error evaluating Isolation Forest: {e}")
        else:
            # Fallback for small history using multivariate heuristic
            cat_mean = np.mean(cat_amounts) if cat_amounts else 0
            if cat_mean > 0 and (amount / cat_mean) >= 2.5 and amount > 2000:
                layer3_score = 0.72
                layer3_flag = True

        # =====================================================================
        # ENSEMBLE COMPOSITE SCORING
        # =====================================================================
        weights = [0.35, 0.35, 0.30]
        composite_score = (
            weights[0] * layer1_score +
            weights[1] * layer2_score +
            weights[2] * layer3_score
        )

        # Boost score if multiple layers concur
        active_layers = sum([1 for flag in [layer1_flag, layer2_flag, layer3_flag] if flag])
        if active_layers >= 2:
            composite_score = min(1.0, composite_score * 1.25)
        elif active_layers == 0 and composite_score < 0.35:
            composite_score = 0.05

        is_anomaly = bool(composite_score >= self.sensitivity or active_layers >= 2)

        # Generate human-friendly agent explanation
        if is_anomaly:
            if not reasons:
                reasons.append(f"Unusual transaction amount ₹{amount:,.0f} compared to historical average")
            explanation = " • ".join(reasons)
        else:
            explanation = f"Consistent with historical spending behavior in {category}."

        layer_results = {
            "layer1_rule_flag": layer1_flag,
            "layer1_score": round(layer1_score, 3),
            "layer2_stat_flag": layer2_flag,
            "layer2_score": round(layer2_score, 3),
            "z_score": round(float(z_score), 2),
            "layer3_ml_flag": layer3_flag,
            "layer3_score": round(layer3_score, 3),
            "active_layers_concurring": active_layers
        }

        return AnomalyResult(
            is_anomaly=is_anomaly,
            anomaly_score=composite_score,
            reason=explanation,
            layer_results=layer_results
        )
