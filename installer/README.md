# Credit Ledger offline installer

Own-source Windows Forms program, compiled with the Windows .NET Framework
C# compiler. No third-party installer runtime, network access, shell commands,
startup entries or downloaded dependencies. The verified 0.22.11 WOTMOD is an
embedded resource. The GUI subsystem avoids a console window.

Run `build.ps1` from PowerShell. It verifies the explicit payload hash, builds
the executable and compiles/runs the engine tests against isolated synthetic
game directories. Test builds are not included in the public archive.

Discovery reads the Windows uninstall registry in both views and bounded
conventional game paths. Folder selection is always available. Installation
requires matching native realm, production ID, supported version, executable
location and active `paths.xml` mod path. XML external entities are prohibited.

Only `.wotmod` files whose `meta.xml` ID is exactly `local.credit_ledger` may
be replaced or removed. Unrecognized content at the intended filename stops
the operation. Newer versions stop downgrades. Reparse points are rejected.
Before writes, previous packages are backed up outside the game, their hashes
are verified and concurrent changes are checked again. Replacement uses a
same-directory staged file. On failure, changed package files are restored;
rollback failure reports the backup directory explicitly. A named mutex
prevents simultaneous installer operations. Player data is never read/written.

Limitations: unsigned executable; active version folder only; no background
updates; supports the explicit 2.4.1.0/2.4.1.1 NA/EU/ASIA contract only.
New game versions need a reviewed compatibility update and rebuilt installer.
WGMods publication/approval of this executable is separate from mod approval.
