#!/bin/bash
# Food Recipes - Main execution script
# Author: Maroš Bednár (AIS 116822)
# Email: bednarmaros341@gmail.com

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << 'EOF'
═══════════════════════════════════════════════════════════════════════════
   Food Recipes IR Pipeline - Central Entrypoint
   Author: Maroš Bednár (AIS 116822)
   Email: bednarmaros341@gmail.com
═══════════════════════════════════════════════════════════════════════════

USAGE:
    ./packaging/run.sh <target> [options]

AVAILABLE TARGETS:
    crawl     - Download recipe pages from food.com
    parse     - Parse HTML → normalized JSONL
    index     - Build inverted index (TSV files)
    search    - Interactive search CLI (TF-IDF/BM25)
    gazetteer - Build ingredient gazetteer
    all       - Run complete pipeline (crawl→parse→index)
    test      - Run unit tests
    clean     - Remove all generated data
    help      - Show this help message

───────────────────────────────────────────────────────────────────────────
QUICK START (Phase 1 Submission):
───────────────────────────────────────────────────────────────────────────

1️⃣  CRAWL (Download 100 recipes for demo):
    ./packaging/run.sh crawl 100

2️⃣  PARSE (Extract structured data):
    ./packaging/run.sh parse

3️⃣  INDEX (Build inverted index):
    ./packaging/run.sh index

4️⃣  SEARCH (Try some queries):
    ./packaging/run.sh search "chicken pasta"
    ./packaging/run.sh search "chocolate dessert"

5️⃣  DEMO (Run 10 Q&A examples for teacher):
    bash packaging/cli_examples.sh

───────────────────────────────────────────────────────────────────────────
ADVANCED EXAMPLES:
───────────────────────────────────────────────────────────────────────────

Crawl with custom limit:
    ./packaging/run.sh crawl 500           # Download 500 recipes
    ./packaging/run.sh crawl 5000          # Full crawl (production)

Search with filters (use Python directly for JSON filters):
    python3 search_cli/run.py \
        --index data/index/v1 \
        --metric bm25 \
        --q "pasta" \
        --k 5 \
        --filter '{"max_total_minutes": 30, "min_rating": 4.0}'

Compare TF-IDF vs BM25:
    python3 search_cli/run.py --index data/index/v1 --metric tfidf --q "pasta" --k 3
    python3 search_cli/run.py --index data/index/v1 --metric bm25 --q "pasta" --k 3

───────────────────────────────────────────────────────────────────────────
TROUBLESHOOTING:
───────────────────────────────────────────────────────────────────────────

Missing dependencies:
    pip3 install -r packaging/requirements.txt

Missing data/raw:
    ./packaging/run.sh crawl 100           # Crawl first

Missing data/normalized/recipes.jsonl:
    ./packaging/run.sh parse               # Parse first

Missing data/index/v1:
    ./packaging/run.sh index               # Index first

Clean everything and restart:
    ./packaging/run.sh clean
    ./packaging/run.sh crawl 100
    ./packaging/run.sh parse
    ./packaging/run.sh index

═══════════════════════════════════════════════════════════════════════════
DOCUMENTATION:
    README_First_Submission.md    - Phase 1 overview (pseudocode + metrics)
    docs/DEMO_GUIDE.md            - Presentation guide for teacher
    docs/CLI_GUIDE.md             - Complete CLI reference
    packaging/cli_examples.sh     - 10 Q&A demo scenarios
═══════════════════════════════════════════════════════════════════════════
EOF
}

# Function to check if Python is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
}

# Function to install dependencies
install_deps() {
    print_status "Installing dependencies..."
    pip3 install -r packaging/requirements.txt
    print_success "Dependencies installed"
}

# Function to run Phase A (seeds)
run_seeds() {
    print_status "Running Phase A: Web Analysis + Seed Extraction"
    python3 -m crawler.run --phase seeds --out data/seed_analysis --qps 0.5
    print_success "Phase A completed - check data/seed_analysis/ for results"
}

# Function to run Phase B (crawl)
run_crawl() {
    print_status "Running Phase B: Recipe Page Crawling"
    
    # Get limit from first argument or default to 100 for demo
    local limit=${1:-100}
    print_status "Crawling $limit recipes from food.com..."
    echo ""
    
    python3 -m crawler.run --phase crawl \
        --out data/raw \
        --limit $limit \
        --qps 0.5
    
    echo ""
    print_success "Phase B completed - downloaded $limit recipes to data/raw/"
    echo ""
    echo "📊 Next steps:"
    echo "   1. Parse the HTML:  ./packaging/run.sh parse"
    echo "   2. Build index:     ./packaging/run.sh index"
    echo "   3. Search recipes:  ./packaging/run.sh search \"chicken\""
}

# Function to run Phase C (parse)
run_parse() {
    print_status "Running Phase C: Parser & Normalization"
    
    # Check if raw data exists
    if [ ! -d "data/raw" ] || [ -z "$(ls -A data/raw 2>/dev/null)" ]; then
        print_error "Raw data not found. Run 'crawl' target first."
        echo ""
        echo "Quick fix:"
        echo "  ./packaging/run.sh crawl 100"
        exit 1
    fi
    
    python3 -m parser.run --raw data/raw --out data/normalized/recipes.jsonl
    
    echo ""
    print_success "Phase C completed - parsed recipes saved to data/normalized/recipes.jsonl"
    echo ""
    echo "📊 Next step:"
    echo "   ./packaging/run.sh index"
}

# Function to run Phase D (index)
run_index() {
    print_status "Running Phase D: Build Search Index"
    
    # Check if normalized data exists
    if [ ! -f "data/normalized/recipes.jsonl" ]; then
        print_error "Normalized recipe data not found. Run 'parse' target first."
        echo ""
        echo "Quick fix:"
        echo "  ./packaging/run.sh parse"
        exit 1
    fi
    
    python3 -m indexer.run --input data/normalized/recipes.jsonl --out data/index/v1
    
    echo ""
    print_success "Phase D (Index) completed - index files saved to data/index/v1/"
    echo ""
    echo "📊 Next steps:"
    echo "   1. Try a search:     ./packaging/run.sh search \"chicken pasta\""
    echo "   2. Run 10 Q&A demo:  bash packaging/cli_examples.sh"
    echo ""
    echo "📖 Full CLI documentation:"
    echo "   - docs/CLI_GUIDE.md           (complete reference)"
    echo "   - README_First_Submission.md  (Phase 1 overview)"
}

# Function to run Phase D (search)
run_search() {
    print_status "Running Phase D: Search CLI"
    
    # Check if index exists
    if [ ! -d "data/index/v1" ]; then
        print_error "Index not found. Run 'index' target first."
        echo ""
        echo "Quick fix:"
        echo "  ./packaging/run.sh index"
        exit 1
    fi
    
    # Get search query from second argument or use default
    local query=${1:-"chicken pasta"}
    print_status "Searching for: '$query' (using BM25)"
    echo ""
    
    python3 -m search_cli.run --index data/index/v1 --metric bm25 --q "$query" --k 5
    
    echo ""
    print_success "Search completed"
    echo ""
    echo "💡 Try more examples:"
    echo "   ./packaging/run.sh search \"chocolate dessert\""
    echo "   ./packaging/run.sh search \"italian pasta\""
    echo "   ./packaging/run.sh search \"healthy salad\""
    echo ""
    echo "📖 For advanced filters, use Python directly:"
    echo "   python3 search_cli/run.py --index data/index/v1 --metric bm25 \\"
    echo "       --q \"pasta\" --k 3 \\"
    echo "       --filter '{\"max_total_minutes\": 30, \"min_rating\": 4.0}'"
    echo ""
    echo "🎯 Run 10 Q&A demo scenarios:"
    echo "   bash packaging/cli_examples.sh"
}

# Function to run Phase E (gazetteer)
run_gazetteer() {
    print_status "Running Phase E: Build Entity Gazetteer"
    
    python3 -m entities.gazetteer_builder --output data/entities/gazetteer_ingredients.tsv
    print_success "Phase E (Gazetteer) completed - check data/entities/ for gazetteer file"
}

# Function to run tests
run_tests() {
    print_status "Running unit tests..."
    python3 -m pytest tests/ -v
    print_success "Tests completed"
}

# Function to clean generated files
clean_data() {
    print_status "Cleaning generated data files..."
    rm -rf data/raw data/normalized data/index data/entities data/eval data/seed_analysis data/wikipedia_recipes
    rm -f data/*.log
    print_success "Data files cleaned"
}

# Main script logic
main() {
    # Check if target is provided
    if [ $# -eq 0 ]; then
        print_error "No target specified"
        show_usage
        exit 1
    fi
    
    TARGET=$1
    
    # Check Python availability
    check_python
    
    # Handle different targets
    case $TARGET in
        "seeds")
            run_seeds
            ;;
        "crawl")
            run_crawl $2
            ;;
        "parse")
            run_parse
            ;;
        "index")
            run_index
            ;;
        "search")
            run_search $2
            ;;
        "gazetteer")
            run_gazetteer
            ;;
        "eval")
            print_warning "Phase G (eval) not implemented yet"
            ;;
        "all")
            print_status "Running complete pipeline (crawl → parse → index)..."
            echo ""
            local limit=${2:-100}
            print_status "Step 1/3: Crawling $limit recipes..."
            run_crawl $limit
            echo ""
            print_status "Step 2/3: Parsing recipes..."
            run_parse
            echo ""
            print_status "Step 3/3: Building index..."
            run_index
            echo ""
            print_success "✅ Pipeline completed! Now try:"
            echo "   ./packaging/run.sh search \"chicken pasta\""
            echo "   bash packaging/cli_examples.sh"
            ;;
        "test")
            run_tests
            ;;
        "clean")
            clean_data
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            print_error "Unknown target: $TARGET"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"

