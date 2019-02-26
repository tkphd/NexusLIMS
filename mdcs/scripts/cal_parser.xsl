<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
                xmlns:d="http://schemas.microsoft.com/ado/2007/08/dataservices"
                xmlns:m="http://schemas.microsoft.com/ado/2007/08/dataservices/metadata"
                xmlns:date="http://exslt.org/dates-and-times"
                extension-element-prefixes="date">
  <xsl:output method="xml"
              indent="yes"
              encoding="UTF-8"
              omit-xml-declaration="yes"/>
  <xsl:variable name="newline">
<xsl:text>
</xsl:text>
  </xsl:variable>
  <xsl:param name="date"/>
  <xsl:param name="user"/>
  <xsl:variable name="entrySelector">

  </xsl:variable>

  <xsl:template match="/feed">

    <xsl:choose>
      <xsl:when test="$date and $user">
        <xsl:apply-templates select="entry[date:date(./content/m:properties/d:StartTime) = $date and ./link/m:inline/entry/content/m:properties/d:UserName/text() = $user]" />
      </xsl:when>
      <xsl:when test="$date">
        <xsl:apply-templates select="entry[date:date(./content/m:properties/d:StartTime) = $date]" />
      </xsl:when>
      <xsl:when test="$user">
        <xsl:apply-templates select="entry[./link/m:inline/entry/content/m:properties/d:UserName/text() = $user]"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates select="entry" />
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

<xsl:template match="entry">
  <xsl:element name="event">
    <xsl:element name="dateSearched">
      <xsl:value-of select="$date"/>
    </xsl:element>
    <xsl:element name="userSearched">
      <xsl:value-of select="$user"/>
    </xsl:element>
    <xsl:element name="title">
      <xsl:value-of select="content/m:properties/d:Title"/>
    </xsl:element>
    <xsl:element name="instrument">
      <xsl:value-of select="substring-before(link[@rel='edit']/@title,'EventsItem')"/>
    </xsl:element>
    <xsl:element name="user">
      <xsl:element name="userName">
        <xsl:value-of select="link/m:inline/entry/content/m:properties/d:UserName"/>
      </xsl:element>
      <xsl:element name="name">
        <xsl:value-of select="link/m:inline/entry/content/m:properties/d:Name"/>
      </xsl:element>
      <xsl:element name="email">
        <xsl:value-of select="link/m:inline/entry/content/m:properties/d:WorkEMail"/>
      </xsl:element>
      <xsl:element name="phone">
        <xsl:value-of select="link/m:inline/entry/content/m:properties/d:WorkPhone"/>
      </xsl:element>
      <xsl:element name="office">
        <xsl:value-of select="link/m:inline/entry/content/m:properties/d:Office"/>
      </xsl:element>
      <xsl:element name="link">
        <xsl:value-of select="link/m:inline/entry/id"/>
      </xsl:element>
      <xsl:element name="userId">
        <xsl:value-of select="link/m:inline/entry/content/m:properties/d:Id"/>
      </xsl:element>
    </xsl:element>
    <xsl:element name="purpose">
      <xsl:value-of select="content/m:properties/d:ExperimentPurpose"/>
    </xsl:element>
    <xsl:element name="sampleDetails">
      <xsl:value-of select="content/m:properties/d:SampleDetails"/>
    </xsl:element>
    <xsl:element name="description">
      <xsl:value-of select="content/m:properties/d:Description"/>
    </xsl:element>
    <xsl:element name="startTime">
      <xsl:value-of select="content/m:properties/d:StartTime"/>
    </xsl:element>
    <xsl:element name="endTime">
      <xsl:value-of select="content/m:properties/d:EndTime"/>
    </xsl:element>
    <xsl:element name="link">
      <xsl:value-of select="id"/>
    </xsl:element>
    <xsl:element name="eventId">
      <xsl:value-of select="content/m:properties/d:Id"/>
    </xsl:element>
  </xsl:element>
<xsl:value-of select="$newline"/>
</xsl:template>

</xsl:stylesheet>
