--
-- PostgreSQL database dump
--

-- Dumped from database version 17.0
-- Dumped by pg_dump version 17.0 (Debian 17.0-1+b2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: donated(character varying); Type: PROCEDURE; Schema: public; Owner: oblivious
--

CREATE PROCEDURE public.donated(IN donor character varying)
    LANGUAGE plpgsql
    AS $$
BEGIN
    UPDATE blood_repo
    SET last_donation = NOW()
    WHERE name = donor;
END;
$$;


ALTER PROCEDURE public.donated(IN donor character varying) OWNER TO oblivious;

--
-- Name: haversine_distance(point, point); Type: FUNCTION; Schema: public; Owner: oblivious
--

CREATE FUNCTION public.haversine_distance(point1 point, point2 point) RETURNS double precision
    LANGUAGE plpgsql IMMUTABLE
    AS $$
DECLARE
    lat1 FLOAT := radians(point1[0]);
    lon1 FLOAT := radians(point1[1]);
    lat2 FLOAT := radians(point2[0]);
    lon2 FLOAT := radians(point2[1]);
    dlat FLOAT := lat2 - lat1;
    dlon FLOAT := lon2 - lon1;
    a FLOAT;
    c FLOAT;
    r FLOAT := 6371; -- Earth's radius in kilometers
BEGIN
    -- Haversine formula
    a := sin(dlat / 2)^2 + cos(lat1) * cos(lat2) * sin(dlon / 2)^2;
    c := 2 * atan2(sqrt(a), sqrt(1 - a));
    RETURN r * c;
END;
$$;


ALTER FUNCTION public.haversine_distance(point1 point, point2 point) OWNER TO oblivious;

--
-- Name: search_donor(character); Type: FUNCTION; Schema: public; Owner: oblivious
--

CREATE FUNCTION public.search_donor(_blood_group character) RETURNS TABLE(name character varying, blood_group character varying, complexities text, last_donation timestamp without time zone, phone_no character[], approximate_distance double precision)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.name,
        b.blood_group,
        b.complexities,
        b.last_donation,
        b.phone_no,
        ROUND(CAST(haversine_distance(b.general_location, h.hospital_location) AS numeric), 2)::float AS approximate_distance
    FROM
        blood_repo b,
        hospital_info h
    WHERE
        b.blood_group = _blood_group
        AND b.last_donation <= NOW() - INTERVAL '3 months'
    ORDER BY
        approximate_distance ASC;
END;
$$;


ALTER FUNCTION public.search_donor(_blood_group character) OWNER TO oblivious;

--
-- Name: validate_blood_group(); Type: FUNCTION; Schema: public; Owner: oblivious
--

CREATE FUNCTION public.validate_blood_group() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Check if the blood_group is valid
    IF NEW.blood_group NOT IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') THEN
        RAISE EXCEPTION 'Invalid blood group: %', NEW.blood_group;
    END IF;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.validate_blood_group() OWNER TO oblivious;

--
-- Name: validate_phone_no(); Type: FUNCTION; Schema: public; Owner: oblivious
--

CREATE FUNCTION public.validate_phone_no() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    phone CHAR(11);
BEGIN
    -- Check if each phone number in the array is exactly 11 digits
    FOREACH phone IN ARRAY NEW.phone_no
    LOOP
        IF length(phone) != 11 THEN
            RAISE EXCEPTION 'Phone number % must be 11 digits long', phone;
        END IF;
    END LOOP;

    -- Ensure that the phone numbers are unique in the table
    IF EXISTS (
        SELECT 1
        FROM blood_repo
        WHERE NEW.phone_no && phone_no
    ) THEN
        RAISE EXCEPTION 'Phone number already exists';
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION public.validate_phone_no() OWNER TO oblivious;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: blood_repo; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.blood_repo (
    name character varying(50),
    blood_group character varying(3),
    complexities text,
    last_donation timestamp without time zone,
    general_location point,
    phone_no character(11)[]
);


ALTER TABLE public.blood_repo OWNER TO oblivious;

--
-- Name: hospital_info; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.hospital_info (
    hospital_location point
);


ALTER TABLE public.hospital_info OWNER TO oblivious;

--
-- Data for Name: blood_repo; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.blood_repo (name, blood_group, complexities, last_donation, general_location, phone_no) FROM stdin;
John Doe	A+	None	2024-10-01 12:00:00	(90.4125,23.8103)	{01712345678}
Jane Smith	O-	High blood pressure	2024-10-05 14:30:00	(90.3705,23.8108)	{01812345678,01723456789}
Alice Johnson	B+	Diabetes	2024-09-15 10:20:00	(89.1951,24.3634)	{01612345678}
Bob Brown	AB-	None	2024-08-20 09:15:00	(90.4561,23.8706)	{01912345678,01898765432}
Charlie Davis	O+	Asthma	2024-10-10 16:45:00	(90.2795,23.685)	{01698765432}
David Wilson	A-	None	2024-07-11 11:00:00	(91.2663,23.8103)	{01787654321}
Eva Martinez	B-	Heart condition	2024-06-30 15:10:00	(89.4951,23.8106)	{01865432109,01923456789}
Frank Harris	AB+	None	2024-05-25 17:30:00	(90.2274,23.8109)	{01745678901}
Grace Lee	O-	None	2024-04-22 13:25:00	(91.7514,22.8572)	{01987654321,01887654321}
Henry Walker	B+	None	2024-03-18 18:10:00	(91.0399,23.8463)	{01756789012}
Samuel Green	A+	None	2024-07-07 05:10:56.110917	(90.4125,23.8103)	{01712345578}
Ian Riley	AB+	Parent series man.	2024-03-24 21:15:24	(89.0804,23.5609)	{01546105463}
Joseph Meyer DVM	A-	Keep machine poor.	2024-05-28 23:02:18	(89.136,23.0716)	{70297425957}
Timothy Liu	AB+	Old site worry.	2024-04-19 10:26:36	(89.995,23.8286)	{90591277609,10974725645}
Alexander Reeves	AB-	Production detail seat involve.	2024-02-22 00:01:56	(89.7541,22.9447)	{11332268466}
Jeffrey Berger	O+	Five hospital.	2024-04-13 22:30:42	(89.0046,23.5987)	{18828087300}
Jason Acevedo	O-	His another.	2024-04-26 12:13:44	(90.798,23.7709)	{75875948432,25772154143,20609921045}
Brenda Peters	O+	Much six write such.	2024-02-15 08:41:19	(90.8755,23.624)	{20164953769}
Danielle Bush	B+	Dog almost.	2024-01-22 16:12:54	(89.5145,23.0369)	{01988391822,04710868615}
Melanie Barron MD	O+	Still scientist.	2024-05-10 06:43:15	(90.8366,23.052)	{01659285024,02136789001}
Rachel Green	A+	Condition diagnosis.	2024-03-04 10:20:30	(90.4563,23.5473)	{01564532211}
Christopher Tan	AB-	Some pain after.	2024-02-14 10:00:50	(89.7741,23.1292)	{01786421513,09327458912}
Elizabeth Lee	B-	Skin rash.	2024-04-08 08:35:55	(90.2132,22.859)	{01787465931}
Catherine Wang	O-	Asthma diagnosis.	2024-01-13 09:12:40	(89.9984,23.2655)	{01956223342}
Oliver Thomas	AB+	Fever.	2024-02-20 18:22:10	(89.6721,23.3441)	{01643629001}
Nathan Foster	O-	Chest pain.	2024-04-02 14:10:58	(90.119,23.6524)	{01475693421}
Ava Lopez	B+	Weight gain.	2024-05-03 11:23:09	(90.212,23.7451)	{01638571200,01905462287}
Oscar Harris	A+	Low energy.	2024-02-10 17:04:53	(89.3425,23.9547)	{01999865441}
Emma Davis	B+	Frequent headaches.	2024-04-17 16:42:37	(90.2123,23.9637)	{01981204572}
David Miller	O+	Insomnia.	2024-05-09 21:11:23	(90.5567,23.184)	{01859231892}
Sophia Johnson	A-	Mood swings.	2024-01-30 05:35:12	(89.7239,23.7654)	{01766491538,01958123450}
Michael Wilson	AB-	Painful joints.	2024-02-25 22:11:23	(90.4241,22.7689)	{01458931266}
Grace Green	O-	Poor appetite.	2024-03-30 08:47:33	(90.0198,23.5162)	{01956412678,01944538790}
Lucas Walker	B+	High stress.	2024-03-12 07:54:27	(89.9451,23.8971)	{01738952190}
Mia Martinez	AB+	Stomach ulcers.	2024-04-03 12:45:21	(89.7809,23.8741)	{01698574325}
John Black	O+	Fever.	2024-02-14 10:21:11	(89.4428,22.943)	{01967823411}
Natalie Collins	A-	Neck pain.	2024-05-22 15:27:42	(90.5394,23.751)	{01783746518,01978235488}
Zoe Wright	B+	Blood pressure.	2024-04-15 12:12:01	(90.1445,23.203)	{01873694201}
James Lee	AB+	Allergies.	2024-03-19 14:55:08	(89.8774,23.2687)	{01729183450,01894629530}
Emily Roberts	O-	Cough.	2024-02-27 17:42:11	(89.4387,23.8763)	{01966474589}
William Clark	A+	Weight loss.	2024-01-18 13:22:56	(90.3478,22.9645)	{01684629537}
valid User	O+	None	2024-10-01 12:00:00	(90.4125,23.8103)	{01712345688}
\.


--
-- Data for Name: hospital_info; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.hospital_info (hospital_location) FROM stdin;
(90.3936972,23.7184291)
\.


--
-- Name: blood_repo blood_group_validation; Type: TRIGGER; Schema: public; Owner: oblivious
--

CREATE TRIGGER blood_group_validation BEFORE INSERT ON public.blood_repo FOR EACH ROW EXECUTE FUNCTION public.validate_blood_group();


--
-- Name: blood_repo validate_phone_no_trigger; Type: TRIGGER; Schema: public; Owner: oblivious
--

CREATE TRIGGER validate_phone_no_trigger BEFORE INSERT OR UPDATE ON public.blood_repo FOR EACH ROW EXECUTE FUNCTION public.validate_phone_no();


--
-- PostgreSQL database dump complete
--

