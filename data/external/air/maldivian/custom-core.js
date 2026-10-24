jQuery(function($) {
"use strict";
	var $window = $(window);	
	if($.fn.navigation){
		$("#main-nav").navigation();
	}
	
	$('#preloader').fadeOut('slow', function () {
	  $(this).remove();
	});
	
	$(".with-waypoint-sticky").waypoint(function() {
		$("#header-waypoint-sticky").toggleClass("header-waypoint-sticky");
		return false;
	}, { offset: "-20px" });
	
	$('[data-toggle="tooltip"]').tooltip();
	
	var backToTop = $("#back-to-top");
	
	$window.scroll(function () {
		if ($(this).scrollTop() > 50) {
			backToTop.fadeIn();
		} else {
			backToTop.fadeOut();
		}
	});
	
	// scroll body to 0px on click
	backToTop.on('click',function () {
		backToTop.tooltip('hide');
		$('body,html').animate({
			scrollTop: 0
		}, 800);
		return false;
	});
	  
/**
 * Smooth scroll to anchor
 */
$("a.nav-link[href^='#']").on("click",function() {
	if (location.pathname.replace(/^\//,'') == this.pathname.replace(/^\//,'') && location.hostname == this.hostname) {
		var target = $(this.hash);
		target = target.length ? target : $('[name=' + this.hash.slice(1) +']');
		if (target.length) {
			$('html,body').animate({
				scrollTop: (target.offset().top - 230) // 70px offset for navbar menu
			}, 1000);
			return false;
		}
	}
});
});
