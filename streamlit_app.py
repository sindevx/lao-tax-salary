import pathlib
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Lao PDR Salary Tax Calculator",
    page_icon="🇱🇦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Remove all Streamlit chrome so the iframe fills the page cleanly
st.markdown(
    """
    <style>
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        footer { display: none !important; }
        .block-container { padding: 0 !important; }
        #root > div:first-child { padding: 0 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

BASE = pathlib.Path(__file__).parent

html = (BASE / "index.html").read_text(encoding="utf-8")
css  = (BASE / "assets" / "tailwind.css").read_text(encoding="utf-8")

# ── Patch 1: inline the local CSS so relative path resolves inside the iframe ─
html = html.replace(
    '<link rel="stylesheet" href="/assets/tailwind.css">',
    f"<style>\n{css}\n</style>",
)

# ── Patch 2: iframe CSS overrides injected into <head> ───────────────────────
#
#  a) Results modal: env(safe-area-inset-top) = 0 on desktop inside an iframe,
#     so the original padding-top of calc(0 + 0.75rem) = 12 px is far too tight.
#     Override to 1.5 rem top / 1.5 rem bottom for comfortable breathing room.
#
#  b) Bottom nav bar: position:fixed inside the iframe sits at the very bottom
#     of the 1100 px iframe, not the browser window — keep it visible.
#
CSS_PATCH = """<style>
/* ── Streamlit iframe overrides ── */
#results:not(.hidden) {
    padding: 1.5rem 1rem 1.5rem !important;
}
</style>
"""
html = html.replace("</head>", CSS_PATCH + "\n</head>", 1)

# ── Patch 3 (was Patch 2): inject iframe compatibility fixes before any app script runs ──────
#
#  Problems in Streamlit's sandboxed iframe:
#    a) history.replaceState → SecurityError (different origin/blob URL).
#       Called on every keystroke via scheduleUrlSync(); crashes the whole
#       syncStateToUrl chain and freezes input handlers.
#    b) localStorage → may be blocked by ITP / browser privacy settings.
#       Results in DOMException that propagates through BCEL rate caching.
#    c) navigator.clipboard.writeText → requires explicit permission policy;
#       absent in most iframe contexts.
#
COMPAT_PATCH = """<script>
(function () {
    // a) Safe history.replaceState — silently ignore SecurityError in iframes
    var _origReplace = history.replaceState.bind(history);
    history.replaceState = function () {
        try { _origReplace.apply(history, arguments); } catch (_) {}
    };

    // b) Safe localStorage — fall back to in-memory store if blocked
    try {
        localStorage.getItem('__streamlit_ping__');
    } catch (_) {
        var _store = {};
        Object.defineProperty(window, 'localStorage', {
            get: function () {
                return {
                    getItem:    function (k)    { return Object.prototype.hasOwnProperty.call(_store, k) ? _store[k] : null; },
                    setItem:    function (k, v) { _store[k] = String(v); },
                    removeItem: function (k)    { delete _store[k]; },
                    clear:      function ()     { _store = {}; },
                    key:        function (i)    { return Object.keys(_store)[i] || null; },
                    get length()               { return Object.keys(_store).length; }
                };
            }
        });
    }

    // c) Safe clipboard.writeText — silently skip if not permitted
    if (navigator.clipboard && navigator.clipboard.writeText) {
        var _origWrite = navigator.clipboard.writeText.bind(navigator.clipboard);
        navigator.clipboard.writeText = function (text) {
            return _origWrite(text).catch(function () {});
        };
    }
})();
</script>
"""
html = html.replace("<head>", "<head>\n" + COMPAT_PATCH, 1)

# ── Patch 3: feature fixes injected just before </body> ───────────────────────
#
#  Fix A — exportToExcel crashes with ReferenceError when the XLSX CDN script
#           fails to load (no try-catch in the original function).
#
#  Fix B — setExchangeRateStatus shows no visual distinction when all exchange
#           rate providers fail; patch makes the fallback message red + bold so
#           the user knows the rate is stale/default.
#
#  Fix C — iframe height: 1100 px gives the full form comfortable room.
#           The results overlay uses position:fixed so it always covers the
#           visible viewport regardless of how much the user has scrolled.
#
FEATURE_PATCH = """<script>
(function () {
    function applyPatches() {
        // ── Fix A: guard exportToExcel against missing XLSX library ────────
        if (typeof exportToExcel === 'function') {
            var _origExport = exportToExcel;
            window.exportToExcel = function () {
                if (typeof XLSX === 'undefined') {
                    var t = (typeof translations !== 'undefined' && translations[currentLanguage]) || {};
                    var title = t.validationError || 'Error';
                    var msg   = t.xlsxNotLoaded  || 'Excel export library failed to load. Please check your connection and try again.';
                    if (typeof showValidationModal === 'function') {
                        showValidationModal(title, msg);
                    } else {
                        alert(msg);
                    }
                    return;
                }
                try {
                    _origExport.apply(this, arguments);
                } catch (e) {
                    var t2 = (typeof translations !== 'undefined' && translations[currentLanguage]) || {};
                    if (typeof showValidationModal === 'function') {
                        showValidationModal(t2.validationError || 'Error', 'Export failed: ' + e.message);
                    }
                }
            };
        }

        // ── Fix B: visually highlight exchange-rate fetch failures ──────────
        if (typeof setExchangeRateStatus === 'function') {
            var _origStatus = setExchangeRateStatus;
            window.setExchangeRateStatus = function (messageKey) {
                _origStatus.apply(this, arguments);
                var el = document.getElementById('exchangeRateStatus');
                if (!el) return;
                if (messageKey === 'exchangeRateFallback') {
                    el.style.color      = '#b45309';
                    el.style.fontWeight = '600';
                    // Prepend a warning icon if not already there
                    if (!el.dataset.warned) {
                        el.textContent = '⚠ ' + el.textContent;
                        el.dataset.warned = '1';
                    }
                } else {
                    el.style.color      = '';
                    el.style.fontWeight = '';
                    delete el.dataset.warned;
                }
            };
        }
    }

    // App scripts run on DOMContentLoaded; apply patches after that fires
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyPatches);
    } else {
        applyPatches();
    }
})();
</script>
"""
html = html.replace("</body>", FEATURE_PATCH + "\n</body>", 1)

# Fix C: 1100 px gives the full form comfortable room; the results overlay
# uses position:fixed so it always covers the visible iframe viewport.
components.html(html, height=1100, scrolling=True)
