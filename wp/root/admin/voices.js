// Show/hide password button on every password field.
(function () {
  document.querySelectorAll('input[type=password]').forEach(function (inp) {
    var wrap = document.createElement('div'); wrap.className = 'pw';
    inp.parentNode.insertBefore(wrap, inp); wrap.appendChild(inp);
    var b = document.createElement('button'); b.type = 'button'; b.className = 'eye'; b.textContent = '👁'; b.setAttribute('aria-label', 'إظهار كلمة السر');
    b.onclick = function () { var show = inp.type === 'password'; inp.type = show ? 'text' : 'password'; b.textContent = show ? '🙈' : '👁'; b.setAttribute('aria-label', show ? 'إخفاء كلمة السر' : 'إظهار كلمة السر'); };
    wrap.appendChild(b);
  });
})();
// Reads the chosen file's length so the site can show it next to the review.
(function () {
  var input = document.getElementById('audio'), len = document.getElementById('len'), out = document.getElementById('dur');
  if (!input) return;
  input.addEventListener('change', function () {
    len.value = '0'; out.textContent = '';
    var f = input.files && input.files[0]; if (!f) return;
    var a = new Audio(), url = URL.createObjectURL(f);
    a.preload = 'metadata';
    a.onloadedmetadata = function () {
      var d = a.duration; URL.revokeObjectURL(url);
      if (!isFinite(d)) return;
      len.value = d.toFixed(1);
      var m = Math.floor(d / 60), s = Math.round(d % 60);
      out.textContent = 'المدة: ' + m + ':' + (s < 10 ? '0' : '') + s + (d > 300 ? ' — أطول من ٥ دقائق، قصّريه أولاً' : '');
    };
    a.src = url;
  });
})();
