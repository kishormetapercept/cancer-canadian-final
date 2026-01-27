<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:math="http://www.w3.org/2005/xpath-functions/math"
    exclude-result-prefixes="xs math"
    version="3.0">
    
    <!--<xsl:output indent="yes"/>-->
    <xsl:strip-space elements="*"/>
    <xsl:template match="field"/>
    
    <xsl:template match="item">
        <xsl:variable name="item_name" select="replace(@name, ' ', '_')"/>
        <xsl:variable name="created" select="substring-before(@created, 'T')"/>
        <xsl:variable name="concat" select="concat($item_name, '_', $created)"/>
        <xsl:text disable-output-escaping="yes">&lt;!DOCTYPE concept PUBLIC "-//OASIS//DTD DITA Concept//EN" "concept.dtd"&gt;</xsl:text>
        <concept id="{concat('X_', substring-before(substring-after(@id, '{'), '}'))}" xml:lang="{@language}" filename="{lower-case($concat)}.dita">
            <xsl:attribute name="rev"><xsl:value-of select="@version"/></xsl:attribute>
            <xsl:choose>
                <xsl:when test="descendant::field[@key='metatitle']">
                    <title outputclass="metatitle">
                        <xsl:copy-of select="descendant::field[@key='pagetitle']/child::content"/>
                    </title>
                </xsl:when>
                <xsl:when test="descendant::field[@key='textblocktitle']">
                    <title outputclass="textblocktitle">
                        <xsl:copy-of select="descendant::field[@key='textblocktitle']/child::content"/>
                    </title>
                </xsl:when>
                <xsl:when test="descendant::field[@key='cardtitle']">
                    <title outputclass="cardtitle">
                        <xsl:copy-of select="descendant::field[@key='cardtitle']/child::content"/>
                    </title>
                </xsl:when>
                <xsl:when test="descendant::field[@key='pagelinksblocktitle']">
                    <title outputclass="pagelinksblocktitle">
                        <xsl:copy-of select="descendant::field[@key='pagelinksblocktitle']/child::content"/>
                    </title>
                </xsl:when>
                <xsl:when test="descendant::field[@key='splitblocktitle']">
                    <title outputclass="pagelinksblocktitle">
                        <xsl:copy-of select="descendant::field[@key='splitblocktitle']/child::content"/>
                    </title>
                </xsl:when>
                <xsl:when test="descendant::field[@key='expandcollapsesectiontitle']">
                    <title outputclass="expandcollapsesectiontitle">
                        <xsl:copy-of select="descendant::field[@key='expandcollapsesectiontitle']/child::content"/>
                    </title>
                </xsl:when>
                <xsl:when test="descendant::field[@key='expandcollapseblocktitle']">
                    <title outputclass="expandcollapseblocktitle">
                        <xsl:copy-of select="descendant::field[@key='expandcollapseblocktitle']/child::content"/>
                    </title>
                </xsl:when>
                <xsl:when test="descendant::field[@key='logocardlisttitle']">
                    <title outputclass="logocardlisttitle">
                        <xsl:copy-of select="descendant::field[@key='logocardlisttitle']/child::content"/>
                    </title>
                </xsl:when>
                <xsl:when test="descendant::field[@key='cardswithctalisttitle']">
                    <title outputclass="cardswithctalisttitle">
                        <xsl:copy-of select="descendant::field[@key='cardswithctalisttitle']/child::content"/>
                    </title>
                </xsl:when>
                <xsl:when test="descendant::field[@key='pagetitle']">
                    <title outputclass="cardswithctalisttitle">
                        <xsl:copy-of select="descendant::field[@key='pagetitle']/child::content"/>
                    </title>
                </xsl:when>
                <xsl:when test="descendant::field[@key='coveosearchblocktitle']">
                    <title outputclass="coveosearchblocktitle">
                        <xsl:copy-of select="descendant::field[@key='coveosearchblocktitle']/child::content"/>
                    </title>
                </xsl:when>
                <xsl:when test="descendant::field[@key='textblocklistchildtitle']">
                    <title outputclass="textblocklistchildtitle">
                        <xsl:copy-of select="descendant::field[@key='textblocklistchildtitle']/child::content"/>
                    </title>
                </xsl:when>
                <xsl:when test="descendant::field[@key='expandcollapsesectiontitle']">
                    <title outputclass="expandcollapsesectiontitle">
                        <xsl:copy-of select="descendant::field[@key='expandcollapsesectiontitle']/child::content"/>
                    </title>
                </xsl:when>
                <xsl:when test="descendant::field[@key='articlecardlisttitle']">
                    <title outputclass="article-cardlist-title">
                        <xsl:copy-of select="descendant::field[@key='articlecardlisttitle']/child::content"/>
                    </title>
                </xsl:when>
                <xsl:when test="descendant::field[@key='contactoptiontitle']">
                    <title outputclass="contact_option_title">
                        <xsl:copy-of select="descendant::field[@key='contactoptiontitle']/child::content"/>
                    </title>
                </xsl:when>
                <xsl:when test="descendant::field[@key='coveosearchblocktitle']">
                    <title outputclass="coveo_search_block_title">
                        <xsl:copy-of select="descendant::field[@key='coveosearchblocktitle']/child::content"/>
                    </title>
                </xsl:when>
                <xsl:when test="descendant::field[@key='embedtitle']">
                    <title outputclass="embed_title">
                        <xsl:copy-of select="descendant::field[@key='embedtitle']/child::content"/>
                    </title>
                </xsl:when>
                
                <xsl:when test="descendant::field[@key='iframetitle']">
                    <title outputclass="iframetitle">
                        <xsl:copy-of select="descendant::field[@key='embedtitle']/child::content"/>
                    </title>
                </xsl:when>
                
                <xsl:when test="descendant::field[@key='mediablocksectiontitle']">
                    <title outputclass="mediablocksectiontitle">
                        <xsl:copy-of select="descendant::field[@key='mediablocksectiontitle']/child::content"/>
                    </title>
                </xsl:when>
                
                <xsl:when test="descendant::field[@key='publicationcardlisttitle']">
                    <title outputclass="publicationcardlisttitle">
                        <xsl:copy-of select="descendant::field[@key='publicationcardlisttitle']/child::content"/>
                    </title>
                </xsl:when>
                
                <xsl:when test="descendant::field[@key='publicationresourcetitle']">
                    <title outputclass="publicationresourcetitle">
                        <xsl:copy-of select="descendant::field[@key='publicationresourcetitle']/child::content"/>
                    </title>
                </xsl:when>
                
                <xsl:when test="descendant::field[@key='publicationtitle']">
                    <title outputclass="publicationtitle">
                        <xsl:copy-of select="descendant::field[@key='publicationtitle']/child::content"/>
                    </title>
                </xsl:when>
                
                <xsl:when test="descendant::field[@key='statisticblocktitle']">
                    <title outputclass="statisticblocktitle">
                        <xsl:copy-of select="descendant::field[@key='statisticblocktitle']/child::content"/>
                    </title>
                </xsl:when>
                
                <xsl:when test="descendant::field[@key='tabscarouselslidetitle']">
                    <title outputclass="tabscarouselslidetitle">
                        <xsl:copy-of select="descendant::field[@key='tabscarouselslidetitle']/child::content"/>
                    </title>
                </xsl:when>
                
                <xsl:when test="descendant::field[@key='textblocklistchildtitle']">
                    <title outputclass="textblocklistchildtitle">
                        <xsl:copy-of select="descendant::field[@key='textblocklistchildtitle']/child::content"/>
                    </title>
                </xsl:when>
                
                <xsl:otherwise>
                    <title>
                        <xsl:apply-templates select="./@name"/>
                    </title>
                </xsl:otherwise>
            </xsl:choose>
            <prolog>
                <critdates>
                    <created date="{$created}"/>
                </critdates>
                <metadata>
                    <keywords>
                        <keyword><xsl:value-of select="@key"/></keyword>
                        <keyword outputclass="parentid"><xsl:value-of select="@parentid"/></keyword>
                    </keywords>
                </metadata>
            </prolog>
            <xsl:apply-templates/>
        </concept>
    </xsl:template>
    
    <xsl:template match="fields">
        <conbody>
            <xsl:apply-templates/>
        </conbody>
    </xsl:template>
    
    <xsl:template match="field[@key='statisticblocktabletitle']">
        <p outputclass="statisticblocktabletitle">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='publicationcopyrightdate']">
        <p outputclass="publicationcopyrightdate">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='publicationnumber']">
        <p outputclass="publicationnumber">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    
    <xsl:template match="field[@key='cardcta']">
        <p outputclass="cardcta">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='tabscarouselslidecta']">
        <p outputclass="tabscarouselslidecta">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='embedblocktitle']">
        <p outputclass="embedblock_title">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    <xsl:template match="field[@key='iframeblocktitle']">
        <p outputclass="iframeblocktitle">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='glossarytermtitle']">
        <p outputclass="glossarytermtitle">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    
    <xsl:template match="field[@key='blockanchortitle']">
        <p outputclass="blockanchortitle">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='splitblockcta']">
        <p outputclass="splitblockcta">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='genericherocta']">
        <p outputclass="genericherocta">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='youtubevideo']">
        <p outputclass="youtubevideo">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='expandcollapsesectioncta']">
        <p outputclass="expandcollapsesectioncta">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='coveosearchblockdescription']">
        <p outputclass="coveosearchblockdescription">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='textblockcta']">
        <p outputclass="textblockcta">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='textblocklisttitle']">
        <p outputclass="textblocklisttitle">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='contactoptionsblocktitle']">
        <p outputclass="textblocklisttitle">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    
    
    <xsl:template match="field[@key='cardswithctalisttitle']">
        <p outputclass="cardswithctalist-title">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='articletitle']">
        <p outputclass="article-title">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='articlehubviewlessfilterslabel']">
        <p outputclass="articlehubviewlessfilterslabel">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='articlehubtitle']">
        <p outputclass="articlehubtitle">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='pagelinksblocklink']">
        <p outputclass="pagelinksblocklink">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='blockanchorid']">
        <p outputclass="blockanchorid">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='publicationnumber']">
        <p outputclass="publicationnumber">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='publicationresourcefile']">
        <p outputclass="publicationresourcefile">
            <xsl:copy-of select="./child::content"/>
        </p>
    </xsl:template>
    
    <xsl:template match="field[@key='cardimage']">
        <fig outputclass="cardimage">
            <xsl:copy-of select="./child::content"/>
        </fig>
    </xsl:template>
    <xsl:template match="field[@key='tabscarouselslideimage']">
        <fig outputclass="tabscarouselslideimage">
            <xsl:copy-of select="./child::content"/>
        </fig>
    </xsl:template>
    <xsl:template match="field[@key='publicationresourceimage']">
        <fig outputclass="publicationresourceimage">
            <xsl:copy-of select="./child::content"/>
        </fig>
    </xsl:template>
    <xsl:template match="field[@key='thumbnailimage']">
        <fig outputclass="thumbnailimage">
            <xsl:copy-of select="./child::content"/>
        </fig>
    </xsl:template>
    
    <xsl:template match="field[@key='opengraphimage']">
        <fig outputclass="opengraphimage">
            <xsl:copy-of select="./child::content"/>
        </fig>
    </xsl:template>
    <xsl:template match="field[@key='publicationimage']">
        <fig outputclass="publicationimage">
            <xsl:copy-of select="./child::content"/>
        </fig>
    </xsl:template>
    
    <xsl:template match="field[@key='youtubethumbnail']">
        <fig outputclass="youtubethumbnail">
            <xsl:copy-of select="./child::content"/>
        </fig>
    </xsl:template>
    
    <xsl:template match="field[@key='publicationcardlistcta']">
        <fig outputclass="publicationcardlistcta">
            <xsl:copy-of select="./child::content"/>
        </fig>
    </xsl:template>
    
    
    <xsl:template match="field[@key='quoteimage']">
        <fig outputclass="quoteimage">
            <xsl:copy-of select="./child::content"/>
        </fig>
    </xsl:template>
    
    <xsl:template match="field[@key='splitblockimage']">
        <fig outputclass="splitblockimage">
            <xsl:copy-of select="./child::content"/>
        </fig>
    </xsl:template>
    
    <xsl:template match="field[@key='pagefeaturedimage']">
        <fig outputclass="pagefeaturedimage">
            <xsl:copy-of select="./child::content"/>
        </fig>
    </xsl:template>
    
    <xsl:template match="field[@key='mediablockimage']">
        <fig outputclass="mediablockimage">
            <xsl:copy-of select="./child::content"/>
        </fig>
    </xsl:template>
    
    <xsl:template match="field[@key='articleimage']">
        <fig outputclass="articleimage">
            <xsl:copy-of select="./child::content"/>
        </fig>
    </xsl:template>
    
    <xsl:template match="field[@key='carddescription']|
        field[@key='pagedescription']|
        field[@key='textblockdescription']|
        field[@key='pagelinksblockdescription']|
        field[@key='splitblockdescription']|
        field[@key='navigationtitle']|
        field[@key='metadescription']|
        field[@key='opengraphtitle']|
        field[@key='opengraphdescription']|
        field[@key='metatitle']|
        field[@key='quote']|
        field[@key='recognition']|
        field[@key='expandcollapsesectiondescription']|
        field[@key='expandcollapseblockcontent']|
        field[@key='textblocklistdescription']|
        field[@key='textblocklistchilddescription']|
        field[@key='splitblockdescription']|
        field[@key='cardswithctalistdescription']|
        field[@key='statisticrowvalue']|
        field[@key='statisticrowlabel']|
        field[@key='articledescription']|
        field[@key='articlehubnoresultsmessage']|
        field[@key='contactoptiondescription']|
        field[@key='description']|
        field[@key='glossarytermdescription']|
        field[@key='iframeblockdescription']|
        field[@key='mediablocksectiondescription']|
        field[@key='publicationcardlistdescription']|
        field[@key='publicationdescription']|
        field[@key='statisticblockdescription']|
        field[@key='tabscarouselslidedescription']|
        field[@key='iframeurl']|
        field[@key='mediablockcaption']|
        field[@key='metasubject']|
        field[@key='logocardlistdescription']|
        field[@key='statisticheadinglabel']|
        field[@key='statisticheadingvalue']|
        field[@key='tabscarouselsectionlabel']|
        field[@key='tabscarouseltabslabel']|
        field[@key='textblocklistcta']|
        field[@key='splitblocktagline']">
        <p outputclass="{@key}">
            <xsl:copy-of select="./child::content"/>
        </p>
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
    
</xsl:stylesheet>
