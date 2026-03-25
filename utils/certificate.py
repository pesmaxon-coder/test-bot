import io, math, os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

W, H = 1280, 905

# Logo fayli yo'li
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "et_logo.png")


def gf(size, bold=False):
    paths = ([
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ] if bold else [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ])
    for p in paths:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except: pass
    return ImageFont.load_default()


def ctext(d, text, y, font, color, w=W):
    bb = d.textbbox((0,0), text, font=font)
    d.text(((w-(bb[2]-bb[0]))//2, y), text, font=font, fill=color)


def wrap(d, text, max_w, font):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        t = (cur+" "+word).strip()
        if d.textbbox((0,0), t, font=font)[2] <= max_w:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = word
    if cur: lines.append(cur)
    return lines


def paste_logo(img, x, y, width):
    """Haqiqiy logoni rasmga joylashtirish"""
    try:
        logo = Image.open(LOGO_PATH).convert("RGBA")
        ratio = width / logo.width
        new_h = int(logo.height * ratio)
        logo = logo.resize((width, new_h), Image.LANCZOS)
        img.paste(logo, (x, y), logo)
        return new_h
    except Exception:
        # Logo topilmasa matn bilan
        d = ImageDraw.Draw(img)
        d.text((x, y), "ENGLISH TEAM", font=gf(30, True), fill=(230,175,30))
        return 40


def draw_seal(d, cx, cy, r=72, author=""):
    """Oltin muhr - initsiallarsiz"""
    gold1=(190,145,25); gold2=(220,180,45); cream=(255,248,225)
    for i in range(28):
        angle = math.radians(i*360/28)
        x1=cx+int((r-6)*math.cos(angle)); y1=cy+int((r-6)*math.sin(angle))
        x2=cx+int((r+5)*math.cos(angle)); y2=cy+int((r+5)*math.sin(angle))
        d.line([x1,y1,x2,y2], fill=gold1, width=4)
    d.ellipse([cx-r,cy-r,cx+r,cy+r], fill=gold2)
    d.ellipse([cx-r+7,cy-r+7,cx+r-7,cy+r-7], fill=gold1)
    d.ellipse([cx-r+16,cy-r+16,cx+r-16,cy+r-16], fill=cream)
    # Yulduzcha
    for i in range(6):
        angle = math.radians(i*60)
        x1=cx+int((r-22)*math.cos(angle)); y1=cy+int((r-22)*math.sin(angle))
        x2=cx+int((r-32)*math.cos(angle+math.radians(30)))
        y2=cy+int((r-32)*math.sin(angle+math.radians(30)))
        d.line([cx,cy,x1,y1], fill=gold1, width=2)


def make_buf(img):
    b = io.BytesIO(); img.save(b, format="PNG"); b.seek(0); return b


def build_body(full_name, test_title, correct, total, pct, author):
    return (full_name + " " + test_title + " fanidan online testda ishtirok etib "
            + str(total) + " ta savoldan " + str(correct) + " ta ("
            + str(int(round(pct,0))) + "%) natija korsatganligi uchun "
            + author + " tomonidan taqdirlanadi.")


def draw_footer(d, img, author, date_str, phone1="", phone2="", y_start=None, style="dark"):
    """Pastki qism: muallif, sana, telefon"""
    if y_start is None:
        y_start = H - 130
    color = (10,10,10) if style=="light" else (255,255,255)
    sub_color = (80,80,80) if style=="light" else (200,200,200)

    d.text((130, y_start), author, font=gf(27,True), fill=color)
    d.text((130, y_start+36), date_str, font=gf(17), fill=sub_color)

    if phone1 or phone2:
        fp = gf(24, True)
        px = W//2 + 60
        if phone1:
            d.text((px, y_start+5), phone1, font=fp, fill=color)
        if phone2:
            d.text((px, y_start+40), phone2, font=fp, fill=color)


# ===========================
# DIZAYN 1: Ko'k Chevron
# ===========================
def d1(full_name, test_title, correct, total, pct, date_str, author, phone1="", phone2=""):
    img = Image.new("RGB", (W,H), (232,237,248))
    d = ImageDraw.Draw(img)
    navy=(25,45,100)

    d.polygon([(0,0),(W,0),(W,H//2),(W//2,0)], fill=(222,229,245))
    d.polygon([(0,H//2),(0,H),(W//2,H)], fill=(218,226,242))
    for i in range(4):
        off=i*65; sz=105-i*12
        d.polygon([(0,off+60),(sz//2,off+60+sz//2),(0,off+60+sz),
                   (45,off+60+sz),(45+sz//2,off+60+sz//2),(45,off+60)], fill=navy)
    d.rectangle([W-85,0,W,H], fill=navy)
    d.rectangle([W-92,0,W-85,H], fill=(38,62,125))

    # Logo
    lh = paste_logo(img, W//2-180, 30, 360)
    title_y = 30 + lh + 10

    ctext(d, "SERTIFIKAT", title_y, gf(70,True), (10,10,10), W-85)
    draw_seal(d, W-170, title_y+110, r=75, author=author)
    d.rectangle([120, title_y+90, W-115, title_y+93], fill=(40,40,70))

    body = build_body(full_name, test_title, correct, total, pct, author)
    lines = wrap(d, body, W-280, gf(21))
    sy = title_y + 105
    for i,line in enumerate(lines):
        bb = d.textbbox((0,0),line,font=gf(21))
        d.text(((W-85-(bb[2]-bb[0]))//2, sy+i*31), line, font=gf(21), fill=(25,25,50))

    ly2 = sy + len(lines)*31 + 35
    d.rectangle([120,ly2,W//2-40,ly2+2], fill=(50,55,80))
    d.rectangle([W//2+40,ly2,W-115,ly2+2], fill=(50,55,80))
    d.rectangle([W//2-70,ly2,W//2+70,ly2+2], fill=(50,55,80))

    fy = H-120
    d.rectangle([120,fy-4,W-115,fy-2], fill=(110,120,155))
    draw_footer(d, img, author, date_str, phone1, phone2, fy+5, style="light")
    return make_buf(img)


# ===========================
# DIZAYN 2: Oltin Chegara
# ===========================
def d2(full_name, test_title, correct, total, pct, date_str, author, phone1="", phone2=""):
    img = Image.new("RGB", (W,H), (255,255,255))
    d = ImageDraw.Draw(img)
    navy=(25,45,100); gold=(215,170,25)

    d.polygon([(W-210,0),(W,0),(W,210)], fill=navy)
    d.polygon([(W-150,0),(W,0),(W,150)], fill=(38,62,125))
    d.polygon([(0,H-210),(210,H),(0,H)], fill=navy)
    d.polygon([(0,H-150),(150,H),(0,H)], fill=(38,62,125))
    d.polygon([(W-95,H),(W,H-95),(W,H)], fill=gold)
    d.polygon([(0,75),(75,0),(0,0)], fill=gold)
    d.rectangle([35,35,W-35,H-35], outline=gold, width=4)
    d.rectangle([42,42,W-42,H-42], outline=gold, width=1)

    # Logo (chap)
    lh = paste_logo(img, 60, 55, 220)

    # Medal (o'ng)
    mx,my = W-145,110
    mc=[(175,45,175),(45,175,45),(45,45,195),(195,175,25)]
    for i in range(8):
        a1=math.radians(i*45); a2=math.radians(i*45+45)
        d.polygon([(mx,my),(mx+int(50*math.cos(a1)),my+int(50*math.sin(a1))),
                   (mx+int(50*math.cos(a2)),my+int(50*math.sin(a2)))], fill=mc[i%4])
    d.ellipse([mx-33,my-33,mx+33,my+33], fill=(235,215,45))
    d.ellipse([mx-26,my-26,mx+26,my+26], fill=(255,235,75))
    d.polygon([(mx-17,my+33),(mx+17,my+33),(mx+11,my+72),(mx,my+58),(mx-11,my+72)], fill=(195,155,18))

    title_y = 60 + lh + 5
    ctext(d, "SERTIFIKAT", title_y, gf(70,True), (10,10,10))
    d.rectangle([95, title_y+80, W-95, title_y+83], fill=(10,10,10))

    body = build_body(full_name, test_title, correct, total, pct, author)
    lines = wrap(d, body, W-250, gf(21))
    sy = title_y + 95
    for i,line in enumerate(lines):
        bb = d.textbbox((0,0),line,font=gf(21))
        d.text(((W-(bb[2]-bb[0]))//2, sy+i*33), line, font=gf(21), fill=(25,25,50))

    fpy = H-165
    d.rectangle([95,fpy,460,fpy+2], fill=(10,10,10))
    draw_footer(d, img, author, date_str, phone1, phone2, fpy+8, style="light")
    return make_buf(img)


# ===========================
# DIZAYN 3: Qora-Oltin
# ===========================
def d3(full_name, test_title, correct, total, pct, date_str, author, phone1="", phone2=""):
    img = Image.new("RGB", (W,H), (255,255,255))
    d = ImageDraw.Draw(img)
    black=(18,18,18); gold=(200,155,25); lgold=(230,185,55)

    d.polygon([(0,0),(220,0),(0,220)], fill=black)
    d.polygon([(185,0),(220,0),(0,220),(0,185)], fill=gold)
    d.polygon([(W-160,0),(W,0),(W,160)], fill=black)
    d.polygon([(W-155,0),(W-110,0),(W,110),(W,155)], fill=gold)
    d.polygon([(0,H-180),(180,H),(0,H)], fill=black)
    d.polygon([(0,H-180),(50,H-180),(180,H),(130,H)], fill=gold)
    d.polygon([(W-200,H),(W,H),(W,H-200)], fill=black)
    d.polygon([(W-200,H),(W-140,H),(W,H-140),(W,H-200)], fill=gold)

    wave_y = H-160
    pts = [(0,wave_y+40)]
    for x in range(0,W+1,8):
        pts.append((x, wave_y+int(30*math.sin(x/80))+int(15*math.sin(x/40))))
    pts.extend([(W,H),(0,H)])
    d.polygon(pts, fill=gold)
    pts2 = [(0,wave_y+55)]
    for x in range(0,W+1,8):
        pts2.append((x, wave_y+50+int(20*math.sin(x/70+1))))
    pts2.extend([(W,H),(0,H)])
    d.polygon(pts2, fill=lgold)

    # Logo markazda
    lh = paste_logo(img, W//2-190, 30, 300)
    title_y = 30 + lh + 5

    mx2,my2 = W-155,90
    d.ellipse([mx2-42,my2-42,mx2+42,my2+42], fill=(210,170,30))
    d.ellipse([mx2-36,my2-36,mx2+36,my2+36], fill=(235,195,55))
    d.ellipse([mx2-28,my2-28,mx2+28,my2+28], fill=(250,220,80))
    d.polygon([(mx2-14,my2+36),(mx2+14,my2+36),(mx2+9,my2+72),
               (mx2,my2+58),(mx2-9,my2+72)], fill=gold)

    ctext(d, "SERTIFIKAT", title_y, gf(85,True), (10,10,10))
    d.rectangle([80, title_y+90, W-80, title_y+93], fill=(180,140,20))

    body = build_body(full_name, test_title, correct, total, pct, author)
    lines = wrap(d, body, W-200, gf(22))
    sy = title_y + 105
    for i,line in enumerate(lines):
        bb = d.textbbox((0,0),line,font=gf(22))
        d.text(((W-(bb[2]-bb[0]))//2, sy+i*34), line, font=gf(22), fill=(25,25,25))

    fy = H-150
    draw_footer(d, img, author, date_str, phone1, phone2, fy, style="light")
    return make_buf(img)


# ===========================
# DIZAYN 4: To'q Ko'k Premium
# ===========================
def d4(full_name, test_title, correct, total, pct, date_str, author, phone1="", phone2=""):
    img = Image.new("RGB", (W,H), (15,25,55))
    d = ImageDraw.Draw(img)
    gold=(210,175,40); lgold=(240,205,70)

    for off in [8,14,20]:
        d.rectangle([off,off,W-off,H-off], outline=gold, width=1)

    d.polygon([(0,0),(300,0),(0,300)], fill=(22,38,80))
    d.polygon([(W,H),(W-300,H),(W,H-300)], fill=(22,38,80))

    lh = paste_logo(img, W//2-170, 28, 340)
    title_y = 28 + lh + 8

    ctext(d, "SERTIFIKAT", title_y, gf(72,True), gold)
    d.rectangle([100, title_y+80, W-100, title_y+83], fill=gold)

    body = build_body(full_name, test_title, correct, total, pct, author)
    lines = wrap(d, body, W-220, gf(22))
    sy = title_y + 98
    for i,line in enumerate(lines):
        bb = d.textbbox((0,0),line,font=gf(22))
        d.text(((W-(bb[2]-bb[0]))//2, sy+i*33), line, font=gf(22), fill=(200,210,235))

    draw_seal(d, W-150, title_y+50, r=65, author=author)

    fy = H-125
    d.rectangle([100,fy-3,W-100,fy-1], fill=gold)
    draw_footer(d, img, author, date_str, phone1, phone2, fy+5, style="dark")
    return make_buf(img)


# ===========================
# DIZAYN 5: Yashil Akademik
# ===========================
def d5(full_name, test_title, correct, total, pct, date_str, author, phone1="", phone2=""):
    img = Image.new("RGB", (W,H), (245,255,248))
    d = ImageDraw.Draw(img)
    green=(20,130,55); dgreen=(15,100,40); gold=(195,155,25)

    d.rectangle([0,0,W,18], fill=green)
    d.rectangle([0,H-18,W,H], fill=green)
    d.rectangle([0,0,18,H], fill=green)
    d.rectangle([W-18,0,W,H], fill=green)
    d.rectangle([18,18,W-18,35], fill=(35,155,70))
    d.rectangle([18,H-35,W-18,H-18], fill=(35,155,70))
    d.polygon([(W-220,18),(W-18,18),(W-18,220)], fill=(35,175,75))

    lh = paste_logo(img, W//2-165, 45, 330)
    title_y = 45 + lh + 5

    ctext(d, "SERTIFIKAT", title_y, gf(70,True), dgreen)
    d.rectangle([80, title_y+80, W-80, title_y+84], fill=green)

    body = build_body(full_name, test_title, correct, total, pct, author)
    lines = wrap(d, body, W-180, gf(22))
    sy = title_y + 100
    for i,line in enumerate(lines):
        bb = d.textbbox((0,0),line,font=gf(22))
        d.text(((W-(bb[2]-bb[0]))//2, sy+i*33), line, font=gf(22), fill=(20,40,20))

    draw_seal(d, W-120, title_y+50, r=65, author=author)

    fy = H-125
    d.rectangle([80,fy-3,W-80,fy-1], fill=green)
    draw_footer(d, img, author, date_str, phone1, phone2, fy+5, style="light")
    return make_buf(img)


# ===========================
# DIZAYN 6: Vintage Krem
# ===========================
def d6(full_name, test_title, correct, total, pct, date_str, author, phone1="", phone2=""):
    img = Image.new("RGB", (W,H), (248,240,215))
    d = ImageDraw.Draw(img)
    brown=(120,75,25); gold=(185,140,30)

    d.rectangle([0,0,W,90], fill=(170,120,48))
    d.rectangle([0,H-75,W,H], fill=(170,120,48))
    for off in [8,14]:
        d.rectangle([off,off,W-off,H-off], outline=(140,95,22), width=1)

    lh = paste_logo(img, W//2-160, 15, 320)
    title_y = 15 + lh - 5

    ctext(d, "SERTIFIKAT", title_y, gf(68,True), (255,245,218))
    d.rectangle([90, title_y+78, W-90, title_y+81], fill=(140,95,22))

    body = build_body(full_name, test_title, correct, total, pct, author)
    lines = wrap(d, body, W-200, gf(22))
    sy = title_y + 95
    for i,line in enumerate(lines):
        bb = d.textbbox((0,0),line,font=gf(22))
        d.text(((W-(bb[2]-bb[0]))//2, sy+i*33), line, font=gf(22), fill=(60,35,8))

    draw_seal(d, W-140, title_y+50, r=68, author=author)

    fy = H-120
    d.rectangle([90,fy-3,W-90,fy-1], fill=(140,95,22))
    draw_footer(d, img, author, date_str, phone1, phone2, fy+5, style="light")
    return make_buf(img)


# ===========================
# DIZAYN 7: Rang-Barang Modern
# ===========================
def d7(full_name, test_title, correct, total, pct, date_str, author, phone1="", phone2=""):
    img = Image.new("RGB", (W,H), (255,255,255))
    d = ImageDraw.Draw(img)

    d.polygon([(0,0),(280,0),(170,150),(0,150)], fill=(225,38,108))
    d.polygon([(W,0),(W-210,0),(W,210)], fill=(255,165,20))
    d.polygon([(0,H),(190,H),(0,H-168)], fill=(88,48,195))
    d.polygon([(W,H),(W-230,H),(W,H-190)], fill=(22,172,112))

    lh = paste_logo(img, W//2-165, 35, 330)
    title_y = 35 + lh + 5

    ctext(d, "SERTIFIKAT", title_y, gf(70,True), (88,48,195))
    d.rectangle([90, title_y+80, W-90, title_y+84], fill=(225,38,108))

    body = build_body(full_name, test_title, correct, total, pct, author)
    lines = wrap(d, body, W-200, gf(22))
    sy = title_y + 100
    for i,line in enumerate(lines):
        bb = d.textbbox((0,0),line,font=gf(22))
        d.text(((W-(bb[2]-bb[0]))//2, sy+i*33), line, font=gf(22), fill=(30,30,30))

    draw_seal(d, W-140, title_y+50, r=65, author=author)

    fy = H-125
    d.rectangle([90,fy-3,W-90,fy-1], fill=(225,38,108))
    draw_footer(d, img, author, date_str, phone1, phone2, fy+5, style="light")
    return make_buf(img)


# ===========================
# DIZAYN 8: Geometrik To'q
# ===========================
def d8(full_name, test_title, correct, total, pct, date_str, author, phone1="", phone2=""):
    img = Image.new("RGB", (W,H), (20,30,50))
    d = ImageDraw.Draw(img)
    gold=(205,172,52); lgold=(230,200,75)

    d.polygon([(0,0),(430,0),(265,215),(0,215)], fill=(30,48,90))
    d.polygon([(0,0),(315,0),(188,158)], fill=(40,65,118))
    d.polygon([(W,H),(W-370,H),(W-215,H-188),(W,H-188)], fill=(30,48,90))
    d.rectangle([0,222,W,227], fill=gold)
    d.rectangle([0,H-90,W,H-85], fill=gold)

    lh = paste_logo(img, W//2-165, 30, 330)
    title_y = 30 + lh

    ctext(d, "SERTIFIKAT", title_y, gf(70,True), gold)
    draw_seal(d, W-148, title_y+60, r=65, author=author)

    body = build_body(full_name, test_title, correct, total, pct, author)
    lines = wrap(d, body, W-180, gf(22))
    sy = title_y + 90
    for i,line in enumerate(lines):
        bb = d.textbbox((0,0),line,font=gf(22))
        d.text(((W-(bb[2]-bb[0]))//2, sy+i*33), line, font=gf(22), fill=(185,200,225))

    fy = H-120
    d.rectangle([100,fy-3,W-100,fy-1], fill=gold)
    draw_footer(d, img, author, date_str, phone1, phone2, fy+5, style="dark")
    return make_buf(img)


DESIGNS = {1:d1, 2:d2, 3:d3, 4:d4, 5:d5, 6:d6, 7:d7, 8:d8}


def generate_certificate(design_num, full_name, test_title, correct, total, author,
                          phone1="+998 95 907 3030", phone2="+998 97 984 3030"):
    pct = (correct/total*100) if total > 0 else 0
    dt = datetime.now().strftime("%d.%m.%Y")
    fn = DESIGNS.get(design_num, d1)
    try:
        return fn(full_name, test_title, correct, total, pct, dt, author, phone1, phone2)
    except Exception as e:
        return d1(full_name, test_title, correct, total, pct, dt, author, phone1, phone2)