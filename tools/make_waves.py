"""Flowing gold light waves: one on deep plum (band), one on luminous ivory (hero)."""
import math, random, sys
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
OUT=sys.argv[1]
def waves(w,h,bg_top,bg_bot,line_rgb,seed,glow_alpha,n=70,dark=True):
    rnd=random.Random(seed)
    y,x=np.mgrid[0:h,0:w]
    t=(y/h)[...,None]; base=np.array(bg_top)*(1-t)+np.array(bg_bot)*t
    # radial light
    cx,cy=w*.62,h*.45; r=np.sqrt(((x-cx)/(w*.6))**2+((y-cy)/(h*.8))**2)[...,None]
    base=base+np.clip(1-r,0,1)**2*np.array([60,30,40] if dark else [10,8,0])
    img=Image.fromarray(np.clip(base,0,255).astype(np.uint8)).convert('RGBA')
    S=2; L=Image.new('L',(w*S,h*S),0); d=ImageDraw.Draw(L)
    for k in range(n):
        ph=k*.045; amp=h*(.16+.05*math.sin(k*.3)); off=h*.52+ (k-n/2)*h*.004
        pts=[(xx*S, (off+amp*math.sin(xx/w*math.pi*1.7+ph+1.2)+amp*.45*math.sin(xx/w*math.pi*3.3-ph*1.5))*S) for xx in range(-20,w+20,5)]
        a=int(255*(.25+.75*math.exp(-((k-n*.55)/(n*.18))**2)))
        d.line(pts,fill=a,width=S)
    L=L.resize((w,h),Image.LANCZOS)
    col=Image.new('RGBA',(w,h),line_rgb+(0,))
    glow=col.copy(); glow.putalpha(L.filter(ImageFilter.GaussianBlur(10)).point(lambda v:int(v*glow_alpha)))
    img.alpha_composite(glow); img.alpha_composite(glow)
    core=col.copy(); core.putalpha(L.point(lambda v:int(v*.85))); img.alpha_composite(core)
    sp=Image.new('RGBA',(w,h),(0,0,0,0)); sd=ImageDraw.Draw(sp)
    for _ in range(260):
        xx=rnd.randint(0,w); yy=int(h*.5+rnd.gauss(0,h*.18)); rr=rnd.choice([1,1,1,2,2,3])
        sd.ellipse((xx-rr,yy-rr,xx+rr,yy+rr),fill=(255,232,170,rnd.randint(90,230)))
    img.alpha_composite(sp.filter(ImageFilter.GaussianBlur(2))); img.alpha_composite(sp)
    return img.convert('RGB')
waves(1800,760,(62,28,53),(40,16,34),(232,192,105),1,.9).save(f"{OUT}/waves-plum.webp",'WEBP',quality=84,method=6)
waves(1800,1000,(253,249,242),(248,236,238),(214,170,80),2,.55,n=60,dark=False).save(f"{OUT}/waves-light.webp",'WEBP',quality=84,method=6)
print('ok')
