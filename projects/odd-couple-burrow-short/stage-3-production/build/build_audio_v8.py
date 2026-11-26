import subprocess, os, math
FFMPEG='/tmp/py/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v9.0.2'
BASE='/home/user/Top1/projects/odd-couple-burrow-short/stage-3-production'
VO=os.path.join(BASE,'master_mix.wav')  # existing VO+light mix
OUT=os.path.join(BASE,'master_mix_v8.wav')
TMP='/tmp/odd_audio_v8'
os.makedirs(TMP, exist_ok=True)

def run(cmd):
    print('RUN', cmd[:200])
    subprocess.check_call(cmd)

# build layers with ffmpeg lavfi
# 1) deep drone
run([FFMPEG,'-y','-f','lavfi','-i','sine=frequency=38:sample_rate=48000:duration=30','-f','lavfi','-i','sine=frequency=76:sample_rate=48000:duration=30',
     '-filter_complex','[0:a]volume=0.08[a0];[1:a]volume=0.03[a1];[a0][a1]amix=inputs=2:duration=first,lowpass=f=120,highpass=f=20,atrim=0:29.94,asetpts=N/SR/TB[a]',
     '-map','[a]','-c:a','pcm_s24le',os.path.join(TMP,'drone.wav')])

# 2) impact hit at twist 9.6s
run([FFMPEG,'-y','-f','lavfi','-i','anoisesrc=color=brown:sample_rate=48000:duration=2',
     '-filter_complex','[0:a]lowpass=f=180,highpass=f=30,afade=t=in:st=0:d=0.01,afade=t=out:st=0.1:d=1.2,volume=0.45,adelay=9600|9600,atrim=0:29.94,asetpts=N/SR/TB[a]',
     '-map','[a]','-c:a','pcm_s24le',os.path.join(TMP,'hit_twist.wav')])

# 3) flood rumble 24-28s
run([FFMPEG,'-y','-f','lavfi','-i','anoisesrc=color=brown:sample_rate=48000:duration=30',
     '-filter_complex','[0:a]lowpass=f=220,highpass=f=25,volume=\'if(between(t,24,28),(t-24)*0.08,if(between(t,28,29.5),0.32-(t-28)*0.18,0))\':eval=frame,atrim=0:29.94,asetpts=N/SR/TB[a]',
     '-map','[a]','-c:a','pcm_s24le',os.path.join(TMP,'flood.wav')])

# 4) whoosh/reveal 5.5s and 17s
run([FFMPEG,'-y','-f','lavfi','-i','anoisesrc=color=pink:sample_rate=48000:duration=30',
     '-filter_complex','[0:a]highpass=f=800,lowpass=f=6000,volume=\'0.12*exp(-pow((t-5.8)*3,2))+0.10*exp(-pow((t-17.2)*3,2))+0.08*exp(-pow((t-28.2)*2.5,2))\':eval=frame,atrim=0:29.94,asetpts=N/SR/TB[a]',
     '-map','[a]','-c:a','pcm_s24le',os.path.join(TMP,'whoosh.wav')])

# 5) subtle pulse
run([FFMPEG,'-y','-f','lavfi','-i','sine=frequency=55:sample_rate=48000:duration=30',
     '-filter_complex','[0:a]volume=\'0.04*(0.5+0.5*sin(2*PI*0.8*t))*(1-0.5*between(t,9,11))\':eval=frame,atrim=0:29.94,asetpts=N/SR/TB[a]',
     '-map','[a]','-c:a','pcm_s24le',os.path.join(TMP,'pulse.wav')])

# Mix
inputs = ['-i',VO,'-i',os.path.join(TMP,'drone.wav'),'-i',os.path.join(TMP,'hit_twist.wav'),'-i',os.path.join(TMP,'flood.wav'),'-i',os.path.join(TMP,'whoosh.wav'),'-i',os.path.join(TMP,'pulse.wav')]
fc = (
 "[0:a]volume=1.0[vo];"
 "[1:a]volume=0.55[dr];"
 "[2:a]volume=0.7[ht];"
 "[3:a]volume=0.8[fl];"
 "[4:a]volume=0.7[wh];"
 "[5:a]volume=0.5[pu];"
 "[vo][dr][ht][fl][wh][pu]amix=inputs=6:duration=first:normalize=0[m];"
 "[m]acompressor=threshold=-18dB:ratio=3:attack=5:release=120:makeup=2,alimiter=limit=-1.0dB:attack=5:release=50,loudnorm=I=-14:TP=-1.0:LRA=11:print_format=summary[out]"
)
run([FFMPEG,'-y',*inputs,'-filter_complex',fc,'-map','[out]','-ar','48000','-c:a','pcm_s24le',OUT])
print('WROTE',OUT)
