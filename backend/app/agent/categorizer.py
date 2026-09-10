import re
from typing import Dict, Any, Tuple, Optional, List
from ml.anomaly_detector import CATEGORIES

# Category keyword knowledge graph
CATEGORY_KEYWORDS = {
    "Food": {
        "keywords": ["restaurant", "cafe", "dinner", "lunch", "breakfast", "burger", "pizza", "zomato", "swiggy", "starbucks", "mcdonald", "subway", "bar", "pub", "bistro", "dhaba", "food", "dining", "meal", "coffee", "chai", "bakery"],
        "subcategories": ["Restaurant", "Cafe & Coffee", "Fast Food", "Food Delivery", "Bars & Nightlife"]
    },
    "Groceries": {
        "keywords": ["supermarket", "groceries", "grocery", "blinkit", "instamart", "zepto", "bigbasket", "vegetables", "fruits", "milk", "mart", "dmart", "spencer", "nature's basket", "reliance fresh"],
        "subcategories": ["Supermarket", "Produce & Dairy", "Online Grocery", "Household Supplies"]
    },
    "Transport": {
        "keywords": ["uber", "ola", "metro", "cab", "taxi", "fuel", "petrol", "diesel", "parking", "toll", "fastag", "bus", "auto", "train", "flight", "rapido"],
        "subcategories": ["Rideshare & Cabs", "Fuel", "Public Transit", "Tolls & Parking", "Flights"]
    },
    "Shopping": {
        "keywords": ["amazon", "flipkart", "myntra", "clothes", "shoes", "mall", "electronics", "zara", "h&m", "nike", "adidas", "shopping", "retail", "croma", "apple store"],
        "subcategories": ["E-Commerce", "Apparel & Shoes", "Electronics", "Home & Lifestyle"]
    },
    "Entertainment": {
        "keywords": ["movie", "cinema", "pvr", "inox", "bookmyshow", "concert", "game", "gaming", "steam", "playstation", "theatre", "amusement", "bowling"],
        "subcategories": ["Movies & Cinema", "Events & Shows", "Gaming", "Outings"]
    },
    "Bills": {
        "keywords": ["electricity", "water bill", "broadband", "wifi", "airtel", "jio", "vi", "recharge", "gas cylinder", "piped gas", "maintenance"],
        "subcategories": ["Electricity", "Internet & Mobile", "Gas & Water", "Utility Bills"]
    },
    "Healthcare": {
        "keywords": ["pharmacy", "medicine", "doctor", "hospital", "clinic", "apollo", "1mg", "pharmeasy", "dentist", "lab test", "diagnostics", "therapy", "gym", "fitness"],
        "subcategories": ["Medicines", "Doctor Consultations", "Fitness & Gym", "Diagnostics"]
    },
    "Education": {
        "keywords": ["course", "udemy", "coursera", "books", "tuition", "school", "college", "fees", "exam", "learning", "training", "university"],
        "subcategories": ["Online Courses", "Tuition & School", "Books & Material", "Certifications"]
    },
    "Travel": {
        "keywords": ["hotel", "airbnb", "resort", "booking.com", "makemytrip", "goibibo", "agoda", "vacation", "trip", "holiday", "tour", "homestay"],
        "subcategories": ["Hotels & Stays", "Flights & Rail", "Holiday Packages", "Activities"]
    },
    "Subscriptions": {
        "keywords": ["netflix", "spotify", "prime", "youtube premium", "hotstar", "disney", "chatgpt", "github", "icloud", "google one", "subscription", "membership"],
        "subcategories": ["Streaming Audio/Video", "Software & Cloud", "Memberships", "Digital Media"]
    },
    "Rent": {
        "keywords": ["rent", "house rent", "flat rent", "landlord", "lease", "deposit"],
        "subcategories": ["Apartment Rent", "Maintenance", "Security Deposit"]
    },
    "Utilities": {
        "keywords": ["plumber", "electrician", "cleaner", "maid", "urban company", "repairs", "laundry", "dry cleaning"],
        "subcategories": ["Home Services", "Repairs", "Cleaning"]
    },
    "Transfers": {
        "keywords": ["transfer", "sent to", "paid to", "rahul", "priya", "amit", "rohit", "neha", "upi to", "family", "friend", "split", "repayment", "loan", "gift"],
        "subcategories": ["Peer-to-Peer", "Family & Friends", "Split Expenses", "Repayment"]
    }
}

class CategorizationEngine:
    """Categorizes transactions with confidence scores and clarification triggers."""

    def __init__(self, confidence_threshold: float = 0.75):
        self.confidence_threshold = confidence_threshold

    def categorize(
        self,
        text_or_merchant: str,
        amount: Optional[float] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        combined_text = f"{text_or_merchant} {description or ''}".lower()

        # Check for ambiguous peer payments: "Paid ₹... to [Name]" or "Sent to [Name]"
        peer_match = re.search(r'(?:paid|sent|given|transferred)\s+(?:₹?\s*\d+(?:,\d+)*)?\s*(?:to\s+)([a-zA-Z]+)', combined_text)
        if not peer_match:
            peer_match = re.search(r'^(?:to\s+)([a-zA-Z]+)', combined_text)

        # Ambiguity scenario explicitly called out in prompt: "Paid ₹2,500 to Rahul"
        if peer_match:
            recipient = peer_match.group(1).capitalize()
            # If there is no other clarifying keyword like "for dinner" or "rent"
            has_explicit_reason = any(w in combined_text for w in ["rent", "dinner", "groceries", "bill", "movie", "ticket"])
            if not has_explicit_reason:
                return {
                    "category": "Transfers",
                    "subcategory": "Peer-to-Peer",
                    "confidence_score": 0.45, # Intentionally low to trigger clarification
                    "reason": f"Payment to individual '{recipient}' without specified purpose.",
                    "needs_clarification": True,
                    "clarification_prompt": f"I found a payment to {recipient}, but I'm not confident about the category. Was this a transfer, loan repayment, gift, dinner split, or something else?",
                    "suggested_categories": ["Transfers", "Food", "Entertainment", "Rent", "Other"]
                }

        # Match against knowledge keywords
        best_category = "Other"
        best_subcategory = "General"
        best_score = 0.50
        match_reason = "Default fallback category"

        for cat, data in CATEGORY_KEYWORDS.items():
            for kw in data["keywords"]:
                if re.search(r'\b' + re.escape(kw) + r'\b', combined_text):
                    score = 0.95 if kw in text_or_merchant.lower() else 0.85
                    if score > best_score:
                        best_score = score
                        best_category = cat
                        best_subcategory = data["subcategories"][0]
                        match_reason = f"Matched merchant/description keyword '{kw}'"

        # Check specific merchant patterns
        if "amazon" in combined_text or "flipkart" in combined_text:
            best_category = "Shopping"
            best_subcategory = "E-Commerce"
            best_score = 0.97
            match_reason = "Recognized premier e-commerce marketplace"
        elif "restaurant" in combined_text or "dining" in combined_text or "zomato" in combined_text or "swiggy" in combined_text:
            best_category = "Food"
            best_subcategory = "Dining Out" if "restaurant" in combined_text else "Food Delivery"
            best_score = 0.96
            match_reason = "Identified restaurant dining activity"
        elif "uber" in combined_text or "ola" in combined_text or "metro" in combined_text:
            best_category = "Transport"
            best_subcategory = "Rideshare & Cabs"
            best_score = 0.98
            match_reason = "Identified transit provider"

        needs_clarification = best_score < self.confidence_threshold

        return {
            "category": best_category,
            "subcategory": best_subcategory,
            "confidence_score": round(best_score, 2),
            "reason": match_reason,
            "needs_clarification": needs_clarification,
            "clarification_prompt": f"I categorized this under {best_category} with moderate confidence. Would you like to confirm or change it?" if needs_clarification else None,
            "suggested_categories": [best_category, "Shopping", "Food", "Bills", "Other"] if needs_clarification else []
        }
