import subprocess
import sys


def run_step(description, command):
    print("\n" + "=" * 60)
    print(description)
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, "-m", command],
        check=True
    )

    return result


def main():

    print("\n")
    print("=" * 60)
    print("        AEGIS SECURITY PIPELINE")
    print("=" * 60)

    # --------------------------------------------------
    # 1. Run ML anomaly detection
    # --------------------------------------------------

    run_step(
        "STEP 1: Running ML anomaly detection",
        "app.anomaly_detection"
    )

    # --------------------------------------------------
    # 2. Run behavioral detection
    # --------------------------------------------------

    run_step(
        "STEP 2: Running behavioral detection",
        "app.behavioral_detector"
    )

    # --------------------------------------------------
    # 3. Combine detection results
    # --------------------------------------------------

    run_step(
        "STEP 3: Combining security alerts",
        "app.combined_detector"
    )

    # --------------------------------------------------
    # 4. Load detection results into PostgreSQL
    # --------------------------------------------------

    run_step(
        "STEP 4: Updating PostgreSQL",
        "app.load_results_to_postgres"
    )

    # --------------------------------------------------
    # 5. Run 3-agent investigation
    # --------------------------------------------------

    run_step(
        "STEP 5: Running AI security investigation",
        "app.save_agent_report"
    )

    print("\n")
    print("=" * 60)
    print("        AEGIS PIPELINE COMPLETE")
    print("=" * 60)
    print("✓ Detection completed")
    print("✓ PostgreSQL updated")
    print("✓ AI investigation completed")
    print("✓ Security report saved")
    print("=" * 60)


if __name__ == "__main__":
    main()