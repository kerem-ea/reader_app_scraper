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
  const markReadBtn = $('#markReadBtn');

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

  async function fetchProgress(){
    try{
      const res = await fetch('/api/progress');
      if(!res.ok) return null;
      return await res.json();
    }catch(e){
      return null;
    }
  }

  function saveProgress(site, num){
    fetch('/api/progress', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({site, chapter: num})
    }).catch(()=>{});
  }

  async function fetchSites(){
    const res = await fetch('/api/sites');
    const data = await res.json();
    siteSelect.innerHTML = '';
    data.forEach(s=>{const opt = document.createElement('option');opt.value=s.id;opt.textContent=s.id;siteSelect.appendChild(opt)});
    if(!data.length) return;

    // resume to whatever site/chapter was last read, if it still exists
    const progress = await fetchProgress();
    const resumeSite = progress && progress.site && data.some(s=>s.id===progress.site) ? progress.site : null;

    if(resumeSite){
      currentSite = resumeSite;
      siteSelect.value = currentSite;
      await loadChapters(currentSite, progress.chapter);
    } else {
      currentSite = data[0].id;
      await loadChapters(currentSite);
    }
  }

  async function loadChapters(site, resumeChapter){
    currentSite = site;
    const res = await fetch(`/api/chapters?site=${encodeURIComponent(site)}`);
    chapters = await res.json();
    tocSelect.innerHTML = '';
    chapters.forEach(ch=>{const opt=document.createElement('option');opt.value=ch.number;opt.textContent=ch.number+': '+ch.title;tocSelect.appendChild(opt)});
    if(!chapters.length) return;

    const hasResume = resumeChapter != null && chapters.some(c=>c.number===resumeChapter);
    current = hasResume ? resumeChapter : chapters[0].number;
    loadChapter(current);
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

  function markAsRead(){
    saveProgress(currentSite, current);
    const originalText = markReadBtn.textContent;
    markReadBtn.textContent = 'Saved ✓';
    setTimeout(()=>{markReadBtn.textContent = originalText}, 1500);
  }

  markReadBtn.addEventListener('click', markAsRead);

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