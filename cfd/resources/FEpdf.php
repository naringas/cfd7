<?php
/*
 * @file
 * Custom class for PDF printing header footer
 */

class FEpdf extends TCPDF {
  protected $doc;
  protected $xsl;
  public function registerHeader($doc) {
    $this->doc = $doc;
    $xsl_header_file = drupal_get_path('module', 'cfd') . '/resources/cfd_header.xsl';
    $xsl_header = new DOMDocument();
    $xsl_header->load($xsl_header_file);
    $this->xsl = new XSLTProcessor();
    $this->xsl->importStylesheet($xsl_header);
  }

  public function Header() {
    $this->xsl->setParameter('', 'pageNumber', $this->getPage());
    $this->writeHTML($this->xsl->transformToXml($this->doc));
    $this->SetTopMargin($this->getY() - 3);
  }

  public function Footer() {
    $this->setY(284);
    $this->SetFontSize(11);
    $this->writeHTML('<strong>Este documento es una impresion de un Comprobante Fiscal Digital.</strong>', TRUE, FALSE, FALSE, FALSE, 'C');
  }
}
