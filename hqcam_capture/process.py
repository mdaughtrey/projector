#!/usr/bin/env python3
import os
import subprocess
import sys
import glob
import shutil
from pathlib import Path

def main():
    # Variables
    PORT = "/dev/ttyACM0"
    PROJECT = "fm229 Matt 13 Months"
    FILM = "8mm"
    FRAMES_DIR = Path.cwd() / "frames"
    FP = FRAMES_DIR / PROJECT
    DEVICE = "/dev/video0"
    VIDEOSIZE = "1280x720"
    EXPOSURES = "12000,4000,8000,12000"
    EXPOSE = EXPOSURES.split(',')
    EDR = f"--exposure {EXPOSURES}"
    GLOB_REGISTRATION = f"????????_{EXPOSE[1]}.png"
    GLOB_CAR = "00000004_10000.reg"
    SAVEWORK = f"--saveallwork --saveworkto {FP}/work"
    DEBUG = ""

    def domount():
        try:
            subprocess.run(["sudo", "mount", "/dev/sda1", "/media/frames", "-o", "user=nobody,password=nobody,rw,file_mode=077,r_mode=07777"], check=True)
            if not (Path("/media/frames") / "frames").exists():
                os.symlink(FRAMES_DIR, "/media/frames/frames")
        except subprocess.CalledProcessError as e:
            print(f"Mount failed: {e}")
            sys.exit(1)

    # Ensure directories exist
    FP.mkdir(parents=True, exist_ok=True)
    for sd in ["car", "capture", "fused", "work"]:
        (FP / sd).mkdir(exist_ok=True)

    def writeconfig():
        config_path = FP / "config.toml"
        if config_path.exists():
            return
        with open(config_path, 'w') as f:
            if FILM == "8mm":
                f.write("[capture]\nwiny = 50\nwinx = 50\nwinw = 110\nwinh = 60\n\n[car]\nyoffset = -32\nysize = 1120\nxoffset = 852\nxsize  = 1380\n")
            else:
                f.write("[capture]\nwinx = 30\nwiny = 206\nwinw = 50\nwinh = 100\n\n[car]\nyoffset = -32\nysize = 1120\n")

    def getcamdev():
        return "/dev/video4"

    def capture():
        writeconfig()
        cmd = [
            "./picam_cap.py", "framecap",
            "--project", str(FP),
            "--frames", "3500",
            "--logfile", "picam_cap.log",
            "--film", FILM,
            "--exposure", EXPOSURES,
            "--startdia", "60",
            "--enddia", "50",
            "--savework",
            "--saveworkto", str(FP / "work"),
            "--saveallwork"
        ]
        subprocess.run(cmd)

    def preview(subdir="car"):
        for ex in EXPOSE:
            pattern = str(FP / subdir / f"%08d_{ex}.png")
            output = FP / f"{PROJECT}_{ex}.mp4"
            cmd = [
                "ffmpeg", "-f", "image2", "-r", "18",
                "-i", pattern,
                "-vcodec", "libx264",
                "-vf", "scale=640x480",
                str(output)
            ]
            subprocess.run(cmd)

    def praw(subdir="capture"):
        pattern = str(FP / subdir / f"????????_{EXPOSE[1]}.png")
        output = FP / f"{PROJECT}_praw.mp4"
        cmd = [
            "ffmpeg", "-f", "image2", "-r", "18",
            "-pattern_type", "glob",
            "-i", pattern,
            "-vcodec", "libx264",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=640x480",
            "-y", str(output)
        ]
        subprocess.run(cmd)

    def pcar(subdir="car"):
        pattern = str(FP / subdir / f"????????_{EXPOSE[1]}.png")
        output = FP / f"{PROJECT}_pcar_{EXPOSE[1]}.mp4"
        cmd = [
            "ffmpeg", "-f", "image2", "-r", "18",
            "-pattern_type", "glob",
            "-i", pattern,
            "-vcodec", "libx264",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=640x480",
            "-y", str(output)
        ]
        subprocess.run(cmd)

    def ptf():
        pattern = str(FP / "fused" / "*.png")
        output = FP / f"{PROJECT}_fused.mp4"
        cmd = [
            "ffmpeg", "-f", "image2", "-r", "18",
            "-pattern_type", "glob",
            "-i", pattern,
            "-vcodec", "libx264",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=640x480",
            "-y", str(output)
        ]
        subprocess.run(cmd)

    def getres():
        cmd = [
            "./usbcap.py",
            "--camindex", getcamdev(),
            "--project", str(FP),
            "--frames", "99999",
            "--logfile", "usbcap.log",
            "--fastforward", "9",
            "--res", "1",
            "getres",
            "--film", "8mm"
        ]
        subprocess.run(cmd)

    def descratch():
        DOCKERNAME = "avxsynth"
        SCRIPT = FP / "avx.avs"
        (FP / "descratch").mkdir(exist_ok=True)
        NUMFRAMES = len(list((FP / "graded").glob("????????.png")))

        avs_content = f"""
LoadPlugin("/AviSynthPlus/avisynth-build/plugins/ImageSeq/libimageseq.so")
LoadPlugin("/RemoveDirt/build/RemoveDirt/libremovedirt.so")
LoadPlugin("/mvtools/build/Sources/libmvtools2.so")
LoadPlugin("/RgTools/build/RgTools/librgtools.so")
LoadPlugin("/mvtools/build/DePanEstimate/libdepanestimate.so")
LoadPlugin("/mvtools/build/DePan/libdepan.so")
LoadPlugin("/mvtools/build/Sources/libmvtools2.so")
function RemoveDirt(clip input, bool "_grey", int "repmode") 
{{
    _grey=default(_grey, false)
    repmode=default(repmode, 16)
    clmode=17
    clensed=Clense(input, grey=_grey, cache=4)
    sbegin = ForwardClense(input, grey=_grey, cache=-1)
    send = BackwardClense(input, grey=_grey, cache=-1)
    alt=Repair(SCSelect(input, sbegin, send, clensed, debug=true), input, mode=repmode, modeU = _grey ? -1 : repmode ) 
    restore=Repair(clensed, input, mode=repmode, modeU = _grey ? -1 : repmode)
    corrected=RestoreMotionBlocks(clensed, restore, neighbour=input, alternative=alt, gmthreshold=70, dist=1, dmode=2, debug=false, noise=10, noisy=12, grey=_grey)
    return RemoveGrain(corrected, mode=clmode, modeU = _grey ? -1 : clmode )
}}	
RemoveDirt(ImageReader("/frames/capture/%08d.png", fps=18.0, end={NUMFRAMES}).converttoYV12())
"""

        with open(SCRIPT, 'w') as f:
            f.write(avs_content)

        docker_cmd = [
            "docker", "run", "--rm", "-h", DOCKERNAME,
            "--name", DOCKERNAME, "-t",
            "-v", f"{FP}:/frames",
            "--entrypoint", "/ffmpeg/ffmpeg",
            f"{DOCKERNAME}:latest",
            "-i", "/frames/avx.avs",
            "-y", "/frames/descratch/%08d.png"
        ]
        subprocess.run(docker_cmd)

    def exptest():
        exposures = EXPOSURES
        for f in range(1000, 100000, 1000):
            exposures += f",{f}"
        cmd = [
            "./picam_cap.py", "framecap",
            "--project", str(FP),
            "--frames", "10",
            "--logfile", "picam_cap.log",
            "--film", "8mm",
            "--exposure", exposures,
            "--startdia", "57",
            "--enddia", "33"
        ]
        subprocess.run(cmd)

    def tonefuse():
        outputnum = 0
        print(f"{FP} is {FP}")
        for file_path in glob.glob(str(FP / "car" / f"????????_{EXPOSE[0]}.png")):
            print(f"file is {file_path}")
            base = os.path.dirname(file_path)
            print(f"base is {base}")
            name = os.path.basename(file_path)
            print(f"{name} is {name}")
            number = name.split('_')[0]
            input_files = [
                str(FP / "car" / f"{number}_{EXPOSE[1]}.png"),
                str(FP / "car" / f"{number}_{EXPOSE[2]}.png"),
                str(FP / "car" / f"{number}_{EXPOSE[3]}.png")
            ]
            output = FP / "fused" / f"{outputnum:08d}.png"
            if not output.exists():
                enfuse_cmd = ["enfuse", "--output", str(output)] + input_files
                subprocess.run(enfuse_cmd)
            outputnum += 1

    def oneshot():
        cmd = [
            "./usbcap.py", "oneshot",
            "--camindex", getcamdev(),
            "--project", str(FP),
            "--logfile", "usbcap.log",
            "--exposure", "10000"
        ]
        subprocess.run(cmd)

    def cam():
        cmd = ["rpicam-hello", "--timeout=180s", "--shutter=9000us"]
        subprocess.run(cmd)

    def doenfuse():
        FRAME = 0
        F0 = FP / "car" / f"{FRAME:08d}_{EXPOSE[1]}.png"
        F1 = FP / "car" / f"{FRAME:08d}_{EXPOSE[2]}.png"
        F2 = FP / "car" / f"{FRAME:08d}_{EXPOSE[3]}.png"
        output = FP / "enfused.png"
        cmd = ["enfuse", "--output", str(output), str(F0), str(F1), str(F2)]
        subprocess.run(cmd)
        # Create grid (omitted for brevity)

    def doregsum():
        with open(FP / "reg.txt", 'w') as regfile:
            for reg_path in (FP / "capture").glob("*.reg"):
                with open(reg_path) as f:
                    regfile.write(f"{reg_path} {f.read().strip()}\n")

    def clean(target=None):
        if target == "reg":
            for f in (FP / "capture").glob("*.reg"):
                f.unlink()
        elif target == "car":
            for f in (FP / "car").glob("*.png"):
                f.unlink()
        elif target == "fused":
            for f in (FP / "fused").glob("*.png"):
                f.unlink()
        elif target == "video":
            for f in FP.glob("*.mp4"):
                f.unlink()
        else:
            print("what?")

    def capturevid():
        with open(PORT, 'w') as port:
            port.write('c90tlf\n')
        cmd = [
            "libcamera-vid",
            "--width", "640",
            "--height", "480",
            "--preview",
            "--framerate", "10",
            "--output", str(FP / "camvideo.mp4"),
            "--timeout", "500000"
        ]
        subprocess.run(cmd)
        with open(PORT, 'w') as port:
            port.write('s\n')

    def car_func():
        cmd = [
            "./01_crop_and_rotate.py",
            "--readfrom", str(FP / "capture" / f"????????_{EXPOSE[2]}.reg"),
            "--writeto", str(FP / "car"),
            "--exp", EXPOSURES,
            "--film", FILM
        ]
        subprocess.run(cmd)

    def registration():
        cmd = [
            "./00_registration.py",
            "--project", str(FP),
            "--readfrom", str(FP / "capture" / f"????????_{EXPOSE[2]}.png"),
            "--writeto", str(FP / "capture"),
            "--film", FILM
        ]
        subprocess.run(cmd)

    # Command mapping
    commands = {
        "capture": capture,
        "all": lambda: (capture(), open(PORT, 'w').write(' \n'), registration(), car_func(), tonefuse(), ptf()),
        "cam": cam,
        "cap1bmp": lambda: subprocess.run([
            "ffmpeg", "-f", "v4l2", "-video_size", VIDEOSIZE,
            "-i", getcamdev(), "-vframes", "1", "-y", str(FRAMES_DIR / "%08d.bmp")
        ]),
        "capmjpeg": lambda: subprocess.run([
            "ffmpeg", "-f", "v4l2", "-framerate", "1", "-video_size", VIDEOSIZE,
            "-i", DEVICE, "-vf", "fps=10", "-y", str(FRAMES_DIR / f"capmjpeg_{VIDEOSIZE}.avi")
        ]),
        "caps": lambda: subprocess.run(["ffmpeg", "-f", "v4l2", "-list_formats", "all", "-i", getcamdev()]),
        "capvid": capturevid,
        "car": car_func,
        "clean": lambda: clean(sys.argv[2] if len(sys.argv) > 2 else None),
        "descratch": descratch,
        "ef": doenfuse,
        "exptest": exptest,
        "gcd": lambda: print(getcamdev()),
        "getres": getres,
        "mount": domount,
        "oneshot": oneshot,
        "pcar": pcar,
        "praw": praw,
        "preview": lambda: preview(sys.argv[2] if len(sys.argv) > 2 else "car"),
        "ptf": ptf,
        "regsum": doregsum,
        "screen": lambda: subprocess.run(["screen", "-L", PORT, "115200"]),
        "startvlc": lambda: subprocess.run([
            "screen", "-dmS", "vlc", "vlc", "--intf", "qt", "--extraintf", "telnet", "--telnet-password", "abc"
        ]),
        "tf": tonefuse
    }

    if len(sys.argv) < 2:
        print("what?")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd in commands:
        commands[cmd]()
    else:
        print("what?")

if __name__ == "__main__":
    main()

