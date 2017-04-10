// jQuery for page scrolling feature - requires jQuery Easing plugin
$(function () {
  scrollOffset();
  $('a.page-scroll').bind('click', function (event) {
    let $anchor = $(this)
    $('html, body').stop().animate({
      // Scroll to top with offset of nav (addition of 2 pixels to ensure correct active header)
      scrollTop: $($anchor.attr('href')).offset().top - mobileNav() + 2
    }, 1500, 'easeInOutExpo')
    event.preventDefault()
  })
})

// Set Scroll Spy to size of Navbar
window.onresize = scrollOffset;
function scrollOffset(){
  document.querySelector("body").dataset.offset = parseInt(jQuery('nav').css('height'))
}

// Determine if Mobile Nav or Desktop Nav
function mobileNav(){
  let mobile = parseInt(jQuery('.navbar-header.page-scroll').css('height'))
  return ( mobile > 1 ? mobile : parseInt(jQuery('nav').css('height')))
}
