# pylint: disable=C0103, too-few-public-methods, locally-disabled, no-self-use, unused-argument
'''View images
'''
import argparse
import os.path as path


import opencvlib.imgpipes.generators as G
from opencvlib.imgpipes import transforms
from opencvlib.view import show
import funclib.iolib as iolib


def main():
    '''
    View image regions in a vgg.json file
    Space advances to the next region, pressing n will be recorded
    in an output text file.

    Example:
    view_images.py part:head "C:/Users/Graham Monkman/OneDrive/Documents/PHD/images/bass/angler/bass-angler.json"
    '''

    cmdline = argparse.ArgumentParser(description='View image regions in a vgg.json file'
                                      'Space advances to the next region, pressing n will be recorded '
                                      'in an output text file.\n\n'
                                      'Example:\n'
                                      'view_images.py -part whole "C:/Users/Graham Monkman/OneDrive/Documents/PHD/images/bass/angler"'
                                      )
    cmdline.add_argument('-part', '--part', help='The region part eg. head.', required=True)
    cmdline.add_argument('-spp', '--spp', help='The species.', required=True)
    cmdline.add_argument('vggfolder', help='VGG JSON file to manipulate')
    args = cmdline.parse_args()


    fld = path.normpath(args.vggfolder)
    vggsp = G.VGGSearchParams(fld, parts=[args.part], species=[args.spp])

    #t1 = transforms.Transform(transforms.togreyscale)
    t2 = transforms.Transform(transforms.equalize_adapthist)
    T = transforms.Transforms(None, t2)

    out = []
    reg = G.VGGDigiKam(None, vggsp, transforms=T)
    
    for img, f, dummy in reg.generate():
        k, dummy1 = show(img)
        if k == 110: #n
            out.append(f)
    iolib.write_to_file(out)



if __name__ == "__main__":
    main()
    #sys.exit(int(main() or 0))
