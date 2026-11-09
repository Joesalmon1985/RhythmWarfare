"""Independent check of a recorded session: clipping, silences, and whether the drop lands where the director scheduled it.
Run with: python -I Tools/music/analyze_recording.py  (edit the list below for the recordings/drop times to check)."""
import wave, numpy as np, sys
def load(p):
    w=wave.open(p); n=w.getnframes(); sr=w.getframerate(); ch=w.getnchannels()
    a=np.frombuffer(w.readframes(n),dtype='<i2').astype(np.float32).reshape(-1,ch)/32768; return a,sr
for name,drops in (('perfect',[54.029,186.442]),('partial',[54.029]),('fail',[87.132])):
    a,sr=load('Evidence/audio/runtime_%s.wav'%name); m=a.mean(1)
    print(name,'dur %.1fs'%(len(a)/sr),'peak %.3f'%np.abs(a).max(),'clipped(>=0.999):',int((np.abs(a)>=0.999).sum()))
    # silences > 250ms after 3.2 s (-60 dB)
    win=int(sr*0.05); r=np.sqrt(np.convolve(m**2,np.ones(win)/win,'same'))[::win//5]
    t=np.arange(len(r))*(win//5)/sr; low=r<10**(-60/20)
    runs=[];s=None
    for i,v in enumerate(low):
        if v and s is None:s=i
        if not v and s is not None: runs.append((t[s],t[i]));s=None
    print('  silent runs (-60 dB, >0.25s):',[(round(x,2),round(y,2)) for x,y in runs if y-x>0.25])
    for d in drops:
        i=int(d*sr); b=np.sqrt((m[i-4*sr:i-int(0.05*sr)]**2).mean()); f=np.sqrt((m[i+int(0.1*sr):i+4*sr]**2).mean())
        # onset: first 10ms window after d-0.3 whose rms exceeds 3x the pre-drop rms
        seg=m[i-int(0.3*sr):i+int(0.6*sr)]; w=int(sr*0.005); e=np.sqrt(np.convolve(seg**2,np.ones(w)/w,'same'))
        k=np.argmax(e>3*b); print('  drop at %.3f: rms before %.3f after %.3f (x%.1f); loud onset at %+.0f ms'%(d,b,f,f/b,(k/sr-0.3)*1000))
