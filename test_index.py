import sys
import time
from src.m2_search import HybridSearch
print("Init HybridSearch...")
search = HybridSearch()
import json
print("Loading real chunks...")
all_chunks = json.load(open("debug_chunks.json", encoding="utf-8"))
print("Indexing...")
search.index(all_chunks)
print("Done indexing!")
