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
    crawl        - Download recipe pages from food.com
    parse        - Parse HTML → normalized JSONL (Food.com only)
    wiki_clean   - Remove Wikipedia artifacts (safe: keeps raw data)
    wiki_parse   - Extract culinary entities from Wikipedia dumps
    enrich       - Combine Food.com + Wikipedia → enriched recipes
    index        - Build inverted index (TSV files, baseline)
    index_lucene - Build PyLucene index (BM25/TF-IDF, production)
    search       - Interactive search CLI (TF-IDF/BM25, baseline)
    search_lucene- PyLucene search with filters
    gazetteer    - Build ingredient gazetteer
    eval         - Run evaluation (P@k, MAP, nDCG)
    all          - Run complete pipeline (parse→wiki→enrich→index)
    test         - Run unit tests
    clean        - Remove all generated data
    help         - Show this help message

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
    print_status "Running Phase C: Parser & Normalization (Food.com only)"
    
    # Check if raw data exists
    if [ ! -d "data/raw" ] || [ -z "$(ls -A data/raw 2>/dev/null)" ]; then
        print_error "Raw data not found. Run 'crawl' target first."
        echo ""
        echo "Quick fix:"
        echo "  ./packaging/run.sh crawl 100"
        exit 1
    fi
    
    python3 -m parser.run --raw data/raw --out data/normalized/recipes_foodcom.jsonl
    
    # Create symlink for backward compatibility
    if [ ! -f "data/normalized/recipes.jsonl" ] || [ ! -L "data/normalized/recipes.jsonl" ]; then
        ln -sf recipes_foodcom.jsonl data/normalized/recipes.jsonl
    fi
    
    echo ""
    print_success "Phase C completed - parsed recipes saved to data/normalized/recipes_foodcom.jsonl"
    echo ""
    echo "📊 Next steps:"
    echo "   1. Extract Wikipedia entities:  ./packaging/run.sh wiki_parse"
    echo "   2. Enrich recipes:              ./packaging/run.sh enrich"
    echo "   3. Build index:                 ./packaging/run.sh index"
}

# Function to clean Wikipedia artifacts (SAFE DELETE per §4)
run_wiki_clean() {
    print_status "Cleaning Wikipedia-derived artifacts (SAFE: keeps raw data)"
    
    print_warning "This will delete:"
    echo "  - data/normalized/wiki_culinary*.jsonl"
    echo "  - data/normalized/recipes_enriched*.jsonl"
    echo "  - entities/wiki_gazetteer*.tsv"
    echo "  - entities/*_test.*"
    echo ""
    echo "This will KEEP (safe):"
    echo "  - data/raw/** (crawler data)"
    echo "  - data/enwiki/** (Wikipedia dumps)"
    echo "  - data/normalized/recipes_foodcom.jsonl (Food.com parse)"
    echo "  - data/index/v1/** (baseline index)"
    echo ""
    
    read -p "Continue? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Cancelled by user"
        exit 0
    fi
    
    # Delete only wiki artifacts
    rm -f data/normalized/wiki_culinary*.jsonl
    rm -f data/normalized/recipes_enriched*.jsonl
    rm -f entities/wiki_gazetteer*.tsv
    rm -f entities/*_test.*
    rm -f data/normalized/*_test.jsonl
    
    print_success "Wiki artifacts cleaned successfully"
    echo ""
    echo "📊 Next step:"
    echo "   ./packaging/run.sh wiki_parse"
}

# Function to run Wikipedia parsing (Spark job per §5)
run_wiki_parse() {
    print_status "Running Wikipedia Entity Extraction (PySpark-style streaming)"
    
    # Check if Wikipedia dumps exist
    if [ ! -f "data/enwiki/enwiki-latest-pages-articles-multistream.xml.bz2" ]; then
        print_error "Wikipedia dump not found"
        echo ""
        echo "Expected file: data/enwiki/enwiki-latest-pages-articles-multistream.xml.bz2"
        echo ""
        echo "Download with:"
        echo "  mkdir -p data/enwiki"
        echo "  cd data/enwiki"
        echo "  wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2"
        echo "  wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-redirect.sql.gz"
        exit 1
    fi
    
    # Get limit from argument (optional)
    local limit_arg=""
    if [ -n "$1" ]; then
        limit_arg="--limit $1"
        print_status "Processing limit: $1 pages"
    else
        print_status "Processing FULL dump (no limit) - this may take 2-4 hours"
    fi
    
    echo ""
    python3 spark_jobs/enwiki_parser.py \
        --dump data/enwiki/enwiki-latest-pages-articles-multistream.xml.bz2 \
        --redirects data/enwiki/enwiki-latest-redirect.sql.gz \
        $limit_arg \
        --out-gazetteer entities/wiki_gazetteer.tsv \
        --out-jsonl data/normalized/wiki_culinary.jsonl
    
    echo ""
    print_success "Wikipedia parsing completed"
    echo ""
    echo "📊 Outputs created:"
    echo "   - entities/wiki_gazetteer.tsv"
    echo "   - data/normalized/wiki_culinary.jsonl"
    echo ""
    echo "📊 Next step:"
    echo "   ./packaging/run.sh enrich"
}

# Function to enrich recipes with Wikipedia knowledge (per §6)
run_enrich() {
    print_status "Enriching Food.com recipes with Wikipedia knowledge"
    
    # Check if required files exist
    if [ ! -f "data/normalized/recipes_foodcom.jsonl" ]; then
        print_error "Food.com recipes not found: data/normalized/recipes_foodcom.jsonl"
        echo "Run: ./packaging/run.sh parse"
        exit 1
    fi
    
    if [ ! -f "entities/wiki_gazetteer.tsv" ]; then
        print_error "Wikipedia gazetteer not found: entities/wiki_gazetteer.tsv"
        echo "Run: ./packaging/run.sh wiki_parse"
        exit 1
    fi
    
    if [ ! -f "data/normalized/wiki_culinary.jsonl" ]; then
        print_error "Wikipedia entities not found: data/normalized/wiki_culinary.jsonl"
        echo "Run: ./packaging/run.sh wiki_parse"
        exit 1
    fi
    
    echo ""
    python3 entities/enricher.py \
        --recipes data/normalized/recipes_foodcom.jsonl \
        --gazetteer entities/wiki_gazetteer.tsv \
        --wiki-entities data/normalized/wiki_culinary.jsonl \
        --output data/normalized/recipes_enriched.jsonl
    
    echo ""
    print_success "Recipe enrichment completed"
    echo ""
    echo "📊 Output created:"
    echo "   - data/normalized/recipes_enriched.jsonl"
    echo ""
    echo "📊 Next step:"
    echo "   ./packaging/run.sh index"
}

# Function to run Phase D (index) - TSV baseline
run_index() {
    print_status "Running Phase D: Build Search Index (TSV baseline)"
    
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

# Function to run PyLucene indexer (production)
run_index_lucene() {
    print_status "Building Lupyne index (BM25) from enriched recipes"
    
    # Check if enriched data exists
    if [ ! -f "data/normalized/recipes_enriched.jsonl" ]; then
        print_error "Enriched recipes not found: data/normalized/recipes_enriched.jsonl"
        echo ""
        echo "Run enrichment first:"
        echo "  ./packaging/run.sh enrich"
        exit 1
    fi
    
    # Check if Homebrew Python with Lupyne is available
    PYTHON_CMD="python3"
    if [ -f "/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14" ]; then
        PYTHON_CMD="/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14"
        print_status "Using Homebrew Python: $PYTHON_CMD"
    else
        print_warning "Homebrew Python not found. Using system Python."
        print_warning "If indexing fails, install PyLucene + Lupyne (see LUPYNE_INSTALL.md)"
    fi
    
    # Get similarity type from argument (default: bm25)
    local similarity=${1:-bm25}
    
    # Set output directory based on similarity
    local output_dir="index/lucene/v2"
    if [ "$similarity" = "tfidf" ]; then
        output_dir="index/lucene/v2_tfidf"
    fi
    
    print_status "Similarity: $similarity"
    print_status "Output: $output_dir"
    echo ""
    
    $PYTHON_CMD indexer/lucene_indexer.py \
        --input data/normalized/recipes_enriched.jsonl \
        --output "$output_dir" \
        --similarity "$similarity"
    
    echo ""
    print_success "PyLucene index built successfully!"
    echo ""
    echo "📊 Index location: $output_dir"
    echo "📊 Log: data/logs/lucene_indexing.log"
    echo ""
    echo "📊 Next steps:"
    echo "   1. Search:  ./packaging/run.sh search_lucene"
    echo "   2. Eval:    ./packaging/run.sh eval"
}

# Function to run unified searcher (TSV or Lupyne)
run_search_lucene() {
    print_status "Running unified search (supports TSV and Lupyne)"
    
    # Check if Homebrew Python with Lupyne is available
    PYTHON_CMD="python3"
    if [ -f "/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14" ]; then
        PYTHON_CMD="/usr/local/Cellar/python@3.14/3.14.0/bin/python3.14"
    fi
    
    # Default parameters
    local query=${1:-"mexican chicken"}
    local k=${2:-10}
    local index=${3:-"index/lucene/v2"}
    
    # Check if specified index exists, fallback to TSV
    if [ ! -d "$index" ]; then
        print_warning "Index not found: $index"
        if [ -d "data/index/v1" ]; then
            print_status "Falling back to TSV index: data/index/v1"
            index="data/index/v1"
        else
            print_error "No index found. Build an index first:"
            echo "  ./packaging/run.sh index        # TSV index"
            echo "  ./packaging/run.sh index_lucene # Lupyne index"
            exit 1
        fi
    fi
    
    print_status "Index: $index"
    print_status "Query: '$query'"
    print_status "Results: $k"
    echo ""
    
    # Use unified search CLI (auto-detects index type)
    $PYTHON_CMD search_cli/run.py \
        --index "$index" \
        --q "$query" \
        --k "$k" \
        --metric bm25 \
        --index-type auto
    
    echo ""
    print_success "Search completed"
    echo ""
    echo "💡 Advanced usage:"
    echo "   # With filters (PyLucene index)"
    echo "   python3 search_cli/run.py \\"
    echo "       --index index/lucene/v2 \\"
    echo "       --q \"chicken pasta\" \\"
    echo "       --k 10 \\"
    echo "       --filter '{\"max_total_minutes\": 30, \"cuisine\": \"Mexican\"}'"
    echo ""
    echo "   # Force TSV index"
    echo "   python3 search_cli/run.py \\"
    echo "       --index data/index/v1 \\"
    echo "       --q \"pasta\" \\"
    echo "       --k 5 \\"
    echo "       --index-type tsv"
}

# Function to run Phase D (search) - unified CLI
run_search() {
    print_status "Running unified search CLI (auto-detects TSV/PyLucene)"
    
    # Get search query from argument or use default
    local query=${1:-"chicken pasta"}
    
    # Try PyLucene index first, fallback to TSV
    local index="data/index/v1"
    if [ -d "index/lucene/v2" ]; then
        index="index/lucene/v2"
        print_status "Using PyLucene index: $index"
    elif [ -d "data/index/v1" ]; then
        print_status "Using TSV index: $index"
    else
        print_error "No index found. Build an index first:"
        echo "  ./packaging/run.sh index        # TSV index"
        echo "  ./packaging/run.sh index_lucene # PyLucene index"
        exit 1
    fi
    
    print_status "Query: '$query' (BM25)"
    echo ""
    
    python3 search_cli/run.py --index "$index" --metric bm25 --q "$query" --k 5 --index-type auto
    
    echo ""
    print_success "Search completed"
    echo ""
    echo "💡 Try more examples:"
    echo "   ./packaging/run.sh search \"chocolate dessert\""
    echo "   ./packaging/run.sh search \"italian pasta\""
    echo "   ./packaging/run.sh search \"healthy salad\""
    echo ""
    echo "📖 For advanced usage:"
    echo "   # PyLucene with filters"
    echo "   python3 search_cli/run.py --index index/lucene/v2 --metric bm25 \\"
    echo "       --q \"pasta\" --k 10 \\"
    echo "       --filter '{\"max_total_minutes\": 30, \"cuisine\": \"Italian\"}'"
    echo ""
    echo "   # TSV index (baseline)"
    echo "   python3 search_cli/run.py --index data/index/v1 --metric bm25 \\"
    echo "       --q \"chicken\" --k 5"
}

# Function to run Phase E (gazetteer)
run_gazetteer() {
    print_status "Running Phase E: Build Entity Gazetteer"
    
    python3 -m entities.gazetteer_builder --output data/entities/gazetteer_ingredients.tsv
    print_success "Phase E (Gazetteer) completed - check data/entities/ for gazetteer file"
}

# Function to run Phase G (eval)
run_eval() {
    print_status "Running Phase G: Evaluation (P@k, Recall@k, MAP, NDCG@k)"
    
    # Check if index exists
    if [ ! -d "data/index/v1" ]; then
        print_error "Index not found. Run 'index' target first."
        echo ""
        echo "Quick fix:"
        echo "  ./packaging/run.sh index"
        exit 1
    fi
    
    # Check if eval files exist
    if [ ! -f "eval/queries.tsv" ]; then
        print_error "Queries file not found: eval/queries.tsv"
        exit 1
    fi
    
    if [ ! -f "eval/qrels.tsv" ]; then
        print_error "Qrels file not found: eval/qrels.tsv"
        exit 1
    fi
    
    python3 eval/run.py --index data/index/v1 --k 5 10
    
    echo ""
    print_success "Phase G (Evaluation) completed - check eval/metrics.tsv for results"
    echo ""
    echo "📊 Results summary:"
    echo "  - 12 test queries evaluated"
    echo "  - Metrics: P@5, R@5, NDCG@5, P@10, R@10, NDCG@10, MAP"
    echo "  - View: cat eval/metrics.tsv"
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
        "wiki_clean")
            run_wiki_clean
            ;;
        "wiki_parse")
            run_wiki_parse $2
            ;;
        "enrich")
            run_enrich
            ;;
        "index")
            run_index
            ;;
        "index_lucene")
            run_index_lucene $2
            ;;
        "search")
            run_search $2
            ;;
        "search_lucene")
            run_search_lucene $2 $3
            ;;
        "gazetteer")
            run_gazetteer
            ;;
        "eval")
            run_eval
            ;;
        "all")
            print_status "Running complete pipeline (parse → wiki → enrich → index)..."
            echo ""
            
            # Step 1: Parse Food.com (skip if already done)
            if [ ! -f "data/normalized/recipes_foodcom.jsonl" ]; then
                print_status "Step 1/4: Parsing Food.com recipes..."
                run_parse
            else
                print_status "Step 1/4: Skipping parse (recipes_foodcom.jsonl exists)"
            fi
            echo ""
            
            # Step 2: Wikipedia parsing (skip if already done)
            if [ ! -f "data/normalized/wiki_culinary.jsonl" ]; then
                print_status "Step 2/4: Parsing Wikipedia entities..."
                local wiki_limit=${2:-100000}
                run_wiki_parse $wiki_limit
            else
                print_status "Step 2/4: Skipping wiki_parse (wiki_culinary.jsonl exists)"
            fi
            echo ""
            
            # Step 3: Enrichment
            print_status "Step 3/4: Enriching recipes with Wikipedia..."
            run_enrich
            echo ""
            
            # Step 4: Indexing
            print_status "Step 4/4: Building search index..."
            run_index
            echo ""
            
            print_success "✅ Pipeline completed! Now try:"
            echo "   ./packaging/run.sh search \"mexican chicken\""
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

