"""Run the product-specific offline pipeline by path.

Usage: python data-pipeline/run.py [case|all] [--seed N]
"""
from engine.pipeline import main

if __name__ == "__main__":
    main()
