(function () {
  var data = null;
  var meta = window.DATA_META || { n: 0, cases: [] };
  var searchBy = 'name';
  var loading = false;

  var input = document.getElementById('searchInput');
  var btn = document.getElementById('searchBtn');
  var resultsDiv = document.getElementById('results');
  var countDiv = document.getElementById('resultsCount');

  function switchTab(mode) {
    searchBy = mode;
    document.querySelectorAll('.tab').forEach(function (t) {
      t.classList.toggle('active', t.dataset.by === mode);
    });
    input.placeholder = mode === 'name' ? 'ادخل اسم الطالب...' : 'ادخل رقم الجلوس...';
    input.value = '';
    resultsDiv.innerHTML = '';
    countDiv.textContent = '';
    input.focus();
  }

  document.querySelectorAll('.tab').forEach(function (t) {
    t.addEventListener('click', function () {
      switchTab(t.dataset.by);
    });
  });

  function statusClass(caseDesc) {
    var s = (caseDesc || '').toLowerCase();
    if (s.indexOf('ناجح') !== -1 || s.indexOf('pass') !== -1 || s.indexOf('success') !== -1) return 'status-pass';
    if (s.indexOf('دور ثان') !== -1 || s.indexOf('second') !== -1) return 'status-second';
    return 'status-fail';
  }

  function showSkeleton() {
    resultsDiv.innerHTML = Array.from({ length: 3 }, function () {
      return '<div class="skeleton"><div class="skeleton-line"></div><div class="skeleton-line"></div></div>';
    }).join('');
  }

  function parseVarints(u8, pos, n) {
    var out = new Float64Array(n);
    for (var i = 0; i < n; i++) {
      var v = 0, s = 0, b;
      do {
        b = u8[pos++];
        v |= (b & 0x7f) << s;
        s += 7;
      } while (b & 0x80);
      out[i] = v;
    }
    return { arr: out, pos: pos };
  }

  function loadData() {
    if (data) return Promise.resolve(data);
    loading = true;
    btn.disabled = true;
    btn.textContent = 'جارِ التحميل...';
    countDiv.textContent = 'جارِ تحميل قاعدة البيانات (مرة واحدة، حوالي 12 ميجابايت)...';
    return fetch('data.gz')
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.arrayBuffer();
      })
      .then(function (gz) {
        if (typeof DecompressionStream === 'undefined') {
          throw new Error('المتصفح لا يدعم فك الضغط');
        }
        var stream = new Blob([gz]).stream().pipeThrough(new DecompressionStream('gzip'));
        return new Response(stream).arrayBuffer();
      })
      .then(function (raw) {
        var u8 = new Uint8Array(raw);
        if (String.fromCharCode(u8[0], u8[1], u8[2], u8[3]) !== 'TW26') {
          throw new Error('تنسيق بيانات غير صحيح');
        }
        var dv = new DataView(u8.buffer, u8.byteOffset, u8.byteLength);
        var n = dv.getUint32(4, true);
        var namesLen = dv.getUint32(8, true);
        var pos = 12;

        var off = parseVarints(u8, pos, n);
        pos = off.pos;
        var offsets = off.arr;
        for (var i = 1; i <= n; i++) offsets[i] += offsets[i - 1];

        var idres = parseVarints(u8, pos, n);
        pos = idres.pos;
        var ids = new Uint32Array(n);
        for (i = 0; i < n; i++) ids[i] = idres.arr[i];

        var degrees = new Uint8Array(u8.buffer, u8.byteOffset + pos, n);
        pos += n;
        var cases = new Uint8Array(u8.buffer, u8.byteOffset + pos, n);
        pos += n;

        var namesStr = new TextDecoder('utf-8').decode(u8.subarray(pos, pos + namesLen));

        data = { n: n, offsets: offsets, ids: ids, degrees: degrees, cases: cases, namesStr: namesStr };
        loading = false;
        btn.disabled = false;
        btn.textContent = 'بحث';
        countDiv.textContent = 'تم تحميل قاعدة البيانات بنجاح ✓';
        return data;
      })
      .catch(function (e) {
        loading = false;
        btn.disabled = false;
        btn.textContent = 'بحث';
        countDiv.textContent = '';
        throw e;
      });
  }

  function searchNames(tokens) {
    var hay = data.namesStr;
    var offsets = data.offsets;
    var out = [];
    for (var i = 0; i < data.n; i++) {
      var start = offsets[i], end = offsets[i + 1];
      var ok = true;
      for (var t = 0; t < tokens.length; t++) {
        var p = tokens[t];
        var pos = hay.indexOf(p, start);
        if (pos === -1 || pos + p.length > end) { ok = false; break; }
      }
      if (ok) out.push(i);
      if (out.length >= 50) break;
    }
    return out;
  }

  function searchId(sid) {
    var ids = data.ids;
    for (var i = 0; i < data.n; i++) {
      if (ids[i] === sid) return [i];
    }
    return [];
  }

  function renderRows(rows) {
    countDiv.textContent = 'تم العثور على ' + rows.length + ' نتيجة';
    resultsDiv.innerHTML = rows.map(function (i, idx) {
      var name = data.namesStr.substring(data.offsets[i], data.offsets[i + 1]);
      var caseDesc = meta.cases[data.cases[i]] || '';
      return '<div class="result-card" style="animation-delay:' + (idx * 60) + 'ms">' +
        '<div class="result-info">' +
        '<div class="result-name"></div>' +
        '<div class="result-id">رقم الجلوس: <span>' + data.ids[i] + '</span></div>' +
        '</div>' +
        '<div class="result-meta">' +
        '<div class="degree"><div class="degree-value">' + data.degrees[i] + '</div><span class="degree-label">الدرجة</span></div>' +
        '<div class="status-badge ' + statusClass(caseDesc) + '">' + caseDesc + '</div>' +
        '</div>' +
        '</div>';
    }).join('');
    resultsDiv.querySelectorAll('.result-name').forEach(function (el, idx) {
      el.textContent = rows[idx] !== undefined ? data.namesStr.substring(data.offsets[rows[idx]], data.offsets[rows[idx] + 1]) : '';
    });
  }

  function search() {
    if (!data) { countDiv.textContent = 'لا تزال قاعدة البيانات تُحمَّل...'; return; }
    var q = input.value.trim();
    if (!q) return;
    showSkeleton();
    var rows;
    if (searchBy === 'id') {
      var sid = parseInt(q, 10);
      if (isNaN(sid)) { resultsDiv.innerHTML = '<div class="error-msg">رقم الجلوس غير صالح</div>'; return; }
      rows = searchId(sid);
    } else {
      var tokens = q.split(/\s+/).map(function (t) { return t.replace(/\s/g, ''); }).filter(Boolean);
      if (!tokens.length) return;
      rows = searchNames(tokens);
    }
    if (!rows.length) {
      countDiv.textContent = '';
      resultsDiv.innerHTML = '<div class="no-results">لا توجد نتائج للبحث</div>';
      return;
    }
    renderRows(rows);
  }

  function runDeepLink() {
    var params = new URLSearchParams(location.search);
    var q = params.get('q');
    var by = params.get('by');
    if (!q) return;
    if (by === 'id' || by === 'name') {
      searchBy = by;
      document.querySelectorAll('.tab').forEach(function (t) {
        t.classList.toggle('active', t.dataset.by === by);
      });
    }
    input.value = q;
    loadData().then(search).catch(function () {
      countDiv.textContent = '';
      resultsDiv.innerHTML = '<div class="error-msg">تعذر تحميل قاعدة البيانات. تحقق من الاتصال وأعد المحاولة.</div>';
    });
  }

  btn.addEventListener('click', function () {
    if (loading) return;
    if (!data) {
      loadData().then(search).catch(function () {
        countDiv.textContent = '';
        resultsDiv.innerHTML = '<div class="error-msg">تعذر تحميل قاعدة البيانات. تحقق من الاتصال وأعد المحاولة.</div>';
      });
    } else {
      search();
    }
  });

  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') btn.click();
  });

  runDeepLink();
})();
