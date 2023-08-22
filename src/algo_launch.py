import argparse


def define_args():
    parser = argparse.ArgumentParser(description='run algo on chosen directory')
    parser.add_argument('-d1', '-obfuscated_loc1', help='enter location of codebase', dest='codebase1', required=True)
    parser.add_argument('-d2', '-obfuscated_loc2', help='enter location of codebase', dest='codebase2', required=True)
    parser.add_argument('-l', help='specify language of database you want to analyse', dest='lang', required=True)
    args = parser.parse_args()
    return args
