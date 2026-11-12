const menuBtn=document.getElementById('menu');const links=document.getElementById('links');const themeBtn=document.getElementById('theme');const navLinks=[...links.querySelectorAll('a')];const sections=[...document.querySelectorAll('main section[id]')];
menuBtn.addEventListener('click',()=>links.classList.toggle('open'));
navLinks.forEach(a=>a.addEventListener('click',()=>links.classList.remove('open')));
const savedTheme=localStorage.getItem('portfolio-theme');if(savedTheme==='light'){document.body.classList.add('light');themeBtn.textContent='☾'}
themeBtn.addEventListener('click',()=>{document.body.classList.toggle('light');const isLight=document.body.classList.contains('light');themeBtn.textContent=isLight?'☾':'☼';localStorage.setItem('portfolio-theme',isLight?'light':'dark')});
const revealObserver=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('visible');revealObserver.unobserve(entry.target)}}),{threshold:.12});document.querySelectorAll('.reveal').forEach(el=>revealObserver.observe(el));
window.addEventListener('scroll',()=>{let id='';sections.forEach(s=>{if(scrollY>=s.offsetTop-180)id=s.id});navLinks.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+id))},{passive:true});
