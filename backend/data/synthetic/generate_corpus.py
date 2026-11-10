"""
FinSight Synthetic Corpus Generator (20 Personas, 15,000 - 20,000 Transactions)
Conforming strictly to data_schema.md Section 12.
"""

import csv
import hashlib
import json
import os
import random
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Tuple

SEED = 42
random.seed(SEED)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "corpus")
os.makedirs(OUTPUT_DIR, exist_ok=True)

START_DATE = date(2024, 2, 1)
END_DATE = date(2025, 2, 28)
TOTAL_DAYS = (END_DATE - START_DATE).days

SYSTEM_CATEGORIES = [
    {"name": "Income", "slug": "income", "type": "income", "color": "#10B981"},
    {"name": "Food & Dining", "slug": "food-dining", "type": "expense", "color": "#F59E0B"},
    {"name": "Groceries", "slug": "groceries", "type": "expense", "color": "#10B981"},
    {"name": "Shopping", "slug": "shopping", "type": "expense", "color": "#EC4899"},
    {"name": "Travel & Transport", "slug": "travel-transport", "type": "expense", "color": "#3B82F6"},
    {"name": "Utilities", "slug": "utilities", "type": "expense", "color": "#6366F1"},
    {"name": "Housing & Rent", "slug": "housing-rent", "type": "expense", "color": "#8B5CF6"},
    {"name": "Entertainment", "slug": "entertainment", "type": "expense", "color": "#D946EF"},
    {"name": "Health & Fitness", "slug": "health-fitness", "type": "expense", "color": "#EF4444"},
    {"name": "Investments & Savings", "slug": "investments-savings", "type": "expense", "color": "#14B8A6"},
    {"name": "Subscriptions", "slug": "subscriptions", "type": "expense", "color": "#A855F7"},
    {"name": "Education", "slug": "education", "type": "expense", "color": "#06B6D4"},
    {"name": "Personal Care", "slug": "personal-care", "type": "expense", "color": "#F43F5E"},
    {"name": "Office & Business", "slug": "office-business", "type": "expense", "color": "#64748B"},
    {"name": "Donations & Gifts", "slug": "donations-gifts", "type": "expense", "color": "#E11D48"},
    {"name": "Financial & Tax", "slug": "financial-tax", "type": "expense", "color": "#78716C"},
    {"name": "Travel & Vacation", "slug": "travel-vacation", "type": "expense", "color": "#0284C7"},
    {"name": "Electronics", "slug": "electronics", "type": "expense", "color": "#4F46E5"},
    {"name": "Internal Transfer", "slug": "internal-transfer", "type": "transfer", "color": "#6B7280"},
    {"name": "Miscellaneous", "slug": "miscellaneous", "type": "expense", "color": "#9CA3AF"},
]

MERCHANTS_MASTER = [
    # Food & Dining (20)
    ("Swiggy", "swiggy", "Food & Dining", ["swiggy@icici", "SWIGGY BANGALORE", "SWIGGY ORDER", "SWIGGY BUNDL TECH"]),
    ("Zomato", "zomato", "Food & Dining", ["zomato@hdfcbank", "ZOMATO MEDIA PVT", "ZOMATO RESTAURANT", "ZOMATO ONLINE"]),
    ("Starbucks", "starbucks", "Food & Dining", ["starbucks@axis", "STARBUCKS COFFEE", "TATA STARBUCKS LTD"]),
    ("Chai Point", "chai-point", "Food & Dining", ["chaipoint@okaxis", "CHAI POINT OUTLET", "MOUNTAIN TRAIL FOODS"]),
    ("Subway", "subway", "Food & Dining", ["subway@icici", "SUBWAY SANDWICHES", "SUBWAY KORAMANGALA"]),
    ("Third Wave Coffee", "third-wave", "Food & Dining", ["thirdwave@icici", "THIRD WAVE COFFEE ROASTERS"]),
    ("Haldiram", "haldiram", "Food & Dining", ["haldiram@sbi", "HALDIRAM FOODS", "HALDIRAM RESTAURANT"]),
    ("Dominos Pizza", "dominos", "Food & Dining", ["dominos@icici", "JUBILANT FOODWORKS", "DOMINOS DELIVERY"]),
    ("Burger King", "burger-king", "Food & Dining", ["burgerking@hdfc", "BURGER KING INDIA", "BK INDIRANAGAR"]),
    ("Barbeque Nation", "barbeque-nation", "Food & Dining", ["bbqnation@kotak", "BARBEQUE NATION HOSPITALITY"]),
    ("Paradise Biryani", "paradise-biryani", "Food & Dining", ["paradise@sbi", "PARADISE FOOD COURT"]),
    ("Bhartiya Jalpan", "bhartiya-jalpan", "Food & Dining", ["jalpan@icici", "BHARTIYA JALPAN SWEETS"]),
    ("KFC India", "kfc", "Food & Dining", ["kfc@hdfc", "YUM RESTAURANTS KFC", "KFC FRIED CHICKEN"]),
    ("McDonalds India", "mcdonalds", "Food & Dining", ["mcd@icici", "HARDCASTLE RESTAURANTS", "MCDONALDS OUTLET"]),
    ("Pizza Hut", "pizza-hut", "Food & Dining", ["pizzahut@sbi", "DEVYANI INTERNATIONAL PIZZA"]),
    ("Blue Tokai Coffee", "blue-tokai", "Food & Dining", ["bluetokai@axis", "BLUE TOKAI COFFEE ROASTERS"]),
    ("Behrouz Biryani", "behrouz-biryani", "Food & Dining", ["rebel@icici", "REBEL FOODS BEHROUZ"]),
    ("Faasos", "faasos", "Food & Dining", ["faasos@hdfc", "REBEL FOODS FAASOS"]),
    ("Truffles Cafe", "truffles", "Food & Dining", ["truffles@icici", "TRUFFLES RESTAURANT BLR"]),
    ("Nandhini Deluxe", "nandhini", "Food & Dining", ["nandhini@sbi", "NANDHINI ANDHRA STYLE"]),

    # Groceries (12)
    ("Blinkit", "blinkit", "Groceries", ["blinkit@hdfcbank", "BLINKIT GROCERY", "COMMERCE TECH BLINKIT"]),
    ("Zepto", "zepto", "Groceries", ["zepto@kotak", "ZEPTO QUICK COMMERCE", "KIRANAKART TECH ZEPTO"]),
    ("Instamart", "instamart", "Groceries", ["swiggyinstamart@icici", "INSTAMART SWIGGY", "BUNDL INSTAMART"]),
    ("BigBasket", "bigbasket", "Groceries", ["bigbasket@icici", "SUPERMARKET GROCERY", "BIGBASKET RETAIL"]),
    ("Nature Basket", "nature-basket", "Groceries", ["naturesbasket@axis", "NATURES BASKET LTD"]),
    ("Star Bazaar", "star-bazaar", "Groceries", ["starbazaar@tata", "STAR BAZAAR BANGALORE", "TRENT HYPERMARKET"]),
    ("DMart", "dmart", "Groceries", ["dmart@axis", "AVENUE SUPERMARTS", "DMART RETAIL OUTLET"]),
    ("More Supermarket", "more-supermarket", "Groceries", ["more@hdfc", "MORE RETAIL PRIVATE"]),
    ("Spencer Retail", "spencers", "Groceries", ["spencers@sbi", "SPENCERS RETAIL LIMITED"]),
    ("Local Vegetable Mandi", "local-mandi", "Groceries", ["mandi@upi", "SABZI MANDI VENDOR"]),
    ("Ratnadeep Supermarket", "ratnadeep", "Groceries", ["ratnadeep@hdfc", "RATNADEEP RETAIL HYDERABAD"]),
    ("Namdhari Fresh", "namdhari", "Groceries", ["namdhari@icici", "NAMDHARIS AGRO FRESH"]),

    # Shopping & Electronics (16)
    ("Amazon India", "amazon", "Shopping", ["amazonpay@apl", "AMZN MKTP IN MUMBAI", "AMAZON SELLER SERVICES"]),
    ("Flipkart", "flipkart", "Shopping", ["flipkart@axis", "FLIPKART INDIA PVT", "FLIPKART INTERNET"]),
    ("Myntra", "myntra", "Shopping", ["myntra@icici", "MYNTRA DESIGNS PVT", "MYNTRA FASHION"]),
    ("Ajio", "ajio", "Shopping", ["ajio@rbi", "RELIANCE RETAIL AJIO", "AJIO ONLINE"]),
    ("Zara", "zara", "Shopping", ["zara@hdfc", "INDITEX TRENTA ZARA", "ZARA RETAIL"]),
    ("Uniqlo", "uniqlo", "Shopping", ["uniqlo@icici", "UNIQLO INDIA PVT", "UNIQLO STORE"]),
    ("H&M", "hnm", "Shopping", ["hnm@hdfc", "H AND M HENNES MAURITZ", "HM RETAIL STORE"]),
    ("Westside", "westside", "Shopping", ["westside@tata", "TRENT LIMITED WESTSIDE"]),
    ("Marks & Spencer", "marks-spencer", "Shopping", ["mns@hdfc", "MARKS AND SPENCER RELIANCE"]),
    ("Decathlon", "decathlon", "Shopping", ["decathlon@icici", "DECATHLON SPORTS INDIA"]),
    ("Apple Store", "apple", "Electronics", ["apple@icici", "APPLE STORE MUMBAI", "APPLE INDIA PVT"]),
    ("Croma", "croma", "Electronics", ["croma@tata", "INFINITI RETAIL CROMA", "CROMA ELECTRONICS"]),
    ("Reliance Digital", "reliance-digital", "Electronics", ["reliancedigital@rbi", "RELIANCE RETAIL DIGITAL"]),
    ("Vijay Sales", "vijay-sales", "Electronics", ["vijaysales@kotak", "VIJAY SALES ELECTRONICS"]),
    ("IKEA India", "ikea", "Shopping", ["ikea@icici", "INGKA CENTRES IKEA", "IKEA NAGASANDRA"]),
    ("Fabindia", "fabindia", "Shopping", ["fabindia@axis", "FABINDIA OVERSEAS"]),

    # Travel & Transport (14)
    ("Uber", "uber", "Travel & Transport", ["uber@icici", "UBER INDIA SYSTEMS", "UBER TRIP BLR"]),
    ("Ola Cabs", "ola", "Travel & Transport", ["ola@axis", "ANI TECHNOLOGIES OLA", "OLA CABS RIDE"]),
    ("Rapido Bike Taxi", "rapido", "Travel & Transport", ["rapido@icici", "ROPPEN TRANSPORT RAPIDO"]),
    ("Namma Metro", "namma-metro", "Travel & Transport", ["bmrcl@sbi", "BANGALORE METRO RAIL", "NAMMA METRO CARD"]),
    ("Delhi Metro DMRC", "delhi-metro", "Travel & Transport", ["dmrc@sbi", "DELHI METRO SMART CARD"]),
    ("MakeMyTrip", "makemytrip", "Travel & Vacation", ["mmt@hdfc", "MAKEMYTRIP INDIA PVT", "MMT FLIGHTS"]),
    ("IRCTC", "irctc", "Travel & Transport", ["irctc@sbi", "IRCTC TICKETING SERVICE", "INDIAN RAILWAYS"]),
    ("IndiGo Airlines", "indigo", "Travel & Vacation", ["indigo@hdfc", "INTERGLOBE AVIATION", "INDIGO TICKETING"]),
    ("Air India", "air-india", "Travel & Vacation", ["airindia@sbi", "AIR INDIA LIMITED TICKETING"]),
    ("HP Petrol Pump", "hp-petrol", "Travel & Transport", ["hppcl@sbi", "HPCL RETAIL OUTLET", "HINDUSTAN PETROLEUM"]),
    ("Indian Oil Petrol", "ioc-petrol", "Travel & Transport", ["ioc@sbi", "INDIAN OIL CORP", "IOCL PETROL BUNK"]),
    ("Bharat Petroleum", "bpcl-petrol", "Travel & Transport", ["bpcl@sbi", "BPCL PETROL PUMP BLR"]),
    ("Fastag Toll", "fastag", "Travel & Transport", ["netc.fastag@icici", "IHMCL FASTAG TOLL", "NHAI TOLL PLAZA"]),
    ("Goibibo", "goibibo", "Travel & Vacation", ["goibibo@axis", "IBIBO GROUP PRIVATE"]),

    # Utilities, Housing & Services (16)
    ("BESCOM Bangalore", "bescom", "Utilities", ["bescom@sbi", "BANGALORE ELECTRICITY", "BESCOM POWER BILL"]),
    ("Tata Power", "tata-power", "Utilities", ["tatapower@icici", "TATA POWER BILL PAYMENT"]),
    ("Adani Electricity", "adani-power", "Utilities", ["adani@hdfc", "ADANI ELECTRICITY MUMBAI"]),
    ("Airtel Broadband", "airtel", "Utilities", ["airtel@kotak", "BHARTI AIRTEL LIMITED", "AIRTEL FIBER"]),
    ("Jio Fiber", "jio", "Utilities", ["jio@icici", "RELIANCE JIO INFOCOMM", "JIO FIBER BROADBAND"]),
    ("Indraprastha Gas", "igl", "Utilities", ["igl@sbi", "INDRAPRASTHA GAS LTD", "IGL PNG BILL"]),
    ("Bharat Gas LPG", "bharat-gas", "Utilities", ["bharatgas@sbi", "BPCL LPG CYLINDER REFILL"]),
    ("House Owner Rent", "house-rent", "Housing & Rent", ["rentowner@icici", "NEFT-HOUSE RENT", "OWNER PROPERTY RENT"]),
    ("NoBroker Maintenance", "nobroker", "Housing & Rent", ["nobroker@hdfc", "NOBROKER HOOD SOCIETY BILL"]),
    ("MyGate Maintenance", "mygate", "Housing & Rent", ["mygate@icici", "VIVISH TECHNOLOGIES MYGATE"]),
    ("Urban Company", "urban-company", "Personal Care", ["urbancompany@icici", "URBAN CLAP TECHNOLOGIES"]),
    ("Naturals Salon", "naturals-salon", "Personal Care", ["naturals@hdfc", "NATURALS BEAUTY CARE"]),
    ("Enrich Salon", "enrich-salon", "Personal Care", ["enrich@axis", "ENRICH BEAUTY SERVICES"]),
    ("Delhi Jal Board", "djb-water", "Utilities", ["djb@sbi", "DELHI JAL BOARD WATER BILL"]),
    ("BWSSB Water Board", "bwssb-water", "Utilities", ["bwssb@sbi", "BANGALORE WATER BOARD"]),
    ("ACT Fibernet", "act-fibernet", "Utilities", ["act@hdfc", "ATRIA CONVERGENCE TECH"]),

    # Subscriptions & Entertainment (12)
    ("Netflix", "netflix", "Subscriptions", ["netflix@hdfc", "NETFLIX ENTERTAINMENT", "NETFLIX INDIA"]),
    ("Spotify India", "spotify", "Subscriptions", ["spotify@icici", "SPOTIFY AB SWEDEN", "SPOTIFY PREMIUM"]),
    ("Disney+ Hotstar", "hotstar", "Subscriptions", ["hotstar@hdfc", "NOVI DIGITAL HOTSTAR", "DISNEY HOTSTAR VIP"]),
    ("YouTube Premium", "youtube", "Subscriptions", ["googlepay@axis", "GOOGLE YOUTUBE PREMIUM", "GOOGLE PLAY"]),
    ("Amazon Prime", "amazon-prime", "Subscriptions", ["amazonprime@apl", "AMAZON PRIME SUBSCRIPTION"]),
    ("Apple Services", "apple-services", "Subscriptions", ["applebill@apple", "APPLE SERVICES ITUNES STORE"]),
    ("BookMyShow", "bookmyshow", "Entertainment", ["bms@icici", "BIGTREE ENTERTAINMENT", "BOOKMYSHOW CINEMA"]),
    ("PVR Cinemas", "pvr", "Entertainment", ["pvr@kotak", "PVR INOX LIMITED", "PVR CINEMAS BLR"]),
    ("INOX Leisure", "inox", "Entertainment", ["inox@hdfc", "INOX LEISURE MULTIPLEX"]),
    ("Sony LIV", "sonyliv", "Subscriptions", ["sonyliv@icici", "CULVER MAX SONYLIV"]),
    ("Zee5 Premium", "zee5", "Subscriptions", ["zee5@axis", "ZEE ENTERTAINMENT ZEE5"]),
    ("Audible India", "audible", "Subscriptions", ["audible@amazon", "AUDIBLE AUDIOBOOKS"]),

    # Health, Fitness & Education (12)
    ("Cult.fit", "cultfit", "Health & Fitness", ["cult@hdfc", "CUREFIT HEALTHCARE", "CULT GYM MEMBERSHIP"]),
    ("Apollo Pharmacy", "apollo-pharmacy", "Health & Fitness", ["apollo@icici", "APOLLO HOSPITALS ENT", "APOLLO PHARMACY"]),
    ("1mg Healthcare", "tata-1mg", "Health & Fitness", ["tata1mg@axis", "1MG TECHNOLOGIES", "TATA 1MG PHARMA"]),
    ("Pharmeasy", "pharmeasy", "Health & Fitness", ["pharmeasy@icici", "AXELIA SOLUTIONS PHARMEASY"]),
    ("Max Healthcare", "max-health", "Health & Fitness", ["maxhealth@hdfc", "MAX HEALTHCARE INSTITUTE"]),
    ("Fortis Hospital", "fortis", "Health & Fitness", ["fortis@sbi", "FORTIS HEALTHCARE HOSP"]),
    ("Manipal Hospital", "manipal", "Health & Fitness", ["manipal@icici", "MANIPAL HEALTH ENTERPRISES"]),
    ("Gold Gym", "golds-gym", "Health & Fitness", ["goldsgym@kotak", "GOLDS GYM FITNESS BLR"]),
    ("Coursera", "coursera", "Education", ["coursera@icici", "COURSERA INC LEARNING"]),
    ("Udemy India", "udemy", "Education", ["udemy@hdfc", "UDEMY ONLINE COURSES"]),
    ("Unacademy", "unacademy", "Education", ["unacademy@axis", "SORTING HAT TECH UNACADEMY"]),
    ("Byjus Classes", "byjus", "Education", ["byjus@sbi", "THINK AND LEARN BYJUS"]),

    # Financial, Investments & Tech Subscriptions (14)
    ("Zerodha Broking", "zerodha", "Investments & Savings", ["zerodha@hdfcbank", "ZERODHA BROKING LTD", "ZERODHA FUND"]),
    ("Groww Invest", "groww", "Investments & Savings", ["groww@icici", "NEXTBILLION TECH GROWW", "GROWW MUTUAL FUND"]),
    ("HDFC Mutual Fund", "hdfc-mf", "Investments & Savings", ["hdfcmf@hdfc", "HDFC ASSET MANAGEMENT", "HDFC MF SIP"]),
    ("ICICI Prudential", "icici-pru", "Investments & Savings", ["icicipru@icici", "ICICI PRUDENTIAL MF", "ICICI PRU LIFE"]),
    ("PPF Public Fund", "ppf-deposit", "Investments & Savings", ["ppf@sbi", "SBI PUBLIC PROVIDENT FUND", "PPF TRANSFER"]),
    ("NPS National Pension", "nps-trust", "Investments & Savings", ["nps@nsdl", "NATIONAL PENSION SYSTEM"]),
    ("GitHub Pro", "github", "Office & Business", ["github@stripe", "GITHUB INC SUBSCRIPTION"]),
    ("OpenAI ChatGPT", "openai", "Office & Business", ["openai@stripe", "OPENAI CHATGPT PLUS"]),
    ("Amazon Web Services", "aws", "Office & Business", ["aws@amazon", "AMAZON WEB SERVICES CLOUD"]),
    ("Vercel Inc", "vercel", "Office & Business", ["vercel@stripe", "VERCEL PLATFORM HOSTING"]),
    ("JetBrains", "jetbrains", "Office & Business", ["jetbrains@card", "JETBRAINS IDE TOOLS"]),
    ("Figma Inc", "figma", "Office & Business", ["figma@stripe", "FIGMA DESIGN SUBSCRIPTION"]),
    ("ClearTax India", "cleartax", "Financial & Tax", ["cleartax@icici", "DEFmacro SOFTWARE CLEARTAX"]),
    ("LIC Insurance", "lic-india", "Financial & Tax", ["lic@sbi", "LIFE INSURANCE CORP OF INDIA"]),

    # Income Sources (8)
    ("Infosys Technologies", "infosys", "Income", ["INFOSYS LTD SALARY", "INF/INB/Salary Credited"]),
    ("TCS e-Serve", "tcs", "Income", ["TATA CONSULTANCY SERVICES", "TCS SALARY CR"]),
    ("Microsoft India", "microsoft", "Income", ["MICROSOFT INDIA R&D", "MSFT SALARY ACC"]),
    ("Razorpay Software", "razorpay-employer", "Income", ["RAZORPAY SOFTWARE SALARY", "RZP PAYROLL"]),
    ("Google India", "google-employer", "Income", ["GOOGLE INDIA PVT LTD", "GOOGLE PAYROLL CR"]),
    ("Wipro Technologies", "wipro", "Income", ["WIPRO LIMITED SALARY", "WIPRO PAYROLL"]),
    ("Freelance Client US", "freelance-client-us", "Income", ["WIRE TRANSFER/UPWORK INC", "CLIENT STRIPE PAY"]),
    ("Consulting Retainer", "consulting-client", "Income", ["NEFT/CONSULTING RETAINER", "TECH ADVISORY FEE"]),
]

PERSONA_SPECS = [
    # 5 Students: low budget, UPI heavy, food/chai/canteen, irregular stipend/pocket money
    {"name": "Rohan Verma", "persona": "student", "income_mode": "pocket_money", "monthly_income": 15000, "txn_rate": 55, "banks": ["SBI"]},
    {"name": "Priya Sharma", "persona": "student", "income_mode": "stipend", "monthly_income": 20000, "txn_rate": 60, "banks": ["HDFC"]},
    {"name": "Ananya Roy", "persona": "student", "income_mode": "pocket_money", "monthly_income": 18000, "txn_rate": 52, "banks": ["ICICI"]},
    {"name": "Aditya Patel", "persona": "student", "income_mode": "stipend", "monthly_income": 22000, "txn_rate": 65, "banks": ["Kotak"]},
    {"name": "Neha Joshi", "persona": "student", "income_mode": "pocket_money", "monthly_income": 16000, "txn_rate": 58, "banks": ["SBI"]},

    # 4 Young Professionals: mid salary, rent, dining, shopping, Uber, movies
    {"name": "Aarav Mehta", "persona": "young_professional", "income_mode": "salary", "monthly_income": 85000, "txn_rate": 53, "banks": ["HDFC", "SBI"]},
    {"name": "Sneha Iyer", "persona": "young_professional", "income_mode": "salary", "monthly_income": 95000, "txn_rate": 70, "banks": ["ICICI", "Axis"]},
    {"name": "Vikram Rao", "persona": "young_professional", "income_mode": "salary", "monthly_income": 78000, "txn_rate": 62, "banks": ["HDFC"]},
    {"name": "Tanvi Deshmukh", "persona": "young_professional", "income_mode": "salary", "monthly_income": 90000, "txn_rate": 68, "banks": ["Axis", "Kotak"]},

    # 4 Salaried Professionals: high stable salary, SIPs, family groceries, school/utilities
    {"name": "Kavita Nair", "persona": "salaried_professional", "income_mode": "salary", "monthly_income": 145000, "txn_rate": 78, "banks": ["HDFC", "ICICI"]},
    {"name": "Rajesh Gupta", "persona": "salaried_professional", "income_mode": "salary", "monthly_income": 175000, "txn_rate": 84, "banks": ["SBI", "HDFC"]},
    {"name": "Meera Sundaram", "persona": "salaried_professional", "income_mode": "salary", "monthly_income": 160000, "txn_rate": 76, "banks": ["ICICI"]},
    {"name": "Amit Saxena", "persona": "salaried_professional", "income_mode": "salary", "monthly_income": 190000, "txn_rate": 88, "banks": ["Axis", "SBI"]},

    # 3 High Spenders: high discretionary, gadgets, luxury dining, business travel
    {"name": "Siddharth Malhotra", "persona": "high_spender", "income_mode": "salary", "monthly_income": 320000, "txn_rate": 96, "banks": ["HDFC", "ICICI", "Axis"]},
    {"name": "Alok Singhania", "persona": "high_spender", "income_mode": "salary", "monthly_income": 380000, "txn_rate": 105, "banks": ["Kotak", "HDFC"]},
    {"name": "Natasha Kapoor", "persona": "high_spender", "income_mode": "salary", "monthly_income": 350000, "txn_rate": 92, "banks": ["Axis", "ICICI"]},

    # 2 Freelancers: variable multi-inflows, tech tools, coffee shops, irregular timing
    {"name": "Kabir Sen", "persona": "freelancer", "income_mode": "irregular", "monthly_income": 110000, "txn_rate": 68, "banks": ["ICICI", "Kotak"]},
    {"name": "Ishaan Verma", "persona": "freelancer", "income_mode": "irregular", "monthly_income": 125000, "txn_rate": 72, "banks": ["HDFC"]},

    # 2 High Savers: low discretionary spend, automated SIPs, frugal living
    {"name": "Pooja Kulkarni", "persona": "high_saver", "income_mode": "salary", "monthly_income": 115000, "txn_rate": 45, "banks": ["SBI", "HDFC"]},
    {"name": "Devendra Parekh", "persona": "high_saver", "income_mode": "salary", "monthly_income": 130000, "txn_rate": 48, "banks": ["ICICI"]},
]

def generate_corpus():
    print(f"Generating comprehensive synthetic financial corpus...")
    users_data = []
    accounts_data = []
    merchants_data = []
    merchant_aliases_data = []
    transactions_data = []
    links_data = []
    budgets_data = []
    goals_data = []
    bills_data = []
    anomalies_data = []
    voice_eval_data = []

    # 1. Build Merchants and Aliases
    merchant_map = {}
    for canonical_name, slug, default_cat, aliases in MERCHANTS_MASTER:
        m_id = str(uuid.uuid4())
        merchant_map[canonical_name] = {
            "id": m_id,
            "name": canonical_name,
            "slug": slug,
            "category": default_cat,
            "aliases": aliases
        }
        merchants_data.append({
            "id": m_id,
            "canonical_name": canonical_name,
            "normalized_key": slug,
            "default_category_slug": default_cat.lower().replace(" ", "-").replace("&", "")
        })
        for alias in aliases:
            merchant_aliases_data.append({
                "id": str(uuid.uuid4()),
                "merchant_id": m_id,
                "alias_pattern": alias,
                "match_type": "contains",
                "priority": 10
            })

    # 2. Iterate Personas and Generate Complete Relational Data
    for p_idx, p in enumerate(PERSONA_SPECS):
        is_primary = (p["name"] == "Aarav Mehta")
        user_id = str(uuid.uuid4())
        email = f"{p['name'].lower().replace(' ', '.')}@example.com"
        users_data.append({
            "id": user_id,
            "email": email,
            "password_hash": "pbkdf2_sha256$260000$dummy$hash",
            "display_name": p["name"],
            "preferred_language": "en",
            "base_currency": "INR",
            "persona_type": p["persona"],
            "is_active": True,
            "is_primary_demo": is_primary
        })

        # Generate Bank Accounts
        user_accounts = []
        for b_idx, b_name in enumerate(p["banks"]):
            acc_id = str(uuid.uuid4())
            acc_type = "savings" if b_idx == 0 else "credit_card"
            mask = str(random.randint(1000, 9999))
            opening_bal = random.randint(25000, 150000) * 100
            user_accounts.append({
                "id": acc_id,
                "user_id": user_id,
                "institution_name": b_name,
                "account_label": f"{b_name} {'Primary' if b_idx == 0 else 'Secondary'}",
                "account_type": acc_type,
                "account_mask": mask,
                "currency": "INR",
                "balance_minor": opening_bal,
                "is_connected": True
            })
            accounts_data.append(user_accounts[-1])

        # Generate Budgets (5 to 7 per user)
        budget_categories = ["Food & Dining", "Groceries", "Shopping", "Travel & Transport", "Entertainment", "Utilities"]
        for cat in budget_categories:
            multiplier = 0.5 if p["persona"] == "student" else (2.0 if p["persona"] == "high_spender" else 1.0)
            base_limit = random.randint(3000, 12000) * 100
            budgets_data.append({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "category_name": cat,
                "limit_minor": int(base_limit * multiplier),
                "period": "monthly",
                "alert_threshold_pct": 80.0
            })

        # Generate Savings Goals (1 to 2 per user)
        goal_titles = [("Emergency Fund", 30000000), ("Dream Vacation", 15000000), ("New MacBook Pro", 18000000), ("Car Down Payment", 40000000)]
        chosen_goals = random.sample(goal_titles, k=random.randint(1, 2))
        for g_title, g_target in chosen_goals:
            current_pct = random.uniform(0.15, 0.75)
            goals_data.append({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "name": g_title,
                "target_amount_minor": g_target,
                "current_amount_minor": int(g_target * current_pct),
                "currency": "INR",
                "color_hex": "#06B6D4",
                "target_date": "2025-12-31",
                "status": "active"
            })

        # Generate Recurring Payments (Bills & Subscriptions)
        bills_specs = [
            ("Airtel Broadband Fiber", "Utilities", 117900, "5th of month"),
            ("Netflix Standard Subscription", "Subscriptions", 64900, "12th of month"),
            ("Spotify Premium Family", "Subscriptions", 17900, "18th of month"),
            ("Cultfit Gym Membership", "Health & Fitness", 250000, "1st of month"),
            ("Bescom Electricity Bill", "Utilities", 185000, "20th of month"),
        ]
        user_bill_count = 3 if p["persona"] == "student" else len(bills_specs)
        for b_name, b_cat, b_amt, b_due in bills_specs[:user_bill_count]:
            bills_data.append({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "name": b_name,
                "category_name": b_cat,
                "amount_minor": b_amt,
                "currency": "INR",
                "due_date_str": b_due,
                "days_left": random.randint(1, 28),
                "auto_pay": True,
                "status": "scheduled"
            })

        # Generate 12 Months of Transactions
        primary_acc = user_accounts[0]
        secondary_acc = user_accounts[1] if len(user_accounts) > 1 else primary_acc

        # Generate recurring monthly income
        current_dt = START_DATE
        while current_dt <= END_DATE:
            # Monthly Inflow
            if p["income_mode"] == "salary" and current_dt.day == 1:
                amt = p["monthly_income"] * 100
                txn_id = str(uuid.uuid4())
                transactions_data.append({
                    "id": txn_id,
                    "user_id": user_id,
                    "account_id": primary_acc["id"],
                    "transaction_date": current_dt.isoformat(),
                    "merchant_name": "Infosys Technologies" if p_idx % 2 == 0 else "Microsoft India",
                    "category_name": "Income",
                    "amount_minor": amt,
                    "currency": "INR",
                    "transaction_kind": "income",
                    "payment_mode": "NEFT",
                    "description_original": f"SALARY CREDITED FOR {current_dt.strftime('%B %Y').upper()}",
                    "is_internal_transfer": False,
                    "is_anomaly": False,
                    "anomaly_reason": None
                })
            elif p["income_mode"] == "pocket_money" and current_dt.day in (1, 15):
                amt = (p["monthly_income"] // 2) * 100
                transactions_data.append({
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "account_id": primary_acc["id"],
                    "transaction_date": current_dt.isoformat(),
                    "merchant_name": "Parent UPI Transfer",
                    "category_name": "Income",
                    "amount_minor": amt,
                    "currency": "INR",
                    "transaction_kind": "income",
                    "payment_mode": "UPI",
                    "description_original": "UPI/Pocket Money Monthly Support",
                    "is_internal_transfer": False,
                    "is_anomaly": False,
                    "anomaly_reason": None
                })
            elif p["income_mode"] == "irregular" and current_dt.day in (8, 22):
                amt = random.randint(35000, 65000) * 100
                transactions_data.append({
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "account_id": primary_acc["id"],
                    "transaction_date": current_dt.isoformat(),
                    "merchant_name": "Freelance Client US",
                    "category_name": "Income",
                    "amount_minor": amt,
                    "currency": "INR",
                    "transaction_kind": "income",
                    "payment_mode": "WIRE",
                    "description_original": f"WIRE TRANSFER INVOICE #{random.randint(100, 999)}",
                    "is_internal_transfer": False,
                    "is_anomaly": False,
                    "anomaly_reason": None
                })

            # Internal Account Transfer (Scenario 10) once every 2 months if multi-account
            if len(user_accounts) > 1 and current_dt.day == 5 and current_dt.month % 2 == 0:
                t_amt = random.randint(5000, 15000) * 100
                debit_id = str(uuid.uuid4())
                credit_id = str(uuid.uuid4())
                transactions_data.append({
                    "id": debit_id,
                    "user_id": user_id,
                    "account_id": primary_acc["id"],
                    "transaction_date": current_dt.isoformat(),
                    "merchant_name": f"Transfer to {secondary_acc['institution_name']}",
                    "category_name": "Internal Transfer",
                    "amount_minor": -t_amt,
                    "currency": "INR",
                    "transaction_kind": "transfer",
                    "payment_mode": "IMPS",
                    "description_original": f"IMPS OUT TO SELF {secondary_acc['account_mask']}",
                    "is_internal_transfer": True,
                    "is_anomaly": False,
                    "anomaly_reason": None
                })
                transactions_data.append({
                    "id": credit_id,
                    "user_id": user_id,
                    "account_id": secondary_acc["id"],
                    "transaction_date": current_dt.isoformat(),
                    "merchant_name": f"Transfer from {primary_acc['institution_name']}",
                    "category_name": "Internal Transfer",
                    "amount_minor": t_amt,
                    "currency": "INR",
                    "transaction_kind": "transfer",
                    "payment_mode": "IMPS",
                    "description_original": f"IMPS IN FROM SELF {primary_acc['account_mask']}",
                    "is_internal_transfer": True,
                    "is_anomaly": False,
                    "anomaly_reason": None
                })
                links_data.append({
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "from_transaction_id": debit_id,
                    "to_transaction_id": credit_id,
                    "link_type": "transfer_pair"
                })

            current_dt += timedelta(days=1)

        # Discretionary Expenses calibrated to reach 16,500 total txns across 20 users
        total_days = (END_DATE - START_DATE).days
        target_txns = 632 if is_primary else int(p["txn_rate"] * 12)
        
        # Select merchants appropriate for persona
        if p["persona"] == "student":
            valid_merchants = [m for m in MERCHANTS_MASTER if m[2] in ("Food & Dining", "Groceries", "Travel & Transport", "Entertainment", "Subscriptions")]
        elif p["persona"] == "high_spender":
            valid_merchants = [m for m in MERCHANTS_MASTER if m[2] not in ("Income", "Internal Transfer")]
        else:
            valid_merchants = [m for m in MERCHANTS_MASTER if m[2] not in ("Income", "Internal Transfer")]

        curr_user_txns = len([t for t in transactions_data if t["user_id"] == user_id])
        needed_discretionary = max(0, target_txns - curr_user_txns)

        for _ in range(needed_discretionary):
            rand_day_offset = random.randint(0, total_days)
            txn_date = START_DATE + timedelta(days=rand_day_offset)
            m_tuple = random.choice(valid_merchants)
            m_name, m_slug, m_cat, m_aliases = m_tuple
            chosen_alias = random.choice(m_aliases)

            # Amounts calibrated to category and persona
            if m_cat == "Food & Dining":
                base_amt = random.randint(80, 850) if p["persona"] == "student" else random.randint(250, 2200)
            elif m_cat == "Groceries":
                base_amt = random.randint(200, 1500) if p["persona"] == "student" else random.randint(800, 5500)
            elif m_cat == "Shopping":
                base_amt = random.randint(499, 2500) if p["persona"] == "student" else random.randint(1500, 12000)
            elif m_cat == "Travel & Transport":
                base_amt = random.randint(30, 250) if p["persona"] == "student" else random.randint(150, 1200)
            elif m_cat == "Electronics":
                base_amt = random.randint(1200, 8500) if p["persona"] == "student" else random.randint(8000, 65000)
            else:
                base_amt = random.randint(150, 1500)

            if p["persona"] == "high_spender":
                base_amt = int(base_amt * 2.8)

            amt_minor = -abs(base_amt * 100)
            account_id = primary_acc["id"] if (len(user_accounts) == 1 or random.random() < 0.75) else secondary_acc["id"]

            t_id = str(uuid.uuid4())
            transactions_data.append({
                "id": t_id,
                "user_id": user_id,
                "account_id": account_id,
                "transaction_date": txn_date.isoformat(),
                "merchant_name": m_name,
                "category_name": m_cat,
                "amount_minor": amt_minor,
                "currency": "INR",
                "transaction_kind": "expense",
                "payment_mode": "UPI" if abs(amt_minor) < 500000 else "Card",
                "description_original": f"UPI/DR/{random.randint(500000000000, 599999999999)}/{chosen_alias}",
                "is_internal_transfer": False,
                "is_anomaly": False,
                "anomaly_reason": None
            })

        # Inject Explicit Labelled Scenarios & Anomalies (12 to 15 per user)
        # Scenario 3: Large one-time purchase
        huge_purchase_date = date(2024, 10, 25)
        huge_t_id = str(uuid.uuid4())
        transactions_data.append({
            "id": huge_t_id,
            "user_id": user_id,
            "account_id": primary_acc["id"],
            "transaction_date": huge_purchase_date.isoformat(),
            "merchant_name": "Apple Store",
            "category_name": "Electronics",
            "amount_minor": -12990000,  # ₹1,29,900
            "currency": "INR",
            "transaction_kind": "expense",
            "payment_mode": "Card",
            "description_original": "POS 401234XXXXXX1234 APPLE STORE MUMBAI",
            "is_internal_transfer": False,
            "is_anomaly": True,
            "anomaly_reason": "Single transaction amount is 8.4x higher than 90-day moving average"
        })
        anomalies_data.append({
            "id": str(uuid.uuid4()),
            "scenario_id": "SCENARIO_03_LARGE_PURCHASE",
            "user_id": user_id,
            "transaction_id": huge_t_id,
            "anomaly_type": "amount_spike",
            "severity": "high",
            "score": 0.94,
            "reason": "Single transaction amount ₹1,29,900 is 8.4x higher than user average",
            "status": "open",
            "created_at": "2024-10-25T14:30:00Z"
        })

        # Scenario 4: Duplicate transaction candidate
        dup_date = date(2024, 11, 14)
        dup_amt = -149900
        for i in range(2):
            d_id = str(uuid.uuid4())
            transactions_data.append({
                "id": d_id,
                "user_id": user_id,
                "account_id": primary_acc["id"],
                "transaction_date": dup_date.isoformat(),
                "merchant_name": "Cult.fit",
                "category_name": "Health & Fitness",
                "amount_minor": dup_amt,
                "currency": "INR",
                "transaction_kind": "expense",
                "payment_mode": "UPI",
                "description_original": f"UPI/50148291029{i}/CUREFIT HEALTHCARE/cult@hdfc",
                "is_internal_transfer": False,
                "is_anomaly": (i == 1),
                "anomaly_reason": "Duplicate transaction detected within 3 minutes for identical amount" if (i == 1) else None
            })
            if i == 1:
                anomalies_data.append({
                    "id": str(uuid.uuid4()),
                    "scenario_id": "SCENARIO_04_DUPLICATE_TXN",
                    "user_id": user_id,
                    "transaction_id": d_id,
                    "anomaly_type": "duplicate_candidate",
                    "severity": "medium",
                    "score": 0.88,
                    "reason": "Identical amount ₹1,499 billed twice at Cult.fit within minutes",
                    "status": "open",
                    "created_at": "2024-11-14T08:04:12Z"
                })

        # Scenario 9: Refund after purchase
        ref_purchase_date = date(2024, 8, 10)
        ref_date = date(2024, 8, 12)
        ref_amt = 345000
        orig_p_id = str(uuid.uuid4())
        ref_id = str(uuid.uuid4())
        transactions_data.append({
            "id": orig_p_id,
            "user_id": user_id,
            "account_id": primary_acc["id"],
            "transaction_date": ref_purchase_date.isoformat(),
            "merchant_name": "Amazon India",
            "category_name": "Shopping",
            "amount_minor": -ref_amt,
            "currency": "INR",
            "transaction_kind": "expense",
            "payment_mode": "Card",
            "description_original": "AMZN MKTP IN MUMBAI ORDER #402-91823-19",
            "is_internal_transfer": False,
            "is_anomaly": False,
            "anomaly_reason": None
        })
        transactions_data.append({
            "id": ref_id,
            "user_id": user_id,
            "account_id": primary_acc["id"],
            "transaction_date": ref_date.isoformat(),
            "merchant_name": "Amazon India",
            "category_name": "Shopping",
            "amount_minor": ref_amt,
            "currency": "INR",
            "transaction_kind": "refund",
            "payment_mode": "Card",
            "description_original": "REFUND/AMZN MKTP IN MUMBAI ORDER #402-91823-19",
            "is_internal_transfer": False,
            "is_anomaly": False,
            "anomaly_reason": None
        })
        links_data.append({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "from_transaction_id": orig_p_id,
            "to_transaction_id": ref_id,
            "link_type": "refund_link"
        })

        # Scenario 5: Subscription price hike anomaly
        sub_hike_date = date(2024, 9, 12)
        sub_hike_id = str(uuid.uuid4())
        transactions_data.append({
            "id": sub_hike_id,
            "user_id": user_id,
            "account_id": primary_acc["id"],
            "transaction_date": sub_hike_date.isoformat(),
            "merchant_name": "Netflix",
            "category_name": "Subscriptions",
            "amount_minor": -79900,  # Increased from ₹649 to ₹799
            "currency": "INR",
            "transaction_kind": "expense",
            "payment_mode": "Card",
            "description_original": "ACH/NETFLIX INDIA PVT LTD PREMIUM UPGRADE",
            "is_internal_transfer": False,
            "is_anomaly": True,
            "anomaly_reason": "Recurring payment increased by 23.1% compared to historical baseline"
        })
        anomalies_data.append({
            "id": str(uuid.uuid4()),
            "scenario_id": "SCENARIO_05_SUBSCRIPTION_HIKE",
            "user_id": user_id,
            "transaction_id": sub_hike_id,
            "anomaly_type": "recurring_price_hike",
            "severity": "low",
            "score": 0.76,
            "reason": "Netflix recurring charge increased from ₹649 to ₹799",
            "status": "resolved",
            "created_at": "2024-09-12T10:00:00Z"
        })

        # Additional Distinct Anomaly Scenarios (to reach 200+ labelled cases across corpus)
        # Scenario 11: Travel spike during festival season (Diwali / New Year)
        festival_date = date(2024, 11, 2)
        travel_spike_id = str(uuid.uuid4())
        transactions_data.append({
            "id": travel_spike_id,
            "user_id": user_id,
            "account_id": primary_acc["id"],
            "transaction_date": festival_date.isoformat(),
            "merchant_name": "MakeMyTrip",
            "category_name": "Travel & Vacation",
            "amount_minor": -4850000,
            "currency": "INR",
            "transaction_kind": "expense",
            "payment_mode": "Card",
            "description_original": "MMT*FLIGHT BOOKING DIWALI FESTIVAL",
            "is_internal_transfer": False,
            "is_anomaly": True,
            "anomaly_reason": "Travel spend spike 5.2x higher than normal quarterly travel baseline"
        })
        anomalies_data.append({
            "id": str(uuid.uuid4()),
            "scenario_id": "SCENARIO_11_FESTIVAL_TRAVEL_SPIKE",
            "user_id": user_id,
            "transaction_id": travel_spike_id,
            "anomaly_type": "seasonal_spike",
            "severity": "medium",
            "score": 0.82,
            "reason": "Diwali festival travel spend ₹48,500 exceeds normal quarterly travel baseline",
            "status": "resolved",
            "created_at": "2024-11-02T16:20:00Z"
        })

        # Scenario 2: Food spending velocity spike
        food_burst_dates = [date(2024, 12, 24), date(2024, 12, 25), date(2024, 12, 26)]
        for fb_idx, fb_d in enumerate(food_burst_dates):
            fb_id = str(uuid.uuid4())
            fb_amt = -random.randint(2800, 4500) * 100
            transactions_data.append({
                "id": fb_id,
                "user_id": user_id,
                "account_id": primary_acc["id"],
                "transaction_date": fb_d.isoformat(),
                "merchant_name": "Barbeque Nation",
                "category_name": "Food & Dining",
                "amount_minor": fb_amt,
                "currency": "INR",
                "transaction_kind": "expense",
                "payment_mode": "UPI",
                "description_original": "UPI/BARBEQUE NATION HOSPITALITY PARTY DINNER",
                "is_internal_transfer": False,
                "is_anomaly": (fb_idx == 2),
                "anomaly_reason": "Category velocity spike: Dining spend tripled over 72-hour window" if (fb_idx == 2) else None
            })
            if fb_idx == 2:
                anomalies_data.append({
                    "id": str(uuid.uuid4()),
                    "scenario_id": "SCENARIO_02_FOOD_DINING_SPIKE",
                    "user_id": user_id,
                    "transaction_id": fb_id,
                    "anomaly_type": "velocity_spike",
                    "severity": "medium",
                    "score": 0.85,
                    "reason": "Dining spend tripled over consecutive 3-day holiday period",
                    "status": "open",
                    "created_at": "2024-12-26T22:15:00Z"
                })

        # Scenario 13: Off-hours or ambiguous merchant charge
        amb_date = date(2025, 1, 18)
        amb_id = str(uuid.uuid4())
        transactions_data.append({
            "id": amb_id,
            "user_id": user_id,
            "account_id": primary_acc["id"],
            "transaction_date": amb_date.isoformat(),
            "merchant_name": "POS*UNKNOWN RETAIL MUMBAI",
            "category_name": "Miscellaneous",
            "amount_minor": -845000,
            "currency": "INR",
            "transaction_kind": "expense",
            "payment_mode": "Card",
            "description_original": "POS 0009182 MUMBAI TXN AUTH 03:42 AM",
            "is_internal_transfer": False,
            "is_anomaly": True,
            "anomaly_reason": "Unrecognized merchant location with transaction timestamp 03:42 AM"
        })
        anomalies_data.append({
            "id": str(uuid.uuid4()),
            "scenario_id": "SCENARIO_13_OFFHOURS_AMBIGUOUS",
            "user_id": user_id,
            "transaction_id": amb_id,
            "anomaly_type": "off_hours_charge",
            "severity": "high",
            "score": 0.91,
            "reason": "Late night charge ₹8,450 from unrecognized merchant at 03:42 AM",
            "status": "open",
            "created_at": "2025-01-18T03:42:00Z"
        })

        # Scenario 7: Budget threshold exceeded anomaly
        b_over_date = date(2025, 2, 10)
        b_over_id = str(uuid.uuid4())
        transactions_data.append({
            "id": b_over_id,
            "user_id": user_id,
            "account_id": primary_acc["id"],
            "transaction_date": b_over_date.isoformat(),
            "merchant_name": "Zara",
            "category_name": "Shopping",
            "amount_minor": -1850000,
            "currency": "INR",
            "transaction_kind": "expense",
            "payment_mode": "Card",
            "description_original": "POS 401234XXXXXX1234 ZARA RETAIL BANGALORE",
            "is_internal_transfer": False,
            "is_anomaly": True,
            "anomaly_reason": "Monthly shopping budget limit ₹15,000 exceeded (current spend: ₹22,400)"
        })
        anomalies_data.append({
            "id": str(uuid.uuid4()),
            "scenario_id": "SCENARIO_07_BUDGET_EXCEEDED",
            "user_id": user_id,
            "transaction_id": b_over_id,
            "anomaly_type": "budget_breach",
            "severity": "medium",
            "score": 0.84,
            "reason": "Shopping budget exceeded 149% of monthly limit following ₹18,500 Zara purchase",
            "status": "open",
            "created_at": "2025-02-10T19:05:00Z"
        })

        # Scenario 12: Foreign currency SaaS transaction
        saas_date = date(2025, 2, 14)
        saas_id = str(uuid.uuid4())
        transactions_data.append({
            "id": saas_id,
            "user_id": user_id,
            "account_id": primary_acc["id"],
            "transaction_date": saas_date.isoformat(),
            "merchant_name": "OpenAI ChatGPT",
            "category_name": "Office & Business",
            "amount_minor": -199900,
            "currency": "INR",
            "transaction_kind": "expense",
            "payment_mode": "Card",
            "description_original": "OPENAI *CHATGPT SUBSCRIPTION USD 20.00 FX MARKUP",
            "is_internal_transfer": False,
            "is_anomaly": True,
            "anomaly_reason": "International card transaction with foreign exchange markup"
        })
        anomalies_data.append({
            "id": str(uuid.uuid4()),
            "scenario_id": "SCENARIO_12_CROSS_BORDER_SAAS",
            "user_id": user_id,
            "transaction_id": saas_id,
            "anomaly_type": "cross_border_charge",
            "severity": "low",
            "score": 0.72,
            "reason": "USD SaaS subscription fee ₹1,999 with cross-border card billing",
            "status": "resolved",
            "created_at": "2025-02-14T11:00:00Z"
        })

        # Scenario 6: Unexpected freelance income spike / tax withholding
        tax_date = date(2024, 7, 15)
        tax_id = str(uuid.uuid4())
        transactions_data.append({
            "id": tax_id,
            "user_id": user_id,
            "account_id": primary_acc["id"],
            "transaction_date": tax_date.isoformat(),
            "merchant_name": "ClearTax India",
            "category_name": "Financial & Tax",
            "amount_minor": -3500000,
            "currency": "INR",
            "transaction_kind": "expense",
            "payment_mode": "NetBanking",
            "description_original": "ITR-V ADVANCE TAX CHALLAN 280 PAYMENT",
            "is_internal_transfer": False,
            "is_anomaly": True,
            "anomaly_reason": "Quarterly advance tax payment spike detected"
        })
        anomalies_data.append({
            "id": str(uuid.uuid4()),
            "scenario_id": "SCENARIO_06_ADVANCE_TAX_SPIKE",
            "user_id": user_id,
            "transaction_id": tax_id,
            "anomaly_type": "amount_spike",
            "severity": "low",
            "score": 0.70,
            "reason": "Quarterly income tax installment ₹35,000 paid via Challan 280",
            "status": "resolved",
            "created_at": "2024-07-15T15:30:00Z"
        })

        # Scenario 14: ATM withdrawal anomaly (High cash out)
        atm_date = date(2024, 12, 31)
        atm_id = str(uuid.uuid4())
        transactions_data.append({
            "id": atm_id,
            "user_id": user_id,
            "account_id": primary_acc["id"],
            "transaction_date": atm_date.isoformat(),
            "merchant_name": "HDFC Bank ATM",
            "category_name": "Miscellaneous",
            "amount_minor": -2500000,
            "currency": "INR",
            "transaction_kind": "expense",
            "payment_mode": "ATM",
            "description_original": "ATM WDL-HDFC ATM MG ROAD BLR CASH WITHDRAWAL",
            "is_internal_transfer": False,
            "is_anomaly": True,
            "anomaly_reason": "High-value cash withdrawal exceeding 3x normal ATM withdrawal limit"
        })
        anomalies_data.append({
            "id": str(uuid.uuid4()),
            "scenario_id": "SCENARIO_14_HIGH_CASH_WITHDRAWAL",
            "user_id": user_id,
            "transaction_id": atm_id,
            "anomaly_type": "cash_withdrawal_spike",
            "severity": "medium",
            "score": 0.81,
            "reason": "Large ATM cash withdrawal of ₹25,000 on New Year's Eve",
            "status": "open",
            "created_at": "2024-12-31T21:40:00Z"
        })

    # 3. Generate 120 Voice Evaluation Cases conforming to Section 12.8
    voice_templates = [
        ("How much did I spend on food last month?", "Food & Dining", "previous_calendar_month", "category_spending", "get_category_breakdown"),
        ("What is my total account balance right now?", None, "current", "total_balance", "get_account_balances"),
        ("Did I overspend on shopping this month?", "Shopping", "current_month", "budget_status", "get_budget_status"),
        ("Are there any suspicious charges or anomalies recently?", None, "recent_30_days", "anomalies", "get_recent_anomalies"),
        ("What bills are due this week?", None, "current_week", "upcoming_bills", "get_upcoming_bills"),
        ("How much have I saved toward my emergency fund?", "Emergency Fund", "all_time", "savings_goal", "get_savings_goals"),
        ("Project my cashflow for the next 3 months", None, "next_90_days", "cashflow_forecast", "get_cashflow_forecast"),
        ("What was my biggest expense in November 2024?", None, "2024-11", "largest_transaction", "get_largest_transactions"),
        ("How much did I spend on Swiggy and Zomato combined?", "Food & Dining", "current_month", "merchant_spending", "get_merchant_breakdown"),
        ("Can I afford to buy a ₹45,000 laptop next month?", None, "next_month", "affordability_check", "assess_affordability"),
        ("What is my overall financial health score?", None, "current", "health_score", "get_financial_health_score"),
        ("Show me all transactions above ₹10,000 in December", None, "2024-12", "filter_transactions", "get_filtered_transactions"),
    ]

    for v_idx in range(120):
        tmpl = voice_templates[v_idx % len(voice_templates)]
        voice_eval_data.append({
            "case_id": f"voice_{v_idx + 1:03d}",
            "utterance": tmpl[0],
            "language": "en",
            "expected_intent": tmpl[3],
            "expected_parameters": {
                "category": tmpl[1],
                "period": tmpl[2]
            },
            "expected_tool": tmpl[4],
            "expected_currency": "INR"
        })

    # 4. Sort Transactions Chronologically for Determinism
    transactions_data.sort(key=lambda t: (t["transaction_date"], t["id"]))

    # 5. Export Canonical CSV and JSONL Files
    print(f"Writing canonical files to {OUTPUT_DIR}...")
    
    def write_csv(filename: str, rows: List[dict]):
        if not rows:
            return
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    write_csv("users.csv", users_data)
    write_csv("bank_accounts.csv", accounts_data)
    write_csv("categories.csv", SYSTEM_CATEGORIES)
    write_csv("merchants.csv", merchants_data)
    write_csv("merchant_aliases.csv", merchant_aliases_data)
    write_csv("transactions.csv", transactions_data)
    write_csv("transaction_links.csv", links_data)
    write_csv("budgets.csv", budgets_data)
    write_csv("savings_goals.csv", goals_data)
    write_csv("recurring_payments.csv", bills_data)
    write_csv("anomaly_ground_truth.csv", anomalies_data)

    voice_path = os.path.join(OUTPUT_DIR, "voice_eval.jsonl")
    with open(voice_path, "w", encoding="utf-8") as f:
        for entry in voice_eval_data:
            f.write(json.dumps(entry) + "\n")

    # 6. Generate Manifest with SHA-256 Checksums
    checksums = {}
    for fname in os.listdir(OUTPUT_DIR):
        if fname == "manifest.json":
            continue
        fpath = os.path.join(OUTPUT_DIR, fname)
        if os.path.isfile(fpath):
            with open(fpath, "rb") as bf:
                checksums[fname] = hashlib.sha256(bf.read()).hexdigest()

    manifest = {
        "generator_version": "2.1.0",
        "random_seed": SEED,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date_range": {
            "start": START_DATE.isoformat(),
            "end": END_DATE.isoformat(),
            "total_days": TOTAL_DAYS
        },
        "entity_counts": {
            "users": len(users_data),
            "personas": len(PERSONA_SPECS),
            "bank_accounts": len(accounts_data),
            "categories": len(SYSTEM_CATEGORIES),
            "merchants": len(merchants_data),
            "merchant_aliases": len(merchant_aliases_data),
            "transactions": len(transactions_data),
            "transaction_links": len(links_data),
            "budgets": len(budgets_data),
            "savings_goals": len(goals_data),
            "recurring_payments": len(bills_data),
            "ground_truth_anomalies": len(anomalies_data),
            "voice_eval_cases": len(voice_eval_data)
        },
        "file_checksums_sha256": checksums
    }

    manifest_path = os.path.join(OUTPUT_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Synthetic corpus generation complete!")
    print(f"Summary:")
    for entity, count in manifest["entity_counts"].items():
        print(f"  - {entity}: {count}")

if __name__ == "__main__":
    generate_corpus()
