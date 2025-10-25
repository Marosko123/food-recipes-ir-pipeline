#!/bin/bash
# Quick test script for all search types
# Author: Maroš Bednár (AIS 116822)

echo "========================================================================"
echo "  TESTING ALL SEARCH TYPES"
echo "  Food Recipes IR Pipeline"
echo "========================================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is required"
    exit 1
fi

# Check if index exists
if [ ! -d "index/lucene/v2" ] && [ ! -d "data/index/v1" ]; then
    echo "ERROR: No index found!"
    echo ""
    echo "Build an index first:"
    echo "  ./packaging/run.sh index_lucene  (Lupyne, recommended)"
    echo "  ./packaging/run.sh index         (TSV, baseline)"
    exit 1
fi

# Create logs directory
mkdir -p data/logs

# Clear old log
rm -f data/logs/search_test.log
rm -f data/logs/search_test_summary.json

echo "Starting comprehensive search test..."
echo ""

# Run test suite
python3 test_all_searches.py

echo ""
echo "========================================================================"
echo "  RESULTS"
echo "========================================================================"
echo ""

# Show log location
if [ -f "data/logs/search_test.log" ]; then
    echo "✓ Test log saved: data/logs/search_test.log"
    echo "✓ Summary JSON: data/logs/search_test_summary.json"
    echo ""
    
    # Show quick summary
    echo "Quick Summary:"
    echo "---"
    tail -20 data/logs/search_test.log
    echo ""
    echo "---"
    echo ""
    echo "View full log:"
    echo "  cat data/logs/search_test.log"
    echo "  less data/logs/search_test.log"
    echo ""
    echo "View summary JSON:"
    echo "  cat data/logs/search_test_summary.json | python3 -m json.tool"
else
    echo "✗ Test log not created - check for errors above"
    exit 1
fi

echo "========================================================================"
echo "  TEST COMPLETE"
echo "========================================================================"
