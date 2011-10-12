<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:cfdi="http://www.sat.gob.mx/cfd/3" xmlns:php="http://php.net/xsl">
<xsl:output method="html"/>
	<xsl:template match="/cfdi:Comprobante">
		<style type="text/css">
			.top {
				text-align: center;
				font-size: 12pt
			}
			table {
				font-size: 10pt;
				width: 100%;
			}
			th, td {
				width: 50%;
			}
			td.h {
				font-weight: bold;
				text-align: left;
			}
			td.box {
			}
			tr.bottom {
			}
			.center-txt {
				text-align: center;
			}
						table {
				width: 100%;
				font-size: 10pt;
			}
			th, td {
				text-align: center;
			}
			td.h {
				font-weight: bold;
			}
			td.l {
				text-align: right;
			}
			td.r {
				text-align: left;
			}
			.box {
			}
		</style>
		<div class="top" style="text-decoration: underline; 	text-align: center;">
			<xsl:text>CFDI - </xsl:text>
			<xsl:value-of select="@tipoDeComprobante" />
		</div>
		<table cellpadding="4" cellspacing="3">
			<tr>
				<th colspan="2">
					<div class="top">
						<xsl:apply-templates select="cfdi:Emisor"/>
					</div>
				</th>
			</tr>
			<tr class="center-txt">
				<td>
					<table>
						<tr>
							<td class="h l">Serie</td>
							<td class="h r"><xsl:value-of select="@serie"/></td>
						</tr>
						<tr>
							<td class="h l">Folio</td>
							<td class="h r"><xsl:value-of select="@folio"/></td>
						</tr>
						<tr>
							<td class="l">Fecha-Hora</td>
							<td class="r"><xsl:value-of select="@fecha"/></td>
						</tr>
						<tr>
							<td class="l">No. Aprobación</td>
							<td class="r"><xsl:value-of select="@noAprobacion"/></td>
						</tr>
						<tr>
							<td class="l">Año Aprobacion</td>
							<td class="r"><xsl:value-of select="@anoAprobacion"/></td>
						</tr>
						<tr>
							<td class="l">No. Certificado</td>
							<td class="r"><xsl:value-of select="@noCertificado"/></td>
						</tr>
					</table>
				</td>
				<td>
					<div class="top">
						<xsl:apply-templates select="cfdi:Receptor"/>
					</div>
					<table class="box">
						<tr>
							<td class="l h">Subtotal</td>
							<td class="r h">$<xsl:value-of select="php:function('number_format', number(@subTotal), 2)"/></td>
						</tr>
						<tr>
							<td class="l h">Descuento global</td>
							<td class="r h">
								<xsl:if test="@descuento">
									$<xsl:value-of select="php:function('number_format', number(@descuento), 2)"/>
								</xsl:if>
							</td>
						</tr>
						<tr>
							<td class="l h">
								<xsl:value-of select="cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado/@impuesto"/>
								<xsl:text> </xsl:text>
								<xsl:if test="cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado/@tasa">
									<xsl:value-of select="cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado/@tasa"/>%
								</xsl:if>
							</td>
							<td class="r h">
								<xsl:if test="cfdi:Impuestos/@totalImpuestosTrasladados">
									$<xsl:value-of select="php:function('number_format', number(cfdi:Impuestos/@totalImpuestosTrasladados), 2)"/>
								</xsl:if>
							</td>
						</tr>
						<tr style="font-size: 12pt">
							<td class="l h">TOTAL</td>
							<td class="r h">$<xsl:value-of select="php:function('number_format', number(@total), 2)"/></td>
						</tr>
					</table>
				</td>
			</tr>
		</table>
		<table cellspacing="0" cellpadding="2" border="1" nobr="true">
			<tr style="font-weight: bold;">
				<th width="8%">Id.</th>
				<th width="57%">Descripcion</th>
				<th width="9%">Cantidad</th>
				<th width="8%">Unidad</th>
				<th width="8%">Valor Unitario</th>
				<th width="10%">Importe</th>
			</tr>
			<xsl:for-each select="cfdi:Conceptos/cfdi:Concepto">
				<tr>
					<td><xsl:if test="@noIdentificacion"><xsl:value-of select="@noIdentificacion"/></xsl:if></td>
					<td style="text-align: left"><xsl:value-of select="@descripcion"/></td>
					<td><xsl:value-of select="@cantidad"/></td>
					<td><xsl:if test="@unidad"><xsl:value-of select="@unidad"/></xsl:if></td>
					<td style="text-align:right;"><xsl:value-of select="php:function('number_format', number(@valorUnitario) ,2)"/></td>
					<td style="text-align:right;">$<xsl:value-of select="php:function('number_format', number(@importe) ,2)"/></td>
				</tr>
			</xsl:for-each>
		</table>
	</xsl:template>

	<!--Direccion-->
	<xsl:template match="cfdi:DomicilioFiscal|cfdi:ExpedidoEn|cfdi:Domicilio">
		<xsl:if test="@calle"><xsl:value-of select="@calle"/></xsl:if>
		<xsl:if test="@noExterior"><xsl:text> Núm. </xsl:text><xsl:value-of select="@noExterior"/></xsl:if>
		<br/>
		<xsl:if test="@colonia"><xsl:text>Col. </xsl:text><xsl:value-of select="@colonia"/></xsl:if>
		<xsl:if test="@localidad"><xsl:text> Loc. </xsl:text><xsl:value-of select="@localidad"/></xsl:if>
		<br/>
		<xsl:if test="@referencia"><xsl:value-of select="@referencia"/><br/></xsl:if>
		<xsl:if test="@municipio"><xsl:value-of select="@municipio"/><xsl:text>, </xsl:text></xsl:if>
		<xsl:if test="@estado"><xsl:value-of select="@estado"/></xsl:if>
		<br/>
		<xsl:if test="@codigoPostal"><xsl:text>C.P. </xsl:text><xsl:value-of select="@codigoPostal"/><xsl:text> </xsl:text></xsl:if>
		<xsl:value-of select="@pais"/>
		<br/>
	</xsl:template>

	<!--Nombre y RFC-->
	<xsl:template match="cfdi:Emisor|cfdi:Receptor">
		<xsl:if test="@nombre"><xsl:value-of select="@nombre"/></xsl:if>
		<br/>
		<strong>RFC: </strong><xsl:value-of select="@rfc"/>
		<br/>
	</xsl:template>
</xsl:stylesheet>
