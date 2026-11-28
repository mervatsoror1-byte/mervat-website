// Ask before sending the reply to the customer.
(function () {
  var b = document.getElementById('sendBtn'); if (!b) return;
  b.addEventListener('click', function (e) {
    var to = (document.getElementById('email') || {}).value || '';
    if (!confirm('إرسال الرد إلى ' + to + '؟')) e.preventDefault();
  });
})();
// Ask before deleting a submission.
document.querySelectorAll('form.del').forEach(function (f) {
  f.addEventListener('submit', function (e) { if (!confirm('حذف إجابات هذه العميلة نهائياً؟')) e.preventDefault(); });
});
