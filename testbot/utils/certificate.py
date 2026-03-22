import os
import io
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 850


def get_font(size, bold=False):
    paths = ([
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ] if bold else [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ])
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def center_text(d, text, y, font, color):
    bb = d.textbbox((0, 0), text, font=font)
    x = (W - (bb[2] - bb[0])) // 2
    d.text((x, y), text, font=font, fill=color)


def body_text(d, text, mx, sy, mw, font, color, sp=12):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textbbox((0, 0), t, font=font)[2] <= mw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    lh = d.textbbox((0, 0), "A", font=font)[3] + sp
    for i, line in enumerate(lines):
        lw = d.textbbox((0, 0), line, font=font)[2]
        d.text((mx + (mw - lw) // 2, sy + i * lh), line, font=font, fill=color)
    return sy + len(lines) * lh


def make_text(name, title, c, t, pct, author):
    return (
        f"Assalomu alaykum hurmatli {name}, siz {title} fanidan "
        f"Online testida ishtirok etib {t} ta savol ichidan {c} ta "
        f"({pct:.0f}%) natija ko'rsatganligingiz uchun {author} "
        f"tomonidan ushbu sertifikat bilan taqdirlandingiz. "
        f"Kelgusi testlarimizda ham faol ishtirokingiz uchun tashakkur."
    )


def to_buf(img):
    b = io.BytesIO()
    img.save(b, format="PNG")
    b.seek(0)
    return b


def d1(name, title, c, t, pct, dt, author):
    img = Image.new("RGB", (W, H), (20, 30, 60))
    d = ImageDraw.Draw(img)
    d.polygon([(0,0),(200,0),(0,280)], fill=(180,20,20))
    d.polygon([(0,0),(148,0),(0,208)], fill=(210,35,35))
    for o in [8,14,20]:
        d.rectangle([o,o,W-o,H-o], outline=(180,150,60), width=1)
    d.ellipse([968,55,1112,199], fill=(200,160,30))
    d.ellipse([984,71,1096,183], fill=(225,190,55))
    d.ellipse([1000,87,1080,167], fill=(180,140,20))
    center_text(d,"SERTIFIKAT",75,get_font(68,True),(220,190,60))
    center_text(d,name.upper(),192,get_font(44,True),(255,255,255))
    d.rectangle([150,265,W-150,268],fill=(180,150,60))
    body_text(d,make_text(name,title,c,t,pct,author),100,283,W-200,get_font(23),(200,210,230),13)
    d.text((130,635),dt,font=get_font(22),fill=(150,170,200))
    d.text((130,660),"SANA",font=get_font(18),fill=(100,120,150))
    center_text(d,author,635,get_font(27),(200,210,230))
    center_text(d,"MUALLIF",662,get_font(18),(100,120,150))
    return to_buf(img)


def d2(name, title, c, t, pct, dt, author):
    img = Image.new("RGB", (W, H), (255,255,255))
    d = ImageDraw.Draw(img)
    for y,h,col in [(0,22,(25,120,55)),(22,14,(180,150,30)),(36,8,(30,160,80)),
                    (H-22,22,(25,120,55)),(H-36,14,(180,150,30)),(H-44,8,(30,160,80))]:
        d.rectangle([0,y,W,y+h],fill=col)
    d.rectangle([0,0,22,H],fill=(25,120,55))
    d.rectangle([W-22,0,W,H],fill=(25,120,55))
    d.ellipse([968,55,1112,199],fill=(200,160,30))
    d.ellipse([984,71,1096,183],fill=(225,190,55))
    d.ellipse([1000,87,1080,167],fill=(180,140,20))
    center_text(d,"SERTIFIKAT",70,get_font(66,True),(22,115,50))
    center_text(d,name.upper(),182,get_font(42,True),(20,20,20))
    d.rectangle([80,252,W-80,255],fill=(180,150,30))
    body_text(d,make_text(name,title,c,t,pct,author),80,270,W-160,get_font(23),(40,40,40),12)
    d.text((100,635),dt,font=get_font(22),fill=(60,60,60))
    d.text((100,660),"Sana",font=get_font(18),fill=(120,120,120))
    center_text(d,author,635,get_font(27),(22,115,50))
    center_text(d,"Muallif",662,get_font(18),(100,100,100))
    return to_buf(img)


def d3(name, title, c, t, pct, dt, author):
    img = Image.new("RGB", (W, H), (248,252,255))
    d = ImageDraw.Draw(img)
    d.rectangle([0,0,W,105],fill=(15,90,170))
    d.rectangle([0,105,W,122],fill=(30,130,210))
    d.rectangle([0,H-85,W,H],fill=(15,90,170))
    d.rectangle([0,H-102,W,H-85],fill=(30,130,210))
    d.ellipse([975,120,1105,250],fill=(250,200,30))
    d.ellipse([988,133,1092,237],fill=(255,215,45))
    d.ellipse([1002,147,1078,223],fill=(220,175,20))
    center_text(d,"SERTIFIKAT",18,get_font(60,True),(255,255,255))
    center_text(d,name,148,get_font(42,True),(15,85,160))
    d.rectangle([80,228,W-80,231],fill=(30,130,210))
    body_text(d,make_text(name,title,c,t,pct,author),80,248,W-160,get_font(23),(30,30,30),12)
    d.text((100,635),dt,font=get_font(22),fill=(60,60,60))
    d.text((100,660),"Sana",font=get_font(18),fill=(120,120,120))
    center_text(d,author,635,get_font(27),(30,30,30))
    center_text(d,"Muallif",662,get_font(18),(100,100,100))
    return to_buf(img)


def d4(name, title, c, t, pct, dt, author):
    img = Image.new("RGB", (W, H), (245,255,248))
    d = ImageDraw.Draw(img)
    for r in [(0,0,W,18),(0,H-18,W,H),(0,0,18,H),(W-18,0,W,H)]:
        d.rectangle(r,fill=(20,150,50))
    d.polygon([(W-220,18),(W-18,18),(W-18,220)],fill=(20,180,60))
    d.ellipse([50,45,165,160],fill=(200,160,30))
    d.ellipse([63,58,152,147],fill=(225,185,50))
    center_text(d,"SERTIFIKAT",55,get_font(66,True),(18,135,45))
    center_text(d,name,165,get_font(42,True),(15,15,15))
    d.rectangle([80,235,W-80,239],fill=(20,150,50))
    body_text(d,make_text(name,title,c,t,pct,author),80,255,W-160,get_font(23),(30,30,30),12)
    d.text((100,635),dt,font=get_font(22),fill=(50,50,50))
    d.text((100,660),"Sana",font=get_font(18),fill=(100,100,100))
    center_text(d,author,635,get_font(27,True),(18,135,45))
    center_text(d,"Test muallifi",662,get_font(18),(80,80,80))
    return to_buf(img)


def d5(name, title, c, t, pct, dt, author):
    img = Image.new("RGB", (W, H), (255,255,255))
    d = ImageDraw.Draw(img)
    d.polygon([(0,0),(340,0),(0,340)],fill=(175,18,18))
    d.polygon([(0,0),(278,0),(0,278)],fill=(205,28,28))
    d.rectangle([15,15,W-15,H-15],outline=(200,160,30),width=3)
    d.ellipse([968,42,1112,186],fill=(200,160,30))
    d.ellipse([982,56,1098,172],fill=(225,190,55))
    d.ellipse([998,72,1082,156],fill=(180,140,20))
    center_text(d,"SERTIFIKAT",60,get_font(66,True),(175,18,18))
    center_text(d,name,172,get_font(42,True),(20,20,20))
    d.rectangle([80,244,W-80,247],fill=(200,160,30))
    body_text(d,make_text(name,title,c,t,pct,author),80,265,W-160,get_font(23),(40,40,40),12)
    d.text((100,630),dt,font=get_font(22),fill=(60,60,60))
    d.text((100,655),"SANA",font=get_font(18),fill=(120,120,120))
    center_text(d,author,630,get_font(27),(40,40,40))
    center_text(d,"MUALLIF",655,get_font(18),(120,120,120))
    return to_buf(img)


def d6(name, title, c, t, pct, dt, author):
    img = Image.new("RGB", (W, H), (245,235,210))
    d = ImageDraw.Draw(img)
    d.rectangle([0,0,W,98],fill=(175,128,55))
    d.rectangle([0,H-78,W,H],fill=(175,128,55))
    for o in [8,14]:
        d.rectangle([o,o,W-o,H-o],outline=(145,95,25),width=1)
    d.ellipse([968,108,1108,248],fill=(178,128,38))
    d.ellipse([982,122,1094,234],fill=(200,155,58))
    d.ellipse([998,138,1078,218],fill=(155,108,22))
    center_text(d,"SERTIFIKAT",14,get_font(60,True),(255,245,220))
    center_text(d,name,155,get_font(42,True),(75,38,8))
    d.rectangle([80,228,W-80,231],fill=(145,95,25))
    body_text(d,make_text(name,title,c,t,pct,author),80,248,W-160,get_font(23),(55,38,8),12)
    d.text((100,632),dt,font=get_font(22),fill=(75,50,10))
    d.text((100,657),"SANA",font=get_font(18),fill=(125,95,45))
    center_text(d,author,632,get_font(27),(75,38,8))
    center_text(d,"MUALLIF",657,get_font(18),(125,95,45))
    return to_buf(img)


def d7(name, title, c, t, pct, dt, author):
    img = Image.new("RGB", (W, H), (255,255,255))
    d = ImageDraw.Draw(img)
    d.polygon([(0,0),(260,0),(160,140),(0,140)],fill=(230,45,115))
    d.polygon([(W,0),(W-200,0),(W,200)],fill=(255,168,25))
    d.polygon([(0,H),(180,H),(0,H-160)],fill=(95,55,200))
    d.polygon([(W,H),(W-220,H),(W,H-180)],fill=(28,178,118))
    d.ellipse([55,55,115,115],fill=(255,168,25))
    d.ellipse([W-115,55,W-55,115],fill=(95,55,200))
    center_text(d,"SERTIFIKAT",55,get_font(66,True),(95,55,200))
    center_text(d,name,165,get_font(42,True),(15,15,15))
    d.rectangle([80,238,W-80,242],fill=(230,45,115))
    body_text(d,make_text(name,title,c,t,pct,author),80,258,W-160,get_font(23),(35,35,35),12)
    d.text((100,632),dt,font=get_font(22),fill=(55,55,55))
    d.text((100,657),"SANA",font=get_font(18),fill=(125,125,125))
    center_text(d,author,632,get_font(27,True),(95,55,200))
    center_text(d,"MUALLIF",657,get_font(18),(125,125,125))
    return to_buf(img)


def d8(name, title, c, t, pct, dt, author):
    img = Image.new("RGB", (W, H), (22,32,52))
    d = ImageDraw.Draw(img)
    d.polygon([(0,0),(420,0),(260,210),(0,210)],fill=(32,52,92))
    d.polygon([(0,0),(310,0),(185,155)],fill=(42,68,118))
    d.polygon([(W,H),(W-360,H),(W-210,H-185),(W,H-185)],fill=(32,52,92))
    d.rectangle([0,225,W,230],fill=(198,168,58))
    d.rectangle([0,598,W,603],fill=(198,168,58))
    d.ellipse([968,48,1112,192],fill=(188,153,38))
    d.ellipse([982,62,1098,178],fill=(210,175,55))
    d.ellipse([998,78,1082,162],fill=(170,135,18))
    center_text(d,"SERTIFIKAT",68,get_font(66,True),(210,178,68))
    center_text(d,name.upper(),158,get_font(42,True),(255,255,255))
    body_text(d,make_text(name,title,c,t,pct,author),80,245,W-160,get_font(23),(188,202,228),13)
    d.text((100,622),dt,font=get_font(22),fill=(155,172,198))
    d.text((100,648),"SANA",font=get_font(18),fill=(98,118,148))
    center_text(d,author,622,get_font(27,True),(210,178,68))
    center_text(d,"MUALLIF",648,get_font(18),(98,118,148))
    return to_buf(img)


DESIGNS = {1:d1,2:d2,3:d3,4:d4,5:d5,6:d6,7:d7,8:d8}


def generate_certificate(design_num, full_name, test_title, correct, total, author):
    pct = (correct / total * 100) if total > 0 else 0
    dt = datetime.now().strftime("%d.%m.%Y")
    fn = DESIGNS.get(design_num, d1)
    try:
        return fn(full_name, test_title, correct, total, pct, dt, author)
    except Exception:
        return d1(full_name, test_title, correct, total, pct, dt, author)
