#!/bin/bash
# kill a screen 
# screen -S session -X quit
# 1. Run setres
# 2. startVLC
# 3. 8mm or S8

PORT=/dev/ttyACM0
PROJECT=fm110
FILM=8mm
FRAMES=${PWD}/frames/
FP=${FRAMES}/${PROJECT}
DEVICE=/dev/video0
#VIDEOSIZE=3264x2448
#VIDEOSIZE=640x480
VIDEOSIZE=1280x720

# Extended Dynamic Range
EXPOSURES="12000,3000,5500,8000"
IFS=, read -ra EXPOSE <<<${EXPOSURES}
EDR="--exposure ${EXPOSURES}"

GLOB_REGISTRATION='????????_'${EXPOSE[1]}'.png'
#GLOB_REGISTRATION='00000004_10000.png'
#GLOB_CAR='????????_'${EXPOSE[1]}'.reg'
GLOB_CAR='00000004_10000.reg'

#exec > >(tee -a usb_${OP}_$(TZ= date +%Y%m%d%H%M%S).log) 2>&1
#exec > >(tee -a process.log) 2>&1

if [[ ! $(mount | grep '/media/frames') ]]; then
	echo '*** SSD is not mounted'
	exit 1
fi

mkdir -p ${FP}

for sd in car capture fused graded descratch work capdebug findsprocket; do
    if [[ ! -d "${FP}/${sd}" ]]; then mkdir -p ${FP}/${sd}; fi
done

getcamdev()
{
    echo "/dev/video4"
}

s8()
{
    ./picam_cap.py framecap --framesto ${FP}/capture --frames 3600 --logfile picam_cap.log \
        --film super8 --exposure ${EXPOSURES} --startdia 57 --enddia 33
}

mm8()
{
    ./picam_cap.py framecap --framesto ${FP}/capture --frames 5000 --logfile picam_cap.log \
        --film 8mm --exposure ${EXPOSURES} --startdia 57 --enddia 33 
}

sertest()
{
    ./usbcap.py --camindex $(getdev) --framesto ${FRAMES}  --frames 99999 --logfile usbcap.log \
        --fastforward 12 --res 1 sertest --film super8 --optocount 6 
}

p2()
{
    subdir=${1:-capture}
    for exp in ${EXPOSURES//,/ }; do
        ls ${FP}/${subdir}/????????_${exp}.png > /tmp/filelist.txt
        echo Generating ${FP}/{subdir}_${exp}.mp4
        mplayer mf://@/tmp/filelist.txt -vf scale=640:480 -vo yuv4mpeg:file=${FP}/${subdir}_${exp}.mp4
    done
}

preview()
{
    subdir=${1:-car}
    # ls ${FP}/${subdir}/????????.png > /tmp/filelist.txt
    #ls ${FP}/${subdir}/*_5000.png > /tmp/filelist.txt
    #mplayer mf://@/tmp/filelist.txt -vf scale=640:480 -vo yuv4mpeg:file=${FP}/${PROJECT}.mp4
    IFS=, read -ra exs <<<${EXPOSURES}
    for ex in $exs; do
        ffmpeg -f image2 -r 18 -i ${FP}/${subdir}/%08d_${ex}.png -vcodec libx264 -vf scale=640x480 ${FP}/${PROJECT}_${ex}.mp4 
    done
}

praw()
{
    subdir=${1:-capture}
#    IFS=, read -ra exs <<<${EXPOSURES}
    ffmpeg -f image2 -r 18 -pattern_type glob -i "${FP}/${subdir}/????????_${EXPOSE[1]}.png" \
        -vcodec libx264 -vf scale=640x480 -y ${FP}/${PROJECT}_praw.mov
}

pcar()
{
    subdir=${1:-car}
    IFS=, read -ra exs <<<${EXPOSURES}
    ffmpeg -f image2 -r 18 -pattern_type glob -i "${FP}/${subdir}/????????_${exs[1]}.png" \
        -vcodec libx264 -vf scale=640x480 -y ${FP}/${PROJECT}_pcar_${exs[1]}.mp4 
}

ptf()
{
    ffmpeg -f image2 -r 18 -pattern_type glob -i "${FP}/fused/*.png" \
        -vcodec libx264 -vf scale=640x480 -y ${FP}/${PROJECT}_fused.mp4 
}

getres()
{
    ./usbcap.py --camindex $(getdev) --framesto ${FP}  --frames 99999 --logfile usbcap.log --fastforward 9 --res 1 getres --film 8mm 
}

mount()
{
#    sudo mount.cifs //NAS-36-FE-22/imageinput /media/nas -o user=nobody,password=nobody,rw,file_mode=077r_mode=07777
#    ln -s frames /media/nas/frames 
    sudo mount /dev/sda1 /media/frames -o user=nobody,password=nobody,rw,file_mode=077r_mode=07777
    if [[ "$?" ]]; then
        ln -s frames /media/frames 
    fi
}

descratch()
{
    DOCKERNAME=avxsynth
    SCRIPT=${FP}/avx.avs
    mkdir -p ${FP}/descratch
#    OUT="${FRAMES}/descratch/%08d.png"
    let NUMFRAMES=$(ls ${FP}/graded/????????.png | wc -l)

(cat <<AVS
LoadPlugin("/AviSynthPlus/avisynth-build/plugins/ImageSeq/libimageseq.so")
LoadPlugin("/RemoveDirt/build/RemoveDirt/libremovedirt.so")
LoadPlugin("/mvtools/build/Sources/libmvtools2.so")
LoadPlugin("/RgTools/build/RgTools/librgtools.so")
LoadPlugin("/mvtools/build/DePanEstimate/libdepanestimate.so")
LoadPlugin("/mvtools/build/DePan/libdepan.so")
LoadPlugin("/mvtools/build/Sources/libmvtools2.so")
function RemoveDirt(clip input, bool "_grey", int "repmode") 
{
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
}	
RemoveDirt(ImageReader("/frames/capture/%08d.png", fps=18.0, end=${NUMFRAMES}).converttoYV12())
AVS
)  > ${SCRIPT}

#    for ff in ${FRAMES}/*.png; do convert $ff -resize 2160x1458\! $ff;  done
    docker run --rm -h ${DOCKERNAME} --name ${DOCKERNAME} -t -v ${FP}/:/frames --entrypoint /ffmpeg/ffmpeg  ${DOCKERNAME}:latest -i /frames/avx.avs -y /frames/descratch/%08d.png
}

exptest()
{
    for ((f=1000;f<100000;f+=1000)); do
        EXPOSURES="${EXPOSURES},$f"
    done
    ./picam_cap.py framecap --framesto ${FP}/capture --frames 10 --logfile picam_cap.log \
        --film super8 --exposure ${EXPOSURES} --startdia 57 --enddia 33 
}

tonefuse()
{
    let outputnum=0
    for file in ${FP}/car/????????_${EXPOSE[1]}.png; do
        base=$(dirname $file)
        name=$(basename $file)
        number=$(echo $name | cut -d_ -f1)
        input="${FP}/car/${number}_${EXPOSE[1]}.png ${FP}/car/${number}_${EXPOSE[2]}.png ${FP}/car/${number}_${EXPOSE[3]}.png"  
        output=${FP}/fused/$(printf '%08u' $outputnum).png
	if [[ ! -f "$output" ]]; then
	        enfuse --output $output $input
	fi
        ((outputnum++))
    done

#    for EXP in $(echo ${EXPOSURES} | cut -d, -f2-); do
#        input="${input} ${FP}/car/
#    done
#
#    enfuse --output enfused.jpg 36000.jpg 66000.jpg 105000.jpg 
#    convert 36000.jpg 66000.jpg +append row1.jpg 
#    convert 105000.jpg enfused.jpg +append row2.jpg
##    convert row1.jpg row2.jpg -append grid.jpg
}

oneshot()
{
    ./usbcap.py oneshot --camindex $(getdev) --framesto ${FP} --logfile usbcap.log  --exposure 10000
}

cam()
{
    rpicam-hello --timeout=180s --shutter=9000us --awb 
}

doenfuse()
{
    FRAME=0
    F0="${FP}/car/$(printf '%08u' ${FRAME})_${EXPOSE[1]}.png"
    F1="${FP}/car/$(printf '%08u' ${FRAME})_${EXPOSE[2]}.png"
    F2="${FP}/car/$(printf '%08u' ${FRAME})_${EXPOSE[3]}.png"

    COMMAND="enfuse --output enfused.png ${F0} ${F1} ${F2}"
    ${COMMAND}
    convert ${F0} ${F1} +append row1.png
    convert ${F2} enfused.png +append row2.png
    convert row1.png row2.png -append enfused_grid.png
    rm row1.png row2.png enfused.png
}

doregsum()
{
    for ff in ${FP}/capture/*.reg; do echo -n $ff; echo -n ' '; cat $ff; echo; done > reg.txt
}

clean()
{
    case "$1" in 
	    reg) rm ${FP}/capture/*.reg ;;
	    car) rm ${FP}/car/*.png ;;
	    fused) rm ${FP}/fused/*.png ;;
	    video) rm ${FP}/*.mp4 ;;
	    *) echo what? ;;
    esac
}

#setres()
#{
#    v4l2-ctl --device $(getdev)  --set-fmt-video=width=2592,height=1944
#}

. venv/bin/activate

case "$1" in 
    avx) ./avx.sh ;;
    dev) ffmpeg -devices ;;
    caps) ffmpeg -f v4l2 -list_formats all -i $(getdev) ;;
    cap1bmp) 
        ffmpeg -f v4l2 -video_size ${VIDEOSIZE} -i $(getdev) -vframes 1 -y ${FRAMES}/%08d.bmp ;;
    capmjpeg) 
        ffmpeg -f v4l2 -framerate 1 -video_size ${VIDEOSIZE} -i ${DEVICE}  -vf fps=10 -y ${FRAMES}/capmjpeg_${VIDEOSIZE}.avi ;;
    copy) ffmpeg -f v4l2 -video_size ${VIDEOSIZE} -i ${DEVICE} -vcodec copy -y ${FRAMES}/rawout_${VIDEOSIZE}.avi ;;
    raw2img) ffmpeg -i ${FRAMES}/rawout_${VIDEOSIZE}.avi -vf fps=10 ${FRAMES}/frame%d.png ;;
    pipe) ffmpeg -f v4l2 -video_size ${VIDEOSIZE} -i ${DEVICE} -vf fps=1 ${FRAMES}/frame%d.png ;;
    stream) ffmpeg -video_size 640x480 -rtbufsize 702000k -framerate 10 -i video="${DEVICE}" -threads 4 -vcodec libh264 -crf 0 -preset ultrafast -f mpegts "udp://pop-os:56666" ;;
    getdev) getdev ;;
    clip) clip ;;
    descratch) descratch ;;
    8mm) 
#        rm frames/${PROJECT}/findsprocket/*.png
#        rm frames/${PROJECT}/capture/*.png
        rm *.log
        mm8
        echo s > ${PORT}
#        mv /tmp/*.png /media/frames/${PROJECT}/findsprocket/
        ;;

    s8) 
        rm *.log
        s8 
        echo s > ${PORT}
        ;;
    preview) shift; preview $@ ;;
    p2) shift; p2 $@ ;;
    sertest) sertest ;;
    getres) getres ;;
    mount) mount ;;
	gcd) getcamdev ;;
    previews) preview capture; preview descratch; preview graded ;;
    all) s8; ./colorgrade.py; descratch; previews ;;
    exptest) exptest ;;
    tonefuse) tonefuse ;;
    oneshot) oneshot ;;
    screen) screen -L ${PORT} 115200 ;;
#    setres) setres ;;
    startvlc) screen -dmS vlc vlc --intf qt --extraintf telnet --telnet-password abc ;;
    praw) praw ;;
    pcar) pcar ;;
    ptf) ptf ;;
    clean) clean $2 ;;
    cfp) scp -r projector:/media/frames/${PROJECT} /mnt/s/frames ;;
    registration) ./00_registration.py --readfrom ${FP}/capture/'????????_'${EXPOSE[1]}'.png'  --writeto ${FP}/capture --film ${FILM} ;;
    #registration) ./00_registration.py --readfrom ${FP}/capture/'00000020_'${EXPOSE[1]}'.png'  --writeto ${FP}/capture --film ${FILM} --saveallwork ;;
    regsum) doregsum ;;
    car) ./01_crop_and_rotate.py --readfrom ${FP}/capture/'????????_'${EXPOSE[1]}'.reg' --writeto ${FP}/car --exp ${EXPOSURES} --film ${FILM} ;;
    #car) ./01_crop_and_rotate.py --readfrom ${FP}/capture/'00004120_'${EXPOSE[1]}'.reg' --writeto ${FP}/car --exp ${EXPOSURES} --film ${FILM} ;;
    tf) tonefuse ;;
    cam) cam ;;
    ef) doenfuse ;;
    *) echo what?
esac

deactivate

