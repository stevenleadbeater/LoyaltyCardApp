#!/usr/bin/env python3
import sys
import os

# Allow running from source tree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from application import LoyaltyCardApplication


def main():
    app = LoyaltyCardApplication()
    return app.run(sys.argv)


if __name__ == '__main__':
    sys.exit(main())
