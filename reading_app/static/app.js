const $ = s => document.querySelector(s)

document.addEventListener('DOMContentLoaded', () => {
  const siteSelect = $('#siteSelect'), tocSelect = $('#tocSelect')
  const titleEl = $('#chapterTitle'), contentEl = $('#chapterContent')
  const subEl = $('#chapterSub')
  const fontSize = $('#fontSize'), lineHeight = $('#lineHeight'), readWidth = $('#readWidth')
  const softFont = $('#softFont'), themeToggle = $('#themeToggle')
  const markReadBtn = $('#markReadBtn'), closeBtn = $('#closeBtn')
  const minimizeBtn = $('#minimizeBtn'), maximizeBtn = $('#maximizeBtn')
  const prevBtn = $('#prevBtn'), nextBtn = $('#nextBtn')
  const prevBtnBottom = $('#prevBtnBottom'), nextBtnBottom = $('#nextBtnBottom')
  const readerContainer = $('#readerContainer'), paperEl = $('.reader-paper')
  const progressBar = $('#progressBar'), statusPercent = $('#statusPercent')
  const statusChapter = $('#statusChapter')
  const loadingSpinner = $('#loadingSpinner')

  let chapters = [], current = 1, currentSite = null

  // Apply styling settings
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

  // Window Maximize State & Drag Blocking
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

  // Prevent pywebview window dragging when maximized or when interacting with toolbar/controls
  window.addEventListener('mousedown', (e) => {
    const isInteractive = e.target.closest('input, select, button, label, #progressTrack, #progressBar, .toolbar-bar, .toolbar-controls, .selectors, .window-controls, .no-drag')
    if (isInteractive) {
      e.stopPropagation()
    } else if (window.isMaximized) {
      const isWindowBar = e.target.closest('.window-bar')
      if (isWindowBar) {
        e.stopPropagation()
      }
    }
  }, true)

  // Track Reading Scroll Progress & Interactive Seeking
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
      readerContainer.scrollTop = pct * totalHeight
    }
  }

  if (progressTrack) {
    progressTrack.addEventListener('mousedown', (e) => {
      e.stopPropagation()
      isDraggingProgress = true
      seekProgress(e)
    })

    window.addEventListener('mousemove', (e) => {
      if (isDraggingProgress) {
        seekProgress(e)
      }
    })

    window.addEventListener('mouseup', () => {
      isDraggingProgress = false
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

  // API calls
  async function fetchProgress() {
    try { return await (await fetch('/api/progress')).json() } catch { return null }
  }

  function saveProgress(site, num) {
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
        titleEl.textContent = 'No Novels Found'
        contentEl.textContent = 'No chapter data found in scraper/data directory. Please check the data path.'
        loadingSpinner.style.display = 'none'
        return
      }

      data.forEach(s => {
        const opt = document.createElement('option')
        opt.value = s.id
        opt.textContent = s.name || s.id
        siteSelect.appendChild(opt)
      })

      const progress = await fetchProgress()
      const resumeSite = progress?.site && data.some(s => s.id === progress.site) ? progress.site : null
      currentSite = resumeSite || data[0].id
      siteSelect.value = currentSite
      await loadChapters(currentSite, progress?.chapter)
    } catch (e) {
      console.error(e)
      titleEl.textContent = 'Error Loading Data'
      contentEl.textContent = 'Failed to load novel index from backend.'
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
        opt.textContent = `${ch.number}: ${ch.title}`
        tocSelect.appendChild(opt)
      })

      if (!chapters.length) {
        titleEl.textContent = 'No Chapters'
        contentEl.textContent = 'This novel does not have any loaded chapters yet.'
        loadingSpinner.style.display = 'none'
        return
      }

      const hasResume = resumeChapter != null && chapters.some(c => c.number === resumeChapter)
      current = hasResume ? resumeChapter : chapters[0].number
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
      titleEl.textContent = ch.title ? `${ch.number} — ${ch.title}` : `Chapter ${ch.number}`
      subEl.textContent = `${currentSite.replace('-', ' ').toUpperCase()} • CHAPTER ${ch.number}`
      contentEl.textContent = ch.text || ''
      tocSelect.value = String(num)
      current = num
      statusChapter.textContent = `Ch. ${num} of ${chapters.length}`
      saveProgress(currentSite, current)
      updateNavButtons()
    } catch (e) {
      console.error(e)
      titleEl.textContent = `Error Loading Chapter ${num}`
      contentEl.textContent = 'Failed to fetch chapter text.'
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

  // Navigation handlers
  prevBtn.onclick = prevBtnBottom.onclick = () => navigate('prev')
  nextBtn.onclick = nextBtnBottom.onclick = () => navigate('next')

  markReadBtn.onclick = () => {
    saveProgress(currentSite, current)
    const origText = markReadBtn.textContent
    markReadBtn.textContent = 'Saved ✓'
    setTimeout(() => markReadBtn.textContent = origText, 1500)
  }

  // Window control buttons & titlebar double-click
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
  siteSelect.onchange = e => { loadChapters(e.target.value) }

  // Keyboard navigation
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