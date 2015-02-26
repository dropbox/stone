Todo
====

- Introduce a file that imports all the necessary babel descriptions together.
    - Version should be specified in this file, or overwritten on the command line?
- Out of order type declarations.
- List(data_type=Float32) -> List(Float32)
- Add tuple type. Only needed for v1 endpoints (ex. delta)
  and then printed by the caller if desired.
- Switch symbol lookup in environment to dynamic lookup.
  - This lets us have circular references... as well as out of order declarations.
