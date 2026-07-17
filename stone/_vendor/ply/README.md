# Vendored PLY

Stone vendors the lexer and parser portions of PLY 3.11 so that it does not
depend on the unmaintained `ply` distribution from PyPI.

## Provenance

- Project: PLY (Python Lex-Yacc)
- Version: 3.11
- Author: David M. Beazley
- Source distribution: <https://pypi.org/project/ply/3.11/>
- PyPI wheel SHA-256:
  `096f9b8350b65ebd2fd1346b12452efe5b9607f7482813ffca50c22722a807ce`
- Vendored files: `__init__.py`, `lex.py`, and `yacc.py`

SHA-256 values before Stone's local security patch:

```text
b31ea204817ffd6288794d22c36592a12a8185c947179121053734c038a04d5f  __init__.py
6da6d12129c801fcc7a3b5aa2d8176a86092687d1bb4cf1ddf3b601da2b7480d  lex.py
105d38deb207ad72581ba8dc6f5e5323648bc1d0a834e4195c237fd4cdfe2389  yacc.py
```

## Stone modifications

Stone removes PLY's complete pickle-table feature from `yacc.py`, including:

- the `picklefile` argument to `yacc()`;
- `LRTable.read_pickle()`;
- `LRGeneratedTable.pickle_table()`; and
- all associated pickle read/write branches and configuration.

This removes the unsafe deserialization functionality described by
CVE-2025-56005. Stone does not load parser tables from pickle files.

The vendored code retains its original BSD license and copyright notices.
Changes to these files must preserve the removal of pickle support and pass
`test/test_vendored_ply.py`.
