const $=s=>document.querySelector(s)
document.addEventListener('DOMContentLoaded',()=>{
  const siteSelect=$('#siteSelect'),tocSelect=$('#tocSelect')
  const titleEl=$('#chapterTitle'),contentEl=$('#chapterContent')
  const fontSize=$('#fontSize'),lineHeight=$('#lineHeight'),readWidth=$('#readWidth')
  const softFont=$('#softFont'),themeToggle=$('#themeToggle')
  const markReadBtn=$('#markReadBtn'),closeBtn=$('#closeBtn')

  let chapters=[],current=1,currentSite=null

  function apply(){
    contentEl.style.fontSize=fontSize.value+'px'
    contentEl.style.lineHeight=lineHeight.value
    contentEl.style.maxWidth=readWidth.value+'px'
    document.body.classList.toggle('soft-font',softFont.checked)
    document.body.classList.toggle('dark',themeToggle.checked)
  }
  fontSize.oninput=lineHeight.oninput=readWidth.oninput=softFont.onchange=themeToggle.onchange=apply
  themeToggle.checked=true
  apply()

  async function fetchProgress(){
    try{return await(await fetch('/api/progress')).json()}catch{return null}
  }

  function saveProgress(site,num){
    fetch('/api/progress',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({site,chapter:num})}).catch(()=>{})
  }

  async function fetchSites(){
    const data=await(await fetch('/api/sites')).json()
    siteSelect.innerHTML=''
    data.forEach(s=>{const opt=document.createElement('option');opt.value=s.id;opt.textContent=s.id;siteSelect.appendChild(opt)})
    if(!data.length)return
    const progress=await fetchProgress()
    const resumeSite=progress?.site&&data.some(s=>s.id===progress.site)?progress.site:null
    currentSite=resumeSite||data[0].id
    siteSelect.value=currentSite
    await loadChapters(currentSite,progress?.chapter)
  }

  async function loadChapters(site,resumeChapter){
    currentSite=site
    chapters=await(await fetch(`/api/chapters?site=${encodeURIComponent(site)}`)).json()
    tocSelect.innerHTML=''
    chapters.forEach(ch=>{const opt=document.createElement('option');opt.value=ch.number;opt.textContent=ch.number+': '+ch.title;tocSelect.appendChild(opt)})
    if(!chapters.length)return
    const hasResume=resumeChapter!=null&&chapters.some(c=>c.number===resumeChapter)
    current=hasResume?resumeChapter:chapters[0].number
    loadChapter(current)
  }

  async function loadChapter(num){
    const ch=await(await fetch(`/api/chapter?site=${encodeURIComponent(currentSite)}&num=${num}`)).json()
    titleEl.textContent=ch.title?`${ch.number} — ${ch.title}`:`${ch.number}`
    contentEl.textContent=ch.text||''
    tocSelect.value=String(num)
    current=num
  }

  markReadBtn.onclick=()=>{
    saveProgress(currentSite,current)
    const t=markReadBtn.textContent
    markReadBtn.textContent='Saved ✓'
    setTimeout(()=>markReadBtn.textContent=t,1500)
  }

  closeBtn.onclick=()=>{
    if(window.pywebview && window.pywebview.api && typeof window.pywebview.api.close==='function'){
      window.pywebview.api.close()
    }else{
      window.close()
    }
  }

  tocSelect.onchange=e=>{current=parseInt(e.target.value);loadChapter(current)}
  siteSelect.onchange=e=>{loadChapters(e.target.value)}

  document.onkeydown=e=>{
    if(e.key==='ArrowRight'){
      const idx=chapters.findIndex(c=>c.number===current)
      if(idx<chapters.length-1)loadChapter(chapters[idx+1].number)
    }
    if(e.key==='ArrowLeft'){
      const idx=chapters.findIndex(c=>c.number===current)
      if(idx>0)loadChapter(chapters[idx-1].number)
    }
  }

  fetchSites()
})