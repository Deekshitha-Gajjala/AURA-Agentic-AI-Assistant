from tools.pdf_tool import build_vectorstore


# ============================================================
# REBUILD PDF VECTORSTORE
# ============================================================

def rebuild_vectorstore():
    """
    Rebuild the AURA PDF vectorstore.
    """

    print("=" * 60)
    print("AURA - REBUILDING PDF VECTORSTORE")
    print("=" * 60)

    try:

        result = build_vectorstore()

        print()
        print("=" * 60)
        print("RESULT")
        print("=" * 60)

        print(result)

        # ----------------------------------------------------
        # Handle the result returned by pdf_tool.py
        # ----------------------------------------------------

        if isinstance(result, dict):

            if result.get("success") is False:

                print()
                print(
                    "Vectorstore rebuild FAILED."
                )

                return False

        print()
        print(
            "Vectorstore rebuild completed successfully."
        )

        return True

    except Exception as e:

        print()
        print("=" * 60)
        print("VECTORSTORE REBUILD ERROR")
        print("=" * 60)

        print(
            str(e)
        )

        print()
        print(
            "Vectorstore rebuild failed."
        )

        return False


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":

    success = rebuild_vectorstore()

    if not success:

        raise SystemExit(1)