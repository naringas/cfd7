<?php
/**
 * @file Contains the settings form
 */

/**
 * Admin form called from path 'admin/config/content/cfdr'
 **/
function cfdr_admin_form() {
  $form['cfdr_scan_path'] = array(
    '#title' => t('Path where to look for .xml files'),
    '#type' => 'textfield',
    '#description' => t('It is recomended to use a restrictive ".htaccess" file in this directory'),
    '#default_value' => variable_get('cfdr_scan_path', 'sites/default/cfd/new'),
  );
  $form['cfdr_move_path'] = array(
    '#title' => t('Path where to move scanned .xml files'),
    '#type' => 'textfield',
    '#description' => t('Must be different from <strong>Path where to look for .xml files</strong>'),
    '#default_value' => variable_get('cfdr_move_path', 'sites/default/cfd'),
  );
  $form['#validate'][] = 'cfdr_admin_form_validate';
  return system_settings_form($form);
}

function cfdr_admin_form_validate($form, &$form_state) {
  if ($form_state['values']['op'] != t('Reset to defaults')) {
    if (!file_prepare_directory($form_state['values']['cfdr_scan_path']))
      form_set_error('cfdr_scan_path', t('Invalid directory'));
    if (!file_prepare_directory($form_state['values']['cfdr_move_path']))
      form_set_error('cfdr_move_path', t('Invalid directory'));
  }
}
