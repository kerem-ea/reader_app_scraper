const $ = s => document.querySelector(s)

document.addEventListener('DOMContentLoaded', () => {
  const siteSelect = $('#siteSelect'), tocSelect = $('#tocSelect')
  const titleEl = $('#chapterTitle'), contentEl = $('#chapterContent')
  const subEl = $('#chapterSub')
  const fontSize = $('#fontSize'), lineHeight = $('#lineHeight'), readWidth = $('#readWidth')
  const softFont = $('#softFont'), themeToggle = $('#themeToggle')
  const markReadBtn = $('#markReadBtn'), closeBtn = $('#closeBtn')
  const minimizeBtn = $('#minimizeBtn'), maximizeBtn = $('#maximizeBtn')
  const taskbarBtn = $('#taskbarBtn'), awakeToggle = $('#awakeToggle')
  const prevBtn = $('#prevBtn'), nextBtn = $('#nextBtn')
  const prevBtnBottom = $('#prevBtnBottom'), nextBtnBottom = $('#nextBtnBottom')
  const readerContainer = $('#readerContainer'), paperEl = $('.reader-paper')
  const progressBar = $('#progressBar'), statusPercent = $('#statusPercent')
  const statusChapter = $('#statusChapter')
  const loadingSpinner = $('#loadingSpinner')

  let chapters = [], current = 1, currentSite = null
  let cachedProgress = null

  function applySettings() {
    contentEl.style.fontSize = fontSize.value + 'px'
    contentEl.style.lineHeight = lineHeight.value
    paperEl.style.maxWidth = readWidth.value + 'px'
    document.body.classList.toggle('soft-font', softFont.checked)
    document.body.classList.toggle('dark', themeToggle.checked)
  }

  fontSize.oninput = lineHeight.oninput = readWidth.oninput = softFont.onchange = themeToggle.onchange = applySettings
  themeToggle.checked = true
  applySettings()

  let hasTaskbar = localStorage.getItem('weaver_has_taskbar') !== 'false'

  function updateTaskbarUI(state) {
    hasTaskbar = !!state
    localStorage.setItem('weaver_has_taskbar', hasTaskbar ? 'true' : 'false')
    if (taskbarBtn) {
      taskbarBtn.textContent = hasTaskbar ? 'Taskbar: On' : 'Taskbar: Off'
      taskbarBtn.title = hasTaskbar
        ? 'Taskbar: On (reserves height for taskbar). Click to switch to Full Monitor Height.'
        : 'Taskbar: Off (fills full monitor height). Click to reserve Taskbar space.'
    }
  }
  updateTaskbarUI(hasTaskbar)

  if (taskbarBtn) {
    taskbarBtn.onclick = () => {
      hasTaskbar = !hasTaskbar
      updateTaskbarUI(hasTaskbar)
      if (window.pywebview?.api?.set_taskbar_mode) {
        window.pywebview.api.set_taskbar_mode(hasTaskbar)
      }
    }
  }

  if (awakeToggle) {
    const savedAwake = localStorage.getItem('weaver_keep_awake') !== 'false'
    awakeToggle.checked = savedAwake
    awakeToggle.onchange = () => {
      localStorage.setItem('weaver_keep_awake', awakeToggle.checked ? 'true' : 'false')
      if (window.pywebview?.api?.set_keep_awake) {
        window.pywebview.api.set_keep_awake(awakeToggle.checked)
      }
    }
  }

  let lastActivityPing = 0
  function pingUserActivity() {
    if (awakeToggle && !awakeToggle.checked) return
    const now = Date.now()
    if (now - lastActivityPing > 5000) {
      lastActivityPing = now
      if (window.pywebview?.api?.ping_activity) {
        window.pywebview.api.ping_activity()
      }
    }
  }

  ['mousemove', 'scroll', 'keydown', 'click', 'wheel', 'touchstart'].forEach(evt => {
    window.addEventListener(evt, pingUserActivity, { passive: true })
  })
  if (readerContainer) {
    readerContainer.addEventListener('scroll', pingUserActivity, { passive: true })
  }

  function syncPyWebviewApi() {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.set_taskbar_mode(hasTaskbar)
      if (awakeToggle) {
        window.pywebview.api.set_keep_awake(awakeToggle.checked)
      }
    } else {
      setTimeout(syncPyWebviewApi, 100)
    }
  }
  syncPyWebviewApi()

  window.isMaximized = true
  window.setWindowMaximizedState = (isMaximized) => {
    window.isMaximized = !!isMaximized
    const windowBar = $('.window-bar')
    if (windowBar) {
      if (window.isMaximized) {
        windowBar.classList.remove('pywebview-drag-region')
        windowBar.style.webkitAppRegion = 'no-drag'
      } else {
        windowBar.classList.add('pywebview-drag-region')
        windowBar.style.webkitAppRegion = 'drag'
      }
    }
  }

  function setupDragBlocker() {
    if (window.pywebview && window.pywebview._jsApiCallback) {
      const origCallback = window.pywebview._jsApiCallback
      window.pywebview._jsApiCallback = function(funcName, params, id) {
        if (funcName === 'pywebviewMoveWindow' && window.isMaximized) {
          return
        }
        return origCallback.apply(this, arguments)
      }
    } else {
      setTimeout(setupDragBlocker, 100)
    }
  }
  setupDragBlocker()

  window.addEventListener('mousedown', (e) => {
    const isProgress = e.target.closest('#progressTrack, #progressBar')
    if (isProgress) return

    const isInteractive = e.target.closest('input, select, button, label, .toolbar-bar, .toolbar-controls, .selectors, .window-controls, .no-drag')
    if (isInteractive) {
      e.stopPropagation()
    } else if (window.isMaximized) {
      const isWindowBar = e.target.closest('.window-bar')
      if (isWindowBar) {
        e.stopPropagation()
      }
    }
  }, true)

  const progressTrack = $('#progressTrack')
  let isDraggingProgress = false

  function seekProgress(e) {
    if (!progressTrack || !readerContainer) return
    const rect = progressTrack.getBoundingClientRect()
    const clickX = e.clientX - rect.left
    const width = rect.width
    if (width <= 0) return
    const pct = Math.max(0, Math.min(1, clickX / width))
    const totalHeight = readerContainer.scrollHeight - readerContainer.clientHeight
    if (totalHeight > 0) {
      readerContainer.scrollTop = Math.round(pct * totalHeight)
    }
  }

  if (progressTrack) {
    progressTrack.addEventListener('mousedown', (e) => {
      e.stopPropagation()
      e.preventDefault()
      isDraggingProgress = true
      readerContainer.style.scrollBehavior = 'auto'
      seekProgress(e)
    })

    window.addEventListener('mousemove', (e) => {
      if (isDraggingProgress) {
        e.preventDefault()
        seekProgress(e)
      }
    })

    window.addEventListener('mouseup', () => {
      if (isDraggingProgress) {
        isDraggingProgress = false
        readerContainer.style.scrollBehavior = ''
      }
    })
  }

  readerContainer.onscroll = () => {
    const totalHeight = readerContainer.scrollHeight - readerContainer.clientHeight
    if (totalHeight <= 0) {
      progressBar.style.width = '100%'
      statusPercent.textContent = '100%'
      return
    }
    const scrolled = Math.min(100, Math.max(0, (readerContainer.scrollTop / totalHeight) * 100))
    progressBar.style.width = scrolled.toFixed(1) + '%'
    statusPercent.textContent = Math.round(scrolled) + '%'
  }

  async function fetchProgress(site) {
    try {
      const url = site ? `/api/progress?site=${encodeURIComponent(site)}` : '/api/progress'
      return await (await fetch(url)).json()
    } catch {
      return null
    }
  }

  function saveProgress(site, num) {
    if (!site || num == null) return
    if (!cachedProgress) cachedProgress = { novels: {} }
    if (!cachedProgress.novels) cachedProgress.novels = {}
    cachedProgress.novels[site] = { chapter: num }
    cachedProgress.site = site
    fetch('/api/progress', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ site, chapter: num })
    }).catch(() => {})
  }

  async function fetchSites() {
    try {
      loadingSpinner.style.display = 'flex'
      const data = await (await fetch('/api/sites')).json()
      siteSelect.innerHTML = ''

      if (!data || !data.length) {
        titleEl.textContent = 'No EPUB Novels Found'
        contentEl.textContent = 'No .epub files found in scraper/data directory or root project folder. Run epub.py or place EPUB files in scraper/data.'
        loadingSpinner.style.display = 'none'
        return
      }

      data.forEach(s => {
        const opt = document.createElement('option')
        opt.value = s.id
        opt.textContent = s.name || s.id
        siteSelect.appendChild(opt)
      })

      cachedProgress = await fetchProgress()
      const resumeSite = cachedProgress?.site && data.some(s => s.id === cachedProgress.site) ? cachedProgress.site : null
      currentSite = resumeSite || data[0].id
      siteSelect.value = currentSite

      const savedChapter = cachedProgress?.novels?.[currentSite]?.chapter || (currentSite === cachedProgress?.site ? cachedProgress?.chapter : null)
      await loadChapters(currentSite, savedChapter)
    } catch (e) {
      console.error(e)
      titleEl.textContent = 'Error Loading Data'
      contentEl.textContent = 'Failed to load EPUB index from backend.'
    } finally {
      loadingSpinner.style.display = 'none'
    }
  }

  async function loadChapters(site, resumeChapter) {
    currentSite = site
    loadingSpinner.style.display = 'flex'
    try {
      chapters = await (await fetch(`/api/chapters?site=${encodeURIComponent(site)}`)).json()
      tocSelect.innerHTML = ''
      if (!Array.isArray(chapters)) chapters = []

      chapters.forEach(ch => {
        const opt = document.createElement('option')
        opt.value = ch.number
        opt.textContent = ch.title || `Chapter ${ch.number}`
        tocSelect.appendChild(opt)
      })

      if (!chapters.length) {
        titleEl.textContent = 'No Chapters Found'
        contentEl.textContent = 'This EPUB file does not contain readable chapter items.'
        loadingSpinner.style.display = 'none'
        return
      }

      let targetChapter = resumeChapter
      if (targetChapter == null) {
        if (cachedProgress?.novels?.[site]?.chapter != null) {
          targetChapter = cachedProgress.novels[site].chapter
        } else {
          const novelProg = await fetchProgress(site)
          if (novelProg?.chapter != null) {
            targetChapter = novelProg.chapter
          }
        }
      }

      const hasResume = targetChapter != null && chapters.some(c => c.number === targetChapter)
      current = hasResume ? targetChapter : chapters[0].number
      await loadChapter(current)
    } catch (e) {
      console.error(e)
      titleEl.textContent = 'Error Loading Chapters'
    } finally {
      loadingSpinner.style.display = 'none'
    }
  }

  async function loadChapter(num) {
    loadingSpinner.style.display = 'flex'
    readerContainer.scrollTop = 0
    try {
      const ch = await (await fetch(`/api/chapter?site=${encodeURIComponent(currentSite)}&num=${num}`)).json()
      titleEl.textContent = ch.title || `Chapter ${ch.number}`
      const cleanBookName = currentSite.split('/').pop().replace(/\.epub$/i, '').toUpperCase()
      subEl.textContent = `${cleanBookName} • CHAPTER ${ch.number}`
      contentEl.textContent = ch.text || ''
      tocSelect.value = String(num)
      current = num
      statusChapter.textContent = `Ch. ${num} of ${chapters.length}`
      saveProgress(currentSite, current)
      updateNavButtons()
    } catch (e) {
      console.error(e)
      titleEl.textContent = `Error Loading Chapter ${num}`
      contentEl.textContent = 'Failed to fetch chapter text from EPUB.'
    } finally {
      loadingSpinner.style.display = 'none'
      readerContainer.onscroll()
    }
  }

  function updateNavButtons() {
    const idx = chapters.findIndex(c => c.number === current)
    const hasPrev = idx > 0
    const hasNext = idx >= 0 && idx < chapters.length - 1

    prevBtn.disabled = prevBtnBottom.disabled = !hasPrev
    nextBtn.disabled = nextBtnBottom.disabled = !hasNext

    prevBtn.style.opacity = prevBtnBottom.style.opacity = hasPrev ? '1' : '0.4'
    nextBtn.style.opacity = nextBtnBottom.style.opacity = hasNext ? '1' : '0.4'
  }

  function navigate(direction) {
    const idx = chapters.findIndex(c => c.number === current)
    if (direction === 'next' && idx >= 0 && idx < chapters.length - 1) {
      loadChapter(chapters[idx + 1].number)
    } else if (direction === 'prev' && idx > 0) {
      loadChapter(chapters[idx - 1].number)
    }
  }

  prevBtn.onclick = prevBtnBottom.onclick = () => navigate('prev')
  nextBtn.onclick = nextBtnBottom.onclick = () => navigate('next')

  markReadBtn.onclick = () => {
    saveProgress(currentSite, current)
    const origText = markReadBtn.textContent
    markReadBtn.textContent = 'Saved ✓'
    setTimeout(() => markReadBtn.textContent = origText, 1500)
  }

  const windowBar = $('.window-bar')
  if (windowBar) {
    windowBar.ondblclick = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'BUTTON') return
      if (window.pywebview?.api?.maximize) {
        window.pywebview.api.maximize()
      }
    }
  }

  minimizeBtn.onclick = () => {
    if (window.pywebview?.api?.minimize) {
      window.pywebview.api.minimize()
    }
  }

  maximizeBtn.onclick = () => {
    if (window.pywebview?.api?.maximize) {
      window.pywebview.api.maximize()
    }
  }

  closeBtn.onclick = () => {
    if (window.pywebview?.api?.close) {
      window.pywebview.api.close()
    } else {
      window.close()
    }
  }

  tocSelect.onchange = e => { current = parseInt(e.target.value); loadChapter(current) }
  siteSelect.onchange = async e => {
    const selectedSite = e.target.value
    await loadChapters(selectedSite)
  }

  document.onkeydown = e => {
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return

    if (e.key === 'ArrowRight') {
      navigate('next')
    } else if (e.key === 'ArrowLeft') {
      navigate('prev')
    } else if (e.key === ' ') {
      e.preventDefault()
      readerContainer.scrollTop += readerContainer.clientHeight * 0.8
    }
  }

  fetchSites()
})