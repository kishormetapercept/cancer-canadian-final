<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:math="http://www.w3.org/2005/xpath-functions/math"
    exclude-result-prefixes="xs math"
    version="3.0">
    
    <xsl:strip-space elements="*"/>
    
    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>
    
    <xsl:template match="concept">
        <xsl:result-document href="{@filename}">
            
            <xsl:text disable-output-escaping="yes">&lt;!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd"&gt;</xsl:text>
            <concept>
                <xsl:if test="@id">
                    <xsl:attribute name="id"><xsl:value-of select="@id"/></xsl:attribute>
                </xsl:if>
                <xsl:if test="@xml:lang">
                    <xsl:attribute name="xml:lang"><xsl:value-of select="@xml:lang"/></xsl:attribute>
                </xsl:if>
                <xsl:attribute name="rev"><xsl:value-of select="$doc/@version"/></xsl:attribute>
                <xsl:copy>
                    <xsl:apply-templates select="@*|node() except @class"/>
                </xsl:copy>
            </concept>
        </xsl:result-document>
    </xsl:template>
    
    <xsl:variable name="filename" select="doc(concat(substring-before(base-uri(), 'xml.dita'), 'xml'))"/>
    
    <xsl:variable name="doc" select="$filename//item"/>
    <xsl:template match="conbody[not(preceding-sibling::prolog)]">
        <prolog>
            <critdates>
                <created date="{$doc/substring-before(@created, 'T')}"/>
            </critdates>
            <metadata>
                <keywords>
                    <keyword><xsl:value-of select="$doc/@key"/></keyword>
                    <keyword outputclass="parentid"><xsl:value-of select="$doc/@parentid"/></keyword>
                </keywords>
            </metadata>
        </prolog>
        <conbody>
            <xsl:apply-templates/>
        </conbody>
    </xsl:template>
    
    
    
    
    <xsl:template match="content[ancestor::concept]">
        <xsl:apply-templates/>
    </xsl:template>
    
    
    <xsl:template match="image">
        <image>
            <xsl:apply-templates select="@*"/>
            <xsl:attribute name="href"><xsl:value-of select="@mediaid"/></xsl:attribute>
            <xsl:apply-templates/>
        </image>
    </xsl:template>
    
    <xsl:template match="link">
        <xref>
            <xsl:choose>
                <xsl:when test="@linktype='external'">
                    <xsl:attribute name="href">
                        <xsl:value-of select="@url"/>
                    </xsl:attribute>
                    <xsl:attribute name="format">
                        <xsl:value-of select="'html'"/>
                    </xsl:attribute>
                    <xsl:attribute name="scope">
                        <xsl:value-of select="'external'"/>
                    </xsl:attribute>
                </xsl:when>
                <xsl:when test="@linktype='media'">
                    <xsl:attribute name="href">
                        <xsl:value-of select="@id"/>
                    </xsl:attribute>
                </xsl:when>
                
                <xsl:when test="@linktype='internal'">
                    <xsl:attribute name="href">
                        <xsl:value-of select="@id"/>
                    </xsl:attribute>
                </xsl:when>
            </xsl:choose>
            <xsl:if test="@text">
                <xsl:value-of select="@text"/>
            </xsl:if>
            <xsl:apply-templates/>
        </xref>
    </xsl:template>
    
    <xsl:template match="a">
        <xref>
        <xsl:choose>
            <xsl:when test="starts-with(@href, '~/link.aspx?')">
                <xsl:attribute name="href">
                    <xsl:value-of select="concat('#X_', substring-after(@href, '~/link.aspx?_id='))"/>
                </xsl:attribute>
            </xsl:when>
            <xsl:when test="@name">
                <xsl:attribute name="name">
                    <xsl:value-of select="@name"/>
                </xsl:attribute>
            </xsl:when>
            <xsl:otherwise>
                <xsl:attribute name="href">
                    <xsl:value-of select="@href"/>
                </xsl:attribute>
                <xsl:attribute name="format">
                    <xsl:value-of select="'html'"/>
                </xsl:attribute>
                <xsl:attribute name="scope">
                    <xsl:value-of select="'external'"/>
                </xsl:attribute>
            </xsl:otherwise>
        </xsl:choose>
        </xref>
    </xsl:template>
    
    <xsl:template match="ul">
        <ul>
            <xsl:apply-templates/>
        </ul>
    </xsl:template>
    
    <xsl:template match="ol">
        <ol>
            <xsl:apply-templates/>
        </ol>
    </xsl:template>

</xsl:stylesheet>
