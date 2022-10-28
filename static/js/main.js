

window.addEventListener('DOMContentLoaded', (event) => {
  console.log('DOM fully loaded and parsed');
   history.pushState(null, null, location.href);
   history.back();
   history.forward();
   window.onpopstate = function () {
     history.go(1);
   };
  
});


$('#search').on('change keydown keyup paste input', function () {
  $('#botonbuscar').click();
});



