(function(){
function wire(f){f.addEventListener('submit',async function(e){e.preventDefault();var b=f.querySelector('[data-btn]'),m=f.querySelector('[data-msg]'),d=Object.fromEntries(new FormData(f)),label=b.textContent;
if(d.botcheck){m.textContent='Thanks!';return}
b.disabled=true;b.textContent='Sending...';
try{var p={_subject:d.subject,_template:'table',_captcha:'false',name:d.name,phone:d.phone,zip:d.zip,city:d.city,service:d.service,notes:d.message,page:location.href,site:f.dataset.site};Object.keys(p).forEach(function(k){if(!p[k])delete p[k]});var r=await fetch('https://formsubmit.co/ajax/'+f.dataset.email,{method:'POST',headers:{'Content-Type':'application/json',Accept:'application/json'},body:JSON.stringify(p)});var j=await r.json();if(!(j.success===true||j.success==='true'))throw 0;try{fetch('/api/lead',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.assign({},d,{access_key:undefined})),keepalive:true})}catch(_){}
f.reset();b.textContent='Sent!';m.textContent="Got it. We'll reach out shortly. Need it sooner? Call (346) 413-9644."}
catch(_){b.disabled=false;b.textContent=label;m.textContent='Something went wrong. Please call or text (346) 413-9644.'}})}
document.querySelectorAll('form[data-quote]').forEach(wire)})();
