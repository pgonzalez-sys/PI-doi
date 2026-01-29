<?xml version="1.0" encoding="UTF-8" ?>
<xsl:stylesheet
  version="3.0"
  expand-text="yes"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:xs="http://www.w3.org/2001/XMLSchema"
  xmlns="http://www.crossref.org/schema/5.3.1"
  xmlns:jats="http://www.ncbi.nlm.nih.gov/JATS1"
  xmlns:fr="http://www.crossref.org/fundref.xsd"
  xmlns:mml="http://www.w3.org/1998/Math/MathML"
  xmlns:ai="http://www.crossref.org/AccessIndicators.xsd"
  xmlns:ali="http://www.niso.org/schemas/ali/1.0/"
  exclude-result-prefixes="xsl xs ali"
  >

  <!--* Convert from a variety of JATS-based formats to Crossref's schema.
      * Version: 0.97
      * Created: April 12th, 2022
      * $Id: JATS_to_Crossref.xsl,v 1.6 2023/04/25 01:03:08 lee Exp $
      *
      * TODO: Replace all bits with TODO and FINDOUT and EXPAND for content types unused in the source
      * Remove TESTING data
      * Figure out permissions/ali:ref license stuff
      * Figure out ref-list when it's webpages
      *
      * Delightful Computing 2022
      *
      *-->

  <xsl:mode on-no-match="shallow-copy" />

  <xsl:param name="depositor-email" as="xs:string" select=" '' "/>

  <!--* Override any publisher-id in the document if needed: *-->
  <xsl:param name="publisher-id-override" as="xs:string?" select=" () " />

  <xsl:output method="xml" indent="yes" media-type="application/xml" encoding="UTF-8" />

  <xsl:variable name="version" static="yes" as="xs:string" select=" '$Revision: 1.6 $' "/>

  <xsl:variable name="publisher-id" as="xs:string"
    select="(
      $publisher-id-override,
      /article/front/journal-meta/journal-id[@journal-id-type='publisher-id'],
      'unknown_publisher'
    )[1]" />

  <xsl:variable name="journal-meta"
    select="/article/front/journal-meta" as="element(journal-meta)" />

  <xsl:variable name="article-meta"
    select="/article/front/article-meta" as="element(article-meta)" />

  <xsl:template match="/">

    <!--* Some sanity tests first. If these fail, no point going forward.
        *-->

    <xsl:choose>
      <xsl:when test="not(/*:article)">
        <xsl:message terminate="yes">FAIL: Input is not an article - {base-uri(/*)}</xsl:message>
      </xsl:when>

      <xsl:when test="jats:article">
        <!--* input is in a jats namespace; remove the namespace
            * bindings and re-try
            *-->
        <xsl:variable name="no-namespace" as="document-node()">
          <xsl:apply-templates mode="remove-namespace" select="node()" />
        </xsl:variable>
        <xsl:apply-templates select="$no-namespace" />
      </xsl:when>

      <xsl:when test="not(/article)">
        <xsl:message terminate="yes">FAIL: Input has a namespace - {base-uri(/*)}</xsl:message>
      </xsl:when>

      <xsl:when test="empty($journal-meta)">
        <xsl:message terminate="yes">FAIL: No journal-meta element found</xsl:message>
      </xsl:when>

      <xsl:when test="empty($article-meta)">
        <xsl:message terminate="yes">FAIL: No article-meta element found</xsl:message>
      </xsl:when>

      <xsl:otherwise>
        <!--* all OK *-->
        <xsl:apply-templates select="article" />
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="article">

    <doi_batch xsi:schemaLocation="http://www.crossref.org/schema/5.3.1 https://www.crossref.org/schemas/crossref5.3.1.xsd">

      <xsl:comment>Generated via JATS_to_Crossref.xsl {$version}</xsl:comment>

      <head>
        <doi_batch_id>{
          $article-meta/article-id[@pub-id-type='doi']
        }</doi_batch_id>

        <timestamp>{
          format-dateTime(
            current-dateTime(),
            '[Y0001][M01][D01][H01][m01][s01]'
          )
        }
        </timestamp>

        <xsl:variable name="publisher-name" select="$journal-meta/publisher/publisher-name" />
        <depositor>
          <!--* We want the publisher name, which could be inside an
              * institution or institution-wrap/institution element.
              * We do not want an institution-id here.
              * The instuitution name potentially contains mixed content
              * (sup and sub elements)
              *-->
          <depositor_name>
            <xsl:apply-templates select="($publisher-name//institution, $publisher-name)[1]/node()" />
          </depositor_name>
	  <email_address>{$depositor-email}</email_address>
        </depositor>
        <registrant>
          <xsl:apply-templates select="($publisher-name//institution, $publisher-name)[1]/node()" />
        </registrant>
      </head>

      <body>
        <journal>
          <!--* defalt language to US English: *-->
          <journal_metadata language="{ (/article/@xml:lang, 'en_US')[1] }" reference_distribution_opts="any">
            <full_title>
              <xsl:apply-templates select="$journal-meta/journal-title-group/journal-title/node()" />
            </full_title>
            <xsl:apply-templates select="$journal-meta/issn"/>
          </journal_metadata>
          <journal_issue>
            <xsl:call-template name="publication_date"/>
          </journal_issue>
          <journal_article publication_type="full_text">
            <titles>
              <title>{normalize-space(string-join($article-meta/title-group/article-title/data(), ' '))}</title>
              <xsl:if test="article/front/article-meta/title-group/article-subtitle">
                <subtitle>{normalize-space(string-join(article/front/article-meta/title-group/article-subtitle/data(), ' '))}</subtitle>
              </xsl:if>
              <xsl:if test="article/front/article-meta/title-group/trans-title-group">
                <original_language_title>{normalize-space(string-join(article/front/article-meta/title-group/trans-title-group/trans-title/data(), ' '))}</original_language_title>
                  <xsl:if test="article/front/article-meta/title-group/trans-title-group/trans-subtitle">
                    <subtitle>{normalize-space(string-join(article/front/article-meta/title-group/trans-title-group/trans-subtitle/data(), ' '))}</subtitle>
                  </xsl:if>
              </xsl:if>
            </titles>
            <contributors>
              <xsl:apply-templates select="$article-meta/contrib-group/contrib" mode="contributors"/>
            </contributors>
            <xsl:for-each select="$article-meta/abstract">
              <xsl:call-template name="abstract"/>
            </xsl:for-each>

            <xsl:apply-templates select="$article-meta/pub-date" />

            <!--*
            <publisher_item>
              <item_number item_number_type="FINDOUT">FINDOUT</item_number>
            </publisher_item>
            *-->

            <!--* The schema says,
                * If a DOI is not participating in CrossMark,
                * FundRef data may be deposited as part of the journal_article metadata;
                * not sure this is going in teh right place - Liam
                *-->
	    <xsl:apply-templates select="$article-meta/funding-group" />

            <ai:program name="AccessIndicators">
	       <xsl:apply-templates select="$article-meta/permissions/license" />
            </ai:program>

            <doi_data>
              <doi>{$article-meta/article-id[@pub-id-type='doi']}</doi>
              <resource>https://doi.org/{$article-meta/article-id[@pub-id-type='doi']}</resource>
              <collection property="crawler-based">
                <item crawler="iParadigms">
                  <resource>https://www.crossref.org/faqs.html</resource>
                </item>
              </collection>
              <collection property="text-mining">
                <item>
                   <resource content_version="vor" mime_type="text/xml">https://www.crossref.org/example.xml</resource>
                </item>
              </collection>
            </doi_data>
            <!--* citation lists - the important part! *-->
            <citation_list>
              <xsl:apply-templates select="//ref-list/ref" />
            </citation_list>
          </journal_article>
        </journal>
      </body>
    </doi_batch>
  </xsl:template>

  <xsl:template match="permissions/license">
    <ai:license_ref>
      <xsl:value-of select="@*:href" />
    </ai:license_ref>
  </xsl:template>

  <xsl:template match="article-meta/funding-group">
    <xsl:apply-templates select="award-group" />
  </xsl:template>

  <xsl:template match="funding-group/award-group">
    <fr:program name="fundref">
      <fr:assertion name="fundgroup">
        <xsl:apply-templates select="funding-source" />
      </fr:assertion>
    </fr:program>
  </xsl:template>

  <xsl:template match="funding-group//funding-source">
    <fr:assertion name="funder_name">
      <xsl:value-of select="named-content[@content-type='funder-name']" />
      <xsl:apply-templates select="named-content[@content-type='funder-identifier']" />
    </fr:assertion>
    <xsl:apply-templates select="award-id" />
  </xsl:template>

  <xsl:template match="named-content[@content-type = 'funder-identifier']">
    <xsl:text>&#xa;</xsl:text><!--* newline *-->
    <fr:assertion name="funder_identifier">{.}</fr:assertion>
  </xsl:template>

  <xsl:template match="funding-group//award-id">
    <fr:assertion name="award_number">{.}</fr:assertion>
  </xsl:template>

  <xsl:template match="ref">
    <!--* Handle one reference. Do we need to manage duplicates? *-->
    <xsl:apply-templates select="mixed-citation" />
  </xsl:template>

  <xsl:template match="mixed-citation" priority="1" />
  <xsl:template match="mixed-citation[@publication-type = ('journal', 'book')]" priority="5">
    <!--* Ignore the text content, which will generally be spaces
        * and punctuation, and pick out what we want:
        *-->
    <citation key="{../@id}">
      <xsl:apply-templates select="*" />
    </citation>
  </xsl:template>

  <!--* delete unwanted elements: *-->
  <xsl:template match="mixed-citation/*" priority="0" />
  <xsl:template match="mixed-citation/text()" priority="0" />

  <xsl:template match="mixed-citation/source">
    <journal_title>
      <xsl:apply-templates/>
    </journal_title>
  </xsl:template>

  <xsl:template match="mixed-citation/article-title">
    <article_title>
      <xsl:apply-templates/>
    </article_title>
  </xsl:template>

  <xsl:template match="mixed-citation/volume">
    <volume>{.}</volume>
  </xsl:template>

  <xsl:template match="mixed-citation/person-group[@person-group-type = 'author']">
    <!--* a list of surname, given-names pairs with punctuation or "and"
        * between them.
        *-->
    <xsl:apply-templates select="string-name[1]" />
  </xsl:template>

  <xsl:template match="mixed-citation/person-group[@person-group-type = 'author']/string-name">
    <author>
      <xsl:value-of select="string-join((surname, given-names), ' ')" />
    </author>
  </xsl:template>

  <xsl:template match="mixed-citation/fpage">
    <first_page>{.}</first_page>
  </xsl:template>

  <xsl:template match="mixed-citation/lpage" />

  <xsl:template match="mixed-citation/year">
    <cYear>{.}</cYear>
  </xsl:template>

  <!--*
      * All customization for various flavors of JATS occur in the following templates.
      *-->

  <!--* Handle ISSNs *-->
  <xsl:template match="issn">
    <xsl:choose>
      <xsl:when test="$publisher-id eq 'oc'">
          <issn media_type="{current()/@publication-format}">{.}</issn>
      </xsl:when>
      <xsl:otherwise>
        <xsl:choose>
          <xsl:when test="current()/@pub-type='epub'">
            <issn media_type="electronic">{.}</issn>
          </xsl:when>
          <xsl:otherwise>
            <issn media_type="print">{.}</issn>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="date-body">
    <!--* iso-8601-date="2021-02-25"
        *                1234-67-90
        *
        * Allow this to take priority over sub-elements
        *-->

    <xsl:variable name="month" select="if (@iso-8601-date) then substring(@iso-8601-date, 6, 2) else month" as="xs:string?" />
    <xsl:variable name="day" select="if (@iso-8601-date) then substring(@iso-8601-date, 9, 2) else day" as="xs:string?" />
    <xsl:variable name="year" select="if (@iso-8601-date) then substring(@iso-8601-date, 1, 4) else year" as="xs:string?" />

    <xsl:if test="$month"><month>{$month}</month></xsl:if>
    <xsl:if test="$day"><day>{$day}</day></xsl:if>
    <xsl:if test="$year"><year>{$year}</year></xsl:if>
  </xsl:template>

  <!--* Handle publication date *-->
  <xsl:template name="publication_date" match="$article-meta">
    <xsl:choose>
      <xsl:when test="$publisher-id eq 'oc'">
        <publication_date media_type="online">
          <xsl:variable name="start" as="xs:string" select="$article-meta/permissions/license/ali:license_ref/@start_date" />
          <year><xsl:value-of select="substring($start,0,5)"/></year>
          <month><xsl:value-of select="substring($start,6,2)"/></month>
          <day><xsl:value-of select="substring($start,9,2)"/></day>
        </publication_date>
      </xsl:when>
      <xsl:otherwise>
	<xsl:apply-templates select="$article-meta/pub-date" />
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="front/article-meta/pub-date">
    <publication_date>
      <xsl:if test="@pub-type">
        <xsl:variable name="media_type_map" as="map(xs:string, xs:string)"
              select="map {
                  'online' : 'online',
                  'print' : 'print',
                  'epub' : 'online'
              }" />
        <xsl:attribute name="media_type"
              select="
                  if (@pub-type = ('online', 'print'))
                  then @pubtype
                  else 'other'" />
      </xsl:if>
      <xsl:call-template name="date-body" />
    </publication_date>
  </xsl:template>

  <!--* Handle contributors *-->
  <xsl:template mode="contributors" match="$article-meta/contrib-group/contrib">
    <!--* Get contributor role *-->
    <xsl:variable name="contributor_role" as="xs:string"
      select="if (@contrib-type = (
        'editor', 'chair', 'reviewer', 'review-assistant', 'stats-reviewer', 'reviewer-external', 'reader', 'translator')
      )
      then xs:string(@contrib-type)
      else 'author'
    "/>

    <!--* Check if first contributor or otherwise *-->
    <xsl:variable name="contributor_sequence" as="xs:string"
      select="if (position() eq 1) then 'first' else 'additional'" />

    <person_name contributor_role="{$contributor_role}" sequence="{$contributor_sequence}">
      <given_name>{string-join(name/given-names, ', ')}</given_name>
      <surname>{name/surname}</surname>
      <!--* handle all the different ways institutions are identified *-->
      <!--* should use templates for these *-->
      <xsl:choose>
        <!--* Handle inline affiliations. *-->
        <xsl:when test="aff">
          <affiliations>
            <xsl:for-each select="aff">
              <xsl:call-template name="affiliations"/>
            </xsl:for-each>
          </affiliations>
        </xsl:when>
        <!--* Handle linked affilitations. *-->
        <xsl:when test="xref[@ref-type='aff']">
          <affiliations>
            <xsl:call-template name="affiliations"/>
          </affiliations>
        </xsl:when>
        <xsl:otherwise>
          <!--* TODO use xsl:when-empty herre *-->
          <xsl:comment>No affiliations found</xsl:comment>
        </xsl:otherwise>
      </xsl:choose>

      <!--* Test for ORCID *-->
      <xsl:if test="contrib-id/@contrib-id-type = 'orcid'">
        <ORCID>
          <!--* optional authenticated attribute is true or false, daefault false *-->
          <xsl:copy-of select="@authenticated" />
          <xsl:value-of select="normalize-space(contrib-id)"/>
        </ORCID>
      </xsl:if>
    </person_name>
  </xsl:template>

  <xsl:template name="affiliations">
    <!--* Get each linked affiliation and parse it out. *-->
    <xsl:for-each select="xref[@ref-type='aff']">
      <xsl:variable name="currentID" select="@rid" as="xs:string"/>
      <xsl:variable name="aff" as="element(aff)?" select="$article-meta/aff[@id=$currentID]" />
      <xsl:choose>
         <xsl:when test="$aff/institution">
            <institution>
              <institution_name>{normalize-space(string-join($aff/institution/data(), ', '))}</institution_name>
              <xsl:if test="$aff/institution-id">
                <institution_id type="{$aff/institution-id/@institution-id-type}">
                  <xsl:value-of select="$aff/institution-id"/>
                </institution_id>
              </xsl:if>
              <!--* FINDOUT: There is no place for acronym in JATS *-->
              <!--institution_acronym></institution_acronym-->
              <xsl:if test="$aff/country">
                <institution_place>{$aff/country}</institution_place>
              </xsl:if>
              <xsl:if test="$aff/institution[@content-type='dept']">
                <institution_department>{$aff/institution[@content-type='dept']}</institution_department>
              </xsl:if>
            </institution>
          </xsl:when>
          <xsl:otherwise>
            <institution>
              <institution_name>{normalize-space(string-join($aff, ', '))}</institution_name>
            </institution>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="abstract" match="$article-meta/abstract//*"
    xmlns:jats="http://www.ncbi.nlm.nih.gov/JATS1">
    <xsl:element name="jats:{local-name()}">
      <xsl:apply-templates select="@* | node()"/>
    </xsl:element>
  </xsl:template>

  <!--* remove namespace bindings *-->
  <xsl:template mode="remove-namespace" match="*">
    <xsl:element name="{local-name()}">
      <xsl:apply-templates select="@*" />
      <xsl:apply-templates select="node()" mode="#current" />
    </xsl:element>
  </xsl:template>

</xsl:stylesheet>

