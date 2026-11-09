import pathlib

def count_file(p: pathlib.Path):
    raw = p.read_text("utf-8")
    lines = raw.splitlines()
    nonblank_noncomment = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    return len(lines), len(nonblank_noncomment)

src = pathlib.Path("src/nesr_logic")
total_lines = 0
total_sloc = 0
for f in sorted(src.glob("*.py")):
    lines, sloc = count_file(f)
    print(f"{f.name:15}: {sloc:3d} SLOC / {lines:3d} total lines")
    total_lines += lines
    total_sloc += sloc

print("-" * 35)
print(f"{'Total':15}: {total_sloc:3d} SLOC / {total_lines:3d} total lines")
