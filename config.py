import os

API_KEY = os.getenv("DART_API_KEY", "").strip()
COMPANY_NAME = "에스씨케이컴퍼니"
START_YEAR = 2010
REPORT_CODES = {
    "annual": "11011",
    "half-year": "11012",
    "quarterly-q1": "11013",
    "quarterly-q3": "11014",
}
BASE_URL = "https://opendart.fss.or.kr/api"
