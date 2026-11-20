/* Agent Studio face engine: an SVG face that blinks, glances at the pointer, lip-syncs to text and (optionally)
   speaks it with the browser's voice. Plain JS, no library. Used by Components/Face (Python) through client_code/face.py.

     AS.faceSVG(cfg)                 static SVG string (thumbnails)
     var f = AS.Face(el, cfg, opts)  live face in el. opts: {live: true}  (false = static, no timers)
       f.set(cfg)                    redraw with a new look (keeps running)
       f.talk(text, lang, speak)     mouth moves through the text; speak=true also reads it aloud. Returns a Promise.
       f.think(on)                   eyes up + "thinking" brows while an answer is on its way
       f.stop()                      stop talking now
       f.destroy()                   remove timers and listeners
     AS.OPTIONS                      the choices the Look tab offers
     AS.speechOK()                   true if the browser can speak
   cfg keys: skin hair hairStyle eyes brows glasses accessory shirt bg voice{rate,pitch}  (all optional) */
(function () {
  'use strict';
  var AS = window.AS = window.AS || {};

  AS.OPTIONS = {
    skin: ['#F6D7C3', '#EBB897', '#D69A72', '#B57650', '#8D5A3B', '#5E3A26'],
    hair: ['#1F1714', '#4A2E1F', '#8A5A35', '#C99A5B', '#E5C48E', '#B4473A', '#9AA0A6', '#3B3F8F'],
    hairStyle: ['short', 'bob', 'curly', 'bun', 'long', 'wavy', 'shaved'],
    eyes: ['#3B2A20', '#4C6A3A', '#2F5E86', '#6B4A2A', '#2A2A2A'],
    brows: ['soft', 'straight', 'arched'],
    glasses: ['none', 'round', 'square'],
    accessory: ['none', 'earrings', 'beret', 'headband', 'scarf'],
    shirt: ['#2E6F6A', '#B0007A', '#1B1A22', '#3E5A99', '#C2623A', '#6D6A75'],
    bg: ['#F8E3F0', '#E1EFEC', '#EFEBE6', '#E4E8F5', '#FBE9DC', '#E9E4F2']
  };
  var DEFAULT = { skin: '#EBB897', hair: '#4A2E1F', hairStyle: 'bob', eyes: '#3B2A20', brows: 'soft', glasses: 'none',
                  accessory: 'none', shirt: '#2E6F6A', bg: '#F8E3F0', voice: { rate: 1, pitch: 1 } };

  function pick(cfg) {
    var c = {}, k;
    for (k in DEFAULT) c[k] = DEFAULT[k];
    if (cfg) for (k in cfg) if (cfg[k] !== undefined && cfg[k] !== null && cfg[k] !== '') c[k] = cfg[k];
    return c;
  }
  // darker / lighter shade of a hex colour (for shadows, lips, outlines)
  function shade(hex, amt) {
    var h = String(hex || '#999999').replace('#', '');
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    var n = parseInt(h, 16), r = n >> 16, g = (n >> 8) & 255, b = n & 255;
    function f(v) { return Math.max(0, Math.min(255, Math.round(amt < 0 ? v * (1 + amt) : v + (255 - v) * amt))); }
    return '#' + ((1 << 24) + (f(r) << 16) + (f(g) << 8) + f(b)).toString(16).slice(1);
  }
  function esc(s) { return String(s).replace(/[<>&"]/g, ''); }

  // ---- the drawing (viewBox 0 0 200 200; head centre 100,92)
  var MOUTHS = {
    rest:  '<path d="M88 128 Q100 134 112 128" fill="none" stroke="LIP" stroke-width="3" stroke-linecap="round"/>',
    smile: '<path d="M85 125 Q100 140 115 125" fill="none" stroke="LIP" stroke-width="3.2" stroke-linecap="round"/>',
    small: '<ellipse cx="100" cy="129" rx="7" ry="3.6" fill="IN"/><path d="M93 128 Q100 125 107 128" fill="none" stroke="LIP" stroke-width="2"/>',
    open:  '<path d="M89 126 Q100 122 111 126 Q109 139 100 140 Q91 139 89 126Z" fill="IN"/><path d="M93 136 Q100 140 107 136" fill="none" stroke="#E07A88" stroke-width="3" stroke-linecap="round"/>',
    wide:  '<path d="M86 126 Q100 123 114 126 Q110 135 100 136 Q90 135 86 126Z" fill="IN"/><path d="M90 127 L110 127" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>',
    round: '<ellipse cx="100" cy="130" rx="5.5" ry="6.5" fill="IN"/>',
    closed:'<path d="M90 129 L110 129" stroke="LIP" stroke-width="3.4" stroke-linecap="round"/>'
  };

  function hairBack(c) {
    var h = c.hair, s = c.hairStyle;
    if (s === 'long') return '<path d="M52 92 Q50 40 100 36 Q150 40 148 92 L152 168 Q100 180 48 168Z" fill="' + h + '"/>';
    if (s === 'bob') return '<path d="M55 96 Q52 42 100 38 Q148 42 145 96 L146 132 Q128 140 120 128 L80 128 Q72 140 54 132Z" fill="' + h + '"/>';
    if (s === 'wavy') return '<path d="M54 92 Q50 40 100 36 Q150 40 146 92 Q156 112 146 128 Q154 146 138 154 L62 154 Q46 146 54 128 Q44 112 54 92Z" fill="' + h + '"/>';
    if (s === 'bun') return '<circle cx="100" cy="30" r="17" fill="' + h + '"/>';
    if (s === 'curly') {
      var out = '', pts = [[60, 70], [56, 92], [62, 112], [140, 70], [144, 92], [138, 112], [72, 50], [128, 50], [100, 40], [86, 44], [114, 44]];
      for (var i = 0; i < pts.length; i++) out += '<circle cx="' + pts[i][0] + '" cy="' + pts[i][1] + '" r="15" fill="' + h + '"/>';
      return out;
    }
    return '';
  }
  function hairFront(c) {
    var h = c.hair, s = c.hairStyle, hi = shade(h, 0.18);
    if (s === 'shaved') return '<path d="M62 78 Q64 46 100 44 Q136 46 138 78 Q120 62 100 62 Q80 62 62 78Z" fill="' + h + '" opacity=".55"/>';
    if (s === 'short') return '<path d="M60 84 Q58 42 100 40 Q142 42 140 84 Q134 64 118 60 Q104 70 80 62 Q66 68 60 84Z" fill="' + h + '"/><path d="M84 52 Q100 46 118 52" fill="none" stroke="' + hi + '" stroke-width="3" stroke-linecap="round"/>';
    if (s === 'curly') return '<path d="M62 80 Q60 48 100 46 Q140 48 138 80 Q128 66 114 70 Q106 60 96 68 Q84 60 74 70 Q66 70 62 80Z" fill="' + h + '"/>';
    if (s === 'bun') return '<path d="M60 84 Q60 44 100 44 Q140 44 140 84 Q126 60 100 58 Q74 60 60 84Z" fill="' + h + '"/><path d="M88 50 Q100 46 112 50" fill="none" stroke="' + hi + '" stroke-width="2.5" stroke-linecap="round"/>';
    if (s === 'long' || s === 'wavy') return '<path d="M60 90 Q58 44 100 42 Q142 44 140 90 Q130 60 104 58 Q98 72 72 72 Q64 78 60 90Z" fill="' + h + '"/>';
    return '<path d="M58 92 Q56 44 100 42 Q144 44 142 92 Q138 66 116 62 Q100 74 70 70 Q60 78 58 92Z" fill="' + h + '"/>';  // bob
  }
  function brows(c, think) {
    var col = shade(c.hair, -0.15), up = think ? -4 : 0, d;
    if (c.brows === 'straight') d = ['M72 ' + (78 + up) + ' L90 ' + (77 + up), 'M110 ' + (77 + up) + ' L128 ' + (78 + up)];
    else if (c.brows === 'arched') d = ['M71 ' + (80 + up) + ' Q80 ' + (71 + up) + ' 90 ' + (77 + up), 'M110 ' + (77 + up) + ' Q120 ' + (71 + up) + ' 129 ' + (80 + up)];
    else d = ['M72 ' + (79 + up) + ' Q81 ' + (75 + up) + ' 90 ' + (78 + up), 'M110 ' + (78 + up) + ' Q119 ' + (75 + up) + ' 128 ' + (79 + up)];
    if (think) d[1] = 'M110 ' + (75 + up) + ' Q119 ' + (69 + up) + ' 128 ' + (76 + up);
    return '<path d="' + d[0] + '" fill="none" stroke="' + col + '" stroke-width="3.6" stroke-linecap="round"/>' +
           '<path d="' + d[1] + '" fill="none" stroke="' + col + '" stroke-width="3.6" stroke-linecap="round"/>';
  }
  function glasses(c) {
    var g = c.glasses, col = '#26232E';
    if (g === 'round') return '<g fill="none" stroke="' + col + '" stroke-width="2.6"><circle cx="81" cy="94" r="12"/><circle cx="119" cy="94" r="12"/><path d="M93 93 Q100 89 107 93M69 92 L60 89M131 92 L140 89"/></g>';
    if (g === 'square') return '<g fill="none" stroke="' + col + '" stroke-width="2.6"><rect x="67" y="84" width="27" height="20" rx="5"/><rect x="106" y="84" width="27" height="20" rx="5"/><path d="M94 92 Q100 88 106 92M67 90 L60 88M133 90 L140 88"/></g>';
    return '';
  }
  function accessory(c) {
    var a = c.accessory, acc = shade(c.shirt, 0.15);
    if (a === 'earrings') return '<circle cx="58" cy="112" r="3.6" fill="#D9A93A"/><circle cx="142" cy="112" r="3.6" fill="#D9A93A"/>';
    if (a === 'beret') return '<path d="M58 62 Q66 30 104 30 Q146 32 146 56 Q130 50 100 52 Q74 52 58 62Z" fill="' + acc + '"/><circle cx="108" cy="29" r="3.5" fill="' + acc + '"/>';
    if (a === 'headband') return '<path d="M60 72 Q100 50 140 72" fill="none" stroke="' + acc + '" stroke-width="7" stroke-linecap="round"/>';
    if (a === 'scarf') return '<path d="M70 150 Q100 166 130 150 L134 162 Q100 178 66 162Z" fill="' + acc + '"/><path d="M112 160 L120 186 L106 186Z" fill="' + shade(acc, -0.12) + '"/>';
    return '';
  }

  function svg(c, st) {
    st = st || {};
    var skin = c.skin, shadow = shade(skin, -0.14), lip = shade(skin, -0.38), inside = '#5A2430';
    var gx = (st.gx || 0) * 3, gy = (st.gy || 0) * 2 + (st.think ? -3 : 0);
    var lid = st.blink ? 1 : 0;
    var mouth = (MOUTHS[st.mouth || 'rest'] || MOUTHS.rest).replace(/LIP/g, lip).replace(/IN/g, inside);
    var eye = function (cx) {
      return '<g class="as-eye"><ellipse cx="' + cx + '" cy="94" rx="8.6" ry="' + (lid ? 1.2 : 6.4) + '" fill="#fff"/>' +
        (lid ? '' : '<circle cx="' + (cx + gx) + '" cy="' + (95 + gy) + '" r="4.4" fill="' + c.eyes + '"/><circle cx="' + (cx + gx) + '" cy="' + (95 + gy) + '" r="2" fill="#111"/><circle cx="' + (cx + gx + 1.4) + '" cy="' + (93.4 + gy) + '" r="1.1" fill="#fff"/>') +
        '<path d="M' + (cx - 9) + ' ' + (lid ? 94 : 90) + ' Q' + cx + ' ' + (lid ? 97 : 85.5) + ' ' + (cx + 9) + ' ' + (lid ? 94 : 90) + '" fill="none" stroke="' + shade(skin, -0.45) + '" stroke-width="2" stroke-linecap="round"/></g>';
    };
    return '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-hidden="true" focusable="false">' +
      '<circle cx="100" cy="100" r="100" fill="' + esc(c.bg) + '"/>' +
      '<g transform="translate(0,' + (st.bob || 0).toFixed(2) + ')">' +
      hairBack(c) +
      '<path d="M40 200 Q42 158 100 150 Q158 158 160 200Z" fill="' + esc(c.shirt) + '"/>' +
      '<path d="M86 136 L86 154 Q100 164 114 154 L114 136Z" fill="' + shadow + '"/>' +
      '<ellipse cx="60" cy="100" rx="7" ry="10" fill="' + shadow + '"/><ellipse cx="140" cy="100" rx="7" ry="10" fill="' + shadow + '"/>' +
      '<ellipse cx="100" cy="96" rx="40" ry="48" fill="' + esc(skin) + '"/>' +
      '<circle cx="76" cy="114" r="7" fill="#E77F86" opacity=".22"/><circle cx="124" cy="114" r="7" fill="#E77F86" opacity=".22"/>' +
      hairFront(c) + accessory(c) + brows(c, st.think) + eye(81) + eye(119) +
      '<path d="M100 98 Q96 112 100 114 Q103 115 105 113" fill="none" stroke="' + shade(skin, -0.3) + '" stroke-width="2.2" stroke-linecap="round"/>' +
      mouth + glasses(c) +
      '</g></svg>';
  }

  AS.faceSVG = function (cfg) { return svg(pick(cfg), {}); };
  AS.speechOK = function () { return !!(window.speechSynthesis && window.SpeechSynthesisUtterance); };

  // letters -> mouth shapes
  function shapes(text) {
    var out = [], t = String(text || '').toLowerCase();
    for (var i = 0; i < t.length; i++) {
      var ch = t[i];
      if (/[aàâ]/.test(ch)) out.push('open');
      else if (/[eéèêiîy]/.test(ch)) out.push('wide');
      else if (/[oôuùûw]/.test(ch)) out.push('round');
      else if (/[mbp]/.test(ch)) out.push('closed');
      else if (/[\s]/.test(ch)) { if (out[out.length - 1] !== 'rest') out.push('rest'); }
      else if (/[.,!?;:]/.test(ch)) { out.push('rest'); out.push('rest'); }
      else if (/[a-zçœ]/.test(ch) && Math.random() < 0.6) out.push('small');
    }
    out.push('smile');
    return out;
  }
  function voiceFor(lang) {
    if (!AS.speechOK()) return null;
    var vs = window.speechSynthesis.getVoices() || [], want = (lang || 'en').slice(0, 2);
    var best = null;
    for (var i = 0; i < vs.length; i++) {
      var l = (vs[i].lang || '').toLowerCase();
      if (l.indexOf(want) !== 0) continue;
      if (!best) best = vs[i];
      if (want === 'fr' && l === 'fr-ca') return vs[i];
      if (want === 'en' && l === 'en-ca') best = vs[i];
    }
    return best;
  }
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  AS.Face = function (el, cfg, opts) {
    opts = opts || {};
    var live = opts.live !== false;
    var c = pick(cfg), st = { mouth: 'smile' }, timers = [], raf = 0, talking = null, dead = false;
    function draw() { if (!dead) el.innerHTML = svg(c, st); }
    function later(fn, ms) { var id = setTimeout(fn, ms); timers.push(id); return id; }
    function blinkLoop() {
      if (dead || !live) return;
      later(function () {
        st.blink = true; draw();
        later(function () { st.blink = false; draw(); blinkLoop(); }, 130);
      }, 2600 + Math.random() * 3200);
    }
    function onMove(e) {
      if (dead) return;
      var r = el.getBoundingClientRect();
      if (!r.width) return;
      var dx = (e.clientX - (r.left + r.width / 2)) / (window.innerWidth / 2);
      var dy = (e.clientY - (r.top + r.height / 2)) / (window.innerHeight / 2);
      st.gx = Math.max(-1, Math.min(1, dx)); st.gy = Math.max(-1, Math.min(1, dy));
      if (!raf) raf = requestAnimationFrame(function () { raf = 0; draw(); });
    }
    if (live && !reduce) window.addEventListener('pointermove', onMove, { passive: true });

    function stop() {
      if (talking) { talking.cancelled = true; talking.done(); talking = null; }
      if (AS.speechOK() && api._spoke) { try { window.speechSynthesis.cancel(); } catch (e) {} }
      st.mouth = 'smile'; st.bob = 0; draw();
    }
    var api = {
      set: function (cfg2) { c = pick(cfg2); draw(); },
      think: function (on) { st.think = !!on; st.mouth = on ? 'rest' : 'smile'; draw(); },
      stop: stop,
      talk: function (text, lang, speak) {
        stop();
        st.think = false;
        var seq = shapes(text), i = 0, step = 72;
        return new Promise(function (resolve) {
          var job = { cancelled: false, done: resolve };
          talking = job;
          var spoken = false;
          if (speak && AS.speechOK()) {
            try {
              var u = new window.SpeechSynthesisUtterance(String(text));
              var v = voiceFor(lang); if (v) u.voice = v;
              u.lang = v ? v.lang : (lang === 'fr' ? 'fr-CA' : 'en-CA');
              u.rate = (c.voice && +c.voice.rate) || 1; u.pitch = (c.voice && +c.voice.pitch) || 1;
              u.onend = function () { if (talking === job) { talking = null; st.mouth = 'smile'; st.bob = 0; draw(); resolve(); } };
              window.speechSynthesis.speak(u); api._spoke = true; spoken = true;
              step = 72 / u.rate;
            } catch (e) { spoken = false; }
          }
          var t0 = performance.now();
          (function tick() {
            if (dead || job.cancelled) return;
            st.mouth = seq[i % seq.length];
            if (!reduce) st.bob = Math.sin((performance.now() - t0) / 260) * 1.2;
            draw();
            i++;
            if (i < seq.length) later(tick, step);
            else if (spoken && talking === job && window.speechSynthesis.speaking) { i = 0; later(tick, step); }  // keep moving until the voice ends
            else if (talking === job) { talking = null; st.mouth = 'smile'; st.bob = 0; draw(); resolve(); }
          })();
        });
      },
      destroy: function () {
        dead = true;
        timers.forEach(clearTimeout); timers = [];
        window.removeEventListener('pointermove', onMove);
        if (raf) cancelAnimationFrame(raf);
      }
    };
    api.say = function (text, lang, speak) { api.talk(text, lang, speak); };  // same, without a Promise (Python would wait on it)
    draw();
    blinkLoop();
    return api;
  };
})();
