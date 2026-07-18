# Generated Test Fixtures

The unit tests build small temporary fixtures at runtime. No browser session,
credential, cookie, token, or real molecular coordinate is stored here.

Covered fixtures:

- 6,034-byte HTML response named as `.tgz`;
- gzip-compressed tar;
- Safari-style uncompressed tar;
- uncompressed tar carrying a `.tgz` suffix;
- corrupt tar and `.crdownload` partial;
- PDB Reader intermediate archive without GROMACS payload;
- path-traversal archive member;
- valid custom-ligand package with `lig.rtf + lig.prm`, no `lig.str`, and
  function-9 connectivity plus `forcefield.itp` dihedraltypes;
- standalone `lig.str` layout;
- package missing one optimized GROMACS dihedraltype.
