<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:cfd="http://www.sat.gob.mx/cfd/2" xmlns:php="http://php.net/xsl">
	<xsl:output method="html"/>
	<xsl:template match="/cfd:Comprobante">
		<style type="text/css">
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
				text-align: left;
			}
			td.r {
				text-align: right;
			}
			.box {
				border: 1px solid black;
			}
		</style>
		<table cellspacing="0" cellpadding="2" border="1" nobr="true">
			<tr style="font-weight: bold;">
				<th width="8%">Id.</th>
				<th width="57%">Descripcion</th>
				<th width="9%">Cantidad</th>
				<th width="8%">Unidad</th>
				<th width="8%">Valor Unitario</th>
				<th width="10%">Importe</th>
			</tr>
			<xsl:for-each select="cfd:Conceptos/cfd:Concepto">
				<tr>
					<td><xsl:if test="@noIdentificacion"><xsl:value-of select="@noIdentificacion"/></xsl:if></td>
					<td style="text-align: left"><xsl:value-of select="@descripcion"/></td>
					<td><xsl:value-of select="@cantidad"/></td>
					<td><xsl:if test="@unidad"><xsl:value-of select="@unidad"/></xsl:if></td>
					<td><xsl:value-of select="@valorUnitario"/></td>
					<td><xsl:value-of select="php:function('number_format', number(@importe), 2)"/></td>
				</tr>
			</xsl:for-each>
		</table>
		<span style="font-size: 6pt"><br/></span>
		<table cellspacing="0" cellpadding="2">
			<tr>
				<td width="60%"  style="vertical-align:middle">
					<br/><br/>
					<strong><xsl:value-of select="@formaDePago"></xsl:value-of></strong>
				</td>
				<td width="40%">
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
								<xsl:value-of select="cfd:Impuestos/cfd:Traslados/cfd:Traslado/@impuesto"/>
								<xsl:text> </xsl:text>
								<xsl:if test="cfd:Impuestos/cfd:Traslados/cfd:Traslado/@tasa">
									<xsl:value-of select="cfd:Impuestos/cfd:Traslados/cfd:Traslado/@tasa"/>%
								</xsl:if>
							</td>
							<td class="r h">
								<xsl:if test="cfd:Impuestos/@totalImpuestosTrasladados">
									$<xsl:value-of select="php:function('number_format', number(cfd:Impuestos/@totalImpuestosTrasladados), 2)"/>
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
			<tr></tr><tr></tr>
			<tr>
				<td class="l" colspan="2">
					<strong>Sello</strong><br/>
					<span style="font-size: 8pt"><xsl:value-of select="@sello"/></span><br/>
				</td>
			</tr>
		</table>
	</xsl:template>
</xsl:stylesheet>
