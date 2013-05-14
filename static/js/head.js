$('#headTab a').click(function (e) {
  //e.preventDefault();
  $(this).tab('show');
})

$('#headTab a[href="/login/"]').tab('show');