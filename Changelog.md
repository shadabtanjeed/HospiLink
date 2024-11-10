# Changes

## 07 Nov

### Tables

```text
                            Table "public.blood_repo"
      Column      |            Type             | Collation | Nullable | Default
------------------+-----------------------------+-----------+----------+---------
 name             | character varying(50)       |           |          |
 blood_group      | character varying(3)        |           |          |
 complexities     | text                        |           |          |
 last_donation    | timestamp without time zone |           |          |
 general_location | point                       |           |          |
 phone_no         | character(11)[]             |           |          |

Triggers:
    blood_group_validation BEFORE INSERT ON blood_repo FOR EACH ROW EXECUTE FUNCTION validate_blood_group()
    validate_phone_no_trigger BEFORE INSERT OR UPDATE ON blood_repo FOR EACH ROW EXECUTE FUNCTION validate_phone_no()
```

```text
                Table "public.hospital_info"
      Column       | Type  | Collation | Nullable | Default
-------------------+-------+-----------+----------+---------
 hospital_location | point |           |          |
```

### Functions and Procedures

```text
 Schema |         Name         |                                Result data type                         |    Argument data types     | Type
--------+----------------------+-------------------------------------------------------------------------+----------------------------+------
 public | donated              |                                                                         | IN donor character varying | proc
 public | haversine_distance   | double precision                                                        | point1 point, point2 point | func
 public | search_donor         | TABLE(name character varying, blood_group ............................) | _blood_group character     | func
 public | validate_blood_group | trigger                                                                 |                            | func
 public | validate_phone_no    | trigger                                                                 |                            | func
(5 rows)
```


## 11 Nov

### Tables
```text
                             Table "public.users"
        Column        |         Type          | Collation | Nullable | Default
----------------------+-----------------------+-----------+----------+---------
 username             | character varying(25) |           | not null |
 password_hash        | character(128)        |           | not null |
 users_type           | users_type            |           | not null |
 security_question    | text                  |           | not null |
 security_answer_hash | character(128)        |           | not null |
Indexes:
    "users_pkey" PRIMARY KEY, btree (username)
Referenced by:
    TABLE "doctors" CONSTRAINT "fk_doctor_username" FOREIGN KEY (username) REFERENCES users(username)
    TABLE "patients" CONSTRAINT "fk_patient_username" FOREIGN KEY (username) REFERENCES users(username)
```

```text
                        Table "public.patients"
    Column    |         Type          | Collation | Nullable | Default
--------------+-----------------------+-----------+----------+---------
 username     | character varying(25) |           | not null |
 phone_no     | character(11)         |           | not null |
 blood_group  | bloodgroup            |           |          |
 complexities | text                  |           |          |
Indexes:
    "patient_pkey" PRIMARY KEY, btree (username)
    "patient_phone_no_key" UNIQUE CONSTRAINT, btree (phone_no)
Foreign-key constraints:
    "fk_patient_username" FOREIGN KEY (username) REFERENCES users(username)
```

```text
                            Table "public.doctors"
       Column        |          Type          | Collation | Nullable | Default
---------------------+------------------------+-----------+----------+---------
 username            | character varying(25)  |           | not null |
 phone_no            | character(11)          |           | not null |
 visiting_days       | day_of_week[]          |           |          |
 visiting_time_start | time without time zone |           |          |
 visiting_time_end   | time without time zone |           |          |
 specialization      | character varying(100) |           |          |
Indexes:
    "doctor_pkey" PRIMARY KEY, btree (username)
    "doctor_phone_no_key" UNIQUE CONSTRAINT, btree (phone_no)
Foreign-key constraints:
    "fk_doctor_username" FOREIGN KEY (username) REFERENCES users(username)
```

```text
                           Table "public.medicine"
       Column       |         Type          | Collation | Nullable | Default
--------------------+-----------------------+-----------+----------+---------
 name               | character varying(50) |           | not null |
 family_name        | character varying(50) |           | not null |
 type               | medicine_type         |           | not null |
 manufacturer       | character varying(50) |           |          |
 strength           | character varying(50) |           | not null |
 manufacturing_date | date                  |           |          |
 expiration_date    | date                  |           |          |
 quantity           | integer               |           |          |
 price              | numeric(10,2)         |           |          |
Indexes:
    "medicine_pkey" PRIMARY KEY, btree (name, strength)
Check constraints:
    "medicine_price_check" CHECK (price >= 0::numeric)
    "medicine_quantity_check" CHECK (quantity >= 0)
```

### Functions and Procedures

```text
 Schema |         Name         |                              Result data type                                |                           Argument data types                                     | Type
--------+----------------------+------------------------------------------------------------------------------+-----------------------------------------------------------------------------------+------
 public | check_user_exists    | boolean                                                                      | p_username character varying                                                      | func
 public | donated              |                                                                              | IN donor character varying                                                        | proc
 public | haversine_distance   | double precision                                                             | point1 point, point2 point                                                        | func
 public | search_donor         | TABLE(name character varying, ..... , approximate_distance double precision) | _blood_group character                                                            | func
 public | signup_doctor        | void                                                                         | p_username character varying, .... ,p_visiting_time_end time without time zone    | func
 public | signup_patient       | void                                                                         | p_username character varying, .... , p_complexities text                          | func
 public | signup_users         | void                                                                         | p_username character varying, .... , pt_complexities text, time without time zone | func
 public | validate_blood_group | trigger                                                                      |                                                                                   | func
 public | validate_phone_no    | trigger                                                                      |                                                                                   | func
(9 rows)
```

