#!/bin/bash

# Bash script to invoke functions in the Python script using case

PYTHON_SCRIPT="process.py"

# Check if the Python script exists
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo "Error: $PYTHON_SCRIPT not found!"
    exit 1
fi

# Function to run the Python script with a given command
run_python() {
    poetry run python "$PYTHON_SCRIPT" "$1"
}

# Case statement to invoke each function in the Python script
case "$1" in
    capture)
        run_python "capture"
        ;;
    all)
        run_python "all"
        ;;
    cam)
        run_python "cam"
        ;;
    cap1bmp)
        run_python "cap1bmp"
        ;;
    capmjpeg)
        run_python "capmjpeg"
        ;;
    caps)
        run_python "caps"
        ;;
    capvid)
        run_python "capvid"
        ;;
    car)
        run_python "car"
        ;;
    clean)
        if [[ -n "$2" ]]; then
            python3 "$PYTHON_SCRIPT" "clean" "$2"
        else
            run_python "clean"
        fi
        ;;
    descratch)
        run_python "descratch"
        ;;
    ef)
        run_python "ef"
        ;;
    exptest)
        run_python "exptest"
        ;;
    gcd)
        run_python "gcd"
        ;;
    getres)
        run_python "getres"
        ;;
    mount)
        run_python "mount"
        ;;
    oneshot)
        run_python "oneshot"
        ;;
    pcar)
        run_python "pcar"
        ;;
    praw)
        run_python "praw"
        ;;
    preview)
        if [[ -n "$2" ]]; then
            python3 "$PYTHON_SCRIPT" "preview" "$2"
        else
            run_python "preview"
        fi
        ;;
    ptf)
        run_python "ptf"
        ;;
    regsum)
        run_python "regsum"
        ;;
    screen)
        run_python "screen"
        ;;
    startvlc)
        run_python "startvlc"
        ;;
    tf)
        run_python "tf"
        ;;
    *)
        echo "Usage: $0 {capture|all|cam|cap1bmp|capmjpeg|caps|capvid|car|clean|descratch|ef|exptest|gcd|getres|mount|oneshot|pcar|praw|preview|ptf|regsum|screen|startvlc|tf}"
        exit 1
        ;;
esac
