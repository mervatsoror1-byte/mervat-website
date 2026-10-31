"""Places the coach cut-outs on luminous brand backgrounds (arch + gold light)."""
import math, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import numpy as np
SRC="brand/photos"; OUT=sys.argv[1]
FOIL=[(0,(150,104,28)),(.2,(222,178,72)),(.4,(255,240,180)),(.55,(226,184,76)),(.75,(170,120,36)),(1,(244,212,120))]
def hexc(h): h=h.lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))
def grad(w,h,stops,ang):
    a=math.radians(ang); y,x=np.mgrid[0:h,0:w]; t=x*math.cos(a)+y*math.sin(a); t=(t-t.min())/(t.max()-t.min())
    o=np.zeros((h,w,3))
    for i in range(len(stops)-1):
        p0,c0=stops[i]; p1,c1=stops[i+1]; m=(t>=p0)&(t<=p1); f=((t-p0)/(p1-p0))[m][:,None]; o[m]=np.array(c0)*(1-f)+np.array(c1)*f
    return Image.fromarray(o.astype(np.uint8))
SCENES={
 'blush':('#FFF9F4','#F6DDE4',['#F3C9D5','#FBE6CC','#E9D6F1']),
 'lilac':('#FCF8FD','#E9DDF2',['#DECAEE','#F7DCE6','#FFF0D6']),
 'champagne':('#FFFBF2','#F5E3CF',['#F9DDB8','#F3CCD6','#FFF4D9']),
}
def scene(w,h,name,seed):
    top,bot,blobs=SCENES[name]; rnd=random.Random(seed)
    img=grad(w,h,[(0,hexc(top)),(1,hexc(bot))],95).convert('RGBA')
    lay=Image.new('RGBA',(w,h),hexc(blobs[0])+(0,)); d=ImageDraw.Draw(lay)
    for c in blobs:
        r=rnd.randint(int(w*.3),int(w*.6)); cx=rnd.randint(0,w); cy=rnd.randint(0,int(h*.8)); d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=hexc(c)+(160,))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(w*.12)))
    # glowing arch behind subject
    S=2; m=Image.new('L',(w*S,h*S),0); md=ImageDraw.Draw(m)
    aw=w*.62*S; ax0=(w*S-aw)/2; atop=h*.08*S; abot=h*.86*S; t=int(w*.006*S)
    for k,inset in enumerate([0,w*.035*S]):
        x0=ax0+inset; x1=ax0+aw-inset; y0=atop+inset
        md.arc((x0,y0,x1,y0+(x1-x0)),180,360,fill=255,width=t); r=(x1-x0)/2
        md.line((x0,y0+r,x0,abot),fill=255,width=t); md.line((x1,y0+r,x1,abot),fill=255,width=t)
    m=m.resize((w,h),Image.LANCZOS)
    fill=Image.new('L',(w*S,h*S),0); fd=ImageDraw.Draw(fill); x0=ax0; x1=ax0+aw
    fd.pieslice((x0,atop,x1,atop+aw),180,360,fill=255); fd.rectangle((x0,atop+aw/2,x1,abot),fill=255)
    fill=fill.resize((w,h),Image.LANCZOS)
    glow=Image.new('RGBA',(w,h),(255,247,232,0)); glow.putalpha(fill.point(lambda v:int(v*.55))); img.alpha_composite(glow)
    halo=Image.new('RGBA',(w,h),(255,224,160,0)); halo.putalpha(m.filter(ImageFilter.GaussianBlur(w*.012)).point(lambda v:int(v*.8))); img.alpha_composite(halo)
    g=grad(w,h,FOIL,40).convert('RGBA'); g.putalpha(m); img.alpha_composite(g)
    # floor line + sparkles
    fl=Image.new('RGBA',(w,h),(0,0,0,0)); ImageDraw.Draw(fl).ellipse((w*.12,h*.84,w*.88,h*.93),fill=(214,170,90,70)); img.alpha_composite(fl.filter(ImageFilter.GaussianBlur(w*.03)))
    sp=Image.new('RGBA',(w,h),(0,0,0,0)); sd=ImageDraw.Draw(sp)
    for _ in range(90):
        x=rnd.randint(0,w); y=rnd.randint(0,h); r=rnd.choice([1,1,2,2,3]); a=rnd.randint(110,230)
        sd.ellipse((x-r,y-r,x+r,y+r),fill=(236,198,110,a))
        if r==3: sd.line((x-10,y,x+10,y),fill=(236,198,110,a//2)); sd.line((x,y-10,x,y+10),fill=(236,198,110,a//2))
    img.alpha_composite(sp.filter(ImageFilter.GaussianBlur(1.6))); img.alpha_composite(sp)
    return img
def place(bg,cut,height_frac,bottom_frac,shadow=True):
    w,h=bg.size; cut=cut.crop(cut.getchannel('A').getbbox())
    H=int(h*height_frac); W=int(cut.width*H/cut.height); c=cut.resize((W,H),Image.LANCZOS)
    x=(w-W)//2; y=int(h*bottom_frac)-H
    if shadow:
        s=Image.new('RGBA',(w,h),(0,0,0,0)); sh=Image.new('RGBA',c.size,(80,40,60,0)); sh.putalpha(c.getchannel('A').point(lambda v:int(v*.18)))
        s.alpha_composite(sh,(x+10,y+12)); bg.alpha_composite(s.filter(ImageFilter.GaussianBlur(14)))
    bg.alpha_composite(c,(x,y)); return bg
def sharpen_up(im,f):
    im=im.resize((im.width*f,im.height*f),Image.LANCZOS)
    rgb=im.convert('RGB').filter(ImageFilter.UnsharpMask(2,60,2)); rgb.putalpha(im.getchannel('A')); return rgb
jobs=[
 # name, cutout, flip(glove to left hand), scene, size, height, bottom, seed
 ('coach-green','green',True,'champagne',(900,1125),.9,.97,1),
 ('coach-navy','navy',True,'lilac',(900,1125),.9,.97,2),
 ('coach-white','white',False,'blush',(900,1125),1.0,1.04,3),
 ('coach-white-square','white',False,'champagne',(900,900),1.05,1.08,4),
]
for name,src,flip,sc,(w,h),hf,bf,seed in jobs:
    cut=Image.open(f"{SRC}/cutout-{src}.png").convert('RGBA')
    if cut.height<900: cut=sharpen_up(cut,2)
    if flip: cut=ImageOps.mirror(cut)
    bg=scene(w,h,sc,seed); img=place(bg,cut,hf,bf)
    img.convert('RGB').save(f"{OUT}/{name}.webp",'WEBP',quality=86,method=6)
    # transparent cut-out also kept for free placement in CSS
    c2=cut.crop(cut.getchannel('A').getbbox()); c2.thumbnail((900,1400)); c2.save(f"{OUT}/{name}-cut.webp",'WEBP',quality=86,method=6)
print('ok')
