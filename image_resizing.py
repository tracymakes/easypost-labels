import os

from PIL import Image


"""
1. Open up the folder of images (get the latest folder somehow?)
2. Loop through the folder (use a counter to keep track of image position)
    - Create blank paper-sized image (if one isn't created already)
    - Grab image
    - Determine whether the image needs to be rotated correctly
        - Rotate if needed
    - Add to paper (even: top, odd: bottom)
"""


#for i, row in enumerate(csv_rows):
current_dir = os.path.dirname(os.path.abspath(__file__))
items = os.listdir(current_dir)

counter = 0
for item in items:
    try:
        im = Image.open(item)
    except IOError:
        #print "Not an image"
        continue

    # if item's width is 1200, means it's a vertical image that needs to be rotated
    if im.size[0] == 1200:
        im = im.rotate(90)

    # if iteration is even, put the image at the top of the blank file
    #print counter
    if counter % 2 == 0:
        empty = Image.open("../blank.jpg")
        empty.paste(im, (300,200))
    else:
        empty.paste(im, (300,1900))
        save_name = "created-%s.jpeg" % counter
        empty.save(save_name)

    counter += 1

save_name = "created-%s.jpeg" % counter
empty.save(save_name, quality=95)
