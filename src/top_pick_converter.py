from PIL import Image
from collections import Counter

# get most common color in img (add to refresh -> rgb val into data.js pls pls pls)
img = img.convert("RGB")
return Counter(img.getdata()).most_common(1)[0][0]

