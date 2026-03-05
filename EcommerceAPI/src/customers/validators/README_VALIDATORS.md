Your validator layer becomes:

    structure validation
          ↓
    API validation
          ↓
    business validation
          ↓
    DB validation



## What senior frameworks do

They create a single validation function that performs the entire verification pipeline.

Example:

`assert_customer_integrity()`

It performs:

    API fetch
    ↓
    API validation
    ↓
    DB fetch
    ↓
    DB validation

