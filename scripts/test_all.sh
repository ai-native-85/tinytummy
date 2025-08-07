#!/bin/bash

# Test runner script for TinyTummy backend

echo "🧪 Running TinyTummy Backend Tests"
echo "=================================="

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing..."
    pip install pytest pytest-cov
fi

# Run tests with coverage
echo "📊 Running tests with coverage..."
pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

# Check test results
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
    echo "📈 Coverage report generated in htmlcov/index.html"
else
    echo "❌ Some tests failed!"
    exit 1
fi

echo ""
echo "🎯 Test Summary:"
echo "- Authentication tests"
echo "- Meal service tests" 
echo "- Integration tests"
echo "- Error handling tests"
echo "- Premium feature tests"
echo "- Gamification tests"
echo "- Offline sync tests" 