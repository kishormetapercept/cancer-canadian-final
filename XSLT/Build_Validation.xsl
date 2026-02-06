<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:math="http://www.w3.org/2005/xpath-functions/math"
    xmlns:ditaarch="http://dita.oasis-open.org/architecture/2005/"
    exclude-result-prefixes="xs math"
    version="3.0">
    
    <xsl:strip-space elements="*"/>
    <xsl:output indent="yes"/>
    
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@* except @class|node()"/>
        </xsl:copy>
    </xsl:template>
    
    
    <xsl:template match="concept[child::concept]">
        <xsl:text>
</xsl:text>
        <xsl:text disable-output-escaping="yes">&lt;!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd"&gt;</xsl:text>
        <xsl:text>
</xsl:text>        <concept>
            <xsl:if test="@id">
                <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
            </xsl:if>
            <xsl:if test="@xml:lang">
                <xsl:attribute name="xml:lang"><xsl:value-of select="@xml:lang"/></xsl:attribute>
            </xsl:if>
            <xsl:attribute name="rev"><xsl:value-of select="@rev"/></xsl:attribute>
    <xsl:if test="@outputclass">
        <xsl:attribute name="outputclass"><xsl:value-of select="@outputclass"/></xsl:attribute>
    </xsl:if>
            <xsl:apply-templates/>
        </concept>
    </xsl:template>
    
    
    <!-- Catch the metadescription <p> under conbody -->
    <xsl:template match="conbody/p[@outputclass='metadescription']|p[@outputclass='navigationtitle']|p[@outputclass='opengraphdescription']|p[@outputclass='opengraphtitle']|
        p[@outputclass='metatitle'][ancestor::concept/title[@outputclass='metatitle']]">
        <!-- Do nothing here so it doesn’t appear in conbody -->
    </xsl:template>
    
    <!-- After the title, insert the moved metadescription -->
    <xsl:template match="title">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
        
        <!-- Insert the new element only if a metadescription exists -->
        <xsl:if test="following-sibling::conbody/p[@outputclass='metadescription']">
            <shortdesc outputclass="metadescription">
                <xsl:value-of select="following-sibling::conbody/p[@outputclass='metadescription']"/>
            </shortdesc>
        </xsl:if>
    </xsl:template>
    
    
    <xsl:template match="concept[ancestor::concept]">
        <xsl:apply-templates/>
    </xsl:template>
    
    <xsl:template match="fig">
        <fig>
            <xsl:attribute name="id">
                <xsl:value-of select="substring-before(substring-after(child::image/@mediaid, '{'), '}')"/>
            </xsl:attribute>
            <xsl:choose>
                <xsl:when test="@outputclass">
                    <xsl:attribute name="outputclass"><xsl:value-of select="@outputclass"/></xsl:attribute>
                </xsl:when>
            </xsl:choose>
            <xsl:apply-templates/>
        </fig>
    </xsl:template>
    <xsl:template match="image">
        <image>
            <xsl:attribute name="placement">
                <xsl:value-of select="'break'"/>
            </xsl:attribute>
            <xsl:attribute name="href">
                <xsl:value-of select="@href"/>
            </xsl:attribute>
            <xsl:attribute name="href"><xsl:value-of select="substring-before(substring-after(@mediaid, '{'), '}')"/></xsl:attribute>
            <xsl:if test="@outputclass">
                <xsl:attribute name="outputclass">
                    <xsl:value-of select="@outputclass"/>
                </xsl:attribute>
            </xsl:if>
            <xsl:apply-templates/>
        </image>
    </xsl:template>
    
    <xsl:template match="ul">
        <ul><xsl:apply-templates/></ul>
    </xsl:template>
    <xsl:template match="li">
        <li><xsl:apply-templates/></li>
    </xsl:template>
    
    <xsl:template match="strong">
        <b><xsl:apply-templates/></b>
    </xsl:template>
    
    <xsl:template match="em">
        <i><xsl:apply-templates/></i>
    </xsl:template>
    
    <xsl:template match="p[@outputclass][child::p]|div|span|br[preceding::*[1][self::br]][not(ancestor::li)]|
        br[following-sibling::*[1][self::br][not(following-sibling::*)]][not(ancestor::li)]">
        <xsl:apply-templates/>
    </xsl:template>
    
    <xsl:template match="br[following-sibling::*[1][self::br][following-sibling::text()]][not(ancestor::li)]">
        <xsl:text disable-output-escaping="yes"><![CDATA[</p><p>]]></xsl:text>
    </xsl:template>
    
    <xsl:template match="br[following-sibling::*[1][self::br]][preceding-sibling::*[1][self::br]][not(ancestor::li)]"></xsl:template>
    
    
    <xsl:template match="br[ancestor::li]"><xsl:apply-templates/></xsl:template>
    
    
    <xsl:template match="p[child::*[1][self::xref[@id]]]">
        <p>
            <xsl:attribute name="id">
                <xsl:value-of select="child::xref/@id"/>
            </xsl:attribute>
            <xsl:apply-templates select="@*"/>
            <xsl:apply-templates/>
        </p>
    </xsl:template>
    <xsl:template match="xref[@id][parent::p]"/>
    <xsl:template match="p[not(child::*|node())]"/>
    <xsl:template match="@style"/>

</xsl:stylesheet>
