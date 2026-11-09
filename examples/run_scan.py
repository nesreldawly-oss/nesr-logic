"""Example showing how to run nesr_logic programmatically."""
import pathlib
import nesr_logic


def main():
    examples_dir = pathlib.Path(__file__).parent
    print(f"Scanning directory: {examples_dir}\n")

    report = nesr_logic.scan(examples_dir)

    # 1. Print formatted terminal summary
    print(report.format_terminal())

    # 2. Print summary dictionary
    print("\nSummary Dictionary:")
    print(report.summary())


if __name__ == "__main__":
    main()
