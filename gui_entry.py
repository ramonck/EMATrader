import argparse

from app import gui

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="DEFAULT")
    gui(parser.parse_args().profile)
