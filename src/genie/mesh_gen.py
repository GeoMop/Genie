"""
Script for generate mesh in separate process.
"""

import time


def main():
    for i in range(1, 6):
        time.sleep(1)
        print(i)
    print("Done.")


if __name__ == "__main__":
    main()
