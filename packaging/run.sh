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
    echo "Food Recipes - Recipes IR Pipeline"
    echo "Author: Maroš Bednár (AIS 116822)"
    echo ""
    echo "Usage: $0 <target>"
    echo ""
    echo "Available targets:"
    echo "  seeds     - Phase A: Web analysis + seed extraction"
    echo "  crawl     - Phase B: Download recipe pages"
    echo "  parse     - Phase C: Parse and normalize recipes"
    echo "  index     - Phase D: Build search index"
    echo "  search    - Phase D: Search CLI"
    echo "  gazetteer - Phase E: Build entity gazetteer"
    echo "  eval      - Phase G: Run evaluation (not implemented yet)"
    echo "  all       - Run all phases in sequence"
    echo "  test      - Run unit tests"
    echo "  clean     - Clean generated data files"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 seeds                    # Extract recipe seeds from sitemaps"
    echo "  $0 crawl 10                 # Crawl 10 recipes for testing"
    echo "  $0 crawl 100                # Crawl 100 recipes"
    echo "  $0 parse                    # Parse downloaded recipes"
    echo "  $0 index                    # Build search index from 10 test recipes"
    echo "  $0 search \"chicken pasta\"   # Search for recipes"
    echo "  $0 all                      # Run complete pipeline"
    echo "  $0 test                     # Run unit tests"
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
    
    # Check if seed file exists
    if [ ! -f "data/seed_analysis/recipe_seeds.txt" ]; then
        print_error "Seed file not found. Run 'seeds' target first."
        exit 1
    fi
    
    # Get limit from first argument or default to 10 for testing
    local limit=${1:-10}
    print_status "Crawling $limit recipes for testing..."
    
    python3 -m crawler.run --phase crawl \
        --seeds data/seed_analysis/recipe_seeds.txt \
        --out data/raw \
        --limit $limit \
        --qps 0.5
    
    print_success "Phase B completed - check data/raw/ for downloaded pages"
}

# Function to run Phase C (parse)
run_parse() {
    print_status "Running Phase C: Parser & Normalization"
    
    # Check if raw data exists
    if [ ! -d "data/raw" ] || [ -z "$(ls -A data/raw 2>/dev/null)" ]; then
        print_error "Raw data not found. Run 'crawl' target first."
        exit 1
    fi
    
    python3 -m parser.run --raw data/raw --out data/normalized/recipes.jsonl
    print_success "Phase C completed - check data/normalized/recipes.jsonl for parsed recipes"
}

# Function to run Phase D (index)
run_index() {
    print_status "Running Phase D: Build Search Index"
    
    # Check if normalized data exists
    if [ ! -f "data/normalized/recipes.jsonl" ]; then
        print_error "Normalized recipe data not found. Run 'parse' target first."
        exit 1
    fi
    
    python3 -m indexer.run --input data/normalized/recipes.jsonl --out data/index/v1
    print_success "Phase D (Index) completed - check data/index/v1/ for index files"
}

# Function to run Phase D (search)
run_search() {
    print_status "Running Phase D: Search CLI"
    
    # Check if index exists
    if [ ! -d "data/index/v1" ]; then
        print_error "Index not found. Run 'index' target first."
        exit 1
    fi
    
    # Get search query from second argument or use default
    local query=${1:-"chicken pasta"}
    print_status "Searching for: '$query'"
    
    python3 -m search_cli.run --index data/index/v1 --metric bm25 --q "$query" --k 5
    print_success "Search completed"
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
            print_status "Running all phases..."
            run_seeds
            print_warning "Remaining phases not implemented yet"
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

