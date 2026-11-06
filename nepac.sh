#!/usr/bin/env bash
date=$(date --date '4 hours ago' '+%Y%m%d')
temphour=$(($(date --date '4 hours ago' '+%H') - $(($(date --date '4 hours ago' '+%H')%6))))

printf -v hour '%02d' $temphour

echo $date $hour

wget -O /home/ubuntu/scripts/py3/npacs/filter.grib2 "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?dir=%2Fgfs.${date}%2F${hour}%2Fatmos&file=gfs.t${hour}z.pgrb2.0p25.f000&var_PRMSL=on&var_UGRD=on&var_VGRD=on&lev_10_m_above_ground=on&lev_mean_sea_level=on&subregion=&toplat=90&leftlon=100&rightlon=300&bottomlat=10"

/home/ubuntu/scripts/py3/npacs/wgrib2 /home/ubuntu/scripts/py3/npacs/filter.grib2 -netcdf /home/ubuntu/scripts/py3/npacs/filter.nc

source ~/anaconda3/etc/profile.d/conda.sh
conda activate py3
python /home/ubuntu/scripts/py3/npacs/nepac.py $date $hour
