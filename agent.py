from __future__ import annotations
import argparse, io, json, os, re, zipfile
from pathlib import Path
from typing import Dict, List, Any
import requests
import pandas as pd
from bs4 import BeautifulSoup
from config import API_KEY, COMPANY_NAME, REPORT_CODES, BASE_URL

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)


def api(path: str, params: dict, binary=False):
    if not API_KEY:
        raise RuntimeError("DART_API_KEY가 설정되지 않았습니다.")
    r = requests.get(f"{BASE_URL}/{path}", params={"crtfc_key": API_KEY, **params}, timeout=60)
    r.raise_for_status()
    return r.content if binary else r.json()


def corp_code() -> str:
    cache = RAW / "corp_code.txt"
    if cache.exists():
        return cache.read_text(encoding="utf-8").strip()
    content = api("corpCode.xml", {}, binary=True)
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        xml = z.read("CORPCODE.xml")
    soup = BeautifulSoup(xml, "xml")
    for item in soup.find_all("list"):
        name = item.corp_name.text.strip() if item.corp_name else ""
        if name == COMPANY_NAME:
            code = item.corp_code.text.strip()
            cache.write_text(code, encoding="utf-8")
            return code
    # historical name fallback
    for item in soup.find_all("list"):
        name = item.corp_name.text.strip() if item.corp_name else ""
        if "스타벅스커피코리아" in name:
            code = item.corp_code.text.strip()
            cache.write_text(code, encoding="utf-8")
            return code
    raise RuntimeError(f"기업 고유번호를 찾지 못했습니다: {COMPANY_NAME}")


def filings(code: str, year: int) -> List[dict]:
    # Filing search endpoint may return max 100 rows; company/year is tiny, so one call is sufficient.
    data = api("list.json", {"corp_code": code, "bgn_de": f"{year}0101", "end_de": f"{year}1231", "page_no": 1, "page_count": 100})
    if data.get("status") != "000":
        return []
    wanted = set(REPORT_CODES.values())
    rows = []
    for x in data.get("list", []):
        report = x.get("report_nm", "")
        if any(k in report for k in ["사업보고서", "반기보고서", "분기보고서"]):
            if x.get("rcept_no"):
                x["year"] = year
                rows.append(x)
    return rows


def save_original(rcept_no: str, year: int, report_name: str):
    outdir = RAW / str(year)
    outdir.mkdir(exist_ok=True)
    safe = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", report_name)
    path = outdir / f"{rcept_no}_{safe}.zip"
    if path.exists():
        return path
    content = api("document.xml", {"rcept_no": rcept_no}, binary=True)
    path.write_bytes(content)
    return path


def structured(code: str, year: int, reprt_code: str) -> List[dict]:
    out = []
    for fs_div in ("OFS", "CFS"):
        data = api("fnlttSinglAcntAll.json", {"corp_code": code, "bsns_year": str(year), "reprt_code": reprt_code, "fs_div": fs_div})
        if data.get("status") == "000":
            for row in data.get("list", []):
                row["fs_div"] = fs_div
                out.append(row)
            if out:
                break
    return out


def num(s):
    if s is None or str(s).strip() in ("", "-"):
        return None
    s = str(s).replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def standardize(rows: List[dict], year: int, period: str) -> List[dict]:
    # Prefer consolidated if available, otherwise separate.
    chosen = [r for r in rows if r.get("fs_div") == "CFS"] or rows
    aliases = {
        "revenue": ["매출액", "수익(매출액)"],
        "gross_profit": ["매출총이익"],
        "operating_income": ["영업이익", "영업이익(손실)"],
        "pretax_income": ["법인세비용차감전순이익", "법인세비용차감전순이익(손실)"],
        "net_income": ["당기순이익", "당기순이익(손실)"],
        "assets": ["자산총계"], "current_assets": ["유동자산"],
        "liabilities": ["부채총계"], "current_liabilities": ["유동부채"],
        "equity": ["자본총계"], "cash": ["현금및현금성자산", "현금및현금성자산(현금성자산 포함)"],
        "receivables": ["매출채권", "매출채권및기타채권"], "inventory": ["재고자산"],
        "accounts_payable": ["매입채무", "매입채무및기타채무"],
        "cfo": ["영업활동현금흐름", "영업활동으로 인한 현금흐름"],
        "cfi": ["투자활동현금흐름", "투자활동으로 인한 현금흐름"],
        "cff": ["재무활동현금흐름", "재무활동으로 인한 현금흐름"],
        "capex": ["유형자산의 취득", "유형자산 취득", "유형자산의 취득으로 인한 현금유출액"],
        "interest_expense": ["이자비용"],
        "ebitda": ["EBITDA"],
    }
    values = {k: None for k in aliases}
    for key, names in aliases.items():
        for r in chosen:
            nm = (r.get("account_nm") or "").strip()
            if nm in names:
                values[key] = num(r.get("thstrm_amount"))
                if period != "annual" and r.get("thstrm_add_amount") not in (None, ""):
                    values[key] = num(r.get("thstrm_add_amount"))
                break
    values.update({"year": year, "period": period, "fs_div": chosen[0].get("fs_div") if chosen else None})
    return [values]



def legacy_extract_zip(zip_path: Path, year: int, period: str) -> dict:
    """Best-effort extraction for pre-2015 reports where structured XBRL API is unavailable.
    It scans DART's original XML tables and maps common Korean account labels to numeric cells.
    Raw ZIP remains the audit source when a legacy row cannot be mapped confidently.
    """
    aliases = {
        "revenue": ["매출액", "수익(매출액)"], "gross_profit": ["매출총이익"],
        "operating_income": ["영업이익", "영업이익(손실)"],
        "pretax_income": ["법인세비용차감전순이익", "법인세비용차감전순이익(손실)"],
        "net_income": ["당기순이익", "당기순이익(손실)"], "assets": ["자산총계"],
        "current_assets": ["유동자산"], "liabilities": ["부채총계"],
        "current_liabilities": ["유동부채"], "equity": ["자본총계"],
        "cash": ["현금및현금성자산", "현금및현금성자산(현금성자산 포함)"],
        "receivables": ["매출채권", "매출채권및기타채권"], "inventory": ["재고자산"],
        "accounts_payable": ["매입채무", "매입채무및기타채무"],
        "cfo": ["영업활동현금흐름", "영업활동으로 인한 현금흐름"],
        "cfi": ["투자활동현금흐름", "투자활동으로 인한 현금흐름"],
        "cff": ["재무활동현금흐름", "재무활동으로 인한 현금흐름"],
        "interest_expense": ["이자비용"],
    }
    values={k:None for k in aliases}
    with zipfile.ZipFile(zip_path) as z:
        names=[n for n in z.namelist() if n.lower().endswith(('.xml','.xhtml','.htm','.html'))]
        for name in names:
            try: raw=z.read(name)
            except Exception: continue
            soup=BeautifulSoup(raw, 'xml')
            # Table-first extraction preserves row/column relationships better than plain text.
            for tr in soup.find_all('tr'):
                cells=[c.get_text(' ', strip=True) for c in tr.find_all(['td','th'])]
                if not cells: continue
                joined=' '.join(cells)
                for key,names2 in aliases.items():
                    if values[key] is not None: continue
                    if any(label in joined for label in names2):
                        nums=[]
                        for cell in cells:
                            m=re.findall(r'(?<![A-Za-z가-힣])[-+]?\d[\d,]*(?:\.\d+)?', cell.replace('△','-'))
                            nums.extend(m)
                        if nums:
                            # First numeric cell after the account label is normally the current-period amount.
                            values[key]=num(nums[0])
            if all(v is not None for v in values.values()): break
    values.update({'year':year,'period':period,'fs_div':'legacy-original-xml'})
    return values

def ratios(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["period", "year"]).copy()
    def div(a,b): return a / b if pd.notna(a) and pd.notna(b) and b != 0 else None
    # Ratios that can be computed from available statement fields.
    for i, r in df.iterrows():
        revenue, op, net = r.get("revenue"), r.get("operating_income"), r.get("net_income")
        assets, equity, ca, cl = r.get("assets"), r.get("equity"), r.get("current_assets"), r.get("current_liabilities")
        cash, liab = r.get("cash"), r.get("liabilities")
        df.at[i,"gross_margin"] = div(r.get("gross_profit"), revenue)
        df.at[i,"operating_margin"] = div(op, revenue)
        df.at[i,"net_margin"] = div(net, revenue)
        df.at[i,"current_ratio"] = div(ca, cl)
        df.at[i,"debt_ratio"] = div(liab, assets)
        df.at[i,"roe"] = div(net, equity)
        df.at[i,"roa"] = div(net, assets)
        df.at[i,"asset_turnover"] = div(revenue, assets)
        df.at[i,"cfo_net_income"] = div(r.get("cfo"), net)
        df.at[i,"fcf"] = (r.get("cfo") - abs(r.get("capex"))) if pd.notna(r.get("cfo")) and pd.notna(r.get("capex")) else None
        df.at[i,"net_debt"] = (liab - cash) if pd.notna(liab) and pd.notna(cash) else None
        if i > 0 and r.get("period") == "annual":
            prev = df.iloc[i-1]
            if prev.get("year") == r.get("year")-1:
                df.at[i,"revenue_growth"] = div(revenue, prev.get("revenue")) - 1 if div(revenue, prev.get("revenue")) is not None else None
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-year", type=int, default=2010)
    ap.add_argument("--end-year", default="auto")
    args = ap.parse_args()
    end_year = int(args.end_year) if args.end_year != "auto" else __import__("datetime").datetime.now().year
    code = corp_code()
    metadata=[]; financial=[]
    for year in range(args.start_year, end_year+1):
        year_filings = filings(code, year)
        for f in year_filings:
            report=f.get("report_nm", "")
            metadata.append({k:f.get(k) for k in ["rcept_no","report_nm","rcept_dt","corp_name","reporter","year"]})
            try:
                raw_path=save_original(f["rcept_no"], year, report)
                if year < 2015:
                    if "사업보고서" in report: period="annual"
                    elif "반기보고서" in report: period="half-year"
                    else: period="quarterly"
                    legacy=legacy_extract_zip(raw_path, year, period)
                    if any(v is not None for k,v in legacy.items() if k not in ("year","period","fs_div")):
                        financial.append(legacy)
            except Exception as e: print("original warning", year, report, e)
        if year >= 2015:
            for period, rc in [("annual", REPORT_CODES["annual"]),("half-year", REPORT_CODES["half-year"]),("quarterly", REPORT_CODES["quarterly-q1"]),("quarterly", REPORT_CODES["quarterly-q3"])]:
                try:
                    rows=structured(code,year,rc)
                    if rows: financial += standardize(rows,year,period)
                except Exception as e: print("structured warning", year, period, e)
    # Deduplicate by year/period; later retrieval can overwrite corrected values.
    df=pd.DataFrame(financial)
    if not df.empty:
        df=df.drop_duplicates(["year","period"],keep="last").sort_values(["year","period"])
        rd=ratios(df)
    else:
        rd=pd.DataFrame()
    (ROOT/"data").mkdir(exist_ok=True)
    pd.DataFrame(metadata).drop_duplicates().to_csv(ROOT/"data/filings.csv",index=False,encoding="utf-8-sig")
    df.to_csv(ROOT/"data/financials.csv",index=False,encoding="utf-8-sig")
    rd.to_csv(ROOT/"data/ratios.csv",index=False,encoding="utf-8-sig")
    payload={"company":COMPANY_NAME,"corp_code":code,"updated_at":__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),"filings":metadata,"financials":df.fillna(value=pd.NA).to_dict(orient="records"),"ratios":rd.fillna(value=pd.NA).to_dict(orient="records")}
    # JSON null conversion
    (ROOT/"public").mkdir(exist_ok=True)
    (ROOT/"public/data.json").write_text(json.dumps(payload,ensure_ascii=False,default=lambda x: None),encoding="utf-8")
    print(f"done: {len(metadata)} filings, {len(df)} financial rows")

if __name__=="__main__": main()
