function cfdr_ajax_complete(data, status) {
  jQuery('#throbber-' + this.cfdr_id).remove();
}
function cfdr_ajax_success() {
  jQuery('#cfdr_id-' + this.cfdr_id).css('border-color', 'green');
}
function cfdr_ajax_error() {
  jQuery('#cfdr_id-' + this.cfdr_id).css('border-color', 'red');
}
function cfdr_ajax_add_throbber(xhr, settings) {
  thrb_id = 'throbber-' + settings.cfdr_id;
  // test if there's a throbber and return false (stop request) if there is
  if (jQuery('#' + thrb_id).length > 0) {
    return false;
  }
  jQuery('#cfdr_id-' + settings.cfdr_id).after('<div id=' + thrb_id + ' style="float:none;display: inline-block; vertical-align: text-bottom;;" class="ajax-progress"><div class="throbber">&nbsp;</div></div>');
}
