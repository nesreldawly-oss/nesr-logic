# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Safe Static Analysis Guarantee

NESR Logic is strictly a static analysis tool:
- **No Code Execution**: Scanned source files are parsed into abstract syntax trees (AST) and tokenized using Python standard library modules (`ast`, `tokenize`). NESR Logic **never executes, evaluates, imports, or runs** scanned Python source files.
- **Zero Telemetry**: NESR Logic does not collect, transmit, or store source code or telemetry data. No network connections are made during scanning.
- **No External Dependencies**: NESR Logic relies entirely on the Python Standard Library, minimizing supply-chain attack surfaces.

## Reporting a Vulnerability

If you discover a security vulnerability in NESR Logic, please do not file a public issue. Instead, report it privately to the maintainers at:

`security@nesr-logic.org` (or via private GitHub Vulnerability Reporting).

You will receive an acknowledgment within 48 hours and regular updates on progress toward a fix.
