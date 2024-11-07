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
