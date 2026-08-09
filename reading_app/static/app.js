function $(sel){return document.querySelector(sel)}

document.addEventListener('DOMContentLoaded', ()=>{
  const siteSelect = $('#siteSelect');
  const tocSelect = $('#tocSelect');
  const titleEl = $('#chapterTitle');
  const contentEl = $('#chapterContent');
  const fontSize = $('#fontSize');
  const lineHeight = $('#lineHeight');
  const readWidth = $('#readWidth');
  const softFont = $('#softFont');
  const themeToggle = $('#themeToggle');

  let chapters = [];
  let current = 1;
  let currentSite = null;

  function applyControls(){
    contentEl.style.fontSize = fontSize.value + 'px';
    contentEl.style.lineHeight = lineHeight.value;
    contentEl.style.maxWidth = readWidth.value + 'px';
    if(softFont.checked) document.body.classList.add('soft-font'); else document.body.classList.remove('soft-font');
    if(themeToggle.checked) document.body.classList.add('dark'); else document.body.classList.remove('dark');
  }

  fontSize.addEventListener('input',applyControls);
  lineHeight.addEventListener('input',applyControls);
  readWidth.addEventListener('input',applyControls);
  softFont.addEventListener('change',applyControls);
  themeToggle.addEventListener('change',applyControls);

  async function fetchSites(){
    const res = await fetch('/api/sites');
    const data = await res.json();
    siteSelect.innerHTML = '';
    data.forEach(s=>{const opt = document.createElement('option');opt.value=s.id;opt.textContent=s.id;siteSelect.appendChild(opt)});
    if(data.length) {currentSite = data[0].id; await loadChapters(currentSite)}
  }

  async function loadChapters(site){
    currentSite = site;
    const res = await fetch(`/api/chapters?site=${encodeURIComponent(site)}`);
    chapters = await res.json();
    tocSelect.innerHTML = '';
    chapters.forEach(ch=>{const opt=document.createElement('option');opt.value=ch.number;opt.textContent=ch.number+': '+ch.title;tocSelect.appendChild(opt)});
    if(chapters.length){current = chapters[0].number; loadChapter(current)}
  }

  async function loadChapter(num){
    const res = await fetch(`/api/chapter?site=${encodeURIComponent(currentSite)}&num=${num}`);
    if(!res.ok) return;
    const ch = await res.json();
    titleEl.textContent = ch.title ? `${ch.number} — ${ch.title}` : `${ch.number}`;
    contentEl.innerText = ch.text || '';
    contentEl.focus();
    // select TOC
    tocSelect.value = String(num);
    current = num;
  }

  // keyboard navigation: left/right move between chapters

  tocSelect.addEventListener('change', e=>{ current = parseInt(e.target.value); loadChapter(current)});
  siteSelect.addEventListener('change', e=>{ loadChapters(e.target.value)});

  // keyboard navigation
  document.addEventListener('keydown', (e)=>{
    if(e.key==='ArrowRight'){
      const idx = chapters.findIndex(c=>c.number===current);
      if(idx<chapters.length-1) loadChapter(chapters[idx+1].number);
    }
    if(e.key==='ArrowLeft'){
      const idx = chapters.findIndex(c=>c.number===current);
      if(idx>0) loadChapter(chapters[idx-1].number);
    }
  });

  applyControls();
  fetchSites();
});
