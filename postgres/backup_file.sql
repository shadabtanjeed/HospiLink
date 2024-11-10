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
-- Name: bloodgroup; Type: TYPE; Schema: public; Owner: oblivious
--

CREATE TYPE public.bloodgroup AS ENUM (
    'A+',
    'A-',
    'B+',
    'B-',
    'AB+',
    'AB-',
    'O+',
    'O-'
);


ALTER TYPE public.bloodgroup OWNER TO oblivious;

--
-- Name: day_of_week; Type: TYPE; Schema: public; Owner: oblivious
--

CREATE TYPE public.day_of_week AS ENUM (
    'sunday',
    'monday',
    'tuesday',
    'wednesday',
    'thursday',
    'friday',
    'saturday'
);


ALTER TYPE public.day_of_week OWNER TO oblivious;

--
-- Name: medicine_type; Type: TYPE; Schema: public; Owner: oblivious
--

CREATE TYPE public.medicine_type AS ENUM (
    'tablet',
    'syrup',
    'injectable',
    'capsule',
    'cream'
);


ALTER TYPE public.medicine_type OWNER TO oblivious;

--
-- Name: users_type; Type: TYPE; Schema: public; Owner: oblivious
--

CREATE TYPE public.users_type AS ENUM (
    'patient',
    'doctor'
);


ALTER TYPE public.users_type OWNER TO oblivious;

--
-- Name: check_user_exists(character varying); Type: FUNCTION; Schema: public; Owner: oblivious
--

CREATE FUNCTION public.check_user_exists(p_username character varying) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
BEGIN
    -- Check if the username exists in the users table
    RETURN EXISTS (
        SELECT 1
        FROM users
        WHERE username = p_username
    );
END;
$$;


ALTER FUNCTION public.check_user_exists(p_username character varying) OWNER TO oblivious;

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
-- Name: login_user(character varying, character); Type: FUNCTION; Schema: public; Owner: oblivious
--

CREATE FUNCTION public.login_user(p_username character varying, p_password_hash character) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    stored_password_hash CHAR(128);
BEGIN
    -- retrieve the stored password hash 
    SELECT password_hash
    INTO stored_password_hash
    FROM users
    WHERE username = p_username;

    -- if passwords matches, return true
    IF stored_password_hash = p_password_hash THEN
        RETURN true;
    ELSE
        RETURN false;
    END IF;

END;
$$;


ALTER FUNCTION public.login_user(p_username character varying, p_password_hash character) OWNER TO oblivious;

--
-- Name: reset_user_password(character varying, character, character); Type: FUNCTION; Schema: public; Owner: oblivious
--

CREATE FUNCTION public.reset_user_password(p_username character varying, p_answer_hash character, p_new_password_hash character) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    is_verified BOOLEAN;
BEGIN
    -- verify the security answer
    is_verified := verify_security_question(p_username, p_answer_hash);

    -- if verified, update password
    IF is_verified THEN
        UPDATE users
        SET password_hash = p_new_password_hash
        WHERE username = p_username;

        RETURN true; -- successful
    ELSE
        RETURN false; -- security answer did not match
    END IF;
    
END;
$$;


ALTER FUNCTION public.reset_user_password(p_username character varying, p_answer_hash character, p_new_password_hash character) OWNER TO oblivious;

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
-- Name: show_security_question(character varying); Type: FUNCTION; Schema: public; Owner: oblivious
--

CREATE FUNCTION public.show_security_question(p_username character varying) RETURNS text
    LANGUAGE plpgsql
    AS $$
DECLARE
    security_question TEXT;
BEGIN
    -- retrieve security question
    SELECT users.security_question
    INTO security_question
    FROM users
    WHERE username = p_username;

    RETURN security_question;
END;
$$;


ALTER FUNCTION public.show_security_question(p_username character varying) OWNER TO oblivious;

--
-- Name: signup_doctor(character varying, character, character varying, public.day_of_week[], time without time zone, time without time zone); Type: FUNCTION; Schema: public; Owner: oblivious
--

CREATE FUNCTION public.signup_doctor(p_username character varying, p_phone_no character, p_specialization character varying, p_visiting_days public.day_of_week[], p_visiting_time_start time without time zone, p_visiting_time_end time without time zone) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO doctors (
        username,
        phone_no,
        specialization,
        visiting_days,
        visiting_time_start,
        visiting_time_end
    ) VALUES (
        p_username,
        p_phone_no,
        p_specialization,
        p_visiting_days,
        p_visiting_time_start,
        p_visiting_time_end
    );
END;
$$;


ALTER FUNCTION public.signup_doctor(p_username character varying, p_phone_no character, p_specialization character varying, p_visiting_days public.day_of_week[], p_visiting_time_start time without time zone, p_visiting_time_end time without time zone) OWNER TO oblivious;

--
-- Name: signup_patient(character varying, character, public.bloodgroup, text); Type: FUNCTION; Schema: public; Owner: oblivious
--

CREATE FUNCTION public.signup_patient(p_username character varying, p_phone_no character, p_blood_group public.bloodgroup, p_complexities text) RETURNS void
    LANGUAGE plpgsql
    AS $$
BEGIN
    INSERT INTO patients (
        username,
        phone_no,
        blood_group,
        complexities
    ) VALUES (
        p_username,
        p_phone_no,
        p_blood_group,
        p_complexities
    );
END;
$$;


ALTER FUNCTION public.signup_patient(p_username character varying, p_phone_no character, p_blood_group public.bloodgroup, p_complexities text) OWNER TO oblivious;

--
-- Name: signup_users(character varying, character, public.users_type, text, character, character, public.bloodgroup, text, character varying, public.day_of_week[], time without time zone, time without time zone); Type: FUNCTION; Schema: public; Owner: oblivious
--

CREATE FUNCTION public.signup_users(p_username character varying, p_password_hash character, p_users_type public.users_type, p_security_question text, p_security_answer_hash character, c_phone_no character, pt_blood_group public.bloodgroup, pt_complexities text, dc_specialization character varying, dc_visiting_days public.day_of_week[], dc_visiting_time_start time without time zone, dc_visiting_time_end time without time zone) RETURNS void
    LANGUAGE plpgsql
    AS $_$
BEGIN

    -- validate username: only lowercase letters, ., _, -, @
     IF p_username !~ '^[a-z0-9._\-@]+$' THEN
        RAISE EXCEPTION 'Invalid Username. Valid characters in username: a-z, 0-9, ., _, -, @';
    END IF;
    -- insert the user into the users table
    INSERT INTO users (
        username,
        password_hash,
        users_type,
        security_question,
        security_answer_hash
    ) VALUES (
        p_username,
        p_password_hash,
        p_users_type,
        p_security_question,
        p_security_answer_hash
    );

    -- based on users_type, call the specific function 
    IF p_users_type = 'patient' THEN
        PERFORM public.signup_patient(
            p_username,
            c_phone_no,
            pt_blood_group,
            pt_complexities
        );
    ELSIF p_users_type = 'doctor' THEN
        PERFORM public.signup_doctor(
            p_username,
            c_phone_no,
            dc_specialization,
            dc_visiting_days,
            dc_visiting_time_start,
            dc_visiting_time_end
        );
    ELSE
        RAISE EXCEPTION 'Invalid user type: %', p_users_type;
    END IF;

END;
$_$;


ALTER FUNCTION public.signup_users(p_username character varying, p_password_hash character, p_users_type public.users_type, p_security_question text, p_security_answer_hash character, c_phone_no character, pt_blood_group public.bloodgroup, pt_complexities text, dc_specialization character varying, dc_visiting_days public.day_of_week[], dc_visiting_time_start time without time zone, dc_visiting_time_end time without time zone) OWNER TO oblivious;

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

--
-- Name: verify_security_question(character varying, character); Type: FUNCTION; Schema: public; Owner: oblivious
--

CREATE FUNCTION public.verify_security_question(p_username character varying, p_answer_hash character) RETURNS boolean
    LANGUAGE plpgsql
    AS $$
DECLARE
    stored_answer_hash CHAR(128);
BEGIN
    -- retrieve the stored security answer
    SELECT security_answer_hash
    INTO stored_answer_hash
    FROM users
    WHERE username = p_username;

    -- return true if the answer hash matches
    RETURN stored_answer_hash = p_answer_hash;

END;
$$;


ALTER FUNCTION public.verify_security_question(p_username character varying, p_answer_hash character) OWNER TO oblivious;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO oblivious;

--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: oblivious
--

ALTER TABLE public.auth_group ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.auth_group_permissions (
    id bigint NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO oblivious;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: oblivious
--

ALTER TABLE public.auth_group_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO oblivious;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: oblivious
--

ALTER TABLE public.auth_permission ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_user; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.auth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL
);


ALTER TABLE public.auth_user OWNER TO oblivious;

--
-- Name: auth_user_groups; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.auth_user_groups (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.auth_user_groups OWNER TO oblivious;

--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: oblivious
--

ALTER TABLE public.auth_user_groups ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: oblivious
--

ALTER TABLE public.auth_user ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_user_user_permissions; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.auth_user_user_permissions (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_user_user_permissions OWNER TO oblivious;

--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: oblivious
--

ALTER TABLE public.auth_user_user_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


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
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO oblivious;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: oblivious
--

ALTER TABLE public.django_admin_log ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO oblivious;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: oblivious
--

ALTER TABLE public.django_content_type ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO oblivious;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: oblivious
--

ALTER TABLE public.django_migrations ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO oblivious;

--
-- Name: doctors; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.doctors (
    username character varying(25) NOT NULL,
    phone_no character(11) NOT NULL,
    visiting_days public.day_of_week[],
    visiting_time_start time without time zone,
    visiting_time_end time without time zone,
    specialization character varying(100)
);


ALTER TABLE public.doctors OWNER TO oblivious;

--
-- Name: hospital_info; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.hospital_info (
    hospital_location point
);


ALTER TABLE public.hospital_info OWNER TO oblivious;

--
-- Name: medicine; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.medicine (
    name character varying(50) NOT NULL,
    family_name character varying(50) NOT NULL,
    type public.medicine_type NOT NULL,
    manufacturer character varying(50),
    strength character varying(50) NOT NULL,
    manufacturing_date date,
    expiration_date date,
    quantity integer,
    price numeric(10,2),
    CONSTRAINT medicine_price_check CHECK ((price >= (0)::numeric)),
    CONSTRAINT medicine_quantity_check CHECK ((quantity >= 0))
);


ALTER TABLE public.medicine OWNER TO oblivious;

--
-- Name: patients; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.patients (
    username character varying(25) NOT NULL,
    phone_no character(11) NOT NULL,
    blood_group public.bloodgroup,
    complexities text
);


ALTER TABLE public.patients OWNER TO oblivious;

--
-- Name: user_authentication_user; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.user_authentication_user (
    id bigint NOT NULL,
    username character varying(255) NOT NULL,
    password_hash text NOT NULL,
    user_type character varying(255) NOT NULL,
    security_question text NOT NULL,
    security_answer_hash text NOT NULL
);


ALTER TABLE public.user_authentication_user OWNER TO oblivious;

--
-- Name: user_authentication_user_id_seq; Type: SEQUENCE; Schema: public; Owner: oblivious
--

ALTER TABLE public.user_authentication_user ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.user_authentication_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: oblivious
--

CREATE TABLE public.users (
    username character varying(25) NOT NULL,
    password_hash character(128) NOT NULL,
    users_type public.users_type NOT NULL,
    security_question text NOT NULL,
    security_answer_hash character(128) NOT NULL
);


ALTER TABLE public.users OWNER TO oblivious;

--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	2	add_permission
6	Can change permission	2	change_permission
7	Can delete permission	2	delete_permission
8	Can view permission	2	view_permission
9	Can add group	3	add_group
10	Can change group	3	change_group
11	Can delete group	3	delete_group
12	Can view group	3	view_group
13	Can add user	4	add_user
14	Can change user	4	change_user
15	Can delete user	4	delete_user
16	Can view user	4	view_user
17	Can add content type	5	add_contenttype
18	Can change content type	5	change_contenttype
19	Can delete content type	5	delete_contenttype
20	Can view content type	5	view_contenttype
21	Can add session	6	add_session
22	Can change session	6	change_session
23	Can delete session	6	delete_session
24	Can view session	6	view_session
25	Can add user	7	add_user
26	Can change user	7	change_user
27	Can delete user	7	delete_user
28	Can view user	7	view_user
\.


--
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
\.


--
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.auth_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.auth_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


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
John Sinha	B-	Invisible	2024-10-01 12:00:00	(90,25)	{01712335678}
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	auth	user
5	contenttypes	contenttype
6	sessions	session
7	user_authentication	user
\.


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2024-11-10 19:20:26.058853+00
2	auth	0001_initial	2024-11-10 19:20:26.387184+00
3	admin	0001_initial	2024-11-10 19:20:26.552803+00
4	admin	0002_logentry_remove_auto_add	2024-11-10 19:20:26.612118+00
5	admin	0003_logentry_add_action_flag_choices	2024-11-10 19:20:26.677786+00
6	contenttypes	0002_remove_content_type_name	2024-11-10 19:20:26.768995+00
7	auth	0002_alter_permission_name_max_length	2024-11-10 19:20:26.856133+00
8	auth	0003_alter_user_email_max_length	2024-11-10 19:20:26.932432+00
9	auth	0004_alter_user_username_opts	2024-11-10 19:20:26.998851+00
10	auth	0005_alter_user_last_login_null	2024-11-10 19:20:27.075875+00
11	auth	0006_require_contenttypes_0002	2024-11-10 19:20:27.138955+00
12	auth	0007_alter_validators_add_error_messages	2024-11-10 19:20:27.20914+00
13	auth	0008_alter_user_username_max_length	2024-11-10 19:20:27.293087+00
14	auth	0009_alter_user_last_name_max_length	2024-11-10 19:20:27.363879+00
15	auth	0010_alter_group_name_max_length	2024-11-10 19:20:27.433685+00
16	auth	0011_update_proxy_permissions	2024-11-10 19:20:27.50758+00
17	auth	0012_alter_user_first_name_max_length	2024-11-10 19:20:27.586214+00
18	sessions	0001_initial	2024-11-10 19:20:27.713766+00
19	user_authentication	0001_initial	2024-11-10 19:31:02.24804+00
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
dbalp91lugytdmotfu80gqj00bsarzux	.eJwdykEKwyAQBdC7_LWFkmblLqfoUsY6jZboiI7QEHL3kq7fO_CWll0gJdgDo3MrlBkWPVIgr1Q-zGGC-ZvTvV5YSRMXhUGNUtiVkT03WNzn6TFf228iwa1NRoXFcoPBS3Ld-Js0cYfFMyZlnOcPs8IsjQ:1tAFNf:xggQtxD4p7mIlvbVuOC5jMl9KRqNmNb6taZ0ekhzBOM	2024-11-24 21:21:59.630801+00
\.


--
-- Data for Name: doctors; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.doctors (username, phone_no, visiting_days, visiting_time_start, visiting_time_end, specialization) FROM stdin;
shahbuggy	12345678901	{monday,wednesday,friday}	09:00:00	17:00:00	Cardiology
dr_smith	98765432100	{monday,wednesday,friday}	09:00:00	17:00:00	Cardiology
shadabtanjeed	042342     	{monday,tuesday,wednesday}	03:13:00	09:13:00	Dentist
\.


--
-- Data for Name: hospital_info; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.hospital_info (hospital_location) FROM stdin;
(90.3936972,23.7184291)
\.


--
-- Data for Name: medicine; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.medicine (name, family_name, type, manufacturer, strength, manufacturing_date, expiration_date, quantity, price) FROM stdin;
Seclo	Omeprazole	tablet	Square Pharmaceuticals	20mg	2023-01-15	2025-01-15	100	12.00
Napa	Paracetamol	tablet	Beximco Pharmaceuticals	500mg	2023-02-10	2026-02-10	200	8.00
Losectil	Omeprazole	capsule	Incepta Pharmaceuticals	40mg	2023-03-05	2026-03-05	150	15.00
Xinc	Zinc	syrup	Square Pharmaceuticals	100ml	2023-04-12	2024-04-12	50	2.00
Maxpro	Esomeprazole	tablet	ACI Limited	40mg	2023-05-18	2025-05-18	100	11.00
Amdocal	Amlodipine	tablet	Square Pharmaceuticals	5mg	2023-06-22	2026-06-22	150	12.50
Monas	Montelukast	tablet	Eskayef Pharmaceuticals	10mg	2023-07-10	2026-07-10	120	14.50
Ciprocin	Ciprofloxacin	tablet	Beximco Pharmaceuticals	500mg	2023-08-15	2025-08-15	200	10.00
Filwel	Multivitamin	tablet	Incepta Pharmaceuticals	500mg	2023-09-20	2025-09-20	100	18.00
Neofloxin	Ciprofloxacin	syrup	Square Pharmaceuticals	100ml	2023-10-25	2024-10-25	50	2.50
Fexo	Fexofenadine	tablet	ACI Limited	120mg	2023-11-05	2025-11-05	100	12.00
Orcef	Cefixime	capsule	Renata Limited	200mg	2023-12-10	2025-12-10	200	17.50
Eromycin	Erythromycin	syrup	Beximco Pharmaceuticals	60ml	2024-01-15	2025-01-15	80	2.10
Levostat	Levofloxacin	tablet	Square Pharmaceuticals	500mg	2024-02-20	2026-02-20	100	19.00
Myosin	Azithromycin	tablet	Eskayef Pharmaceuticals	500mg	2024-03-25	2026-03-25	150	20.00
Meropen	Meropenem	injectable	ACI Limited	500mg	2024-04-30	2026-04-30	50	5.00
Renalox	Cefpodoxime	tablet	Incepta Pharmaceuticals	200mg	2024-05-05	2026-05-05	200	16.00
Azithrocin	Azithromycin	syrup	Square Pharmaceuticals	100ml	2024-06-10	2025-06-10	60	2.20
Epinal	Cetirizine	tablet	Beximco Pharmaceuticals	10mg	2024-07-15	2026-07-15	100	8.00
Pantonix	Pantoprazole	tablet	Square Pharmaceuticals	40mg	2024-08-20	2026-08-20	200	13.00
Aspra	Esomeprazole	capsule	Eskayef Pharmaceuticals	40mg	2024-09-25	2026-09-25	100	17.00
Histacin	Loratadine	tablet	ACI Limited	10mg	2024-10-10	2026-10-10	200	12.00
Aristobet	Betamethasone	cream	Beximco Pharmaceuticals	0.1%	2024-11-15	2025-11-15	30	2.50
Ceftron	Ceftriaxone	injectable	Incepta Pharmaceuticals	1g	2024-12-05	2026-12-05	50	4.00
Xtrazol	Lansoprazole	tablet	Square Pharmaceuticals	30mg	2025-01-15	2027-01-15	150	16.00
Celib	Celecoxib	tablet	Eskayef Pharmaceuticals	200mg	2025-02-20	2027-02-20	120	18.00
Xinc Plus	Zinc & Multivitamins	tablet	ACI Limited	500mg	2025-03-15	2027-03-15	200	19.00
Flagyl	Metronidazole	syrup	Beximco Pharmaceuticals	100ml	2025-04-05	2026-04-05	80	2.30
Tramin	Thiamine	tablet	Incepta Pharmaceuticals	100mg	2025-05-10	2027-05-10	100	10.00
Fluvir	Oseltamivir	capsule	Square Pharmaceuticals	75mg	2025-06-20	2027-06-20	150	35.00
Amlocard	Amlodipine	tablet	Eskayef Pharmaceuticals	5mg	2025-07-15	2028-07-15	200	12.00
Doloten	Paracetamol	tablet	Beximco Pharmaceuticals	500mg	2025-08-05	2028-08-05	250	9.00
Histamin	Chlorpheniramine	tablet	Square Pharmaceuticals	4mg	2025-09-10	2028-09-10	200	11.00
Seclo Kids	Omeprazole	syrup	ACI Limited	60ml	2025-10-15	2027-10-15	50	2.40
Monatil	Montelukast	tablet	Incepta Pharmaceuticals	10mg	2025-11-20	2028-11-20	150	17.00
Zempro	Esomeprazole	tablet	Square Pharmaceuticals	20mg	2025-12-25	2028-12-25	100	13.50
Zinex	Cefuroxime	tablet	Eskayef Pharmaceuticals	500mg	2026-01-15	2028-01-15	80	18.00
Bactol	Amoxicillin	capsule	Beximco Pharmaceuticals	500mg	2026-02-20	2028-02-20	200	11.00
Salbutam	Salbutamol	syrup	Square Pharmaceuticals	100ml	2026-03-25	2027-03-25	60	2.20
Corbex	Vitamin B Complex	tablet	Incepta Pharmaceuticals	500mg	2026-04-10	2028-04-10	200	15.00
Glucomin	Metformin	tablet	Square Pharmaceuticals	500mg	2026-05-20	2028-05-20	120	12.00
Xenax	Alprazolam	tablet	Beximco Pharmaceuticals	0.5mg	2023-10-01	2025-10-01	100	12.00
Rigel	Ranitidine	tablet	Incepta Pharmaceuticals	150mg	2026-11-15	2029-11-15	200	11.00
Pantor	Pantoprazole	tablet	ACI Limited	40mg	2026-12-05	2028-12-05	100	15.50
Hydrozole	Hydrocortisone	cream	Square Pharmaceuticals	1%	2027-01-15	2029-01-15	30	2.80
Chloromycetin	Chloramphenicol	capsule	Beximco Pharmaceuticals	250mg	2026-06-15	2028-06-15	200	16.00
Furadonin	Nitrofurantoin	tablet	Eskayef Pharmaceuticals	100mg	2026-07-20	2028-07-20	150	13.00
Metrogyl	Metronidazole	syrup	Square Pharmaceuticals	100ml	2026-08-25	2027-08-25	80	2.30
Pyridoxine	Vitamin B6	tablet	Incepta Pharmaceuticals	50mg	2026-09-05	2028-09-05	100	9.00
Vitamax	Multivitamins	tablet	ACI Limited	500mg	2026-10-10	2028-10-10	250	20.00
\.


--
-- Data for Name: patients; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.patients (username, phone_no, blood_group, complexities) FROM stdin;
john_doe	12345678901	A+	Diabetes
shadab_tanjeed	32523      	B+	Black
shadabtanjeed2	042342     	A-	White
\.


--
-- Data for Name: user_authentication_user; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.user_authentication_user (id, username, password_hash, user_type, security_question, security_answer_hash) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: oblivious
--

COPY public.users (username, password_hash, users_type, security_question, security_answer_hash) FROM stdin;
zoro	santoryu                                                                                                                        	doctor	Nothing Happened	The very very very strongest                                                                                                    
sanji	melorine                                                                                                                        	patient	love sick?	Real Men forgives womens' lies                                                                                                  
john_doe	hashed_password_example                                                                                                         	patient	What is your favorite color?	hashed_answer_example                                                                                                           
dr_smith	hashed_password_example                                                                                                         	doctor	What is your favorite subject?	hashed_answer_example                                                                                                           
shadabtanjeed	837ae03e1636ff7ca43d825a473be620babec1f82ba6a8d88351675b6b6578dbadc9fa51e3b136e8caf665c8d99b571bc07fde877c1ac464503aa9660ef966bc	doctor	Hospital Name?	6d736f3fa0965ed048cb2436559a5dd6878e7ed7e7e33a91cbf4135ca174dd949f3a40ceeb9ce6507bad89a43f0e036ee1d5fff798433efa30171b41d5672cc0
shadab_tanjeed	cbaf1ee32c13479b85ebdebf62c917c30bf9d2c487622da6428d5ba09d9e6dbf03662f55642f8b2e50881eeab09c8ea50413966d725105d1792761fea67d3b4a	patient	What are you?	5e319bb988ec9857ee5f8e77b0923e16424e72d0ce74c09a394011bd2f441cd0265575173f2699c0d76dac1d07d68e886485bb7d73dc7fdfd9df211499eebff2
shadabtanjeed2	837ae03e1636ff7ca43d825a473be620babec1f82ba6a8d88351675b6b6578dbadc9fa51e3b136e8caf665c8d99b571bc07fde877c1ac464503aa9660ef966bc	patient	what is your password?	cc8d8ce7b9b4ec7f5abd1a302f3b9b31cef8a4d291f56c800971467f506d93158f4985460ed77ac5baebc560661bf0970d8acb5c24f84908f91bd55c1dbb56d6
shahbuggy	Asus                                                                                                                            	doctor	Emon sadinotae ki amra ceyecilam?	Haa                                                                                                                             
\.


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oblivious
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oblivious
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oblivious
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 28, true);


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oblivious
--

SELECT pg_catalog.setval('public.auth_user_groups_id_seq', 1, false);


--
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oblivious
--

SELECT pg_catalog.setval('public.auth_user_id_seq', 1, false);


--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oblivious
--

SELECT pg_catalog.setval('public.auth_user_user_permissions_id_seq', 1, false);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oblivious
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 1, false);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oblivious
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 7, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oblivious
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 19, true);


--
-- Name: user_authentication_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: oblivious
--

SELECT pg_catalog.setval('public.user_authentication_user_id_seq', 1, false);


--
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups auth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups auth_user_groups_user_id_group_id_94350c0c_uniq; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_group_id_94350c0c_uniq UNIQUE (user_id, group_id);


--
-- Name: auth_user auth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions auth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_permission_id_14a6b632_uniq; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_permission_id_14a6b632_uniq UNIQUE (user_id, permission_id);


--
-- Name: auth_user auth_user_username_key; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_username_key UNIQUE (username);


--
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: doctors doctor_phone_no_key; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.doctors
    ADD CONSTRAINT doctor_phone_no_key UNIQUE (phone_no);


--
-- Name: doctors doctor_pkey; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.doctors
    ADD CONSTRAINT doctor_pkey PRIMARY KEY (username);


--
-- Name: medicine medicine_pkey; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.medicine
    ADD CONSTRAINT medicine_pkey PRIMARY KEY (name, strength);


--
-- Name: patients patient_phone_no_key; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patient_phone_no_key UNIQUE (phone_no);


--
-- Name: patients patient_pkey; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patient_pkey PRIMARY KEY (username);


--
-- Name: user_authentication_user user_authentication_user_pkey; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.user_authentication_user
    ADD CONSTRAINT user_authentication_user_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (username);


--
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: oblivious
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: oblivious
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: oblivious
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: oblivious
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- Name: auth_user_groups_group_id_97559544; Type: INDEX; Schema: public; Owner: oblivious
--

CREATE INDEX auth_user_groups_group_id_97559544 ON public.auth_user_groups USING btree (group_id);


--
-- Name: auth_user_groups_user_id_6a12ed8b; Type: INDEX; Schema: public; Owner: oblivious
--

CREATE INDEX auth_user_groups_user_id_6a12ed8b ON public.auth_user_groups USING btree (user_id);


--
-- Name: auth_user_user_permissions_permission_id_1fbb5f2c; Type: INDEX; Schema: public; Owner: oblivious
--

CREATE INDEX auth_user_user_permissions_permission_id_1fbb5f2c ON public.auth_user_user_permissions USING btree (permission_id);


--
-- Name: auth_user_user_permissions_user_id_a95ead1b; Type: INDEX; Schema: public; Owner: oblivious
--

CREATE INDEX auth_user_user_permissions_user_id_a95ead1b ON public.auth_user_user_permissions USING btree (user_id);


--
-- Name: auth_user_username_6821ab7c_like; Type: INDEX; Schema: public; Owner: oblivious
--

CREATE INDEX auth_user_username_6821ab7c_like ON public.auth_user USING btree (username varchar_pattern_ops);


--
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: oblivious
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: oblivious
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: oblivious
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: oblivious
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: blood_repo blood_group_validation; Type: TRIGGER; Schema: public; Owner: oblivious
--

CREATE TRIGGER blood_group_validation BEFORE INSERT ON public.blood_repo FOR EACH ROW EXECUTE FUNCTION public.validate_blood_group();


--
-- Name: blood_repo validate_phone_no_trigger; Type: TRIGGER; Schema: public; Owner: oblivious
--

CREATE TRIGGER validate_phone_no_trigger BEFORE INSERT OR UPDATE ON public.blood_repo FOR EACH ROW EXECUTE FUNCTION public.validate_phone_no();


--
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups auth_user_groups_group_id_97559544_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_group_id_97559544_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups auth_user_groups_user_id_6a12ed8b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: doctors fk_doctor_username; Type: FK CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.doctors
    ADD CONSTRAINT fk_doctor_username FOREIGN KEY (username) REFERENCES public.users(username);


--
-- Name: patients fk_patient_username; Type: FK CONSTRAINT; Schema: public; Owner: oblivious
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT fk_patient_username FOREIGN KEY (username) REFERENCES public.users(username);


--
-- PostgreSQL database dump complete
--

