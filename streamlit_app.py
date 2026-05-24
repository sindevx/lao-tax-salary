import pathlib
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Lao PDR Salary Tax Calculator",
    page_icon="🇱🇦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Remove all Streamlit chrome so the iframe fills the page cleanly
st.markdown(
    """
    <style>
        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        footer { display: none !important; }
        .block-container { padding: 0 !important; max-width: 100% !important; }
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

# ── Patch 2: inject iframe compatibility fixes before any app script runs ──────
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

# Height covers the full form; the fixed results overlay sits on top within
# the iframe viewport, which is the correct behaviour.
components.html(html, height=980, scrolling=True)
