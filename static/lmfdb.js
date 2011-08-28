/* this file contains global javascript code for all parts of the lmfdb website
   it's just one file for faster page loading */

/* only show main content after processing all the latex */
$(function() {
  function show_content() {
    $("#content").show();
    $("#mathjax-info").hide();
  }
  MathJax.Hub.Queue(function() {show_content()});
  $("#mathjax-info").click(function() {show_content()});

  /* 
  var $mjlog = $("#mathjax-log");
  MathJax.Hub.Register.MessageHook("New Math",function (msg) {
    var script = MathJax.Hub.getJaxFor(message[1]).SourceElement();
    var txt = msg.join(" ")+": '"+script.text+"'";
    $mjlog.html(txt);
  });
  */
}); 

/* code for the properties sidepanel on the right */
/** collapser: stored height is used to track progress. */
function properties_collapser(evt) {
  evt.preventDefault();
  var $pb = $("#properties-body");
  var $pc = $("#properties-collapser");
  var $ph = $("#properties-header");
  var pb_w = $pb.width();
  $pb.animate({"height": "toggle", "width":  "toggle"}, 
    { duration: 2 * $pb.height(),
      step: function(now) { 
       var rot = 180 - 180 * (now/pb_w);
       $pc.css("-webkit-transform", "rotate("+rot+"deg)" );
       $pc.css("-moz-transform", "rotate("+rot+"deg)" );
       $pc.css("-o-transform", "rotate("+rot+"deg)" );
      },
      complete: function () {
        if ($pb.css("display") == "none") {
          $pc.css("-webkit-transform", "rotate(180deg)" );
        } else { 
          $pc.css("-webkit-transform", "rotate(0deg)" );
        }
      }
    }
  );
}


$(function() {
 $("#properties-header").click(function(evt) { properties_collapser(evt); });
 $("#properties-collapser").click(function(evt) { properties_collapser(evt); });
});

/* providing watermark examples in those forms, that have an 'example=...' attribute */
$(function () {
  $('input[example]').watermark($(this).attr('example'));
  $('textarea[example]').watermark($(this).attr('example'), {useNative:false});
});

/* javascript code for the knowledge db features */
// global counter, used to uniquely identify each help-output element
// that's necessary because the same knowl could be referenced several times
// on the same page
var knowl_id_counter = 0;
 
function knowl_click_handler($el, evnt) {
  evnt.preventDefault();
  
  // the knowl attribute holds the id of the knowl
  var knowl_id = $el.attr("knowl");
  // the uid is necessary if we want to reference the same content several times
  var uid = $el.attr("knowl-uid");
  var output_id = '#knowl-output-' + uid; 
  var $output_id = $(output_id);
 
  // if we already have the content, toggle visibility
  if ($output_id.length > 0) {
    $output_id.slideToggle("fast");
    $el.toggleClass("active");

  // otherwise download it
  } else { 
    $el.addClass("active");
    // create the element for the content, insert it after the one where the 
    // knowl element is included (e.g. inside a <h1> tag) (sibling in DOM)
    var idtag = "id='"+output_id.substring(1) + "'";
    $el.parent().after("<div class='knowl-output loading'" +idtag+ ">loading '"+knowl_id+"' …</div>");
 
    // "select" where the output is and get a hold of it 
    var $output = $(output_id);
    $output.show();
 
    $output.load('/knowledge/render/' + knowl_id, function(response, status, xhr) { 
      $output.removeClass("loading");
      if (status == "error") {
        $el.removeClass("active");
        $output.html("<div class='knowl-output error'>ERROR: " + xhr.status + " " + xhr.statusText + '</div>');
      } else if (status == "timeout") {
        $el.removeClass("active");
        $output.html("<div class='knowl-output error'>ERROR: timeout. " + xhr.status + " " + xhr.statusText + '</div>');
      } else {
        $output.hide();
        MathJax.Hub.Queue(['Typeset', MathJax.Hub, output_id.substring(1)]);
        // inside the inserted knowl might be more references: process them, attach the handler!
        $output.find("*[knowl]").each(function() {
           var $knowl = $(this);
           $knowl.attr("knowl-uid", knowl_id_counter);
           knowl_id_counter++;
           $knowl.click(function(evnt) { knowl_click_handler($knowl, evnt) });
        });
      }
      // in any case, reveal the new output after mathjax has finished
      MathJax.Hub.Queue([ function() { $output.slideDown("slow"); }]);
    });
  }
} //~~ end click handler for *[knowl] elements

/** for each one register a click handler that does the 
 *  download/show/hide magic. also register a unique ID to 
 *  avoid wrong behaviour if the same reference is used several times. */
$(function() {
  $("*[knowl]").each(function() { 
    $(this).attr("knowl-uid", knowl_id_counter);
    knowl_id_counter++;
  });
  $("*[knowl]").click(function(evt) {knowl_click_handler($(this), evt)});
});

//~~ end knowl js section
