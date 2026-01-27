<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xinfo="http://ns.expertinfo.se/cms/xmlns/1.0"
    xmlns:l="local:functions" exclude-result-prefixes="xs l xinfo" version="2.0">

    <xsl:output indent="no" method="xml"/>

    <xsl:template match="node() | @*">
        <xsl:copy>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:copy>
    </xsl:template>
    
    <xsl:template match="content">
        <content>
            <xsl:choose>
                <xsl:when test="contains(., '&lt;') or contains(., '&amp;')">
                    <xsl:try>
                        <xsl:copy-of
                            select="parse-xml-fragment(
                            concat('&lt;root&gt;', ., '&lt;/root&gt;')
                            )/root/node()"
                        />
                        <xsl:catch>
                            <xsl:value-of select="." disable-output-escaping="yes"/>
                        </xsl:catch>
                    </xsl:try>
                </xsl:when>
                
                <xsl:otherwise>
                    <xsl:apply-templates/>
                </xsl:otherwise>
                
            </xsl:choose>
        </content>
    </xsl:template>
</xsl:stylesheet>