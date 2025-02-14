# pylint: disable=C0302, line-too-long, too-few-public-methods, too-many-branches, too-many-statements, no-member
'''General export of multipage pdfs to images

PDFs are converted to images in a subfolder, created programmatically.

Arguments
    -s: <path containing pdf>

e.g.
pdf2img.py -s c:/temp/pdfs
'''
import argparse
import os.path as path


from pdf2image import convert_from_path
import funclib.iolib as iolib

_POP_PATH = 'C:/Program Files (x86)/poppler-0.68.0/bin' #path to poppler


def _make_output_fold(pdf_path):
    '''str -> str
    gets issue'''
    d, fname, _ = iolib.get_file_parts(pdf_path)
    fld = '%s/%s' % (d, fname)
    iolib.create_folder(fld)
    return fld


def _get_img_name(pdf_path, pg_nr, ext='.jpg'):
    assert ext[0] == '.', 'ext argument is dotted'
    return path.normpath('%s/%s%s' % (_make_output_fold(pdf_path), pg_nr, ext))



def main():
    '''main'''
    cmdline = argparse.ArgumentParser(description=__doc__) #use the module __doc__

    #named: eg script.py -part head
    cmdline.add_argument('source', help='Source PDFs')
    args = cmdline.parse_args()
    src = path.normpath(args.source)

    n = sum([1 for x in iolib.file_list_generator1(src, wildcards='*.pdf', recurse=False)])
    PP = iolib.PrintProgress(bar_length=20, init_msg='Processing pdfs...', maximum=n)

    for _, _, _, full_pdf_path in iolib.file_list_generator_dfe(src, wildcards='*.pdf', recurse=False):
        _make_output_fold(full_pdf_path)
        img = convert_from_path(full_pdf_path, poppler_path=_POP_PATH, dpi=300, fmt='jpg')

        for x, i in enumerate(img, 1):
            imgout = _get_img_name(full_pdf_path, x)
            i.save(fp=imgout, dpi=(300, 300))

        PP.increment(show_time_left=True)



if __name__ == "__main__":
    main()
