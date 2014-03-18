import os, sys


def read_file(file_to_read):
    file = open( "%s" % file_to_read, 'r')
    copy = file.readlines()
    string = ''.join(copy)
    return string
