# pylint: disable=C0103, too-few-public-methods, locally-disabled,no-self-use, unused-argument
__doc__ = ('Arrange and merge pdfs and images for a given folder root. Currently this code is highly specific\n\n'
           'Syntax: path_export.py <root> <output>\n'
            'Args\n'
            'root: root folder to walk\n'
            'output: output file\n'
            'Example:\n'
            'path_export C:\temp C:\temp\results.csv'
            )


import argparse
import funclib.iolib as _iolib


def main():
    '''main'''
    cmdline = argparse.ArgumentParser(description=__doc__) #use the module __doc__

    #named: eg script.py -part head
    cmdline.add_argument('-part', '--part', help='The region part eg. head.', required=True)

    #argument present or not: e.g. scipt.py -f
    #args.fix == True
    cmdline.add_argument('-f', '--fix', help='Fix it', action='store_true')

    #positional: e.g. scipt.py c:/temp
    #args.folder == 'c:/temp'
    cmdline.add_argument('folder', help='folder')

    #get a list from comma delimited args
    
    #see https://stackoverflow.com/questions/15753701/argparse-option-for-passing-a-list-as-option
    f = lambda s: [int(itme) for item in s.split(',')]
    parser.add_argument('-l', '--list', type=f, help='delimited list input, eg -l 12,13,14')
    #mylist = args.list
    
    #multiple positional arguments: e.g. script.py -files_in 'c:/' 'd:/'
    #for fname in args.files_in:
    cmdline.add_argument('-i', '--files_in', help='VGG JSON files to merge', nargs='+')
    args = cmdline.parse_args()
    if args.recurse == True:
        #dostuff
    
    
if __name__ == "__main__":
    main()


