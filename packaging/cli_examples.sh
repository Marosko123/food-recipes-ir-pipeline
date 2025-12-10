#!/bin/bash
# Food Recipes Search CLI - 10 Q&A Demo Examples
# Author: Maroš Bednár (AIS ID: 116822)
# Updated: November 27, 2025

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════════════"
echo "   Food Recipes Search CLI - Demo Examples"
echo "════════════════════════════════════════════════════════════"
echo ""

# Function to run example
run_example() {
    local num="$1"
    local question="$2"
    local answer="$3"
    local cmd1="$4"
    local cmd2="$5"
    
    echo -e "${YELLOW}Q${num}: ${question}${NC}"
    echo -e "${GREEN}A${num}: ${answer}${NC}"
    echo ""
    
    echo -e "${CYAN}Index V1 (TSV):${NC}"
    echo "$cmd1"
    echo ""
    eval "$cmd1" | head -30
    echo ""
    
    echo -e "${CYAN}Index V2 (Lucene):${NC}"
    echo "$cmd2"
    echo ""
    eval "$cmd2" | head -30
    echo ""
    
    echo "─────────────────────────────────────────────────────────────"
    echo ""
}

# Q1: Quick chicken recipe under 30 minutes
run_example "1" \
    "Chcem rýchle kuracie jedlo do 30 minút" \
    "Top 3 kuracích receptov s časom ≤30 min, hodnotenie ≥4.0" \
    "python3 search_cli/run.py --index data/index/v1 --metric bm25 --q 'chicken' --k 3 --filter '{\"max_total_minutes\": 30, \"min_rating\": 4.0}'" \
    "python3 search_cli/run.py --index index/v2 --metric bm25 --q 'chicken' --k 3 --filter '{\"max_total_minutes\": 30, \"min_rating\": 4.0}'"

# Q2: Italian pasta under 45 minutes
run_example "2" \
    "Chcem talianske cestoviny do 45 minút" \
    "Top 3 talianske pasta recepty s časom ≤45 min" \
    "python3 search_cli/run.py --index data/index/v1 --metric bm25 --q 'italian pasta' --k 3 --filter '{\"max_total_minutes\": 45, \"min_rating\": 4.0}'" \
    "python3 search_cli/run.py --index index/v2 --metric bm25 --q 'italian pasta' --k 3 --filter '{\"max_total_minutes\": 45, \"min_rating\": 4.0}'"

# Q3: Healthy salad with protein
run_example "3" \
    "Hľadám zdravý šalát s vysokým obsahom bielkovín" \
    "Top 3 šaláty s proteínom ≥15g, kalórie ≤400" \
    "python3 search_cli/run.py --index data/index/v1 --metric bm25 --q 'salad healthy' --k 3 --filter '{\"max_calories\": 400, \"min_protein\": 15}'" \
    "python3 search_cli/run.py --index index/v2 --metric bm25 --q 'salad healthy' --k 3 --filter '{\"max_calories\": 400, \"min_protein\": 15}'"

# Q4: Chocolate dessert for party
run_example "4" \
    "Potrebujem čokoládový dezert na oslavu" \
    "Top 3 čokoládové dezerty, vysoko hodnotené (≥4.5★)" \
    "python3 search_cli/run.py --index data/index/v1 --metric bm25 --q 'chocolate dessert cake' --k 3 --filter '{\"min_rating\": 4.5}'" \
    "python3 search_cli/run.py --index index/v2 --metric bm25 --q 'chocolate dessert cake' --k 3 --filter '{\"min_rating\": 4.5}'"

# Q5: Mexican quick meal
run_example "5" \
    "Chcem mexickú kuchyňu, ale rýchlo" \
    "Top 3 mexické recepty do 45 min, dobre hodnotené" \
    "python3 search_cli/run.py --index data/index/v1 --metric bm25 --q 'mexican' --k 3 --filter '{\"max_total_minutes\": 45, \"min_rating\": 4.0}'" \
    "python3 search_cli/run.py --index index/v2 --metric bm25 --q 'mexican' --k 3 --filter '{\"max_total_minutes\": 45, \"min_rating\": 4.0}'"

# Q6: Low calorie soup
run_example "6" \
    "Chcem ľahkú polievku s nízkym obsahom kalórií" \
    "Top 3 polievky s kalóriami ≤300" \
    "python3 search_cli/run.py --index data/index/v1 --metric bm25 --q 'soup light' --k 3 --filter '{\"max_calories\": 300}'" \
    "python3 search_cli/run.py --index index/v2 --metric bm25 --q 'soup light' --k 3 --filter '{\"max_calories\": 300}'"

# Q7: Quick breakfast
run_example "7" \
    "Rýchla raňajková inšpirácia do 15 minút" \
    "Top 3 raňajky s prípravou ≤15 min" \
    "python3 search_cli/run.py --index data/index/v1 --metric bm25 --q 'breakfast eggs quick' --k 3 --filter '{\"max_total_minutes\": 15}'" \
    "python3 search_cli/run.py --index index/v2 --metric bm25 --q 'breakfast eggs quick' --k 3 --filter '{\"max_total_minutes\": 15}'"

# Q8: Vegetarian pasta
run_example "8" \
    "Vegetariánske cestoviny s dobrou chuťou" \
    "Top 3 pasta recepty, dobre hodnotené (≥4.0★)" \
    "python3 search_cli/run.py --index data/index/v1 --metric bm25 --q 'pasta vegetarian' --k 3 --filter '{\"min_rating\": 4.0}'" \
    "python3 search_cli/run.py --index index/v2 --metric bm25 --q 'pasta vegetarian' --k 3 --filter '{\"min_rating\": 4.0}'"

# Q9: High protein dinner
run_example "9" \
    "Chcem večeru s vysokým obsahom bielkovín" \
    "Top 3 večere s proteínom ≥25g, kalórie ≤600" \
    "python3 search_cli/run.py --index data/index/v1 --metric bm25 --q 'chicken beef dinner protein' --k 3 --filter '{\"min_protein\": 25, \"max_calories\": 600}'" \
    "python3 search_cli/run.py --index index/v2 --metric bm25 --q 'chicken beef dinner protein' --k 3 --filter '{\"min_protein\": 25, \"max_calories\": 600}'"

# Q10: TF-IDF vs BM25 (V2)
echo -e "${YELLOW}Q10: Aký je rozdiel medzi TF-IDF a BM25 (na V2 indexe)?${NC}"
echo -e "${GREEN}A10: Ukážka rovnakého query s oboma metrikami${NC}"
echo ""
echo -e "${CYAN}TF-IDF (V2):${NC}"
echo "python3 search_cli/run.py --index index/v2_tfidf --metric tfidf --q 'pasta carbonara' --k 3"
python3 search_cli/run.py --index index/v2_tfidf --metric tfidf --q "pasta carbonara" --k 3 2>&1 | grep -E "(^[0-9]\.|Score:|Total results:)" || true
echo ""
echo -e "${CYAN}BM25 (V2):${NC}"
echo "python3 search_cli/run.py --index index/v2 --metric bm25 --q 'pasta carbonara' --k 3"
python3 search_cli/run.py --index index/v2 --metric bm25 --q "pasta carbonara" --k 3 2>&1 | grep -E "(^[0-9]\.|Score:|Total results:)" || true
echo ""
echo "─────────────────────────────────────────────────────────────"
echo ""

echo "════════════════════════════════════════════════════════════"
echo "   ✅ All 10 Q&A examples completed!"
echo "════════════════════════════════════════════════════════════"
echo ""
