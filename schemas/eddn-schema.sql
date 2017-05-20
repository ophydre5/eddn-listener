--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: eddn; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON DATABASE "eddn" IS 'EDDN messages';


--
-- Name: SCHEMA "public"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA "public" IS 'standard public schema';


--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "plpgsql" WITH SCHEMA "pg_catalog";


--
-- Name: EXTENSION "plpgsql"; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION "plpgsql" IS 'PL/pgSQL procedural language';


SET search_path = "public", pg_catalog;

--
-- Name: message_search_insert(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION "message_search_insert"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$BEGIN NEW.message_search = lower(NEW.message::text)::jsonb; RETURN NEW; END;$$;


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: messages; Type: TABLE; Schema: public; Owner: -; Tablespace: 
--

CREATE TABLE "messages" (
    "id" integer NOT NULL,
    "received" timestamp without time zone DEFAULT "now"() NOT NULL,
    "message" "jsonb",
    "message_search" "jsonb",
    "blacklisted" boolean,
    "message_valid" boolean,
    "schema_test" boolean,
    "schemaref" "text",
    "gatewaytimestamp" timestamp without time zone
);


--
-- Name: messages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE "messages_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE "messages_id_seq" OWNED BY "messages"."id";


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY "messages" ALTER COLUMN "id" SET DEFAULT "nextval"('"messages_id_seq"'::"regclass");


--
-- Name: messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -; Tablespace: 
--

ALTER TABLE ONLY "messages"
    ADD CONSTRAINT "messages_pkey" PRIMARY KEY ("id");


--
-- Name: gatewaytimestamp; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX "gatewaytimestamp" ON "messages" USING "btree" ("gatewaytimestamp") WITH ("fillfactor"='50');


--
-- Name: message_idx; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX "message_idx" ON "messages" USING "gin" ("message");


--
-- Name: message_search; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX "message_search" ON "messages" USING "gin" ("message_search");


--
-- Name: received_index; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX "received_index" ON "messages" USING "btree" ("received") WITH ("fillfactor"='50');


--
-- Name: schemaref; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX "schemaref" ON "messages" USING "btree" ("schemaref") WITH ("fillfactor"='50');


--
-- Name: softwarename; Type: INDEX; Schema: public; Owner: -; Tablespace: 
--

CREATE INDEX "softwarename" ON "messages" USING "gin" (((("message" -> 'header'::"text") -> 'softwareName'::"text")));


--
-- Name: message_search_insert; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER "message_search_insert" BEFORE INSERT ON "messages" FOR EACH ROW EXECUTE PROCEDURE "message_search_insert"();


--
-- Name: public; Type: ACL; Schema: -; Owner: -
--

REVOKE ALL ON SCHEMA "public" FROM PUBLIC;
REVOKE ALL ON SCHEMA "public" FROM "postgres";
GRANT ALL ON SCHEMA "public" TO "postgres";
GRANT ALL ON SCHEMA "public" TO PUBLIC;


--
-- Name: messages; Type: ACL; Schema: public; Owner: -
--

REVOKE ALL ON TABLE "messages" FROM PUBLIC;
REVOKE ALL ON TABLE "messages" FROM "eddnadmin";
GRANT ALL ON TABLE "messages" TO "eddnadmin";
GRANT SELECT,INSERT ON TABLE "messages" TO "eddnlistener";


--
-- Name: messages_id_seq; Type: ACL; Schema: public; Owner: -
--

REVOKE ALL ON SEQUENCE "messages_id_seq" FROM PUBLIC;
REVOKE ALL ON SEQUENCE "messages_id_seq" FROM "eddnadmin";
GRANT ALL ON SEQUENCE "messages_id_seq" TO "eddnadmin";
GRANT UPDATE ON SEQUENCE "messages_id_seq" TO "eddnlistener";


--
-- PostgreSQL database dump complete
--

