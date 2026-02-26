/* ============================================================
   HOME.JS — Dashboard: API-based state, tasks, mood, charts
   ============================================================ */

// ── HELPERS ──────────────────────────────────────────────────
function todayStr() {
    return new Date().toISOString().split('T')[0];
}

function getLast7Days() {
    const days = [];
    for (let i = 6; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        days.push(d.toISOString().split('T')[0]);
    }
    return days;
}

function getCookie(name) {
    const val = document.cookie.split(';').map(c => c.trim());
    for (const c of val) {
        if (c.startsWith(name + '=')) return decodeURIComponent(c.slice(name.length + 1));
    }
    return null;
}

const CSRF = () => getCookie('csrftoken');

async function apiFetch(url, method = 'GET', body = null) {
    const opts = {
        method,
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF() },
    };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    return res.json();
}

// ── STATE (in-memory cache) ───────────────────────────────────
let state = {
    tasks:        [],
    moodLogs:     [],
    selectedMood: null,
};

async function loadAllData() {
    const [tasksRes, moodRes] = await Promise.all([
        apiFetch('/api/tasks/'),
        apiFetch('/api/mood/'),
    ]);
    state.tasks    = tasksRes.tasks   || [];
    state.moodLogs = moodRes.logs     || [];
}

// ── NAV ──────────────────────────────────────────────────────
function showPage(id) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('page-' + id).classList.add('active');

    const idx = { dashboard: 0, planner: 1, mood: 2, analytics: 3 }[id];
    document.querySelectorAll('.nav-btn')[idx].classList.add('active');

    if (id === 'dashboard') renderDashboard();
    if (id === 'planner')   renderPlanner();
    if (id === 'mood')      renderMood();
    if (id === 'analytics') renderAnalytics();
}

// ── MODAL ────────────────────────────────────────────────────
function openModal(id)  { document.getElementById('modal-' + id).classList.add('open'); }
function closeModal(id) { document.getElementById('modal-' + id).classList.remove('open'); }

document.querySelectorAll('.modal-overlay').forEach(m => {
    m.addEventListener('click', e => { if (e.target === m) m.classList.remove('open'); });
});

// ── TASKS ────────────────────────────────────────────────────
async function addTask() {
    const name = document.getElementById('taskName').value.trim();
    if (!name) { showToast('⚠️', 'Please enter a task name'); return; }

    const task = {
        name,
        date:       document.getElementById('plannerDatePicker').value || todayStr(),
        time:       document.getElementById('taskTime').value || '09:00',
        duration:   parseFloat(document.getElementById('taskDuration').value) || 1,
        priority:   document.getElementById('taskPriority').value,
        difficulty: parseInt(document.getElementById('taskDifficulty').value),
        done:       false,
    };

    const res = await apiFetch('/api/tasks/', 'POST', task);
    task.id = res.id;
    state.tasks.push(task);

    closeModal('task');
    ['taskName', 'taskTime', 'taskDuration'].forEach(id => document.getElementById(id).value = '');
    showToast('✅', 'Task added!');
    renderDashboard();
    renderPlanner();
}

async function quickAddTask() {
    const name = document.getElementById('quickName').value.trim();
    if (!name) { showToast('⚠️', 'Enter a task name'); return; }

    const task = {
        name,
        date:       document.getElementById('plannerDatePicker').value || todayStr(),
        time:       document.getElementById('quickTime').value || '09:00',
        duration:   parseFloat(document.getElementById('quickDuration').value) || 1,
        priority:   document.getElementById('quickPriority').value,
        difficulty: parseInt(document.getElementById('quickDifficulty').value),
        done:       false,
    };

    const res = await apiFetch('/api/tasks/', 'POST', task);
    task.id = res.id;
    state.tasks.push(task);

    document.getElementById('quickName').value     = '';
    document.getElementById('quickTime').value     = '';
    document.getElementById('quickDuration').value = '';
    showToast('✅', 'Task added!');
    renderPlanner();
    renderDashboard();
}

async function toggleTask(id) {
    const t = state.tasks.find(t => t.id === id);
    if (!t) return;
    t.done = !t.done;
    await apiFetch(`/api/tasks/${id}/`, 'PATCH', { done: t.done });
    renderDashboard();
    renderPlanner();
    await updateBurnoutRing(todayStr());
}

async function deleteTask(id) {
    await apiFetch(`/api/tasks/${id}/`, 'DELETE');
    state.tasks = state.tasks.filter(t => t.id !== id);
    renderDashboard();
    renderPlanner();
    showToast('🗑', 'Task removed');
}

// ── BURNOUT ───────────────────────────────────────────────────
async function fetchBurnout(date) {
    const res = await apiFetch(`/api/burnout/?date=${date}`);
    return res;
}

async function updateBurnoutRing(date) {
    const res = await fetchBurnout(date);
    const bi  = res.index || 0;

    const circumference = 264;
    const offset = circumference - (bi / 100) * circumference;
    const ring  = document.getElementById('burnoutRing');
    const num   = document.getElementById('burnoutNum');
    const badge = document.getElementById('burnoutStatusBadge');
    if (ring)  ring.style.strokeDashoffset = offset;
    if (num)   num.textContent             = bi;
    if (badge) badge.textContent           = res.level || '—';

    return res;
}

// ── DASHBOARD ────────────────────────────────────────────────
async function renderDashboard() {
    const today      = todayStr();
    const todayTasks = state.tasks.filter(t => t.date === today);
    const done       = todayTasks.filter(t => t.done).length;
    const total      = todayTasks.length;

    document.getElementById('progressText').textContent = `${done}/${total}`;
    document.getElementById('progressBar').style.width  = total > 0
        ? `${Math.round(done / total * 100)}%` : '0%';

    // Burnout ring
    const burnout = await updateBurnoutRing(today);

    // Smart alert
    if (burnout.recommendations && burnout.recommendations.length > 0) {
        document.getElementById('smartAlert').textContent = burnout.recommendations[0];
    }

    // Task list
    const el = document.getElementById('dashTaskList');
    if (todayTasks.length === 0) {
        el.innerHTML = '<div class="empty-state"><div class="empty-icon">📝</div>No tasks yet. Add your first task!</div>';
    } else {
        el.innerHTML = todayTasks
            .sort((a, b) => a.time.localeCompare(b.time))
            .map(t => taskItemHTML(t, false))
            .join('');
    }

    // Status dots
    const todayLog = getTodayLog();
    if (todayLog) {
        renderDots('moodDots',   todayLog.mood);
        renderDots('energyDots', Math.round(todayLog.mental / 20));
    }

    // Week summary
    const weekTasks = getWeekTasks();
    const weekDone  = weekTasks.filter(t => t.done).length;
    document.getElementById('weekTasks').textContent = `${weekDone}/${weekTasks.length}`;

    const energies = state.moodLogs.slice(-7).map(l => l.mental);
    document.getElementById('weekEnergy').textContent = energies.length > 0
        ? `${Math.round(energies.reduce((a, b) => a + b, 0) / energies.length)}%` : '—';

    const reflDays = state.moodLogs.slice(-7).filter(l => l.reflection && l.reflection.trim()).length;
    document.getElementById('weekReflections').textContent = `${reflDays}/7`;
}

function taskItemHTML(t, showTime = true) {
    return `<div class="task-item">
        <div class="task-check ${t.done ? 'done' : ''}" onclick="toggleTask(${t.id})"></div>
        <div class="task-info">
            <div class="task-name ${t.done ? 'done' : ''}">${t.name}</div>
            <div class="task-tags">
                <span class="tag ${t.priority}">${t.priority}</span>
                <span class="tag diff">Difficulty: ${t.difficulty}/5</span>
                ${showTime ? `<span class="tag diff">${t.time} · ${t.duration}h</span>` : ''}
            </div>
        </div>
        <button class="task-del" onclick="deleteTask(${t.id})">×</button>
    </div>`;
}

function renderDots(id, val) {
    const el = document.getElementById(id);
    el.innerHTML = [1, 2, 3, 4, 5]
        .map(i => `<div class="dot ${i <= val ? 'filled' : ''}"></div>`)
        .join('');
}

// ── PLANNER ──────────────────────────────────────────────────
async function renderPlanner() {
    const dateVal = document.getElementById('plannerDatePicker').value || todayStr();
    document.getElementById('plannerDatePicker').value = dateVal;

    const d = new Date(dateVal + 'T00:00:00');
    document.getElementById('plannerDateDisplay').textContent =
        d.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

    const dayTasks = state.tasks
        .filter(t => t.date === dateVal)
        .sort((a, b) => a.time.localeCompare(b.time));

    const sl = document.getElementById('scheduleList');
    if (dayTasks.length === 0) {
        sl.innerHTML = '<div class="empty-state"><div class="empty-icon">🗓</div>No tasks for this day. Add some!</div>';
    } else {
        sl.innerHTML = dayTasks.map(t => `
            <div class="schedule-item ${t.priority}">
                <div class="schedule-time">${t.time}<br><span style="font-size:10px;">${t.duration}h</span></div>
                <div class="schedule-info">
                    <div class="schedule-name" style="${t.done ? 'text-decoration:line-through;color:var(--text3);' : ''}">${t.name}</div>
                    <div class="task-tags" style="margin-top:6px;">
                        <span class="tag ${t.priority}">${t.priority} priority</span>
                        <span class="tag diff">Difficulty: ${t.difficulty}/5</span>
                    </div>
                </div>
                <button class="task-check ${t.done ? 'done' : ''}" style="margin-top:0;" onclick="toggleTask(${t.id})"></button>
                <button class="schedule-del" onclick="deleteTask(${t.id})">×</button>
            </div>`).join('');
    }

    const doneTasks  = dayTasks.filter(t => t.done).length;
    const totalHours = dayTasks.reduce((a, t) => a + t.duration, 0);
    const avgDiff    = dayTasks.length > 0
        ? (dayTasks.reduce((a, t) => a + t.difficulty, 0) / dayTasks.length).toFixed(1) : 0;

    document.getElementById('statCompletion').textContent = `${doneTasks}/${dayTasks.length}`;
    document.getElementById('statTime').textContent       = `${totalHours.toFixed(1)}h`;
    document.getElementById('statAvgDiff').textContent    = avgDiff;
    document.getElementById('statTasks').textContent      = dayTasks.length;
}

// ── MOOD ─────────────────────────────────────────────────────
function selectMood(val) {
    state.selectedMood = val;
    document.querySelectorAll('.mood-emoji').forEach((el, i) => {
        el.classList.toggle('selected', i === val - 1);
    });
}

function updateSlider(el, labelId) {
    el.style.setProperty('--val', el.value + '%');
    document.getElementById(labelId).textContent = el.value + '%';
}

function updatePhys(el, labelId, unit, barId, max) {
    const val = parseInt(el.value);
    const pct = Math.round(val / max * 100);
    el.style.setProperty('--val', pct + '%');
    document.getElementById(labelId).textContent = val + unit;
    document.getElementById(barId).style.width   = pct + '%';
}

async function saveMoodData() {
    if (!state.selectedMood) { showToast('⚠️', 'Please select your mood first'); return; }

    const log = {
        date:       todayStr(),
        mood:       state.selectedMood,
        mental:     parseInt(document.getElementById('mentalSlider').value),
        physical:   parseInt(document.getElementById('physSlider').value),
        sleep:      parseInt(document.getElementById('sleepSlider').value),
        hydration:  parseInt(document.getElementById('hydSlider').value),
        screenTime: parseInt(document.getElementById('screenSlider').value),
        movement:   parseInt(document.getElementById('movSlider').value),
        reflection: document.getElementById('reflectionText').value.trim(),
    };

    await apiFetch('/api/mood/', 'POST', log);

    // Оновлюємо локальний кеш
    state.moodLogs = state.moodLogs.filter(l => l.date !== todayStr());
    state.moodLogs.push(log);

    showToast('✅', 'Mood & energy saved!');
    renderMood();
    renderDashboard();
    renderAnalytics();
}

function renderMood() {
    const todayLog = getTodayLog();
    if (todayLog) {
        selectMood(todayLog.mood);

        const set = (sliderId, labelId, val, suffix, barId, max) => {
            document.getElementById(sliderId).value = val;
            document.getElementById(labelId).textContent = val + suffix;
            document.getElementById(sliderId).style.setProperty('--val', Math.round(val / max * 100) + '%');
            if (barId) document.getElementById(barId).style.width = Math.round(val / max * 100) + '%';
        };

        document.getElementById('mentalSlider').value = todayLog.mental;
        document.getElementById('mentalVal').textContent = todayLog.mental + '%';
        document.getElementById('mentalSlider').style.setProperty('--val', todayLog.mental + '%');

        document.getElementById('physSlider').value = todayLog.physical;
        document.getElementById('physVal').textContent = todayLog.physical + '%';
        document.getElementById('physSlider').style.setProperty('--val', todayLog.physical + '%');

        set('sleepSlider',  'sleepVal',  todayLog.sleep,      'h',       'sleepBar',  12);
        set('hydSlider',    'hydVal',    todayLog.hydration,  ' glasses','hydBar',    12);
        set('screenSlider', 'screenVal', todayLog.screenTime, 'h',       'screenBar', 16);
        set('movSlider',    'movVal',    todayLog.movement,   ' min',    'movBar',    120);

        if (todayLog.reflection) {
            document.getElementById('reflectionText').value = todayLog.reflection;
        }
    }

    const logs7 = state.moodLogs.slice(-7);
    if (logs7.length > 0) {
        const avg = arr => arr.reduce((a, b) => a + b, 0) / arr.length;
        document.getElementById('wAvgMood').textContent   = avg(logs7.map(l => l.mood)).toFixed(1);
        document.getElementById('wAvgEnergy').textContent = Math.round(avg(logs7.map(l => l.mental))) + '%';
        document.getElementById('wAvgSleep').textContent  = avg(logs7.map(l => l.sleep)).toFixed(1) + 'h';
        document.getElementById('wAvgMove').textContent   = Math.round(avg(logs7.map(l => l.movement))) + 'm';
    }

    renderAIInsights(todayLog);
}

function renderAIInsights(log) {
    if (!log) return;
    const insights = [];

    if (log.sleep >= 7)        insights.push('✅ Great sleep duration! Keep it up.');
    else if (log.sleep < 6)    insights.push('😴 Sleep is below optimal. Try to get 7–8 hours.');
    if (log.screenTime > 8)    insights.push('⚠️ Screen time is high. Consider a digital detox.');
    else if (log.screenTime <= 4) insights.push('✅ Good screen time balance!');
    if (log.hydration < 6)     insights.push(`💧 Try to increase water intake by ${8 - log.hydration} more glasses.`);
    else                       insights.push('💧 Great hydration today!');
    if (log.movement < 20)     insights.push('🏃 Try to move more — even a 20-min walk helps.');
    else                       insights.push(`🏃 Good movement today (${log.movement} min)!`);

    document.getElementById('aiInsights').innerHTML = `
        <div class="insight-title">🤖 AI Insights</div>
        <div style="font-size:13px;color:var(--text3);margin-bottom:8px;">Based on your inputs:</div>
        ${insights.map(i => `<div class="insight-item">${i}</div>`).join('')}
    `;
}

// ── ANALYTICS ────────────────────────────────────────────────
async function renderAnalytics() {
    const today   = todayStr();
    const burnout = await fetchBurnout(today);
    const bi      = burnout.index || 0;
    const level   = burnout.level || 'Low';

    document.getElementById('aCurrentIdx').textContent  = bi;
    document.getElementById('gaugeNum').textContent     = bi;
    document.getElementById('gaugeStatus').textContent  = level;
    document.getElementById('gaugeCircle').style.strokeDashoffset = 314 - (bi / 100) * 314;

    const descriptions = {
        Low:      'Your burnout level is low. Keep maintaining healthy habits!',
        Moderate: 'Your burnout level is moderate. Balance your workload and rest regularly.',
        High:     'Burnout level is high. Prioritize rest, reduce workload, and seek support.',
    };
    document.getElementById('burnoutDescription').textContent = descriptions[level] || '';

    const logs7 = state.moodLogs.slice(-7);
    if (logs7.length > 0) {
        const avg = arr => arr.reduce((a, b) => a + b, 0) / arr.length;
        document.getElementById('aAvgMood').textContent   = avg(logs7.map(l => l.mood)).toFixed(1);
        document.getElementById('aEnergyLvl').textContent = Math.round(avg(logs7.map(l => l.mental))) + '%';
    } else {
        document.getElementById('aAvgMood').textContent   = '—';
        document.getElementById('aEnergyLvl').textContent = '—';
    }

    const weekTasks = getWeekTasks();
    const totalH    = weekTasks.reduce((a, t) => a + t.duration, 0);
    document.getElementById('aWorkload').textContent  = totalH > 0 ? `${totalH.toFixed(0)}h` : '—';
    document.getElementById('aWorkloadH').textContent =
        totalH >= 40 ? 'Heavy this week' :
        totalH >= 20 ? 'Moderate this week' : 'Light this week';

    await renderCharts();
}

// ── CHARTS ───────────────────────────────────────────────────
let chartInstances = {};

async function renderCharts() {
    Object.values(chartInstances).forEach(c => c && typeof c.destroy === 'function' && c.destroy());

    const days      = getLast7Days();
    const dayLabels = days.map(d => new Date(d + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'short' }));

    // Burnout per day
    const burnoutData = await Promise.all(days.map(async d => {
        const res = await fetchBurnout(d);
        return res.index || 0;
    }));

    const workloadData = days.map(d =>
        state.tasks.filter(t => t.date === d).reduce((a, t) => a + t.duration, 0)
    );
    const moodData   = days.map(d => { const l = state.moodLogs.find(l => l.date === d); return l ? l.mood * 20 : null; });
    const energyData = days.map(d => { const l = state.moodLogs.find(l => l.date === d); return l ? l.mental   : null; });

    chartInstances.burnout  = drawBarChart('burnoutChart',  dayLabels, burnoutData,  '#e8327c', 100);
    chartInstances.workload = drawBarChart('workloadChart', dayLabels, workloadData, '#c026d3', 12);
    chartInstances.mood     = drawLineChart('moodChart',    dayLabels, moodData, energyData);
}

function drawBarChart(canvasId, labels, data, color, max) {
    const canvas = document.getElementById(canvasId);
    const ctx    = canvas.getContext('2d');
    const W      = canvas.offsetWidth || 300;
    const H      = 140;
    canvas.width = W; canvas.height = H;
    ctx.clearRect(0, 0, W, H);

    const pad    = { left: 30, right: 10, top: 10, bottom: 24 };
    const chartW = W - pad.left - pad.right;
    const chartH = H - pad.top  - pad.bottom;
    const barW   = chartW / labels.length * 0.6;
    const gap    = chartW / labels.length;

    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth   = 1;
    for (let i = 0; i <= 4; i++) {
        const y = pad.top + chartH - (i / 4) * chartH;
        ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(W - pad.right, y); ctx.stroke();
        ctx.fillStyle = 'rgba(255,255,255,0.3)';
        ctx.font      = '10px DM Sans';
        ctx.textAlign = 'right';
        ctx.fillText(Math.round(max * i / 4), pad.left - 4, y + 4);
    }

    const grad = ctx.createLinearGradient(0, pad.top, 0, pad.top + chartH);
    grad.addColorStop(0, color);
    grad.addColorStop(1, color + '33');

    data.forEach((val, i) => {
        const x    = pad.left + i * gap + gap / 2 - barW / 2;
        const barH = chartH * (val || 0) / max;
        const y    = pad.top + chartH - barH;
        ctx.fillStyle = grad;
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(x, y, barW, barH, [4, 4, 0, 0]);
        else ctx.rect(x, y, barW, barH);
        ctx.fill();

        ctx.fillStyle = 'rgba(255,255,255,0.4)';
        ctx.textAlign = 'center';
        ctx.font      = '10px DM Sans';
        ctx.fillText(labels[i], pad.left + i * gap + gap / 2, H - 4);
    });

    return { destroy: () => {} };
}

function drawLineChart(canvasId, labels, data1, data2) {
    const canvas = document.getElementById(canvasId);
    const ctx    = canvas.getContext('2d');
    const W      = canvas.offsetWidth || 600;
    const H      = 120;
    canvas.width = W; canvas.height = H;
    ctx.clearRect(0, 0, W, H);

    const pad    = { left: 30, right: 10, top: 10, bottom: 24 };
    const chartW = W - pad.left - pad.right;
    const chartH = H - pad.top  - pad.bottom;
    const n      = labels.length;
    const step   = chartW / (n - 1 || 1);

    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth   = 1;
    for (let i = 0; i <= 4; i++) {
        const y = pad.top + chartH * (1 - i / 4);
        ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(W - pad.right, y); ctx.stroke();
    }

    function drawLine(data, color) {
        const pts = data.map((v, i) => [pad.left + i * step, pad.top + chartH * (1 - (v || 0) / 100)]);
        if (pts.filter((_, i) => data[i] !== null).length < 2) return;

        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth   = 2.5;
        ctx.lineJoin    = 'round';
        let started = false;
        pts.forEach(([x, y], i) => {
            if (data[i] === null) { started = false; return; }
            if (!started) { ctx.moveTo(x, y); started = true; } else ctx.lineTo(x, y);
        });
        ctx.stroke();

        pts.forEach(([x, y], i) => {
            if (data[i] === null) return;
            ctx.beginPath(); ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fillStyle = color; ctx.fill();
            ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(x, y, 2, 0, Math.PI * 2); ctx.fill();
        });
    }

    drawLine(data1, '#e8327c');
    drawLine(data2, '#f59e0b');

    ctx.fillStyle = 'rgba(255,255,255,0.4)';
    ctx.font      = '10px DM Sans';
    ctx.textAlign = 'center';
    labels.forEach((l, i) => ctx.fillText(l, pad.left + i * step, H - 4));

    return { destroy: () => {} };
}

// ── HELPERS ──────────────────────────────────────────────────
function getWeekTasks() {
    const days = getLast7Days();
    return state.tasks.filter(t => days.includes(t.date));
}

function getTodayLog() {
    return state.moodLogs.find(l => l.date === todayStr()) || null;
}

// ── TOAST ────────────────────────────────────────────────────
function showToast(icon, msg) {
    const t = document.getElementById('toast');
    document.getElementById('toastIcon').textContent = icon;
    document.getElementById('toastMsg').textContent  = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2500);
}

// ── USER ─────────────────────────────────────────────────────
function loadUser() {
    const username = window.__USERNAME__ || '?';
    const initial  = username[0].toUpperCase();
    document.getElementById('avatarBtn').textContent      = initial;
    document.getElementById('headerGreeting').textContent = `Hi, ${username}!`;
}

function logout() {
    window.location.href = window.__LOGOUT_URL__;
}

// ── INIT ─────────────────────────────────────────────────────
async function init() {
    loadUser();
    document.getElementById('plannerDatePicker').value = todayStr();
    await loadAllData();
    await renderDashboard();

    window.addEventListener('resize', () => {
        if (document.getElementById('page-analytics').classList.contains('active')) {
            renderCharts();
        }
    });
}

init();
