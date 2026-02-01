#!/bin/bash
# kill a screen 
# screen -S session -X quit
# 1. Run setres
# 2. startVLC
# 3. 8mm or S8

PORT=/dev/ttyACM0
PROJECT="fm229 Matt 13 Months"
#FILM=super8
FILM=8mm
FRAMES=${PWD}/frames/
FP=${FRAMES}/${PROJECT}
DEVICE=/dev/video0
#VIDEOSIZE=3264x2448
#VIDEOSIZE=640x480
VIDEOSIZE=1280x720

# Extended Dynamic Range
#EXPOSURES="12000,3000,5500,8000"
EXPOSURES="12000,4000,8000,12000"
IFS=, read -ra EXPOSE <<<${EXPOSURES}
EDR="--exposure ${EXPOSURES}"

GLOB_REGISTRATION='????????_'${EXPOSE[1]}'.png'
#GLOB_REGISTRATION='00000004_10000.png'
#GLOB_CAR='????????_'${EXPOSE[1]}'.reg'
GLOB_CAR='00000004_10000.reg'
SAVEWORK='--saveallwork --saveworkto '${FP}'/work'
#DEBUG='--debugpy'
DEBUG=''


#exec > >(tee -a usb_${OP}_$(TZ= date +%Y%m%d%H%M%S).log) 2>&1
#exec > >(tee -a process.log) 2>&1
domount()
{
#    sudo mount.cifs //NAS-36-FE-22/imageinput /media/nas -o user=nobody,password=nobody,rw,file_mode=077r_mode=07777
#    ln -s frames /media/nas/frames 
    sudo mount /dev/sda1 /media/frames -o user=nobody,password=nobody,rw,file_mode=077,r_mode=07777
    if [[ "$?" ]]; then
        ln -s frames /media/frames 
    fi
}

#if [[ ! $(mount | grep '/media/frames') ]]; then
#	echo '*** SSD is not mounted'
#    domount
#	exit 1
#fi

mkdir -p ${FP}

for sd in car capture fused work; do
    if [[ ! -d "${FP}/${sd}" ]]; then mkdir -p ${FP}/${sd}; fi
done


writeconfig()
{
    if [[  -f "${FP}/config.toml" ]]; then
        return
    fi
    if [[ "8mm" == "${FILM}" ]]; then
    cat <<CFG8MM > ${FP}/config.toml
[capture]
winy = 50
winx = 50
winw = 110
winh = 60

[car]
yoffset = -32
ysize = 1120
xoffset = 330
xsize  = 450
CFG8MM

    else
    cat <<CFGSUPER8 > ${FP}/config.toml
[capture]
winx = 30
winy = 206
winw = 50
winh = 100

[car]
yoffset = -32
ysize = 1120
CFGSUPER8

    fi
}

getcamdev()
{
    echo "/dev/video4"
}


capture()
{
#        --film 8mm --exposure ${EXPOSURES} --startdia 170 --enddia 33 \
    writeconfig
    ./picam_cap.py framecap --project ${FP} --frames 3500 --logfile picam_cap.log \
        --film ${FILM} --exposure ${EXPOSURES} --startdia 60 --enddia 50  \
            --savework --saveworkto ${FP}/work --saveallwork
}

# sertest()
# {
#     ./usbcap.py --camindex $(getdev) --project ${FRAMES}  --frames 99999 --logfile usbcap.log \
#         --fastforward 12 --res 1 sertest --film super8 --optocount 6 
# }

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
        -vcodec libx264 -pix_fmt yuv420p -vf scale=640x480 -y ${FP}/${PROJECT}_praw.mp4
}

pcar()
{
    subdir=${1:-car}
    IFS=, read -ra exs <<<${EXPOSURES}
    ffmpeg -f image2 -r 18 -pattern_type glob -i "${FP}/${subdir}/????????_${exs[1]}.png" \
        -vcodec libx264 -pix_fmt yuv420p -vf scale=640x480 -y ${FP}/${PROJECT}_pcar_${exs[1]}.mp4 
}

ptf()
{
    ffmpeg -f image2 -r 18 -pattern_type glob -i "${FP}/fused/*.png" \
        -vcodec libx264 -pix_fmt yuv420p -vf scale=640x480 -y ${FP}/${PROJECT}_fused.mp4 
}

getres()
{
    ./usbcap.py --camindex $(getdev) --project ${FP}  --frames 99999 --logfile usbcap.log --fastforward 9 --res 1 getres --film 8mm 
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
    ./picam_cap.py framecap --project ${FP} --frames 10 --logfile picam_cap.log \
        --film 8mm --exposure ${EXPOSURES} --startdia 57 --enddia 33 
}

tonefuse()
{
    let outputnum=0
    echo $FP is  $FP
    for file in ${FP}/car/????????_${EXPOSE[0]}.png; do
        echo file is $file
        base=$(dirname "'"$file"'")
        echo base is $base
        name=$(basename "'"$file"'")
        echo $name is $name
        continue
        number=$(echo $name | cut -d_ -f1)
        input="${FP}/car/${number}_${EXPOSE[1]}.png" "${FP}/car/${number}_${EXPOSE[2]}.png" "${FP}/car/${number}_${EXPOSE[3]}.png"  
        output="${FP}/fused/$(printf '%08u' $outputnum).png"
	if [[ ! -f "$output" ]]; then
echo	        enfuse --output $output $input
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
    ./usbcap.py oneshot --camindex $(getdev) --project ${FP} --logfile usbcap.log  --exposure 10000
}

cam()
{
    rpicam-hello --timeout=180s --shutter=9000us 
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

capturevid()
{
    echo 'c90tlf' > ${PORT}
    libcamera-vid --width 640 --height 480 --preview --framerate 10 --output ${FP}/camvideo.mp4 --timeout 500000
    echo s > ${PORT}
# {ffmpeg -i camvideo.mp4 captured_video/%06d.png

}

car()
{
    echo ./01_crop_and_rotate.py --readfrom "${FP}/capture/????????_${EXPOSE[2]}.reg" --writeto "${FP}/car" --exp ${EXPOSURES} --film ${FILM}
    ./01_crop_and_rotate.py \
        --readfrom "${FP}/capture/????????_${EXPOSE[2]}.reg" \
        --writeto "${FP}/car" \
        --exp ${EXPOSURES} \
        --film ${FILM}
}


registration()
{
    echo ./00_registration.py \
        --project "'"${FP}"'" \
        --readfrom "'"${FP}/capture/'????????'_${EXPOSE[2]}.png"'" \
        --writeto "'"${FP}/capture"'" \
        --film ${FILM} #  ${SAVEWORK} ${DEBUG}
}

#setres()
#    v4l2-ctl --device $(getdev)  --set-fmt-video=width=2592,height=1944
#}

#. venv/bin/activate

case "$1" in 
    capture) capture; echo s > ${PORT} ;;
    all) capture
        echo ' ' > ${PORT}
        registration
        car
        tonefuse
        ptf ;;
    avx) ./avx.sh ;;
    cam) cam ;;
    cap1bmp) 
        ffmpeg -f v4l2 -video_size ${VIDEOSIZE} -i $(getdev) -vframes 1 -y ${FRAMES}/%08d.bmp ;;
    capmjpeg) 
        ffmpeg -f v4l2 -framerate 1 -video_size ${VIDEOSIZE} -i ${DEVICE}  -vf fps=10 -y ${FRAMES}/capmjpeg_${VIDEOSIZE}.avi ;;
    caps) ffmpeg -f v4l2 -list_formats all -i $(getdev) ;;
    capvid) capturevid ;;
    car) car ;;
    cfp) scp -r projector:/media/frames/${PROJECT} /mnt/s/frames ;;
    clean) clean $2 ;;
    clip) clip ;;
    copy) ffmpeg -f v4l2 -video_size ${VIDEOSIZE} -i ${DEVICE} -vcodec copy -y ${FRAMES}/rawout_${VIDEOSIZE}.avi ;;
    descratch) descratch ;;
    ef) doenfuse ;;
    exptest) exptest ;;
	gcd) getcamdev ;;
    dev) ffmpeg -devices ;;
    getdev) getdev ;;
    getres) getres ;;
    mktf) ffmpeg -f image2 -r 18 -pattern_type glob -i "${FP}/fused/*.png" -c:v copy ${FP}/${FP}_fused.mkv ;;
    mount) domount ;;
    oneshot) oneshot ;;
    p2) shift; p2 $@ ;;
    pcar) pcar ;;
    pipe) ffmpeg -f v4l2 -video_size ${VIDEOSIZE} -i ${DEVICE} -vf fps=1 ${FRAMES}/frame%d.png ;;
    praw) praw ;;
    preview) shift; preview $@ ;;
    previews) preview capture; preview descratch; preview graded ;;
    ptf) ptf ;;
    raw2img) ffmpeg -i ${FRAMES}/rawout_${VIDEOSIZE}.avi -vf fps=10 ${FRAMES}/frame%d.png ;;
    registration) registration ;;
    regsum) doregsum ;;
    screen) screen -L ${PORT} 115200 ;;
    sertest) sertest ;;
    startvlc) screen -dmS vlc vlc --intf qt --extraintf telnet --telnet-password abc ;;
    stream) ffmpeg -video_size 640x480 -rtbufsize 702000k -framerate 10 -i video="${DEVICE}" -threads 4 -vcodec libh264 -crf 0 -preset ultrafast -f mpegts "udp://pop-os:56666" ;;
    tf) tonefuse ;;
    tsd) ./test_sprocket_detect.py framecap --useframes ${FP}/captured_video/'*.png' --film 8mm --project ${FP} --logfile tsd.log ;;
    *) echo what?
esac

#deactivate

