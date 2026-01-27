<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

    <xsl:mode on-no-match="shallow-copy"/>

    <xsl:template match="text()">
        <xsl:variable name="decoded">
            <xsl:value-of select="." disable-output-escaping="yes"/>
        </xsl:variable>

        <xsl:value-of select="replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            replace(
            $decoded,
            '&amp;aacute;', '&#225;'),
            '&amp;acirc;', '&#226;'),
            '&amp;Agrave;', '&#192;'),
            '&amp;agrave;', '&#224;'),
            '&amp;amp;', '&#38;'),
            '&amp;Ccedil;', '&#199;'),
            '&amp;ccedil;', '&#231;'),
            '&amp;Eacute;', '&#201;'),
            '&amp;eacute;', '&#233;'),
            '&amp;ecirc;', '&#234;'),
            '&amp;Egrave;', '&#200;'),
            '&amp;egrave;', '&#232;'),
            '&amp;euml;', '&#235;'),
            '&amp;hellip;', '&#8230;'),
            '&amp;iacute;', '&#237;'),
            '&amp;Icirc;', '&#206;'),
            '&amp;icirc;', '&#238;'),
            '&amp;iquest;', '&#191;'),
            '&amp;iuml;', '&#239;'),
            '&amp;laquo;', '&#171;'),
            '&amp;ldquo;', '&#8220;'),
            '&amp;lsquo;', '&#8216;'),
            '&amp;mdash;', '&#8212;'),
            '&amp;minus;', '&#8722;'),
            '&amp;nbsp;', '&#160;'),
            '&amp;ndash;', '&#8211;'),
            '&amp;ntilde;', '&#241;'),
            '&amp;oacute;', '&#243;'),
            '&amp;ocirc;', '&#244;'),
            '&amp;oelig;', '&#339;'),
            '&amp;ograve;', '&#242;'),
            '&amp;quot;', '&#34;'),
            '&amp;raquo;', '&#187;'),
            '&amp;rdquo;', '&#8221;'),
            '&amp;rsquo;', '&#8217;'),
            '&amp;uacute;', '&#250;'),
            '&amp;ucirc;', '&#251;'),
            '&amp;ugrave;', '&#249;'),
            '&amp;deg;', '&#176;'),
            '&amp;Ecirc;', '&#202;'),
            '&amp;micro;', '&#181;'),
            '&amp;Ocirc;', '&#212;'),
            '&amp;thinsp;', '&#8201;'),
            '&amp;bull;', '&#8226;'),
            '&amp;frac12;', '&#189;'),
            '&amp;frac14;', '&#188;'),
            '&amp;frac34;', '&#190;'),
            '&amp;middot;', '&#183;'),
            '&amp;times;', '&#215;')
            "/>
    </xsl:template>

</xsl:stylesheet>
