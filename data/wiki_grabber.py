import os
import sys
import re
import wikipediaapi
import numpy as np
import pandas as pd
from cards import all_card_sets

OUT_DIR = "./wiki_data"
CARD_SETS = all_card_sets

COLUMN_NAMES = ["page_title", "card", "sentence"]
PUNCTUATION_REGEX = r"\.\s+|!\s+|\?\s+|:\s+"

VERBOSE = True

# TODO: Punctionation can sometimes end up at the end of a line and not get removed
# TODO: account for author names like W.D. debois
# TODO: skip pages that have already been downloaded
# TODO: Sometimes the api does not return any values the for "see also" section.
# TODO: Add option of grabbing all pages from all links on a page

def splitSentences(text):
    all_sentences = []

    for line in text.split("\n"):
        if len(line) <= 0: continue                     # Remove spacer lines

        sentences = re.split(PUNCTUATION_REGEX, line)
        if len(sentences) == 1: continue                # Remove lines with only
        for sentence in sentences:                      # one split (titles)
            if len(sentence) == 0: continue
            all_sentences.append(sentence)

    return all_sentences

def sentences2Data(page_title, card_name, sentences):
    return list(map(lambda s: [page_title, card_name, s], sentences))

def getPageData(page, card_name, r_titles=["See also"], r_depth=1):
    if not page.exists(): return []
    if VERBOSE: print(f"Extracting {page.title}")

    # Get page text
    page_text = page.text
    page_text = page_text.replace("|", "")
    page_sentences = splitSentences(page_text)
    data = sentences2Data(page.title, card_name, page_sentences)

    # Check depth
    if r_depth == 0: return data

    # Recurse on subsections
    r_subsections = [page.section_by_title(r_title) for r_title in r_titles]
    r_subsections = list(filter(lambda s: not s is None, r_subsections))
    r_subsections_text = " ".join([r_s.text for r_s in r_subsections])
    for link_name, link_page in page.links.items():
        if link_name in r_subsections_text:
            linked_page_data = getPageData(link_page, card_name, r_titles=r_titles, r_depth=(r_depth - 1))
            data += linked_page_data

    return data

if __name__ == "__main__":
    wiki_wiki = wikipediaapi.Wikipedia(language="en",
                                 extract_format=wikipediaapi.ExtractFormat.WIKI)

    for card_set in CARD_SETS:
        out_filename = os.path.join(OUT_DIR, f"{card_set.name}.csv")
        extracted_data = []

        for card in card_set.cards:
            page = wiki_wiki.page(card.wiki_name)
            page_data = getPageData(page, card.name, r_titles=["See also"], r_depth=1)

            extracted_data += page_data

        cleaned_df = pd.DataFrame(extracted_data, columns=COLUMN_NAMES)
        cleaned_df.to_csv(out_filename, sep="|", index=False)
