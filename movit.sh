#!/bin/bash

let fromcount=241
let tocount=3852
frompath=frames/fm117a/capture
topath=frames/fm117/capture

while [[ -f "${frompath}/"$(printf '%08d_10000.png' ${fromcount}) ]]; do
	for exp in 10000 16000 22000; do
		cp ${frompath}/$(printf '%08d' $fromcount)_${exp}.png  ${topath}/$(printf '%08d' $tocount)_${exp}.png 
	done
	((fromcount++))
	((tocount++))
done


#for ii in {3852..4408}; do rm frames/fm117/capture/*${ii}_*.png; done
