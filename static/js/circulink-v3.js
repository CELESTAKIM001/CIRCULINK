(function(){
  'use strict';
  const root=document.documentElement;
  const saved=localStorage.getItem('circulink-theme');
  if(saved==='dark'||saved==='light') root.dataset.theme=saved;
  const toggle=document.querySelector('[data-theme-toggle]');
  if(toggle){
    const sync=()=>{const dark=root.dataset.theme==='dark';toggle.setAttribute('aria-pressed',String(dark));toggle.title=dark?'Use light theme':'Use dark theme';};
    sync();
    toggle.addEventListener('click',()=>{const next=root.dataset.theme==='dark'?'light':'dark';root.dataset.theme=next;localStorage.setItem('circulink-theme',next);sync();});
  }
  document.querySelectorAll('[data-nav-toggle]').forEach(btn=>btn.addEventListener('click',()=>{const open=document.body.classList.toggle('nav-open');btn.setAttribute('aria-expanded',String(open));}));
  document.querySelectorAll('.v3-rail a').forEach(a=>a.addEventListener('click',()=>document.body.classList.remove('nav-open')));
  const current=location.pathname.replace(/\/$/,'')||'/';
  document.querySelectorAll('.v3-nav a[data-nav]').forEach(a=>{const p=(a.getAttribute('href')||'').replace(/\/$/,'')||'/';if(p==='/'?current==='/':current===p||current.startsWith(p+'/'))a.setAttribute('aria-current','page');});
})();
