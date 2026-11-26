import argparse

from app import gui
from i18n import LANGUAGES

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="DEFAULT")
    parser.add_argument("--lang", choices=LANGUAGES)
    args = parser.parse_args()
    gui(args.profile, args.lang)
