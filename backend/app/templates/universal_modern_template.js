const header=document.querySelector('.site-header');const menuBtn=document.querySelector('.menu-toggle');const menu=document.querySelector('.nav-links');const themeBtn=document.querySelector('.theme-toggle');const links=[...document.querySelectorAll('.nav-links a')];const sections=[...document.querySelectorAll('main section[id]')];
function closeMenu(){menu.classList.remove('open');menuBtn.setAttribute('aria-expanded','false')}
menuBtn.addEventListener('click',()=>{const open=menu.classList.toggle('open');menuBtn.setAttribute('aria-expanded',String(open))});
links.forEach(link=>link.addEventListener('click',closeMenu));
window.addEventListener('scroll',()=>header.classList.toggle('scrolled',window.scrollY>24),{passive:true});
const sectionObserver=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){links.forEach(a=>a.classList.toggle('active',a.getAttribute('href')==='#'+entry.target.id))}}),{rootMargin:'-35% 0px -55%'});sections.forEach(section=>sectionObserver.observe(section));
const revealObserver=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('visible');revealObserver.unobserve(entry.target)}}),{threshold:.12});document.querySelectorAll('.reveal').forEach(el=>revealObserver.observe(el));
const savedTheme=localStorage.getItem('portfolio-theme');if(savedTheme==='light')document.body.classList.add('light');themeBtn.addEventListener('click',()=>{document.body.classList.toggle('light');localStorage.setItem('portfolio-theme',document.body.classList.contains('light')?'light':'dark')});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMenu()});
