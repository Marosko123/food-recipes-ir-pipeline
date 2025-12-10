#!/bin/bash
# Demo script for Food Recipes IR Pipeline
# Demonstrates various search capabilities and query types
# 
# Search Features:
# - Basic BM25/TF-IDF search
# - Multi-term queries
# - Ingredient-based search
# - Cuisine filtering
# - Time range filtering
# - Detailed output with Wikipedia enrichment

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}\n"
}

print_section() {
    echo -e "\n${YELLOW}─── $1 ───${NC}\n"
}

print_cmd() {
    echo -e "${GREEN}$ $1${NC}\n"
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    PYTHON="python"
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    PYTHON="python"
else
    PYTHON="python3"
fi

# Use TSV index (always works without PyLucene)
INDEX="index/v1"

# Check if index exists
if [ ! -d "$INDEX" ]; then
    echo -e "${RED}ERROR: Index not found at $INDEX${NC}"
    echo "Please run the indexer first: python -m indexer.run"
    exit 1
fi

echo -e "${GREEN}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  🍳 Food Recipes IR Pipeline - Demo${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Using Python: $PYTHON${NC}"
echo -e "${GREEN}Using Index: $INDEX (TSV/BM25)${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════════${NC}"

# ============================================================================
# SECTION 1: BASIC SEARCH
# ============================================================================
print_header "SECTION 1: BASIC SEARCH"

# 1. Basic Search
print_section "1.1 Basic BM25 Search"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'grilled chicken' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 2. TF-IDF Search
print_section "1.2 TF-IDF Search (same query)"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric tfidf --q 'grilled chicken' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 3. Detailed output with Wikipedia
print_section "1.3 Detailed Output (with Wikipedia enrichment)"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'italian sausage soup' --k 2 --detail"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# ============================================================================
# SECTION 2: MULTI-TERM QUERIES
# ============================================================================
print_header "SECTION 2: MULTI-TERM QUERIES"

# 4. Two-term query
print_section "2.1 Two terms: chocolate cake"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'chocolate cake' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 5. Three-term query
print_section "2.2 Three terms: grilled chicken breast"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'grilled chicken breast' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 6. Beef stew
print_section "2.3 Two terms: beef stew"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'beef stew' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# ============================================================================
# SECTION 3: INGREDIENT-BASED SEARCH
# ============================================================================
print_header "SECTION 3: INGREDIENT-BASED SEARCH"

# 7. Chicken + Garlic
print_section "3.1 Ingredients: chicken garlic"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'chicken garlic' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 8. Tomato + Basil
print_section "3.2 Ingredients: tomato basil"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'tomato basil' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 9. Salmon + Lemon
print_section "3.3 Ingredients: salmon lemon"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'salmon lemon' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 10. Baking Ingredients
print_section "3.4 Baking: flour eggs sugar"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'flour eggs sugar' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# ============================================================================
# SECTION 4: CUISINE SEARCH
# ============================================================================
print_header "SECTION 4: CUISINE SEARCH"

# 11. Italian
print_section "4.1 Cuisine: italian pasta"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'italian pasta' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 12. Mexican
print_section "4.2 Cuisine: mexican tacos"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'mexican tacos' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 13. Thai
print_section "4.3 Cuisine: thai peanut noodles"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'thai peanut noodles' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 14. French
print_section "4.4 Cuisine: french sauce"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'french sauce' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# ============================================================================
# SECTION 5: ORIGIN/REGION SEARCH
# ============================================================================
print_header "SECTION 5: ORIGIN/REGION SEARCH"

# 15. Mediterranean
print_section "5.1 Region: mediterranean"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'mediterranean' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 16. Caribbean
print_section "5.2 Region: caribbean"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'caribbean' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 17. Asian
print_section "5.3 Region: asian rice"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'asian rice' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# ============================================================================
# SECTION 6: SPECIFIC DISH SEARCHES
# ============================================================================
print_header "SECTION 6: SPECIFIC DISH SEARCHES"

# 18. Lasagna
print_section "6.1 Dish: lasagna"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'lasagna' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 19. Risotto
print_section "6.2 Dish: risotto"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'risotto' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 20. Cheesecake
print_section "6.3 Dish: cheesecake"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'cheesecake' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 21. Tiramisu
print_section "6.4 Dish: tiramisu"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'tiramisu' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 22. Guacamole
print_section "6.5 Dish: guacamole"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'guacamole' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# ============================================================================
# SECTION 7: DIETARY SEARCHES
# ============================================================================
print_header "SECTION 7: DIETARY SEARCHES"

# 23. Vegan
print_section "7.1 Dietary: vegan chocolate"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'vegan chocolate' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 24. Low carb
print_section "7.2 Dietary: low carb"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'low carb' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 25. Healthy
print_section "7.3 Dietary: healthy vegetables"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'healthy vegetables' --k 3"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# ============================================================================
# SECTION 8: DETAILED OUTPUT EXAMPLES
# ============================================================================
print_header "SECTION 8: DETAILED OUTPUT (Wikipedia Enrichment)"

# 26. Detailed - Chicken recipe
print_section "8.1 Detailed: chicken garlic (with Wikipedia)"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'chicken garlic' --k 1 --detail"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# 27. Detailed - Pasta recipe
print_section "8.2 Detailed: italian pasta (with Wikipedia)"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'italian pasta' --k 1 --detail"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# ============================================================================
# SECTION 9: JSON OUTPUT
# ============================================================================
print_header "SECTION 9: JSON OUTPUT (for API integration)"

# 28. JSON output
print_section "9.1 JSON Output: chocolate cake"
CMD="$PYTHON -m search_cli.run --index $INDEX --metric bm25 --q 'chocolate cake' --k 2 --json"
print_cmd "$CMD"
eval $CMD 2>/dev/null

# ============================================================================
# SUMMARY
# ============================================================================
print_header "DEMO COMPLETED"

echo -e "${GREEN}✅ Demo completed successfully!${NC}"
echo ""
echo "Query Types Demonstrated:"
echo "  - Basic BM25/TF-IDF search"
echo "  - Multi-term queries"
echo "  - Ingredient-based search"
echo "  - Cuisine search"
echo "  - Origin/region search"
echo "  - Specific dish searches"
echo "  - Dietary searches"
echo "  - Detailed output with Wikipedia enrichment"
echo "  - JSON output for API integration"
echo ""
echo "Total queries demonstrated: 28"
echo ""
echo -e "${BLUE}For more options run:${NC}"
echo "  python -m search_cli.run --help"
