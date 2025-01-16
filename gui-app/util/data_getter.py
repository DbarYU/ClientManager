import requests
from bs4 import BeautifulSoup
from sec_edgar_downloader import Downloader
from datetime import datetime,timedelta
from sec_cik_mapper import StockMapper
import os
import re
import spacy
from itertools import islice
from transformers import BartForConditionalGeneration, BartTokenizer
from sec_downloader import Downloader as DownloaderV2
from sec_downloader.types import RequestedFilings
import json

nlp = spacy.load('en_core_web_sm')
mapper = StockMapper()
ticker_to_cik = mapper.ticker_to_cik
cik_to_ticker = mapper.cik_to_tickers
keywords = ["ex99", "press", "release", "exhibit99", "ex-99", "q4","q3","q2","q1","ex"]
headers = {
    "User-Agent": "DothanBar@gmail.com"
}
patterns = {
    "Quarterly Results": r"Results\s+of\s+Operations\s+and\s+Financial\s+Condition\.?",
    "Departure of Directors": r"Departure\s+of\s+Directors\s+or\s+Certain\s+Officers;.*?Officers\.?",
    "Other Events": r"Other\s+Events\.?",
    "Regulation FD Disclosure": r"Regulation\s+FD\s+Disclosure\.?",
    "Changes in Company’s Certifying Accountant": "Changes in Company’s Certifying Accountant\.?",
    "Submission of Matters to a Vote of Security Holders.": "Submission of Matters to a Vote of Security Holders."
}
regex = (
    r"Results\s+of\s+Operations\s+and\s+Financial\s+Condition\.?|"
    r"Departure\s+of\s+Directors\s+or\s+Certain\s+Officers;.*?Officers\.?|"
    r"Other\s+Events\.?|"
    r"Regulation\s+FD\s+Disclosure\.?|"
    r"Changes\s+in\s+Company’s\s+Certifying\s+Accountant\.?"
)

model = BartForConditionalGeneration.from_pretrained("facebook/bart-large-cnn")
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")

dl_v2 = DownloaderV2("Dothan", "dbar@example.com")

def get_prev_update(ticker):
    if not has_new_press_release_happened(ticker):
        return None
    """ticker can be either CIK or actual ticker"""
    text, type_of_pr, pr_text, date, accession_number = _get_content_v2(ticker)
    cik = ticker_to_cik[ticker]
    pr_link = get_press_release_link(text,cik= cik,accession_number=accession_number)
    if text is None:
        return "No Recent Data", "No Recent Data", "No Recent Data", accession_number
    if pr_text is None:
        summary =  text_from_8_k(text)
        pr_link = "No Link Available"
    else:
        summary = type_of_pr + ": " + _get_summary(pr_text)
    date_object = datetime.strptime(date, "%Y-%m-%d")

    # Format the date to a verbal representation
    verbal_date = date_object.strftime("%B %d, %Y")
    return summary,verbal_date,pr_link,accession_number



def _get_exhibit_99_k_v2(content,cik,accession_number):
    base_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/"

    soup = BeautifulSoup(content, "html.parser")
    links = soup.find_all("a", href=True)
    for link in links:
        if link["href"].endswith(".htm") or link["href"].endswith(".html") or link["href"].endswith(".jpg"):
            return base_url + link["href"]
    else:
        return "No Press Release Found"


def _get_summary(text):
    text = re.sub(r'\s+', ' ', text.strip())
    text = re.sub(r'\(.*?\)', '', text)

    inputs = tokenizer.encode("summarize: " + text, return_tensors="pt", max_length=1024, truncation=True)

    summary_ids = model.generate(inputs, max_length=100, min_length=30, length_penalty=2.0, num_beams=4,
                                 early_stopping=True)
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)


def _extract_type(text):
    for category, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return category
    return ""

def _get_content_v2(ticker):
    metadatas = dl_v2.get_filing_metadatas(RequestedFilings(ticker_or_cik=ticker, form_type="8-K", limit=1))
    metadata = metadatas[0]
    response = requests.get(metadata.primary_doc_url, headers=headers)
    if response.status_code == 200:
        text = response.text
        type_of_pr = _extract_type(text)
        pr_text = _get_press_release_text(metadata.primary_doc_url,metadata.cik,metadata.accession_number)
        date = metadata.report_date
        accession_number = metadata.accession_number
        return text, type_of_pr, pr_text, date, accession_number
    else:
        return None

def _get_press_release_text(url, cik, accession_number):
    text = requests.get(url, headers=headers).text
    link = get_press_release_link(text, cik, accession_number)
    if not link:
        return None
    response = requests.get(link, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'\(.*?\)', '', text)
        return text
    else:
        return None


def get_press_release_link(content, cik, accession_number):
    accession_number = accession_number.replace("-","")
    base_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/"
    soup = BeautifulSoup(content, "html.parser")
    links = soup.find_all("a", href=True)

    for link in links:
        if link["href"].endswith(".htm") or link["href"].endswith(".html") or link["href"].endswith(".jpg"):
            return base_url + link["href"]
    else:
        return None


def has_new_press_release_happened(ticker):
    metadatas = dl_v2.get_filing_metadatas(RequestedFilings(ticker_or_cik=ticker, form_type="8-K", limit=1))
    metadata = metadatas[0]
    prev_file = metadata.accession_number
    with open("C:\\Users\dotha\OneDrive\Desktop\FreedomCapitalMarketsProject\gui-app\clients.json", 'r') as f:
        data = json.load(f)

    for record in data:
        if record.get("ticker") == ticker:
            client_prev_record = record.get("accession_number")
            if client_prev_record == prev_file:
                return False
            else:
                return True

    return True
def get_company_name_based_of_cik(cik):
    ticker = cik_to_ticker.get(cik)
    if ticker is None:
        raise ValueError


def text_from_8_k(content):
    soup = BeautifulSoup(content, 'lxml-xml')
    text = soup.get_text()
    match = re.search(regex, text)

    if match:
        # Get everything after the match
        remaining_text = text[match.end():].strip()

        # Use spaCy to detect sentences in the remaining text
        doc = nlp(remaining_text)
        full_sentence = " ".join(sent.text.strip() for sent in doc.sents)
        return _get_summary(full_sentence)