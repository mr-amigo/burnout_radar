/* ============================================================
   LOGIN.JS — Auth page: particles, welcome screen, tab switch
   ============================================================ */

// ── PARTICLES ────────────────────────────────────────────────
(function initParticles() {
    const container = document.getElementById('particles');
    if (!container) return;

    for (let i = 0; i < 12; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        const size = Math.random() * 60 + 20;
        p.style.cssText = [
            `width:${size}px`,
            `height:${size}px`,
            `left:${Math.random() * 100}%`,
            `animation-duration:${Math.random() * 15 + 10}s`,
            `animation-delay:-${Math.random() * 15}s`,
            `opacity:${(Math.random() * 0.3 + 0.1).toFixed(2)}`
        ].join(';');
        container.appendChild(p);
    }
})();

// ── WELCOME → AUTH ───────────────────────────────────────────
function showAuth() {
    document.getElementById('welcomeScreen').style.display = 'none';
    document.getElementById('authScreen').style.display   = 'block';
}

// ── TAB SWITCH ───────────────────────────────────────────────
function switchTab(tab) {
    const isLogin = tab === 'login';

    document.getElementById('loginForm').style.display    = isLogin ? 'block' : 'none';
    document.getElementById('registerForm').style.display = isLogin ? 'none'  : 'block';
    document.getElementById('tabLogin').classList.toggle('active',    isLogin);
    document.getElementById('tabRegister').classList.toggle('active', !isLogin);
}

// ── AUTO-SHOW AUTH IF FORM ERRORS ────────────────────────────
// window.__HAS_FORM_ERRORS__ is set inline in login.html by Django template
if (window.__HAS_FORM_ERRORS__) {
    showAuth();
}
