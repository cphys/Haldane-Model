# Script to get spectrums

muRes=51
kResolution=101
width=30


python3 graphineHaldaneModel.py $muRes $kResolution $width
python3 berryCurve.py $muRes $kResolution $width

