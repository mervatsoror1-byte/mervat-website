"""Generates the soft, light artwork covers (pastel aurora + silk lines + metallic gold symbol)."""
import math, random, sys
from PIL import Image, ImageDraw, ImageFilter, ImageChops
import numpy as np

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
GOLD = [(0,(122,84,18)),(.18,(214,165,55)),(.36,(255,241,181)),(.5,(226,184,76)),(.66,(150,104,28)),(.82,(246,214,122)),(1,(176,128,40))]

def hexc(h): h=h.lstrip('#'); return tuple(int(h[i:i+2],16) for i in (0,2,4))

def grad_img(w,h,stops,angle=35):
    a=math.radians(angle); y,x=np.mgrid[0:h,0:w]
    t=(x*math.cos(a)+y*math.sin(a)); t=(t-t.min())/(t.max()-t.min())
    out=np.zeros((h,w,3))
    for i in range(len(stops)-1):
        p0,c0=stops[i]; p1,c1=stops[i+1]
        m=(t>=p0)&(t<=p1); f=((t-p0)/(p1-p0))[m][:,None]
        out[m]=np.array(c0)*(1-f)+np.array(c1)*f
    return Image.fromarray(out.astype(np.uint8))

def background(w,h,top,bottom,blobs,seed):
    rnd=random.Random(seed)
    base=grad_img(w,h,[(0,hexc(top)),(1,hexc(bottom))],angle=100)
    layer=Image.new('RGB',(w,h),hexc(top))
    lay=Image.new('RGBA',(w,h),hexc(blobs[0])+(0,)); d=ImageDraw.Draw(lay)
    for c in blobs:
        r=rnd.randint(int(w*.25),int(w*.55)); cx=rnd.randint(0,w); cy=rnd.randint(0,h)
        d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=hexc(c)+(170,))
    lay=lay.filter(ImageFilter.GaussianBlur(w*.12))
    img=base.convert('RGBA'); img.alpha_composite(lay)
    # silk lines
    silk=Image.new('RGBA',(w,h),(0,0,0,0)); sd=ImageDraw.Draw(silk)
    ph=rnd.random()*6; amp=h*rnd.uniform(.05,.09); y0=h*rnd.uniform(.55,.75)
    for k in range(38):
        pts=[(x, y0+k*h*.006+amp*math.sin(x/w*math.pi*1.6+ph+k*.05)+amp*.5*math.sin(x/w*math.pi*3.1+k*.08)) for x in range(-10,w+10,6)]
        sd.line(pts,fill=(255,255,255,int(60-k)),width=2)
    img.alpha_composite(silk.filter(ImageFilter.GaussianBlur(.6)))
    return img

def sparkles(img,n,seed,area=None):
    rnd=random.Random(seed); w,h=img.size
    sp=Image.new('RGBA',(w,h),(0,0,0,0)); d=ImageDraw.Draw(sp)
    for _ in range(n):
        x=rnd.randint(0,w); y=rnd.randint(0,h); r=rnd.choice([1,1,2,2,3,4])
        a=rnd.randint(120,255); c=rnd.choice([(255,236,170),(255,250,230),(232,196,110)])
        d.ellipse((x-r,y-r,x+r,y+r),fill=c+(a,))
        if r>=3:
            L=r*4; d.line((x-L,y,x+L,y),fill=c+(a//2,),width=1); d.line((x,y-L,x,y+L),fill=c+(a//2,),width=1)
    glow=sp.filter(ImageFilter.GaussianBlur(3))
    img.alpha_composite(glow); img.alpha_composite(sp)

def gold_symbol(img,draw_fn,scale=1.0):
    w,h=img.size; S=3
    m=Image.new('L',(w*S,h*S),0); d=ImageDraw.Draw(m)
    draw_fn(d,w*S,h*S,scale)
    m=m.resize((w,h),Image.LANCZOS)
    g=grad_img(w,h,GOLD,angle=40).convert('RGBA')
    # glow
    glow=Image.new('RGBA',(w,h),(255,226,150,0)); glow.putalpha(m.filter(ImageFilter.GaussianBlur(w*.02)).point(lambda v:int(v*.75)))
    img.alpha_composite(glow)
    shadow=Image.new('RGBA',(w,h),(110,60,40,0)); shadow.putalpha(m.filter(ImageFilter.GaussianBlur(4)).point(lambda v:int(v*.35)))
    img.alpha_composite(shadow,(0,4))
    g.putalpha(m); img.alpha_composite(g)

def ring(d,cx,cy,r,t): d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=255,width=int(t))
def arc(d,cx,cy,r,a0,a1,t): d.arc((cx-r,cy-r,cx+r,cy+r),a0,a1,fill=255,width=int(t))

# ----- symbols (drawn into a mask, size-relative) -----
def s_attach(d,w,h,s):  # two rings, one opening
    cx,cy,r,t=w*.5,h*.42,w*.17*s,w*.012
    ring(d,cx-r*.55,cy,r,t); arc(d,cx+r*.55,cy,r,200,520-60,t)
    for i in range(3): d.ellipse((cx+r*1.75+i*w*.035-w*.007,cy-r*.9-i*w*.03-w*.007,cx+r*1.75+i*w*.035+w*.007,cy-r*.9-i*w*.03+w*.007),fill=255)
def s_decode(d,w,h,s):  # seed of life
    cx,cy,r,t=w*.5,h*.42,w*.1*s,w*.007
    ring(d,cx,cy,r,t)
    for k in range(6):
        a=k*math.pi/3; ring(d,cx+r*math.cos(a),cy+r*math.sin(a),r,t)
    ring(d,cx,cy,r*2,t*1.4)
def s_light(d,w,h,s):  # radiant
    cx,cy,r,t=w*.5,h*.42,w*.08*s,w*.01
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=255)
    for k in range(24):
        a=k*math.pi/12; L=r*(2.6 if k%2==0 else 1.9)
        d.line((cx+r*1.35*math.cos(a),cy+r*1.35*math.sin(a),cx+L*math.cos(a),cy+L*math.sin(a)),fill=255,width=int(t))
def s_child(d,w,h,s):  # small heart held in crescent
    cx,cy,r,t=w*.5,h*.42,w*.19*s,w*.011
    arc(d,cx,cy,r,20,160+180-20,t)
    hr=r*.33
    d.ellipse((cx-hr,cy-hr*1.1,cx,cy-hr*.1),fill=255); d.ellipse((cx,cy-hr*1.1,cx+hr,cy-hr*.1),fill=255)
    d.polygon([(cx-hr*.98,cy-hr*.45),(cx+hr*.98,cy-hr*.45),(cx,cy+hr*.9)],fill=255)
def s_heart_wave(d,w,h,s):
    cx,cy,r,t=w*.5,h*.42,w*.16*s,w*.01
    pts=[]
    for i in range(361):
        a=math.radians(i); x=16*math.sin(a)**3; y=13*math.cos(a)-5*math.cos(2*a)-2*math.cos(3*a)-math.cos(4*a)
        pts.append((cx+x*r/16,cy-y*r/16))
    d.line(pts,fill=255,width=int(t),joint='curve')
    wv=[(x,cy+math.sin((x-cx)/(w*.045))*w*.035*math.exp(-((x-cx)/(w*.18))**2)) for x in np.linspace(w*.14,w*.86,300)]
    d.line(wv,fill=255,width=int(t*.8))
def s_sun(d,w,h,s):
    cx,cy,r,t=w*.5,h*.47,w*.15*s,w*.01
    d.pieslice((cx-r,cy-r,cx+r,cy+r),180,360,fill=255)
    for i in range(4):
        y=cy+w*.03+i*w*.03; L=w*(.32-i*.06); d.line((cx-L,y,cx+L,y),fill=255,width=int(t*(1-i*.15)))
    for k in range(9):
        a=math.pi+k*math.pi/8; d.line((cx+r*1.2*math.cos(a),cy+r*1.2*math.sin(a),cx+r*1.55*math.cos(a),cy+r*1.55*math.sin(a)),fill=255,width=int(t))
def s_lotus(d,w,h,s):
    cx,cy,r,t=w*.5,h*.46,w*.2*s,w*.011
    def petal(ang,L,W):
        pts=[]
        for i in range(61):
            u=i/60; y=-L*u; x=W*math.sin(math.pi*u)**1.2
            pts.append((x,y))
        pts=pts+[(-x,y) for x,y in reversed(pts)]
        ca,sa=math.cos(ang),math.sin(ang)
        d.line([(cx+x*ca-y*sa,cy+x*sa+y*ca) for x,y in pts],fill=255,width=int(t),joint='curve')
    petal(0,r*1.2,r*.32)
    for a,L in [(.55,1.0),(-.55,1.0),(1.05,.8),(-1.05,.8)]: petal(a,r*L,r*.3)
    d.line((cx-r*1.1,cy+t,cx+r*1.1,cy+t),fill=255,width=int(t))
def s_ripple(d,w,h,s):
    cx,cy,t=w*.5,h*.5,w*.008
    for i,rr in enumerate([.06,.13,.21,.3]):
        rx=w*rr*s; ry=rx*.32; d.ellipse((cx-rx,cy-ry,cx+rx,cy+ry),outline=255,width=int(t*(1.3-i*.2)))
    dr=w*.035; d.ellipse((cx-dr,cy-w*.2-dr,cx+dr,cy-w*.2+dr),fill=255)
    d.polygon([(cx-dr*.95,cy-w*.2-dr*.25),(cx+dr*.95,cy-w*.2-dr*.25),(cx,cy-w*.2-dr*2.6)],fill=255)
def s_eye(d,w,h,s):
    cx,cy,r,t=w*.5,h*.42,w*.27*s,w*.012
    up=[(cx+x,cy-r*.55*math.sin(math.pi*(x+r)/(2*r))) for x in np.linspace(-r,r,200)]
    lo=[(cx+x,cy+r*.55*math.sin(math.pi*(x+r)/(2*r))) for x in np.linspace(-r,r,200)]
    d.line(up,fill=255,width=int(t)); d.line(lo,fill=255,width=int(t))
    ring(d,cx,cy,r*.33,t); d.ellipse((cx-r*.14,cy-r*.14,cx+r*.14,cy+r*.14),fill=255)
    for k in range(7):
        a=math.pi+math.pi*(k+1)/8; d.line((cx+r*.78*math.cos(a),cy-r*.15+r*.6*math.sin(a),cx+r*.98*math.cos(a),cy-r*.15+r*.78*math.sin(a)),fill=255,width=int(t*.8))
def s_book(d,w,h,s):  # arched door + crescent
    cx,cy,t=w*.5,h*.48,w*.01
    W,H=w*.2*s,w*.3*s
    d.arc((cx-W,cy-H-W,cx+W,cy-H+W),180,360,fill=255,width=int(t)); d.line((cx-W,cy-H,cx-W,cy+H*.6),fill=255,width=int(t)); d.line((cx+W,cy-H,cx+W,cy+H*.6),fill=255,width=int(t))
    d.line((cx-W*1.5,cy+H*.6,cx+W*1.5,cy+H*.6),fill=255,width=int(t))
    r=W*.35; d.ellipse((cx-r,cy-H*.75-r,cx+r,cy-H*.75+r),fill=255); d.ellipse((cx-r*.55,cy-H*.75-r*1.1,cx+r*1.25,cy-H*.75+r*.7),fill=0)
def s_vip(d,w,h,s):  # crown of light: arch + star
    cx,cy,t=w*.5,h*.45,w*.009
    for i,k in enumerate([.3,.24,.18]):
        W=w*k*s; d.arc((cx-W,cy-W,cx+W,cy+W),180,360,fill=255,width=int(t*(1.2-i*.2)))
    r=w*.05; pts=[]
    for k in range(8):
        a=-math.pi/2+k*math.pi/4; rr=r if k%2==0 else r*.32; pts.append((cx+rr*math.cos(a),cy-w*.06+rr*math.sin(a)))
    d.polygon(pts,fill=255)

P = {
 'rose':  ('#FFF8F3','#F3D5DE',['#EFC2CF','#F8E2C8','#E3C8EC']),
 'lilac': ('#FBF6FD','#E6D6F0',['#DCC6EC','#F4D6E2','#FBEAD0']),
 'peach': ('#FFF8EE','#F7DCCB',['#F9D2B8','#F5C6D2','#FFF0C9']),
 'pearl': ('#FFFDF8','#EFE4E8',['#F1D9E1','#EAE0F2','#FAEBD2']),
 'mauve': ('#F7EAF0','#D9B3C8',['#CFA0BD','#EBC7D3','#F6DFC5']),
 'dawn':  ('#FFF3E6','#F2CFD6',['#FFD9A8','#F4BCCB','#FFEFC9']),
}
JOBS = [
 ('attach','rose',s_attach),('decode','lilac',s_decode),('light','peach',s_light),('child','rose',s_child),
 ('breath','pearl',s_heart_wave),('morning','dawn',s_sun),('peace','lilac',s_lotus),('calm','mauve',s_ripple),
 ('course','pearl',s_eye),('book','mauve',s_book),('vip','peach',s_vip),
]
for i,(name,pal,fn) in enumerate(JOBS):
    top,bottom,blobs=P[pal]
    w,h=(900,1200)
    img=background(w,h,top,bottom,blobs,seed=i*7+3)
    sparkles(img,120,seed=i)
    gold_symbol(img,fn)
    noise=np.random.default_rng(i).normal(0,4,(h,w,1))
    arr=np.clip(np.array(img.convert('RGB')).astype(float)+noise,0,255).astype(np.uint8)
    Image.fromarray(arr).save(f"{OUT}/{name}.webp",'WEBP',quality=82,method=6)
print("ok")
