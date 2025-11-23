#!/bin/bash
# Demo script for Food Recipes IR Pipeline
# Demonstrates various search capabilities and query types

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}\n"
}

print_cmd() {
    echo -e "${GREEN}$ $1${NC}\n"
}

# Detect Python
if [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
else
    PYTHON="python3"
fi

# 1. Basic Search
print_header "1. BASIC SEARCH (BM25)"
CMD="$PYTHON search_cli/run.py --index data/index/v1 --metric bm25 --q 'grilled chicken' --k 3"
print_cmd "$CMD"
eval $CMD

# 2. Boolean Query (Implicit OR between terms)
print_header "2. BOOLEAN QUERY (Implicit OR)"
CMD="$PYTHON search_cli/run.py --index data/index/v1 --metric bm25 --q 'chicken OR pasta' --k 3"
print_cmd "$CMD"
eval $CMD

# 3. Phrase Query (Exact phrase matching)
print_header "3. PHRASE QUERY"
CMD="$PYTHON search_cli/run.py --index data/index/v1 --metric bm25 --q '\"chocolate cake\"' --k 3"
print_cmd "$CMD"
eval $CMD

# 4. Filter by Time (Range Query)
print_header "4. FILTER: Time < 30 mins"
CMD="$PYTHON search_cli/run.py --index data/index/v1 --metric bm25 --q 'pasta' --k 3 --filter '{\"max_total_minutes\": 30}'"
print_cmd "$CMD"
eval $CMD

# 5. Filter by Cuisine (Exact Match)
print_header "5. FILTER: Cuisine = Mexican"
CMD="$PYTHON search_cli/run.py --index data/index/v1 --metric bm25 --q 'chicken' --k 3 --filter '{\"cuisine\": \"Mexican\"}'"
print_cmd "$CMD"
eval $CMD

# 6. Filter by Ingredients (Must Include)
print_header "6. FILTER: Must include 'garlic'"
CMD="$PYTHON search_cli/run.py --index data/index/v1 --metric bm25 --q 'shrimp' --k 3 --filter '{\"include_ingredients\": \"garlic\"}'"
print_cmd "$CMD"
eval $CMD

# 7. Complex Filter (Time + Cuisine + Ingredient)
print_header "7. COMPLEX FILTER (Time + Cuisine + Ingredient)"
CMD="$PYTHON search_cli/run.py --index data/index/v1 --metric bm25 --q 'dinner' --k 3 --filter '{\"max_total_minutes\": 45, \"cuisine\": \"Italian\", \"include_ingredients\": \"tomato\"}'"
print_cmd "$CMD"
eval $CMD

# 8. TF-IDF Comparison
print_header "8. TF-IDF COMPARISON (Same query as #1)"
CMD="$PYTHON search_cli/run.py --index data/index/v1 --metric tfidf --q 'grilled chicken' --k 3"
print_cmd "$CMD"
eval $CMD

echo -e "\n${GREEN}✅ Demo completed!${NC}"
