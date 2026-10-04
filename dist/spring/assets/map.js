(function(){var el=document.getElementById('jjMap');if(!el)return;
function init(){if(!window.L)return setTimeout(init,150);
var cities=JSON.parse(el.dataset.cities||'[]'),jobs=JSON.parse(el.dataset.jobs||'[]');
var map=L.map(el,{scrollWheelZoom:false});L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,attribution:'&copy; OpenStreetMap'}).addTo(map);
var b=[];cities.forEach(function(c){L.circle([c.lat,c.lon],{radius:9000,color:'#14F500',weight:1,fillColor:'#14F500',fillOpacity:.12}).addTo(map);
L.marker([c.lat,c.lon]).addTo(map).bindPopup('<a href="'+c.u+'"><b>'+c.n+'</b><br>Junk removal in '+c.n+'</a>');b.push([c.lat,c.lon])});
jobs.forEach(function(j){L.circleMarker([j.lat,j.lon],{radius:8,color:'#fff',weight:2,fillColor:'#14F500',fillOpacity:1}).addTo(map).bindPopup((j.img?'<img src="'+j.img+'" style="width:180px;border-radius:8px"><br>':'')+'<b>'+j.t+'</b>'+(j.area?'<br>'+j.area:''));b.push([j.lat,j.lon])});
map.fitBounds(b,{padding:[30,30]});el.classList.add('jj-dark')}
init()})();
