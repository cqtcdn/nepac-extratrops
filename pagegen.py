import math
import ftplib
import datetime
import pickle
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

def getwindstormwindcolor(w):
	if w >= 64:
		color = '#cd5c5c'
	elif w >= 48:
		color = '#9400d3'
	else:
		color = '#dda0dd'
	return color

def determine_title(wind, wstype):
	if wstype == 'WS':
		if wind >= 64:
			title = 'Hurricane-Force Low'
			hclass = 'hurricane'
		elif wind >= 48:
			title = 'Storm-Force Low'
			hclass = 'storm'
		else:
			title = 'Gale-Force Low'
			hclass = 'gale'
	else:
		title = 'Ex-Windstorm'
		hclass = 'ex'

	return (title, hclass)

def formatdatafortable(tctime, tclat, tclon, tcwind, tcpres, tctype):
	ftime = f'{tctime[0:4]}-{tctime[4:6]}-{tctime[6:8]} {tctime[8:10]}:00'
	
	if tclat >= 0:
		flat = f'{math.fabs(tclat):.1f}&deg;N'
	else:
		flat = f'{math.fabs(tclat):.1f}&deg;S'
		
	if tclon >= 180:
		tclon -= 360
		flon = f'{math.fabs(tclon):.1f}&deg;W'
	else:
		flon = f'{math.fabs(tclon):.1f}&deg;E'
	
	#can add support for kpg/u here later
	fwind = f'{tcwind} kts'
	
	if tcpres != 0:
		fpres = f'{tcpres} hPa'
	else:
		fpres = '0000 hPa'
	
	#handle all special types first
	if tctype == 'PR':
		ftype = 'Pre-windstorm'
		if tcwind >= 34:
			fclass = 'ey'
		else:
			fclass = 'ex'
	elif tctype == 'EX':
		ftype = 'Ex-windstorm'
		if tcwind >= 34:
			fclass = 'ey'
		else:
			fclass = 'ex'
	elif tctype == 'TS' or tctype == 'TD' or tctype == 'TY' or tctype == 'HU':
		ftype = 'Tropical cyclone'
		if tcwind >= 34:
			fclass = 'ey'
		else:
			fclass = 'ex'
	elif tctype == 'PD':
		ftype = 'Post-tropical depression'
		fclass = 'ex'
	elif tctype == 'PS':
		ftype = 'Post-tropical storm'
		fclass = 'ey'
	else:
		#windstorm
		if tcwind >= 64:
			ftype = 'Hurricane-force low'
			fclass = 'hurricane'
		elif tcwind >= 48:
			ftype = 'Storm-force low'
			fclass = 'storm'
		else:
			ftype = 'Gale-force low'
			fclass = 'gale'
	
	return (ftime, flat, flon, fwind, fpres, ftype, fclass)

#load in data from a file in /trackdata
t = datetime.datetime.now()
title_thismonth = t.strftime('%B %Y')
month = t.strftime('%b').lower()
yy = int(t.strftime('%y'))
mm = int(t.strftime('%m'))

if mm <= 6:
    season = f'{yy-1:02}{yy:02}'
else:
    season = f'{yy:02}{yy+1:02}'

fname = f'{month}{yy:02}' #input('file to parse: ')
yyyymm = t.strftime('%Y%m')

f = open(f'/home/ubuntu/scripts/py3/npacs/curmonth', 'r')
k = f.readlines()

#read through the file and parse data into the master dictionary
all_storm_tracks = {}
for line in k:
	s = line.strip().split(',')
	
	if len(s) == 1:
		sname = s[0]
		continue

	sid = ''.join(s[0:2])
	stime = s[2]

	slat = float(s[5][:-1])
	if s[6][-1] == 'E':
		slon = float(s[6][:-1])
	else:
		slon = -float(s[6][:-1])+360.
	swind = int(s[7])
	try:
		spres = int(s[8])
	except:
		spres = 9999
	stype = s[9]
	
	#compose storm full storm id
	full_storm_id = f'{season}{sid}' #2627NW01 for the first windstorm forming in nwpac in 2026-27
	
	if full_storm_id not in all_storm_tracks:
		print(f'windstorm identified: {full_storm_id}')
	
		#initialize these only at the first point
		all_storm_tracks[full_storm_id] = {}
		all_storm_tracks[full_storm_id]['name'] = sname
		all_storm_tracks[full_storm_id]['times'] = []
		all_storm_tracks[full_storm_id]['lats'] = []
		all_storm_tracks[full_storm_id]['lons'] = []
		all_storm_tracks[full_storm_id]['winds'] = []
		all_storm_tracks[full_storm_id]['press'] = []
		all_storm_tracks[full_storm_id]['types'] = []
		all_storm_tracks[full_storm_id]['max_wind'] = 0
		all_storm_tracks[full_storm_id]['min_pres'] = 9999

	#continuously update these with each new point
	all_storm_tracks[full_storm_id]['times'].append(stime)
	all_storm_tracks[full_storm_id]['lats'].append(slat)
	all_storm_tracks[full_storm_id]['lons'].append(slon)
	all_storm_tracks[full_storm_id]['winds'].append(swind)
	all_storm_tracks[full_storm_id]['press'].append(spres)
	all_storm_tracks[full_storm_id]['types'].append(stype)

	#update these only if it's a windstorm
	if stype == 'WS':
		#only if it's the first time it's a windstorm
		if 'formation_month' not in all_storm_tracks[full_storm_id]:
			all_storm_tracks[full_storm_id]['formation_month'] = stime[4:6]
			all_storm_tracks[full_storm_id]['formation_date'] = stime[6:8]
			
		#keep continuously updated
		all_storm_tracks[full_storm_id]['dissipation_month'] = stime[4:6]
		all_storm_tracks[full_storm_id]['dissipation_date'] = stime[6:8]
		#and we find a new stronger intensity
		if swind > all_storm_tracks[full_storm_id]['max_wind']:
			all_storm_tracks[full_storm_id]['max_wind'] = swind
		if spres < all_storm_tracks[full_storm_id]['min_pres']:
			all_storm_tracks[full_storm_id]['min_pres'] = spres

#set up plot
parallels = np.arange(0, 90, 10)
meridians = np.arange(-180, 180, 10)

proj = ccrs.LambertConformal(central_latitude=50., central_longitude=-165.)

fig = plt.figure(figsize=(19.2, 10.8))
ax = fig.add_axes([0.0, 0.0, 0.915, 0.915], projection=proj)
ax.set_extent([-220., -110., 67., 30.], crs=ccrs.PlateCarree())

#plt.rcParams['font.sans-serif'] = 'Segoe UI'

tf = ccrs.PlateCarree()._as_mpl_transform(ax)

#ax.add_geometries(coastline.geometries(), crs=ccrs.PlateCarree(), edgecolor=(0., 0., 0.), linewidth=1.0, facecolor='none')
ax.coastlines(resolution='50m', linewidth=0.5, color='#000000', zorder=0)

gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=1, color=(0.2, 0.2, 0.2), linestyle='-')
gl.xlabel_bottom = True
gl.xlabel_top = True
gl.xlocator = mticker.FixedLocator(meridians)
gl.ylocator = mticker.FixedLocator(parallels)
gl.xformatter = LongitudeFormatter()
gl.yformatter = LatitudeFormatter()

ax.add_feature(cfeature.LAND.with_scale('50m'), facecolor='#dddddd', zorder=-1) #bfbfbf
ax.add_feature(cfeature.LAKES.with_scale('50m'), facecolor='#b0ffff', zorder=-1) #80d4ff
ax.add_feature(cfeature.OCEAN.with_scale('50m'), facecolor='#b0ffff', zorder=-1) #80d4ff

edgecolor = '#222222'

#init page
t_thismonth = datetime.datetime(int(yyyymm[0:4]), int(yyyymm[4:6]), 1, 0, 0, 0)
t_lastmonth = t_thismonth + datetime.timedelta(days=-15)
t_nextmonth = t_thismonth + datetime.timedelta(days=45)

title_thismonth = t_thismonth.strftime('%B %Y')
link_lastmonth = t_lastmonth.strftime('%b%y').lower()
link_nextmonth =  t_nextmonth.strftime('%b%y').lower()

html = f'<head>\n<link rel="stylesheet" href="../seasonsum.css">\n</head>\n\n'
html += f'<title>{title_thismonth} North Pacific windstorms</title>\n\n'
html += f'<div class="month-nav">\n\t<p class="month-navigation"><a href="{link_lastmonth}.html">←</a></p> <p class="month-header">{title_thismonth}</p> <p class="month-navigation"><a href="{link_nextmonth}.html">→</a></p>\n</div>'
html += '<p class="track-data-header"><span style="color:red">[PRELIMINARY]</span></p>\n\n'
html += f'<img src="./trackmaps/{fname}.png" />\n\n<p class="track-data-header">Windstorm summary</p>\n\n'

nw_html = '<table>\n\t<tr class="header">\n\t\t<td><b>id</b></td>\n\t\t<td><b>Windstorm</b></td>\n\t\t<td><b>Active dates</b></td>\n\t\t<td><b>Max wind</b></td>\n\t\t<td><b>Min pres.</b></td>\n\t</tr>\n'
ne_html = '<table>\n\t<tr class="header">\n\t\t<td><b>id</b></td>\n\t\t<td><b>Windstorm</b></td>\n\t\t<td><b>Active dates</b></td>\n\t\t<td><b>Max wind</b></td>\n\t\t<td><b>Min pres.</b></td>\n\t</tr>\n'
trackdata_html = '<p class="track-data-header">Track data</p>\n\n'

#loop through each storm
#todo: do we need a list of storms parsed on this run?

for storm_id in all_storm_tracks.keys():
	#for each storm, add to nw or ne summary table
	stitle, sclass = determine_title(all_storm_tracks[storm_id]['max_wind'], 'WS')
	storm_name = all_storm_tracks[storm_id]['name']
	
	#create dummy datetimes
	t_formed = datetime.datetime(2026, int(all_storm_tracks[storm_id]["formation_month"]), 1, 0, 0, 0)
	t_dissipated = datetime.datetime(2026, int(all_storm_tracks[storm_id]["dissipation_month"]), 1, 0, 0, 0)
	#so we can extract the month name
	month_formed = t_formed.strftime('%B')
	month_dissipated = t_dissipated.strftime('%B')
	
	if month_formed == month_dissipated:
		#if formation and dissipation month are the same, remove this formatting from the summary row, we don't need it
		month_dissipated = ''
	else:
		#if they're different, we want it, but add a space
		month_dissipated += ' '
	
	summary_row_html = f'\t<tr class="{sclass}">\n\t\t<td><a href="#{storm_id[4:]}">{storm_id[4:]}</a></td>\n\t\t<td>{stitle} {storm_name}</td>\n\t\t<td>{month_formed} {int(all_storm_tracks[storm_id]["formation_date"])} &ndash; {month_dissipated}{int(all_storm_tracks[storm_id]["dissipation_date"])}</td>\n\t\t<td>{all_storm_tracks[storm_id]["max_wind"]} kts</td>\n\t\t<td>{all_storm_tracks[storm_id]["min_pres"]} hPa</td>\n\t</tr>\n'
	
	#add to either nw or ne summary table
	if storm_id[4:6] == 'NW':
		nw_html += summary_row_html
	elif storm_id[4:6] == 'NE':
		ne_html += summary_row_html

	#make its own track data table
	trackdata_html += f'<p class="npac-track-data-subheader" id="{storm_id[4:]}"><b>{storm_id[4:]}</b> &ndash; {stitle} {storm_name}</p>\n\n'
	trackdata_html += '<table>\n\t<tr class="header">\n\t\t<td><b>Time</b></td>\n\t\t<td><b>Strength</b></td>\n\t\t<td><b>Lat</b></td>\n\t\t<td><b>Lon</b></td>\n\t\t<td><b>Wind</b></td>\n\t\t<td><b>Pres.</b></td>\n\t</tr>'
	
	#access track data
	wstimes = all_storm_tracks[storm_id]['times']
	wslats = all_storm_tracks[storm_id]['lats']
	wslons = all_storm_tracks[storm_id]['lons']
	wswinds = all_storm_tracks[storm_id]['winds']
	wspress = all_storm_tracks[storm_id]['press']
	wstypes = all_storm_tracks[storm_id]['types']
	
	max_wind = all_storm_tracks[storm_id]['max_wind']
	
	for x in range(0, len(wstimes)):
		#add row to track data table
		ftime, flat, flon, fwind, fpres, ftype, fclass = formatdatafortable(wstimes[x], wslats[x], wslons[x], wswinds[x], wspress[x], wstypes[x])
		trackdata_html += f'\t<tr class="{fclass}">\n\t\t<td>{ftime}</td>\n\t\t<td>{ftype}</td>\n\t\t<td>{flat}</td>\n\t\t<td>{flon}</td>\n\t\t<td>{fwind}</td>\n\t\t<td>{fpres}</td>\n\t</tr>\n'
		
		#plotting stuff
		if wstypes[x] == 'PR' or wstypes[x] == 'EX':
			color = '#aaaaaa'
			mark = 'x'
			medgecolor = color
			msize = 12
			medgewidth = 1
			lstyle = 'dotted' #dashed
			lwidth = 2.5
		elif wstypes[x] == 'TS' or wstypes[x] == 'TD' or wstypes[x] == 'TY' or wstypes[x] == 'HU': #special handling of tropical cyclones
			color = '#aaaaaa'
			mark = 'x'
			medgecolor = color
			msize = 12
			medgewidth = 1
			lstyle = 'solid'
			lwidth = 3
		else:
			color = getwindstormwindcolor(wswinds[x])
			medgecolor = edgecolor
			msize = 12
			medgewidth = 1
			lstyle = 'solid'
			lwidth = 3
		
		#plot track on monthly map
		ax.plot(wslons[x:x+2], wslats[x:x+2], c=color, linestyle=lstyle, linewidth=lwidth, marker='none', transform=ccrs.PlateCarree(), zorder=1)
		
	#plot name
	max_color = getwindstormwindcolor(max_wind)
	ax.annotate(storm_name, xy=(wslons[0], wslats[0]), xytext=(-5, 0), textcoords='offset points', ha='right', va='center', color=max_color, transform=ccrs.PlateCarree())
	
	trackdata_html += '</table>\n\n'
	
#assemble the page
#we need nw and ne tables side by side, then all the individual storm track data below
nw_html += '</table>\n\n'
ne_html += '</table>\n\n'

html += '<div class="nw-ne-table-container">'
html += nw_html
html += ne_html
html += '</div>\n\n'

html += trackdata_html

#save html to file
f = open(f'/home/ubuntu/scripts/py3/npacs/pages/{fname}.html', 'w')
f.write(html)
f.close()

print('saving figure...')
plt.savefig(f"/home/ubuntu/scripts/py3/npacs/img/{fname}.png", bbox_inches='tight', pad_inches=0, dpi=100)
print('figure saved!')
plt.close()

#upload
#upload
facc = open('creds', 'r')
k = facc.readlines()

ftpacc = k[0].strip()
ftppass = k[1].strip()

session = ftplib.FTP('ftp.paladinofstorms.net',ftpacc,ftppass)

f = open(f'/home/ubuntu/scripts/py3/npacs/img/{fname}.png', 'rb')
session.cwd('/npac/trackdata/trackmaps/')
session.storbinary(f'STOR {fname}.png', f)
f.close()

print(f'uploading {fname}.html...')

f = open(f'/home/ubuntu/scripts/py3/npacs/pages/{fname}.html', 'rb')
session.cwd('/npac/trackdata/')
session.storbinary(f'STOR {fname}.html', f)
f.close()

session.quit()
