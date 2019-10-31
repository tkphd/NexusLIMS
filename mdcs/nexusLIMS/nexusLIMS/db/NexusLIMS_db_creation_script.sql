-- Creator:       MySQL Workbench 8.0.18/ExportSQLite Plugin 0.1.0
-- Author:        Joshua Taillon
-- Caption:       NexusLIMS DB
-- Project:       Nexus Microscopy LIMS
-- Changed:       2019-10-31 10:10
-- Created:       2019-10-30 14:21
PRAGMA foreign_keys = OFF;

-- Schema: nexuslims_db
--   A database to hold information about the instruments and sessions logged in the Nexus Microscopy Facility
ATTACH "nexuslims_db.sqlite" AS "nexuslims_db";
BEGIN;
CREATE TABLE "nexuslims_db"."instruments"(
  "instrument_pid" VARCHAR(100) PRIMARY KEY NOT NULL,-- The unique identifier for an instrument in the Nexus Microscopy facility
  "api_url" TEXT NOT NULL,-- The calendar API url for this instrument
  "calendar_name" TEXT NOT NULL,-- The "user-friendly" name of the calendar for this instrument as displayed on the sharepoint resource (e.g. "FEI Titan TEM")
  "calendar_url" TEXT NOT NULL,-- "The URL to this instrument's web-accessible calendar on the sharepoint resource"
  "location" VARCHAR(100) NOT NULL,-- The physical location of this instrument (building and room number)
  "schema_name" TEXT NOT NULL,-- The name of instrument as defined in the Nexus Microscopy schema and displayed in the records
  "property_tag" VARCHAR(20) NOT NULL,-- The NIST property tag for this instrument
  "filestore_path" TEXT NOT NULL,-- The path (relative to the Nexus facility root) on the central file storage where this instrument stores its data
  CONSTRAINT "instrument_pid_UNIQUE"
    UNIQUE("instrument_pid"),
  CONSTRAINT "api_url_UNIQUE"
    UNIQUE("api_url"),
  CONSTRAINT "property_tag_UNIQUE"
    UNIQUE("property_tag"),
  CONSTRAINT "filestore_path_UNIQUE"
    UNIQUE("filestore_path")
);
INSERT INTO "instruments"("instrument_pid","api_url","calendar_name","calendar_url","location","schema_name","property_tag","filestore_path") VALUES('***REMOVED***', 'https://***REMOVED***/***REMOVED***/_vti_bin/ListData.svc/***REMOVED***', 'FEI HeliosDB', 'https://***REMOVED***/***REMOVED***/Lists/***REMOVED***/calendar.aspx', '***REMOVED***', 'FEI Helios', '***REMOVED***', './Aphrodite');
INSERT INTO "instruments"("instrument_pid","api_url","calendar_name","calendar_url","location","schema_name","property_tag","filestore_path") VALUES('***REMOVED***', 'https://***REMOVED***/***REMOVED***/_vti_bin/ListData.svc/***REMOVED***', 'FEI Quanta200', 'https://***REMOVED***/***REMOVED***/Lists/***REMOVED***/calendar.aspx', '***REMOVED***', 'FEI Quanta200', '***REMOVED***', './Quanta');
INSERT INTO "instruments"("instrument_pid","api_url","calendar_name","calendar_url","location","schema_name","property_tag","filestore_path") VALUES('***REMOVED***', 'https://***REMOVED***/***REMOVED***/_vti_bin/ListData.svc/***REMOVED***', 'FEI Titan STEM', 'https://***REMOVED***/***REMOVED***/Lists/***REMOVED***/calendar.aspx', '***REMOVED***', 'FEI Titan STEM', '***REMOVED***', './643Titan');
INSERT INTO "instruments"("instrument_pid","api_url","calendar_name","calendar_url","location","schema_name","property_tag","filestore_path") VALUES('***REMOVED***', 'https://***REMOVED***/***REMOVED***/_vti_bin/ListData.svc/***REMOVED***', 'FEI Titan TEM', 'https://***REMOVED***/***REMOVED***/Lists/***REMOVED***/calendar.aspx', '***REMOVED***', 'FEI Titan TEM', '***REMOVED***', './Titan');
INSERT INTO "instruments"("instrument_pid","api_url","calendar_name","calendar_url","location","schema_name","property_tag","filestore_path") VALUES('***REMOVED***', 'https://***REMOVED***/***REMOVED***/_vti_bin/ListData.svc/***REMOVED***', 'Hitachi S4700', 'https://***REMOVED***/***REMOVED***/Lists/***REMOVED***/calendar.aspx', '***REMOVED***', 'Hitachi S4700', '***REMOVED***', './***REMOVED***');
INSERT INTO "instruments"("instrument_pid","api_url","calendar_name","calendar_url","location","schema_name","property_tag","filestore_path") VALUES('***REMOVED***', 'https://***REMOVED***/***REMOVED***/_vti_bin/ListData.svc/***REMOVED***', 'Hitachi-S5500', 'https://***REMOVED***/***REMOVED***/Lists/***REMOVED***/calendar.aspx', '***REMOVED***', 'Hitachi S5500', '***REMOVED***', './S5500');
INSERT INTO "instruments"("instrument_pid","api_url","calendar_name","calendar_url","location","schema_name","property_tag","filestore_path") VALUES('***REMOVED***', 'https://***REMOVED***/***REMOVED***/_vti_bin/ListData.svc/***REMOVED***', 'JEOL ***REMOVED***', 'https://***REMOVED***/***REMOVED***/Lists/***REMOVED***/calendar.aspx', '***REMOVED***', 'JEOL ***REMOVED***', '***REMOVED***', './JEOL3010');
INSERT INTO "instruments"("instrument_pid","api_url","calendar_name","calendar_url","location","schema_name","property_tag","filestore_path") VALUES('***REMOVED***', 'https://***REMOVED***/***REMOVED***/_vti_bin/ListData.svc/***REMOVED***', 'JEOL JSM7100', 'https://***REMOVED***/***REMOVED***/Lists/***REMOVED***/calendar.aspx', '***REMOVED***', 'JEOL JSM7100', '***REMOVED***', './7100Jeol');
INSERT INTO "instruments"("instrument_pid","api_url","calendar_name","calendar_url","location","schema_name","property_tag","filestore_path") VALUES('***REMOVED***', 'https://***REMOVED***/***REMOVED***/_vti_bin/ListData.svc/***REMOVED***', 'Philips CM30', 'https://***REMOVED***/***REMOVED***/Lists/***REMOVED***/calendar.aspx', '***REMOVED***', 'Philips CM30', '***REMOVED***', './***REMOVED***');
INSERT INTO "instruments"("instrument_pid","api_url","calendar_name","calendar_url","location","schema_name","property_tag","filestore_path") VALUES('***REMOVED***', 'https://***REMOVED***/***REMOVED***/_vti_bin/ListData.svc/***REMOVED***', 'Philips EM400', 'https://***REMOVED***/***REMOVED***/Lists/***REMOVED***/calendar.aspx', '***REMOVED***', 'Philips EM400', '***REMOVED***', './EM400');
CREATE TABLE "nexuslims_db"."session_log"(
  "id_session_log" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
  "instrument" VARCHAR(100) NOT NULL,-- The instrument associated with this session (foreign key reference to the 'instruments' table)
  "timestamp" DATETIME NOT NULL,-- The date and time of the logged event
  "event_type" TEXT NOT NULL CHECK("event_type" IN('START', 'END')),-- The type of log for this session either "START" or "END"
  "record_status" TEXT NOT NULL CHECK("record_status" IN('COMPLETED', 'WAITING_FOR_END', 'TO_BE_BUILT')) DEFAULT 'WAITING_FOR_END',-- The status of the record associated with this session. One of 'WAITING_FOR_END' (has a start event, but no end event), 'TO_BE_BUILT' (session has ended, but record not yet built), or 'COMPLETED' (record has been built)
  "user" VARCHAR(50),-- The NIST "short style" username associated with this session (if known)
  CONSTRAINT "id_session_log_UNIQUE"
    UNIQUE("id_session_log"),
  CONSTRAINT "fk_instrument"
    FOREIGN KEY("instrument")
    REFERENCES "instruments"("instrument_pid")
    ON DELETE CASCADE
    ON UPDATE CASCADE
);
CREATE INDEX "nexuslims_db"."session_log.fk_instrument_idx" ON "session_log" ("instrument");
COMMIT;
