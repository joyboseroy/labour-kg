"""
Download Indian Labour Acts and Codes from working sources.

Sources:
- PRS India (prsindia.org) - has clean PDFs of all Acts and Codes
- legislative.gov.in - official government source
- clc.gov.in - Chief Labour Commissioner

Run: python3 scripts/download_acts.py
Output: data/raw/*.txt
"""

import os, time, subprocess, requests

HEADERS = {"User-Agent": "academic_labour_law_research/0.1 (non-commercial research)"}
RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)

ACTS = {
    "industrial_disputes_act_1947": {
        "era": "old", "short": "IDA 1947",
        "urls": [
            "https://prsindia.org/files/bills_acts/acts_parliament/1947/Industrial%20Disputes%20Act,%201947.pdf",
            "https://clc.gov.in/clc/sites/default/files/IDA1947.pdf",
            "https://labour.gov.in/sites/default/files/TheIndustrialDisputesAct1947_0.pdf",
        ],
    },
    "contract_labour_act_1970": {
        "era": "old", "short": "CLA 1970",
        "urls": [
            "https://prsindia.org/files/bills_acts/acts_parliament/1970/Contract%20Labour%20Act,%201970.pdf",
            "https://clc.gov.in/clc/sites/default/files/CLRA1970.pdf",
            "https://labour.gov.in/sites/default/files/TheContractLabour(RegulationandAbolition)Act1970.pdf",
        ],
    },
    "minimum_wages_act_1948": {
        "era": "old", "short": "MWA 1948",
        "urls": [
            "https://prsindia.org/files/bills_acts/acts_parliament/1948/Minimum%20Wages%20Act,%201948.pdf",
            "https://clc.gov.in/clc/sites/default/files/MWA1948.pdf",
            "https://labour.gov.in/sites/default/files/TheMinimumWagesAct1948_0.pdf",
        ],
    },
    "payment_of_wages_act_1936": {
        "era": "old", "short": "PWA 1936",
        "urls": [
            "https://prsindia.org/files/bills_acts/acts_parliament/1936/Payment%20of%20Wages%20Act,%201936.pdf",
            "https://clc.gov.in/clc/sites/default/files/PWA1936.pdf",
            "https://labour.gov.in/sites/default/files/ThePaymentofWagesAct1936_0.pdf",
        ],
    },
    "code_on_wages_2019": {
        "era": "new", "short": "CW 2019",
        "urls": [
            "https://prsindia.org/files/bills_acts/bills_parliament/2019/Code%20on%20Wages,%202019.pdf",
            "https://labour.gov.in/sites/default/files/CodeonWages2019_0.pdf",
            "https://egazette.gov.in/WriteReadData/2019/210356.pdf",
        ],
    },
    "industrial_relations_code_2020": {
        "era": "new", "short": "IRC 2020",
        "urls": [
            "https://prsindia.org/files/bills_acts/bills_parliament/2020/Industrial%20Relations%20Code,%202020.pdf",
            "https://labour.gov.in/sites/default/files/TheIndustrialRelationsCode2020.pdf",
            "https://egazette.gov.in/WriteReadData/2020/222039.pdf",
        ],
    },
    "code_on_social_security_2020": {
        "era": "new", "short": "CSS 2020",
        "urls": [
            "https://prsindia.org/files/bills_acts/bills_parliament/2020/Code%20on%20Social%20Security,%202020.pdf",
            "https://labour.gov.in/sites/default/files/TheCodeonSocialSecurity2020.pdf",
            "https://egazette.gov.in/WriteReadData/2020/222040.pdf",
        ],
    },
    "osh_code_2020": {
        "era": "new", "short": "OSH 2020",
        "urls": [
            "https://prsindia.org/files/bills_acts/bills_parliament/2020/Occupational%20Safety,%20Health%20and%20Working%20Conditions%20Code,%202020.pdf",
            "https://labour.gov.in/sites/default/files/TheOccupationalSafetyHealthandWorkingConditionsCode2020.pdf",
            "https://egazette.gov.in/WriteReadData/2020/222038.pdf",
        ],
    },
}


def pdf_to_text(pdf_path: str) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", pdf_path, "-"],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode == 0:
        return result.stdout
    return ""


def download_pdf(url: str, name: str) -> str | None:
    pdf_path = f"/tmp/{name}.pdf"
    try:
        r = requests.get(url, headers=HEADERS, timeout=40, stream=True)
        if r.status_code != 200:
            return None
        with open(pdf_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        text = pdf_to_text(pdf_path)
        if len(text.strip()) > 500:
            return text
        return None
    except Exception as e:
        print(f"    Error: {e}")
        return None


def download_all():
    for name, meta in ACTS.items():
        out_path = os.path.join(RAW_DIR, f"{name}.txt")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            print(f"  {meta['short']}: already exists, skipping.")
            continue

        print(f"\nDownloading {meta['short']} ({meta['era']})...")
        text = None
        for url in meta["urls"]:
            print(f"  trying {url[:60]}...")
            text = download_pdf(url, name)
            if text:
                print(f"  got {len(text):,} chars")
                break
            time.sleep(1)

        if text:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"# {name}\n# era: {meta['era']}\n# short: {meta['short']}\n\n")
                f.write(text)
        else:
            print(f"  ALL URLs FAILED for {name}")
            print(f"  Please download manually and save as data/raw/{name}.txt")
            print(f"  Try: https://prsindia.org/legislative-research/acts-and-bills")

        time.sleep(2)

    print("\n── Download summary ──")
    for name, meta in ACTS.items():
        path = os.path.join(RAW_DIR, f"{name}.txt")
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            size = os.path.getsize(path)
            print(f"  OK      {meta['short']:12} ({size:>8,} bytes)")
        else:
            print(f"  MISSING {meta['short']}")


if __name__ == "__main__":
    download_all()
