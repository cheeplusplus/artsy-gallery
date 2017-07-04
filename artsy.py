#!/usr/bin/env python3
'''Artsy, an artsy sort of gallery.'''

import os
import shutil
from distutils.dir_util import copy_tree
from resizeimage import resizeimage
from PIL import Image
from data import get_art_data
from templater import Templater


templater = Templater("templates")


def generateThumbnailSize(img, width, filename):
    thumb = resizeimage.resize_thumbnail(img, [width, width])
    thumb.save(filename, img.format)


def generateThumbnails(artistdir, image, widths):
    thumbnails = {}

    def get_path(size):
        return "%s/%s_%s.%s" % (artistdir, image["slug"], size, image["imgext"])

    # Copy full image file
    fullpath = get_path("full")
    shutil.copy2(image["relpath"], fullpath)
    thumbnails["full"] = os.path.basename(fullpath)

    # Generate actual thumbnails
    with Image.open(image["relpath"]) as img:
        for width in list(widths):
            filename = get_path(width)
            generateThumbnailSize(img, width, filename)
            thumbnails[width] = os.path.basename(filename)

    return thumbnails


# TODO: Don't update files that don't need updating
def generate_static_site(input_dir, output_dir, limit):
    '''Output templates to filesystem.'''
    # Get data and fail on error
    data, errors = get_art_data(input_dir, limit)
    if len(errors) > 0:
        print("Got parser errors")
        for error in errors:
            print(error)
        return False

    # Recreate the output directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir, ignore_errors=True)

    # Copy static files (and create output dir)
    copy_tree("static", output_dir)

    # Generate image templates
    for image in data["files"]:
        artistslug = image["artist"]["slug"]
        slug = image["slug"]
        artistdir = "%s/%s" % (output_dir, artistslug)
        if not os.path.exists(artistdir):
            os.makedirs(artistdir)
        outfile = "%s/%s.html" % (artistdir, slug)

        # Generate thumbnails
        thumbnails = generateThumbnails(artistdir, image, [120, 512])
        image["thumbnails"] = thumbnails

        # Write templated file
        with open(outfile, "w") as f:
            td = templater.generate("image", **image)
            f.write(td)

    # Generate artist templates
    for artist in data["artists"]:
        slug = artist["slug"]
        artistdir = "%s/%s" % (output_dir, slug)
        outfile = "%s/index.html" % (artistdir)

        # Write templated file
        with open(outfile, "w") as f:
            td = templater.generate("artist", **artist)
            f.write(td)

    # Generate index file
    with open("%s/index.html" % output_dir, "w") as f:
        td = templater.generate("index", **data)
        f.write(td)

    return True


if __name__ == "__main__":
    if generate_static_site("testdata", "output"):
        print("Files written.")
    else:
        print("Failed with errors.")
