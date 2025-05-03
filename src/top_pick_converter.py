from PIL import Image
from collections import Counter

def get_background_color(img):
    img = img.convert("RGB")
    return Counter(img.getdata()).most_common(1)[0][0]

def resize_and_crop_center(img, tw, th):
    w, h = img.size
    if w/h > tw/th:
        new_h = th
        new_w = int(w * th / h)
    else:
        new_w = tw
        new_h = int(h * tw / w)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - tw)//2
    top  = (new_h - th)//2
    return img.crop((left, top, left+tw, top+th))

def create_horizontal_gradient(width, height, start_rgba, solid_ratio=0.7, gradient_ratio=0.3):
    """
    Creates an RGBA horizontal gradient image.

    Parameters:
    - solid_ratio: Proportion of width with solid color (alpha=255)
    - gradient_ratio: Proportion of width used for gradient fade (alpha from 255 → 0)

    The remaining width will have alpha=0.
    """
    base = Image.new("RGBA", (width, height), start_rgba)
    alpha = Image.new("L", (width, height), 0)
    pix = alpha.load()

    solid_width = int(width * solid_ratio)
    gradient_width = int(width * gradient_ratio)

    for x in range(width):
        if x < solid_width:
            a = 255
        elif x < solid_width + gradient_width:
            a = int(255 * (1 - (x - solid_width) / gradient_width))
        else:
            a = 0
        for y in range(height):
            pix[x, y] = a

    base.putalpha(alpha)
    return base

def apply_gradient_overlay(base_img, grad_img, pos=(0,0)):
    base = base_img.convert("RGBA")
    base.paste(grad_img, pos, grad_img)
    return base

def build_card(portrait_path, output_path="card_output2.png"):
    # specs
    CW, CH = 782, 330
    IW, IH = 410, 330
    GW     = 514

    # load & prep
    portrait = Image.open(portrait_path)
    bg       = get_background_color(portrait)
    portrait = resize_and_crop_center(portrait, IW, IH).convert("RGBA")

    # card base
    card = Image.new("RGB", (CW, CH), bg)
    card.paste(portrait, (CW - IW, 0), portrait)

    # gradient
    start_rgba = bg + (255,)
    gradient = create_horizontal_gradient(GW, CH, start_rgba, solid_ratio=0.7, gradient_ratio=0.3)


    # composite
    final = apply_gradient_overlay(card, gradient, (0,0))
    final.save(output_path)
    final.show()

# test
if __name__ == "__main__":
    build_card("thumbnail.jpg")
