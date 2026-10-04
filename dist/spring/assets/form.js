(function(){var f=document.getElementById('quoteForm');if(!f)return;
f.addEventListener('submit',async function(e){e.preventDefault();var b=document.getElementById('formBtn'),m=document.getElementById('formMsg'),d=Object.fromEntries(new FormData(f));
if(!f.dataset.key||f.dataset.key.indexOf('YOUR_')===0){var body=Object.keys(d).filter(function(k){return k!=='access_key'&&k!=='botcheck'&&d[k]}).map(function(k){return k+': '+d[k]}).join('\n');
location.href='mailto:'+f.dataset.email+'?subject='+encodeURIComponent('Quote request: '+(f.dataset.site||''))+'&body='+encodeURIComponent(body);return}
b.disabled=true;b.textContent='Sending...';
try{var r=await fetch('https://api.web3forms.com/submit',{method:'POST',headers:{'Content-Type':'application/json',Accept:'application/json'},body:JSON.stringify(d)});var j=await r.json();if(!j.success)throw 0;f.reset();b.textContent='Sent!';m.textContent="Got it. We'll reach out shortly. Need it sooner? Call (346) 413-9644."}
catch(_){b.disabled=false;b.textContent='Get My Fast Quote';m.textContent='Something went wrong. Please call or text (346) 413-9644.'}})})();
